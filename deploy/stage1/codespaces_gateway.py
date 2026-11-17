"""Private Codespaces ingress for the unchanged loopback A Gateway.

The forwarded port MUST remain GitHub-private. This adapter does not authenticate
GitHub identities itself and is not an approved public/production ingress.
"""
from pathlib import Path
import os
import re

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

MAX_BODY = 9 * 1024 * 1024
COOKIE_NAMES = {"sunrise_a_sid", "sunrise_a_login_csrf"}
REQUEST_HEADERS = {"accept", "content-type", "x-csrf-token", "idempotency-key", "sec-fetch-site"}
HOP_HEADERS = {"connection", "transfer-encoding", "keep-alive", "upgrade", "proxy-authenticate", "proxy-authorization", "te", "trailer"}


def build_proxy(public_host: str, ca_file: str, *, transport=None):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-8000\.app\.github\.dev", public_host):
        raise ValueError("An exact Codespaces port-8000 hostname is required")
    ca = Path(ca_file)
    if not ca.is_file() or ca.is_symlink():
        raise ValueError("A real local Gateway CA file is required")
    public_origin = "https://" + public_host
    backend = "https://127.0.0.1:18916"

    async def forward(request: Request):
        # Codespaces rewrites Host to localhost:8000. Trust its exact external
        # hostname only from the loopback tunnel, with Uvicorn proxy headers
        # disabled so client.host remains the actual TCP peer.
        host = request.headers.get("host", "").lower()
        tunnel = (
            host == "localhost:8000"
            and request.client is not None
            and request.client.host == "127.0.0.1"
            and request.headers.getlist("x-forwarded-host") == [public_host]
            and request.headers.getlist("x-forwarded-proto") == ["https"]
        )
        if len(request.headers.getlist("host")) != 1 or (host != public_host and not tunnel):
            return JSONResponse({"detail": "Unapproved trial hostname"}, status_code=403)
        origin = request.headers.get("origin")
        # The measured private tunnel also rewrites same-origin browser POSTs
        # to https://localhost:8000. Require its verified routing envelope AND
        # an explicit same-origin Fetch Metadata signal for that narrow form.
        rewritten_origin = (tunnel and origin == "https://localhost:8000"
            and request.headers.getlist("sec-fetch-site") == ["same-origin"])
        if len(request.headers.getlist("origin")) > 1 or (
                origin is not None and origin != public_origin and not rewritten_origin):
            return JSONResponse({"detail": "Cross-origin trial request denied"}, status_code=403)
        if request.headers.get("sec-fetch-site") not in (None, "none", "same-origin"):
            return JSONResponse({"detail": "Cross-site trial request denied"}, status_code=403)
        if request.url.path == "/":
            return RedirectResponse("/auth/login", status_code=303)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BODY:
                return JSONResponse({"detail": "Trial upload too large"}, status_code=413)
        headers = {k: v for k, v in request.headers.items() if k.lower() in REQUEST_HEADERS}
        if origin is not None:
            headers["origin"] = backend
        # Only Sunrise cookies cross the local TLS boundary, not GitHub/tunnel
        # credentials. A fresh client per request avoids shared session jars.
        cookies = {k: v for k, v in request.cookies.items() if k in COOKIE_NAMES}
        raw_path = request.scope.get("raw_path", request.url.path.encode()).decode("ascii")
        target = backend + raw_path
        if request.url.query:
            target += "?" + request.url.query
        try:
            async with httpx.AsyncClient(verify=str(ca), transport=transport, cookies=cookies,
                    trust_env=False, follow_redirects=False, timeout=100) as client:
                upstream = await client.request(request.method, target,
                    headers=headers, content=bytes(body))
        except httpx.HTTPError:
            return JSONResponse({"detail": "Trial Gateway unavailable"},
                status_code=503, headers={"Cache-Control": "no-store"})
        content = upstream.content
        if "text/html" in upstream.headers.get("content-type", ""):
            content = content.decode("utf-8").replace("本機合成測試", "Cloud 合成試用").replace(
                "本機合成環境", "Cloud 合成試用環境").encode("utf-8")
        response_headers = {k: v for k, v in upstream.headers.items()
            if k.lower() not in HOP_HEADERS | {"content-length", "content-encoding", "set-cookie"}}
        response = Response(content, status_code=upstream.status_code, headers=response_headers)
        for cookie in upstream.headers.get_list("set-cookie"):
            response.headers.append("set-cookie", cookie)
        response.headers["X-Sunrise-Environment"] = "CLOUD_SYNTHETIC_TRIAL"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["Cache-Control"] = "no-store"
        return response

    return Starlette(routes=[Route("/{path:path}", forward, methods=["GET", "POST"])])


def application():
    return build_proxy(os.environ["SUNRISE_TRIAL_HOST"], os.environ["VAULT_GATEWAY_CA_FILE"])
