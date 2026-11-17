"""A-only Supabase/PostgreSQL Cloud variant. Original local Gateway unchanged."""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote, urlsplit
from uuid import UUID

import httpx
import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent
VAULT = ROOT / "vault_assets"
MAX_PDF = 3 * 1024 * 1024
COOKIE = "sunrise_cloud_session"
LOGIN_COOKIE = "sunrise_cloud_login"
BUCKET = "sunrise-a-originals"


@dataclass(frozen=True)
class Config:
    url: str
    publishable_key: str
    service_key: str
    master_key: str
    admin_id: str
    admin_email: str
    origins: tuple[str, ...]
    schools: tuple[str, ...] = ("synthetic-cloud-stage1", "synthetic-cloud-negative")
    secure: bool = True

    @classmethod
    def environment(cls):
        primary = os.environ["CLOUD_PUBLIC_ORIGIN"]
        origins = [primary]
        if os.environ.get("VERCEL_URL"):
            origins.append("https://" + os.environ["VERCEL_URL"])
        return cls(os.environ["SUPABASE_URL"], os.environ["SUPABASE_PUBLISHABLE_KEY"],
            os.environ["SUPABASE_SERVICE_KEY"], os.environ["CLOUD_MASTER_KEY"],
            os.environ["CLOUD_ADMIN_ID"], os.environ["CLOUD_ADMIN_EMAIL"], tuple(origins))

    def validate(self):
        if not re.fullmatch(r"https://[a-z]{20}\.supabase\.co", self.url):
            raise ValueError("Exact Supabase project URL required")
        UUID(self.admin_id)
        if "@" not in self.admin_email or len(self.service_key) < 40 or len(self.publishable_key) < 30:
            raise ValueError("Cloud auth secrets required")
        if self.service_key == self.publishable_key:
            raise ValueError("A server credential must differ from the public key")
        raw = base64.urlsafe_b64decode(self.master_key)
        if len(raw) != 32:
            raise ValueError("Cloud encryption key required")
        if not self.origins or any(urlsplit(o).path or urlsplit(o).query or urlsplit(o).fragment
                or not urlsplit(o).netloc or urlsplit(o).username for o in self.origins):
            raise ValueError("Exact public origins required")
        if self.secure and any(not o.startswith("https://") for o in self.origins):
            raise ValueError("Public TLS required")
        if not self.secure and os.environ.get("VERCEL"):
            raise ValueError("Insecure test cookies cannot run on Vercel")
        return self

    def crypto(self, purpose):
        material = hmac.new(base64.urlsafe_b64decode(self.master_key), purpose.encode(), hashlib.sha256).digest()
        return Fernet(base64.urlsafe_b64encode(material))


class ShellInput(BaseModel):
    academic_year: str = Field(min_length=1, max_length=32)
    grade: str = Field(min_length=1, max_length=32)
    subject: str = Field(min_length=1, max_length=48)
    curriculum_stream: str = Field(min_length=1, max_length=48)

    @field_validator("academic_year", "grade", "subject", "curriculum_stream")
    @classmethod
    def clean(cls, value, info):
        value = plain(value, 48)
        if info.field_name == "academic_year" and not re.fullmatch(r"[A-Za-z0-9._ -]{1,32}", value):
            raise ValueError("Invalid academic year")
        return value


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def clean(cls, value):
        return plain(value, 300)


class SchoolInput(BaseModel):
    school_id: str = Field(min_length=1, max_length=100)


def plain(value, maximum):
    value = value.strip()
    if not value or len(value) > maximum or any(unicodedata.category(c) in ("Cc", "Cf") for c in value):
        raise ValueError("Nonempty visible text required")
    return value


