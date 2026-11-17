"""Ingress negatives; fake transport here is not a Native runtime smoke."""
import importlib.util
from pathlib import Path

import httpx
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cloud_proxy", ROOT / "deploy/stage1/codespaces_gateway.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)
HOST = "synthetic-space-abcdef-8000.app.github.dev"


@pytest.fixture
def setup(tmp_path):
    ca = tmp_path / "ca.pem"
    ca.write_text("test transport does not perform TLS")
    seen = []

    def backend(request):
        seen.append(request)
        return httpx.Response(200, content="本機合成測試".encode(), headers=[
            ("content-type", "text/html; charset=utf-8"),
            ("set-cookie", "sunrise_a_sid=one; Secure; HttpOnly; SameSite=Strict"),
            ("set-cookie", "sunrise_a_login_csrf=two; Secure; HttpOnly"),
            ("content-security-policy", "default-src 'self'; script-src 'self'")])

    app = proxy.build_proxy(HOST, str(ca), transport=httpx.MockTransport(backend))
    with TestClient(app, base_url="https://" + HOST) as client:
        yield client, seen, ca


@pytest.mark.parametrize("headers", [
    {"host": "attacker.example"},
    {"origin": "https://attacker.example"},
    {"origin": "http://" + HOST},
    {"origin": "https://" + HOST + ".attacker.example"},
    {"sec-fetch-site": "cross-site"},
])
def test_unapproved_origins_never_reach_gateway(setup, headers):
    client, seen, _ = setup
    assert client.post("/auth/login", headers=headers).status_code == 403
    assert seen == []


def test_origin_translation_keeps_scope_and_auth_headers_but_not_tunnel_credentials(setup):
    client, seen, _ = setup
    response = client.post("/vault/v1/shells/one/search?synthetic=1", content=b"{}", headers={
        "origin": "https://" + HOST, "x-csrf-token": "synthetic-csrf",
        "idempotency-key": "synthetic-request", "x-forwarded-host": "attacker.example",
        "authorization": "Bearer synthetic-tunnel-token",
        "cookie": "github_tunnel=private; sunrise_a_sid=synthetic-session"})
    assert response.status_code == 200
    request = seen[0]
    assert str(request.url) == "https://127.0.0.1:18916/vault/v1/shells/one/search?synthetic=1"
    assert request.headers["origin"] == "https://127.0.0.1:18916"
    assert request.headers["x-csrf-token"] == "synthetic-csrf"
    assert request.headers["idempotency-key"] == "synthetic-request"
    assert "github_tunnel" not in request.headers["cookie"]
    assert "x-forwarded-host" not in request.headers
    assert "authorization" not in request.headers
    assert response.text == "Cloud 合成試用"
    assert len(response.headers.get_list("set-cookie")) == 2
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_large_body_and_wrong_methods_are_rejected_without_forwarding(setup):
    client, seen, _ = setup
    assert client.post("/auth/login", content=b"x" * (proxy.MAX_BODY + 1)).status_code == 413
    assert client.delete("/vault/v1/shells/one").status_code == 405
    assert seen == []


def test_upstream_outage_is_sanitized(setup):
    _, _, ca = setup
    def failed(request):
        raise httpx.ConnectError("synthetic private details")
    app = proxy.build_proxy(HOST, str(ca), transport=httpx.MockTransport(failed))
    with TestClient(app, base_url="https://" + HOST) as client:
        response = client.get("/admin")
    assert response.status_code == 503
    assert "private details" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_non_codespaces_host_and_missing_ca_fail_closed(tmp_path):
    ca = tmp_path / "ca.pem"
    ca.write_text("fixture")
    with pytest.raises(ValueError):
        proxy.build_proxy("attacker.example", str(ca))
    with pytest.raises(ValueError):
        proxy.build_proxy(HOST, str(tmp_path / "missing.pem"))