class Provider:
    def __init__(self, cfg, transport=None):
        self.cfg, self.transport = cfg, transport
        self.keys, self.keys_at = [], 0

    async def request(self, method, path, *, token=None, server=False, body=None, data=None, headers=None):
        key = self.cfg.service_key if server else self.cfg.publishable_key
        auth = (None if key.startswith("sb_secret_") else key) if server else token
        head = {"apikey": key}
        if auth:
            head["Authorization"] = "Bearer " + auth
        head.update(headers or {})
        try:
            async with httpx.AsyncClient(transport=self.transport, trust_env=False, timeout=25,
                    follow_redirects=False) as client:
                response = await client.request(method, self.cfg.url + path,
                    headers=head, json=body, content=data)
        except httpx.HTTPError as error:
            raise HTTPException(503, "Cloud provider unavailable; outcome unconfirmed") from error
        if response.status_code >= 400:
            status = response.status_code if response.status_code in (400,401,403,404,409,413,422,429) else 503
            try:
                code = response.json().get("code", "")
                if isinstance(code,str) and re.fullmatch(r"PT(400|401|403|404|409|413|422|429)", code):
                    status = int(code[2:])
            except (ValueError, AttributeError):
                pass
            raise HTTPException(status, "Cloud request denied" if status < 500 else "Cloud operation unconfirmed")
        return response

    async def auth(self, method, path, token=None, body=None):
        r = await self.request(method, "/auth/v1/" + path, token=token, body=body)
        return r.json() if r.content else {}

    async def claims(self, token, *, mfa=True):
        try:
            head = jwt.get_unverified_header(token)
            if head.get("alg") not in ("ES256", "RS256", "EdDSA") or not head.get("kid"):
                raise ValueError("Asymmetric Supabase signing key required")
            if time.monotonic() - self.keys_at > 300 or not any(k.get("kid") == head["kid"] for k in self.keys):
                self.keys = (await self.auth("GET", ".well-known/jwks.json"))["keys"]
                self.keys_at = time.monotonic()
            matching = [k for k in self.keys if k.get("kid") == head["kid"]]
            if len(matching) != 1:
                raise ValueError("Unknown signing key")
            key = jwt.PyJWK.from_dict(matching[0], algorithm=head["alg"]).key
            claims = jwt.decode(token, key, algorithms=[head["alg"]], audience="authenticated",
                issuer=self.cfg.url + "/auth/v1", options={"require":["sub","exp","iat","aud","iss","session_id","aal"]})
            if claims["sub"] != self.cfg.admin_id or (mfa and claims["aal"] != "aal2"):
                raise ValueError("Admin MFA required")
            UUID(claims["session_id"])
        except (jwt.PyJWTError, ValueError, KeyError, TypeError) as error:
            raise HTTPException(401, "Valid administrator authentication required") from error
        user = await self.auth("GET", "user", token=token)
        if user.get("id") != self.cfg.admin_id:
            raise HTTPException(401, "Administrator identity mismatch")
        return claims

    async def rpc(self, name, state=None, **values):
        if state:
            values = {"p_actor":self.cfg.admin_id,"p_session":state["session_id"],
                "p_school":state["school_id"],"p_csrf":state["csrf"],**values}
        response = await self.request("POST", "/rest/v1/rpc/" + name, server=True, body=values)
        return response.json()

    async def original(self, path):
        return (await self.request("GET", "/storage/v1/object/authenticated/" + BUCKET + "/" + quote(path,safe="/"), server=True)).content

    async def put_original(self, path, content):
        return await self.request("POST", "/storage/v1/object/" + BUCKET + "/" + quote(path,safe="/"),
            server=True, data=content, headers={"Content-Type":"application/octet-stream","x-upsert":"false"})


def extract_pdf(payload):
    with tempfile.TemporaryDirectory(prefix="sunrise-a-") as temporary:
        path = Path(temporary) / "source.pdf"
        path.write_bytes(payload)
        try:
            result = subprocess.run([sys.executable, "-I", str(ROOT / "pdf_worker.py"), str(path)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=18, check=False)
            data = json.loads(result.stdout) if len(result.stdout) <= 8 * 1024 * 1024 else {}
            text = data.get("text", "")
            if result.returncode or not text.strip() or len(text.encode()) > 1048576:
                raise ValueError("No bounded PDF text")
            return text
        except (subprocess.TimeoutExpired, ValueError, KeyError) as error:
            raise HTTPException(422, "PDF text cannot be read within trial limits; scanned PDFs need OCR") from error


def build_app(cfg=None, provider=None, extractor=extract_pdf):
    cfg = (cfg or Config.environment()).validate()
    service = provider or Provider(cfg)
    cookie_crypto, blob_crypto = cfg.crypto("session-v1"), cfg.crypto("original-v1")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.provider = service

    def encode(data):
        return cookie_crypto.encrypt(json.dumps(data,separators=(",", ":")).encode()).decode()

    def decode(request, name=COOKIE, ttl=3600):
        try:
            return json.loads(cookie_crypto.decrypt(request.cookies.get(name, "").encode(), ttl=ttl))
        except (InvalidToken, ValueError, TypeError) as error:
            raise HTTPException(401, "Authentication required") from error

    def set_cookie(response, state, name=COOKIE, seconds=3600):
        response.set_cookie(name, encode(state), max_age=seconds, secure=cfg.secure,
            httponly=True, samesite="strict", path="/")

    def same_origin(request):
        origin = request.headers.get("origin")
        if origin is not None:
            # TLS can terminate before ASGI. Only configured public origins
            # count; neither ASGI's internal scheme nor forwarded data is ACL.
            if origin not in cfg.origins or urlsplit(origin).netloc != request.headers.get("host"):
                raise HTTPException(403, "Origin denied")
        if request.headers.get("sec-fetch-site") not in (None, "none", "same-origin"):
            raise HTTPException(403, "Cross-site request denied")

    def csrf(request, state):
        same_origin(request)
        if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), state.get("csrf", "")):
            raise HTTPException(403, "CSRF invalid")

    async def principal(request, *, write=False, pending=False):
        state = decode(request)
        claims = await service.claims(state["token"], mfa=not pending)
        if claims["session_id"] != state.get("session_id"):
            raise HTTPException(401, "Session identity mismatch")
        if write:
            csrf(request, state)
        await service.rpc("vault_auth_session",p_actor=cfg.admin_id,p_session=claims["session_id"])
        if not pending:
            if state.get("pending") or state.get("school_id") not in cfg.schools:
                raise HTTPException(403, "MFA and school required")
            await service.rpc("vault_session", state)
        return state

    async def start_session(token):
        claims = await service.claims(token)
        result = await service.rpc("vault_open_session", p_actor=cfg.admin_id,
            p_session=claims["session_id"], p_school=cfg.schools[0])
        return {"token":token,"session_id":claims["session_id"],"school_id":result["school_id"],
            "csrf":result["csrf_token"],"pending":False}

    def pending_state(token, claims):
        return {"token":token,"session_id":claims["session_id"],"csrf":secrets.token_urlsafe(32),"pending":True}

    @app.middleware("http")
    async def security(request, call_next):
        hosts = {urlsplit(o).netloc for o in cfg.origins}
        if request.headers.get("host") not in hosts:
            return JSONResponse({"detail":"Unapproved website host"},status_code=403)
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > MAX_PDF + 65536):
            return JSONResponse({"detail":"Trial upload limit is3MiB"},status_code=413)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>MAX_PDF+65536:
                return JSONResponse({"detail":"Trial upload limit is3MiB"},status_code=413)
        request._body = bytes(body)
        response = await call_next(request)
        response.headers.update({"Cache-Control":"no-store","X-Content-Type-Options":"nosniff",
            "X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","X-Robots-Tag":"noindex, nofollow",
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        if cfg.secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/")
    async def home():
        return RedirectResponse("/auth/login",status_code=303)

    @app.get("/health")
    async def health():
        return {"website":"running","scope":"A_CLOUD_SYNTHETIC_TRIAL","formal_R01":"NOT_VERIFIED"}

    @app.get("/auth/login")
    async def login_page():
        challenge = secrets.token_urlsafe(32)
        html = (VAULT / "templates/login.html").read_text().replace("__SUNRISE_LOGIN_CSRF__", escape(challenge))
        html = cloud_labels(html).replace("/assets/app.js", "/assets/cloud-auth.js")
        response = HTMLResponse(html)
        set_cookie(response,{"csrf":challenge},LOGIN_COOKIE,600)
        return response

    @app.post("/auth/login")
    async def login(request:Request,password:str=Form(...),csrf_value:str=Form(...,alias="csrf")):
        same_origin(request)
        challenge = decode(request, LOGIN_COOKIE, 600)
        if not hmac.compare_digest(challenge["csrf"],csrf_value):
            raise HTTPException(403,"Login CSRF invalid")
        result = await service.auth("POST","token?grant_type=password",body={"email":cfg.admin_email,"password":password})
        token = result["access_token"]
        claims = await service.claims(token,mfa=False)
        state = await start_session(token) if claims["aal"] == "aal2" else pending_state(token,claims)
        response = JSONResponse({"authenticated":not state["pending"],"next":"/auth/mfa" if state["pending"] else "/admin"})
        set_cookie(response,state)
        response.delete_cookie(LOGIN_COOKIE,secure=cfg.secure,httponly=True,samesite="strict")
        return response

    @app.get("/auth/mfa")
    async def mfa_page(request:Request):
        try:
            await principal(request,pending=True)
        except HTTPException:
            return RedirectResponse("/auth/login",status_code=303)
        return HTMLResponse(account_page("mfa"))

    @app.get("/auth/mfa/state")
    async def mfa_state(request:Request):
        state = await principal(request,pending=True)
        user = await service.auth("GET","user",token=state["token"])
        verified = [f["id"] for f in user.get("factors",[]) if f.get("factor_type")=="totp" and f.get("status")=="verified"]
        return {"csrf_token":state["csrf"],"factor_id":verified[0] if verified else None}

    @app.post("/auth/mfa/enroll")
    async def mfa_enroll(request:Request):
        state = await principal(request,write=True,pending=True)
        user = await service.auth("GET","user",token=state["token"])
        if any(f.get("status")=="verified" for f in user.get("factors",[])):
            raise HTTPException(409,"A verified factor already exists")
        for factor in user.get("factors",[]):
            if factor.get("status")=="unverified" and factor.get("factor_type")=="totp":
                await service.auth("DELETE","factors/"+str(UUID(factor["id"])),token=state["token"])
        enrolled = await service.auth("POST","factors",token=state["token"],body={"factor_type":"totp","friendly_name":"Sunrise Cloud"})
        return {"factor_id":enrolled["id"],"qr_code":enrolled["totp"]["qr_code"],"secret":enrolled["totp"]["secret"]}

    @app.post("/auth/mfa/verify")
    async def mfa_verify(request:Request,factor_id:str=Form(...),code:str=Form(...)):
        state = await principal(request,write=True,pending=True)
        if not re.fullmatch(r"[0-9]{6}",code):
            raise HTTPException(422,"Six digit code required")
        try:
            factor_id = str(UUID(factor_id))
        except ValueError as error:
            raise HTTPException(422,"Valid factor identifier required") from error
        challenge = await service.auth("POST","factors/"+factor_id+"/challenge",token=state["token"])
        verified = await service.auth("POST","factors/"+factor_id+"/verify",token=state["token"],
            body={"challenge_id":challenge["id"],"code":code})
        final = await start_session(verified["access_token"])
        response = JSONResponse({"authenticated":True,"next":"/admin"})
        set_cookie(response,final)
        return response

    @app.get("/auth/me")
    async def me(request:Request):
        state = await principal(request)
        return await service.rpc("vault_session",state)

    @app.post("/auth/logout")
    async def logout(request:Request):
        state = await principal(request,write=True,pending=True)
        await service.auth("POST","logout?scope=local",token=state["token"])
        response = JSONResponse({"authenticated":False})
        response.delete_cookie(COOKIE,secure=cfg.secure,httponly=True,samesite="strict")
        return response

    @app.post("/auth/school")
    async def switch(request:Request,body:SchoolInput):
        state = await principal(request,write=True)
        if body.school_id not in cfg.schools:
            raise HTTPException(403,"School denied")
        result = await service.rpc("vault_switch_school",state,p_new_school=body.school_id)
        response = JSONResponse(result)
        set_cookie(response,{**state,"school_id":result["school_id"],"csrf":result["csrf_token"]})
        return response

    @app.get("/account/password")
    async def password_page(request:Request):
        try:
            await principal(request)
        except HTTPException:
            return RedirectResponse("/auth/login",status_code=303)
        return HTMLResponse(account_page("password"))

    @app.post("/account/password")
    async def password_change(request:Request,current_password:str=Form(...),new_password:str=Form(...),confirm_password:str=Form(...)):
        state = await principal(request,write=True)
        check_password(new_password,confirm_password)
        check = await service.auth("POST","token?grant_type=password",body={"email":cfg.admin_email,"password":current_password})
        if check["user"]["id"] != cfg.admin_id:
            raise HTTPException(403,"Admin mismatch")
        await service.auth("POST","logout?scope=local",token=check["access_token"])
        await service.auth("PUT","user",token=state["token"],body={"password":new_password})
        await service.auth("POST","logout?scope=local",token=state["token"])
        response = JSONResponse({"changed":True,"next":"/auth/login"})
        response.delete_cookie(COOKIE,secure=cfg.secure,httponly=True,samesite="strict")
        return response

    @app.get("/auth/activate")
    async def activation_page():
        response = HTMLResponse(account_page("activate"))
        set_cookie(response,{"csrf":secrets.token_urlsafe(32)},LOGIN_COOKIE,600)
        return response

    @app.get("/auth/activation-csrf")
    async def activation_csrf(request:Request):
        state = decode(request,LOGIN_COOKIE,600)
        return {"csrf_token":state["csrf"]}

    @app.post("/auth/activate")
    async def activate(request:Request,activation_code:str=Form(...),new_password:str=Form(...),confirm_password:str=Form(...)):
        state = decode(request,LOGIN_COOKIE,600)
        csrf(request,state)
        check_password(new_password,confirm_password)
        if not re.fullmatch(r"[a-f0-9]{40,128}",activation_code):
            raise HTTPException(422,"Owner activation code required")
        result = await service.auth("POST","verify",body={"token_hash":activation_code,"type":"recovery"})
        token = result["access_token"]
        claims = await service.claims(token,mfa=False)
        await service.auth("PUT","user",token=token,body={"password":new_password})
        response = JSONResponse({"next":"/auth/mfa"})
        set_cookie(response,pending_state(token,claims))
        response.delete_cookie(LOGIN_COOKIE,secure=cfg.secure,httponly=True,samesite="strict")
        return response

    @app.get("/admin")
    async def admin(request:Request):
        try:
            await principal(request)
        except HTTPException as error:
            if error.status_code in (401,403):
                return RedirectResponse("/auth/login",status_code=303)
            raise
        html = cloud_labels((VAULT/"templates/admin.html").read_text())
        html = html.replace('<button id="logout"', '<a href="/account/password" class="button secondary">更改密碼</a><button id="logout"')
        html = html.replace("上載包含文字的合成測試 PDF", "上載不超過3MiB、100頁且包含文字的合成測試 PDF")
        return HTMLResponse(html)

    @app.get("/assets/app.js")
    async def ui_js():
        return Response((VAULT/"ui.js").read_bytes(),media_type="application/javascript")

    @app.get("/assets/style.css")
    async def ui_css():
        return Response((VAULT/"style.css").read_bytes(),media_type="text/css")

    @app.get("/assets/cloud-auth.js")
    async def auth_js():
        return Response((ROOT/"auth.js").read_bytes(),media_type="application/javascript")

    @app.get("/vault/v1/shells")
    async def shells(request:Request):
        state = await principal(request)
        result = await service.rpc("vault_list_shells",state)
        await principal(request)
        return result

    @app.post("/vault/v1/shells")
    async def create(request:Request,body:ShellInput):
        state = await principal(request,write=True)
        key = operation_key(request)
        result = await service.rpc("vault_create_shell",state,p_key=key,p_payload=body.model_dump())
        created = result.pop("created")
        return JSONResponse(result,status_code=201 if created else 200)

    @app.get("/vault/v1/shells/{shell_id}")
    async def shell(request:Request,shell_id:str):
        state = await principal(request)
        result = await service.rpc("vault_get_shell",state,p_shell=identifier(shell_id))
        await principal(request)
        return result

    @app.post("/vault/v1/shells/{shell_id}/archive")
    async def archive(request:Request,shell_id:str):
        state = await principal(request,write=True)
        return await service.rpc("vault_archive_shell",state,p_shell=identifier(shell_id))

    @app.get("/vault/v1/shells/{shell_id}/materials")
    async def materials(request:Request,shell_id:str):
        state = await principal(request)
        result = await service.rpc("vault_materials",state,p_shell=identifier(shell_id))
        await principal(request)
        return {"materials":[public_source(x) for x in result["materials"]]}

    @app.post("/vault/v1/shells/{shell_id}/materials")
    async def upload(request:Request,shell_id:str,file:UploadFile=File(...),title:str=Form(...),license:str=Form(...),retention:str=Form(...)):
        state = await principal(request,write=True)
        shell_id = identifier(shell_id)
        key = operation_key(request)
        try:
            name = plain(file.filename or "",180)
            metadata = {"title":plain(title,200),"license":plain(license,120),"retention":plain(retention,100),"original_name":name}
        except ValueError as error:
            raise HTTPException(422,"Visible title/license/retention and safe filename required") from error
        if Path(name).name!=name or "\\" in name or not name.lower().endswith(".pdf") or file.content_type not in ("application/pdf","application/octet-stream"):
            raise HTTPException(422,"PDF filename and type required")
        content = await file.read(MAX_PDF+1)
        if len(content)>MAX_PDF:
            raise HTTPException(413,"Trial limit is3MiB")
        if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
            raise HTTPException(422,"Invalid PDF")
        metadata["sha256"] = hashlib.sha256(content).hexdigest()
        text = await asyncio.to_thread(extractor,content)
        source = await service.rpc("vault_reserve_source",state,p_shell=shell_id,p_key=key,p_metadata=metadata)
        cipher = blob_crypto.encrypt(content)
        try:
            await service.put_original(source["original_path"],cipher)
        except HTTPException as error:
            if error.status_code not in (400,409):
                raise
        stored = await service.original(source["original_path"])
        try:
            original = blob_crypto.decrypt(stored)
        except InvalidToken as error:
            raise HTTPException(503,"Stored original cannot be verified") from error
        if hashlib.sha256(original).hexdigest()!=metadata["sha256"]:
            raise HTTPException(409,"Original hash conflict; preserved for investigation")
        await principal(request,write=True)
        finished = await service.rpc("vault_finish_source",state,p_shell=shell_id,p_source=source["source_id"],
            p_text=text,p_cipher_sha=hashlib.sha256(stored).hexdigest())
        return JSONResponse(public_source(finished),status_code=201 if source["created"] else 200)

    @app.post("/vault/v1/shells/{shell_id}/search")
    async def search(request:Request,shell_id:str,body:SearchInput):
        state = await principal(request,write=True)
        shell_id = identifier(shell_id)
        result = await service.rpc("vault_search",state,p_shell=shell_id,p_query=body.query,p_limit=body.limit)
        for hit in result["results"]:
            owned = await service.rpc("vault_source",state,p_shell=shell_id,p_source=hit["source_id"])
            if owned["school_id"]!=state["school_id"] or owned["shell_id"]!=shell_id or owned["state"]!="READY":
                raise HTTPException(403,"Source ownership changed")
        await principal(request)
        return result

    @app.get("/vault/v1/shells/{shell_id}/materials/{source_id}/download")
    async def download(request:Request,shell_id:str,source_id:str):
        state = await principal(request)
        shell_id = identifier(shell_id)
        before = await service.rpc("vault_source",state,p_shell=shell_id,p_source=source_id)
        if before["state"]!="READY":
            raise HTTPException(409,"Source not ready")
        stored = await service.original(before["original_path"])
        if hashlib.sha256(stored).hexdigest()!=before["cipher_sha256"]:
            raise HTTPException(503,"Encrypted original hash mismatch")
        try:
            content = blob_crypto.decrypt(stored)
        except InvalidToken as error:
            raise HTTPException(503,"Original encryption verification failed") from error
        if len(content)>MAX_PDF or hashlib.sha256(content).hexdigest()!=before["sha256"]:
            raise HTTPException(503,"Original hash mismatch")
        await principal(request)
        after = await service.rpc("vault_source",state,p_shell=shell_id,p_source=source_id)
        if before!=after:
            raise HTTPException(403,"Source binding changed")
        return Response(content,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=source.pdf"})

    return app


def cloud_labels(html):
    return html.replace("本機合成測試", "Cloud 合成試用").replace("本機合成環境", "Cloud 合成試用環境").replace(
        "請勿上載真實學生資料", "只用合成教材。免費試用受服務休眠及配額限制，未提供全天候可用保證")


def identifier(value):
    try:
        return str(UUID(value))
    except ValueError as error:
        raise HTTPException(404,"Record not found") from error


def operation_key(request):
    key = request.headers.get("idempotency-key", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",key):
        raise HTTPException(400,"Idempotency-Key required")
    return key


def public_source(row):
    return {k:v for k,v in row.items() if k not in ("original_path","cipher_sha256","full_text","created")}


def check_password(password, confirmation):
    if password!=confirmation or not 12<=len(password)<=128 or password.isspace() or any(unicodedata.category(c)=="Cc" for c in password):
        raise HTTPException(422,"Passwords must match and contain12–128 characters")


def account_page(kind):
    return (ROOT/"account.html").read_text().replace("__PAGE__",kind)
