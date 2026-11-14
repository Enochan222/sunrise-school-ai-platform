"""Sunrise A-only local synthetic Gateway. Backend-dependent gates remain closed.

Use `VAULT_...` env values, bind loopback only. OpenAPI/docs intentionally disabled.
"""
import hashlib
import hmac
import json
import re
import secrets
import time
import unicodedata
from collections import defaultdict,deque
from datetime import datetime,timezone
from html import escape
from pathlib import Path
from threading import Lock

import jwt
from argon2 import PasswordHasher,exceptions as argon_errors
from fastapi import FastAPI,Request,HTTPException,UploadFile,File,Form
from fastapi.responses import HTMLResponse,JSONResponse,Response,RedirectResponse
from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired
from pydantic import BaseModel,Field,field_validator

from config import Settings,from_env
from native import Native,NativeUnavailable,NativeOwnershipError
from store import Store,Conflict,Indeterminate
from surreal_store import SurrealStore,SurrealConfig,SurrealUnavailable

SESSION_COOKIE='sunrise_a_sid'
LOGIN_COOKIE='sunrise_a_login_csrf'
YEAR_RE=re.compile(r'^[A-Za-z0-9._ -]{1,32}$')
ID_RE=re.compile(r'^[A-Za-z0-9_-]{1,80}$')

class ShellInput(BaseModel):
    academic_year:str=Field(min_length=1,max_length=32)
    grade:str=Field(min_length=1,max_length=32)
    subject:str=Field(min_length=1,max_length=48)
    curriculum_stream:str=Field(min_length=1,max_length=48)

    @field_validator('academic_year','grade','subject','curriculum_stream')
    @classmethod
    def canonical_classification(cls,value,info):
        stripped=value.strip()
        if not stripped or any(unicodedata.category(c) in ('Cc','Cf') for c in stripped):
            raise ValueError('Invalid or invisible classification characters')
        if info.field_name=='academic_year' and not YEAR_RE.fullmatch(stripped):
            raise ValueError('Academic year must use ASCII year code')
        return stripped

class SchoolSwitchInput(BaseModel):
    school_id:str=Field(min_length=1,max_length=100)

class SearchInput(BaseModel):
    query:str=Field(min_length=1,max_length=300)
    limit:int=Field(default=20,ge=1,le=50)

    @field_validator('query')
    @classmethod
    def canonical_search_query(cls,value):
        text=value.strip()
        if not text or any(unicodedata.category(c)=='Cc' for c in text):
            raise ValueError('Nonempty plain text query required')
        return text


def build_app(cfg:Settings|None=None,native=None):
    cfg=(cfg or from_env()).validate()
    store=(Store(cfg.sqlite_file) if cfg.store_backend=='synthetic_sqlite' else
           SurrealStore(SurrealConfig(cfg.surreal_ws_url,cfg.surreal_user,cfg.surreal_password,
               cfg.surreal_namespace,cfg.surreal_database),cfg.actor_id))
    upstream=native or Native(cfg.native_url,cfg.native_password,
                                    text_only_verified=cfg.native_text_only_verified,
                                    max_download_bytes=cfg.max_pdf_bytes)
    app=FastAPI(title='Sunrise Private A Vault — Synthetic',docs_url=None,redoc_url=None,openapi_url=None)
    serializer=URLSafeTimedSerializer(cfg.session_secret,salt='sunrise-a-session')
    login_serializer=URLSafeTimedSerializer(cfg.session_secret,salt='sunrise-login-csrf')
    ph=PasswordHasher()
    allowed_schools=frozenset(cfg.allowed_schools())
    attempts=defaultdict(deque)
    attempt_lock=Lock()
    maintenance_lock=Lock()
    mutation_count=[0]
    gateway_instance=secrets.token_hex(16)  # changes on every Gateway process start
    maintenance_path_digest=(hashlib.sha256(
        cfg.maintenance_file.encode('utf-8')).hexdigest() if cfg.maintenance_file else None)
    app.state.store=store
    app.state.native=upstream
    # WP07: trusted local templates are served ONLY through existing Gateway routes.
    # Load once on startup, fail closed if deploy bundle omitted either HTML file.
    template_dir=Path(__file__).parent/'templates'
    login_template=(template_dir/'login.html').read_text(encoding='utf-8')
    admin_template=(template_dir/'admin.html').read_text(encoding='utf-8')
    login_marker='__SUNRISE_LOGIN_CSRF__'
    if login_template.count(login_marker)!=1:
        raise RuntimeError('WP07 login CSRF template marker must occur exactly once')
    if login_marker in admin_template or '<script>' in admin_template.lower():
        raise RuntimeError('WP07 admin template contains disallowed marker or inline script')

    def origin_guard(req:Request):
        # CSRF origin guard applies even to /auth/login; strict same-origin on browser POSTs.
        origin=req.headers.get('origin')
        if origin:
            from urllib.parse import urlsplit
            u=urlsplit(origin)
            if u.scheme not in ('http','https') or u.netloc!=req.headers.get('host'):
                raise HTTPException(403,'Origin mismatch')
        fetch_site=req.headers.get('sec-fetch-site')
        if fetch_site not in (None,'none','same-origin'):
            raise HTTPException(403,'Cross-site request forbidden')

    def rate_limit(req):
        ip=req.client.host if req.client else 'unknown'
        now=time.monotonic()
        with attempt_lock:
            q=attempts[ip]
            while q and q[0]<now-60:q.popleft()
            if len(q)>=8:raise HTTPException(429,'Too many login attempts')
            q.append(now)

    def credentials(req:Request,permission=None,write=False):
        if write:origin_guard(req)
        authorization=req.headers.get('authorization','')
        if authorization:
            if not authorization.startswith('Bearer ') or not cfg.service_public_key:
                raise HTTPException(401,'Invalid authorization')
            try:
                claims=jwt.decode(authorization[7:],cfg.service_public_key,algorithms=['RS256'],
                    issuer=cfg.service_issuer,audience=cfg.service_audience,
                    options={'require':['sub','iss','aud','exp','iat','nbf','jti','school_id','scope']},leeway=5)
                if (not isinstance(claims['school_id'],str) or
                    claims['school_id'] not in allowed_schools or not permission or
                    not isinstance(claims['scope'],str) or permission not in claims['scope'].split() or
                    not isinstance(claims['sub'],str) or not claims['sub'].strip() or
                    len(claims['sub'])>256 or
                    any(unicodedata.category(c)=='Cc' for c in claims['sub']) or
                    not isinstance(claims['jti'],str) or not claims['jti'] or
                    claims['exp']-claims['iat']>300):
                    raise HTTPException(403,'Service scope denied')
                return {'school_id':claims['school_id'],'actor_id':claims['sub'],'service':True,'csrf':None}
            except jwt.PyJWTError:
                raise HTTPException(401,'Invalid service token')
        token=req.cookies.get(SESSION_COOKIE)
        if not token:raise HTTPException(401,'Authentication required')
        try:sid=serializer.loads(token,max_age=3600)
        except (BadSignature,SignatureExpired):raise HTTPException(401,'Invalid session')
        state=store.session(sid)
        if not state or state.get('school_id') not in allowed_schools:
            raise HTTPException(401,'Session revoked, expired or school not allowed')
        if write and not hmac.compare_digest(str(req.headers.get('x-csrf-token','')),state['csrf']):
            raise HTTPException(403,'CSRF token missing or invalid')
        return {'school_id':state['school_id'],'actor_id':cfg.actor_id,
                'service':False,'csrf':state['csrf']}

    def admin_only(p):
        if p['service']:raise HTTPException(403,'Admin only')

    def revalidate_response_principal(req,first,permission=None):
        # A school-switch/CSRF rotation or JWT expiry while waiting on the
        # private Native API must not release stale-school content. Check again
        # immediately before constructing the client response's first byte.
        current=credentials(req,permission=permission)
        if (current['school_id']!=first['school_id'] or
                current['actor_id']!=first['actor_id'] or
                current['service']!=first['service'] or
                current['csrf']!=first['csrf']):
            raise HTTPException(403,'Session school or credential changed during read')
        return current

    def get_owned_shell(p,shell_id):
        s=store.shell(p['school_id'],shell_id)
        if not s:raise HTTPException(404,'Shell not found')
        return s

    def material_actor_options(principal):
        # Formal A SurrealDB operation identity follows verified JWT subject;
        # legacy SQLite is exclusively a synthetic fixture without service IAM.
        return {'actor_id':principal['actor_id']} if isinstance(store,SurrealStore) else {}

    def return_error(e):
        if isinstance(e,Conflict): raise HTTPException(409,str(e))
        if isinstance(e,(Indeterminate,NativeUnavailable)): raise HTTPException(503,'Native operation not confirmed; fail closed')
        if isinstance(e,NativeOwnershipError): raise HTTPException(403,'Native ownership verification failed')
        raise e

    @app.middleware('http')
    async def secure_headers(req:Request,call_next):
        # Never trust forwarded proxy headers to make a private service public.
        host=req.url.hostname
        if host not in ('127.0.0.1','localhost','testserver','::1'):
            return JSONResponse({'detail':'Loopback-only synthetic gateway'},status_code=403)
        # GET /materials may cause pinned Native last_viewed_at DB writes.
        # During cold capture freeze *all* routes except the read-only /health
        # barrier, including reads, before snapshotting the shared ON DB.
        mutation=req.url.path!='/health'
        if mutation:
            with maintenance_lock:
                if cfg.maintenance_file and Path(cfg.maintenance_file).exists():
                    return JSONResponse({'detail':'A-only maintenance write freeze'},status_code=503)
                mutation_count[0]+=1
        try:
            response=await call_next(req)
        finally:
            if mutation:
                with maintenance_lock:
                    mutation_count[0]-=1
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
            'X-Frame-Options':'DENY','Referrer-Policy':'same-origin',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"})
        return response

    @app.get('/health')
    def health():
        with maintenance_lock:
            active=mutation_count[0]
        return {'gateway':'running','native':'NOT_VERIFIED',
                'stage':'LOCAL_SYNTHETIC_DEVELOPMENT','release':'NOT_APPROVED',
                'maintenance':bool(cfg.maintenance_file and Path(cfg.maintenance_file).exists()),
                'mutations_in_flight':active,
                'gateway_instance':gateway_instance,
                'maintenance_path_sha256':maintenance_path_digest}

    @app.get('/auth/login',response_class=HTMLResponse)
    def login_form():
        csrf=secrets.token_urlsafe(24)
        # Preserve the signed, HttpOnly ten-minute login-CSRF cookie below.
        html=login_template.replace(login_marker,escape(csrf,quote=True))
        resp=HTMLResponse(html)
        resp.set_cookie(LOGIN_COOKIE,login_serializer.dumps(csrf),httponly=True,secure=cfg.session_secure,samesite='strict',max_age=600)
        return resp

    @app.post('/auth/login')
    async def login(req:Request,password:str=Form(...),csrf:str=Form(...)):
        origin_guard(req);rate_limit(req)
        try:expected=login_serializer.loads(req.cookies.get(LOGIN_COOKIE,''),max_age=600)
        except (BadSignature,SignatureExpired):raise HTTPException(403,'Login CSRF invalid')
        if not hmac.compare_digest(csrf,expected):raise HTTPException(403,'Login CSRF invalid')
        try:correct=ph.verify(cfg.admin_hash,password)
        except (argon_errors.VerifyMismatchError,argon_errors.InvalidHashError,argon_errors.VerificationError):correct=False
        if not correct:raise HTTPException(401,'Invalid credentials')
        sid=secrets.token_urlsafe(32);session_csrf=secrets.token_urlsafe(32)
        store.add_session(sid,cfg.school_id,session_csrf)
        if 'text/html' in req.headers.get('accept',''):
            resp=RedirectResponse('/admin',status_code=303)
        else:
            resp=JSONResponse({'authenticated':True,'school_id':cfg.school_id,'csrf_token':session_csrf})
        resp.set_cookie(SESSION_COOKIE,serializer.dumps(sid),httponly=True,secure=cfg.session_secure,samesite='strict',max_age=3600)
        resp.delete_cookie(LOGIN_COOKIE)
        return resp

    @app.post('/auth/school')
    def switch_school(req:Request,body:SchoolSwitchInput):
        principal=credentials(req,write=True)
        admin_only(principal)
        if body.school_id not in allowed_schools:
            raise HTTPException(403,'School not permitted by server-side allowlist')
        sid=serializer.loads(req.cookies.get(SESSION_COOKIE,''),max_age=3600)
        new_csrf=secrets.token_urlsafe(32)
        try:
            switched=store.switch_school(sid,principal['school_id'],body.school_id,
                                         principal['csrf'],new_csrf,cfg.actor_id)
        except (Indeterminate,SurrealUnavailable) as error:
            raise HTTPException(503,'Active school rotation uncertain; reauthenticate or readback') from error
        return {'school_id':switched['school_id'],'actor_id':cfg.actor_id,
                'csrf_token':new_csrf,'available_schools':list(cfg.allowed_schools())}

    @app.post('/auth/logout')
    def logout(req:Request):
        p=credentials(req,write=True);admin_only(p)
        sid=serializer.loads(req.cookies.get(SESSION_COOKIE,''),max_age=3600)
        store.del_session(sid)
        response=JSONResponse({'logged_out':True})
        response.delete_cookie(SESSION_COOKIE)
        return response

    @app.get('/auth/me')
    def me(req:Request):
        p=credentials(req)
        admin_only(p)
        return {'school_id':p['school_id'],'actor_id':p['actor_id'],
                'csrf_token':p['csrf'],'available_schools':list(cfg.allowed_schools())}

    @app.get('/vault/v1/shells')
    def list_shells(req:Request):
        p=credentials(req,permission='vault.shell.read')
        return {'shells':store.list_shells(p['school_id'])}

    @app.post('/vault/v1/shells',status_code=201)
    async def create_shell(req:Request,body:ShellInput):
        p=credentials(req,write=True);admin_only(p)
        key=req.headers.get('idempotency-key','')
        if not ID_RE.fullmatch(key):raise HTTPException(400,'Idempotency-Key required (ASCII letters/digits/_/-)')
        data=body.model_dump()
        try:
            record,is_new=store.start_shell(p['school_id'],key,data)
        except Conflict as e:
            return_error(e)
        except Indeterminate as e:
            if not getattr(store,'is_durable',False):
                return_error(e)
            # A SurrealDB reservation survives a lost native create ACK. NEVER re-send CREATE.
            op=store.operation(p['school_id'],key,'shell')
            from surreal_store import _digest
            if (not op or op.get('payload_sha')!=_digest(data) or
                    not str(op.get('marker','')).startswith('sunrise-a-op-v1:')):
                return_error(Indeterminate('Reservation identity cannot be reconciled'))
            try:
                matches=await upstream.find_notebooks_by_marker(op['marker'])
                if len(matches)!=1:
                    store.quarantine(p['school_id'],key)
                    return_error(Indeterminate('Missing or duplicate native creation marker'))
                reserved={'shell_id':op['shell_id'],'school_id':p['school_id'],**data}
                return store.complete_shell(p['school_id'],key,reserved,matches[0])
            except (NativeUnavailable,Indeterminate) as failure:
                return_error(failure)
        if not is_new:return JSONResponse(record,status_code=200)
        try:
            name='Sunrise '+ ' / '.join(data[k] for k in ('academic_year','grade','subject','curriculum_stream'))
            if getattr(store,'is_durable',False):
                nb_id=await upstream.create_notebook(name,marker=record['creation_marker'])
                # Re-read the exact marker; never trust title or a possibly lost POST receipt.
                readback=await upstream.find_notebooks_by_marker(record['creation_marker'])
                if readback!=[nb_id]:
                    raise Indeterminate('Native notebook marker/readback mismatch')
            else:
                nb_id=await upstream.create_notebook(name)
            return store.complete_shell(p['school_id'],key,record,nb_id)
        except Exception as e:
            store.quarantine(p['school_id'],key)
            if isinstance(e,(NativeUnavailable,Indeterminate)):return_error(e)
            # Fail closed for any unknown response or DB failure after native create.
            raise HTTPException(503,'Notebook creation indeterminate; reconcile before retry') from e

    @app.get('/vault/v1/shells/{shell_id}')
    def get_shell(req:Request,shell_id:str):
        return get_owned_shell(credentials(req,permission='vault.shell.read'),shell_id)

    @app.post('/vault/v1/shells/{shell_id}/archive')
    def archive_shell(req:Request,shell_id:str):
        p=credentials(req,write=True);admin_only(p)
        get_owned_shell(p,shell_id)
        return store.archive(p['school_id'],shell_id)

    @app.get('/vault/v1/shells/{shell_id}/materials')
    async def list_materials(req:Request,shell_id:str):
        p=credentials(req,permission='vault.materials.read')
        s=get_owned_shell(p,shell_id)
        material_rows=store.list_materials(p['school_id'],shell_id)
        # Live revalidate every Native source before returning any metadata.
        # Status is a conservative read-only view of the pinned Native Worker,
        # not a durable "READY" claim from the upload receipt.
        safe_rows=[]
        for m in material_rows:
            try:
                src=await upstream.ensure_owned(m['source_id'],s['notebook_id'])
                view=dict(m)
                view['state']=Native.processing_state(src)
                safe_rows.append(view)
            except (NativeUnavailable,NativeOwnershipError) as e:return_error(e)
        revalidate_response_principal(req,p,permission='vault.materials.read')
        return {'materials':safe_rows}

    @app.post('/vault/v1/shells/{shell_id}/materials',status_code=201)
    async def upload_material(req:Request,shell_id:str,file:UploadFile=File(...),
                              title:str=Form(...),license:str=Form(...),retention:str=Form(...)):
        p=credentials(req,write=True,permission='vault.materials.write')
        s=get_owned_shell(p,shell_id)
        if s['archived']:raise HTTPException(409,'Archived shells are read-only')
        title,license,retention=title.strip(),license.strip(),retention.strip()
        if (not title or len(title)>200 or not license or len(license)>120 or
                not retention or len(retention)>100 or
                any(unicodedata.category(c) in ('Cc','Cf') for field in (title,license,retention) for c in field)):
            raise HTTPException(422,'Title/license/retention metadata required')
        name=Path(file.filename or '').name
        if (name!=file.filename or not name.lower().endswith('.pdf') or
                len(name)>180 or '\\' in name or
                any(unicodedata.category(c) in ('Cc','Cf') for c in name) or
                file.content_type not in ('application/pdf','application/octet-stream')):
            raise HTTPException(422,'Only safe uploaded PDFs allowed')
        content=await file.read(cfg.max_pdf_bytes+1)
        if len(content)>cfg.max_pdf_bytes or not content.startswith(b'%PDF-') or b'%%EOF' not in content[-2048:]:
            raise HTTPException(422,'Invalid or oversized PDF')
        digest=hashlib.sha256(content).hexdigest()
        key=req.headers.get('idempotency-key','')
        if not ID_RE.fullmatch(key):raise HTTPException(400,'Idempotency-Key required for upload')
        fingerprint=hashlib.sha256(json.dumps([digest,title,license,retention,name],separators=(',',':')).encode()).hexdigest()
        metadata={'sha256':digest,'title':title,'license':license,
                  'retention':retention,'original_name':name}
        options=material_actor_options(p)
        if isinstance(store,SurrealStore):
            options['metadata']=metadata
        try:
            receipt_old,is_new=store.start_material(p['school_id'],shell_id,key,fingerprint,**options)
        except (Conflict,Indeterminate) as e:return_error(e)
        if not is_new:
            return JSONResponse({'source_id':receipt_old['source_id'],'sha256':receipt_old['sha256'],
                'state':'SUBMITTED_NATIVE_PROCESSING','version':1},status_code=200)
        try:
            receipt=await upstream.upload_pdf(s['notebook_id'],content,name,title)
            source_id=receipt['id']
            # Native POST ACK is NOT an atomic A journal commit. Save its exact
            # Source ID durably before further owner/hash readback. If ACK was
            # lost we have no trustworthy Source ID: quarantine, never POST again.
            if isinstance(store,SurrealStore):
                store.record_material_receipt(p['school_id'],shell_id,key,source_id,
                                              **material_actor_options(p))
            # Do not expose uncertain source if ownership cannot be confirmed.
            await upstream.ensure_owned(source_id,s['notebook_id'])
            store.finish_material(p['school_id'],shell_id,key,source_id,title,digest,name,license,retention,**material_actor_options(p))
            return {'source_id':source_id,'sha256':digest,'state':'SUBMITTED_NATIVE_PROCESSING','version':1}
        except (NativeUnavailable,NativeOwnershipError) as e:
            store.quarantine_material(p['school_id'],shell_id,key,**material_actor_options(p))
            return_error(e)
        except Exception as e:
            store.quarantine_material(p['school_id'],shell_id,key,**material_actor_options(p))
            raise HTTPException(503,'Source mapping unconfirmed; manual reconciliation required') from e

    @app.get('/vault/v1/shells/{shell_id}/materials/{source_id}/download')
    async def download(req:Request,shell_id:str,source_id:str):
        p=credentials(req,permission='vault.materials.read')
        s=get_owned_shell(p,shell_id)
        m=store.material(source_id,shell_id,p['school_id'])
        if not m:raise HTTPException(404,'Material not found')
        try:
            await upstream.ensure_owned(source_id,s['notebook_id'])
            payload=await upstream.original(source_id,m['sha256'])
            # Double-check ownership before first byte; no streaming any native bytes.
            await upstream.ensure_owned(source_id,s['notebook_id'])
        except (NativeUnavailable,NativeOwnershipError) as e:return_error(e)
        revalidate_response_principal(req,p,permission='vault.materials.read')
        return Response(payload,media_type='application/pdf',headers={'Content-Disposition':"attachment; filename=source.pdf"})

    @app.post('/vault/v1/shells/{shell_id}/search')
    async def search(req:Request,shell_id:str,body:SearchInput):
        p=credentials(req,write=True,permission='vault.search.read')
        s=get_owned_shell(p,shell_id)
        # Must never allow global search or unsafe native vector fallback.
        if not s['notebook_id'].startswith('notebook:'):raise HTTPException(503,'Unverified notebook identity')
        try: result=await upstream.search(s['notebook_id'],body.query,body.limit)
        except NativeUnavailable as e:return_error(e)
        # Defence-in-depth: source id and owner both verified per hit; do not leak raw foreign snippets.
        safe=[]
        for hit in result:
            source_id=hit.get('parent_id')
            if not isinstance(source_id,str):raise HTTPException(503,'Unverifiable search hit')
            m=store.material(source_id,shell_id,p['school_id'])
            if not m:raise HTTPException(403,'Search ownership violation')
            try:await upstream.ensure_owned(source_id,s['notebook_id'])
            except (NativeUnavailable,NativeOwnershipError) as e:return_error(e)
            safe.append({'source_id':source_id,'title':m['title'],'relevance':hit.get('relevance')})
        revalidate_response_principal(req,p,permission='vault.search.read')
        return {'results':safe,'total_count':len(safe),'search_type':'text'}

    @app.get('/admin',response_class=HTMLResponse)
    def dashboard(req:Request):
        p=credentials(req);admin_only(p)
        # HTML is not an unguarded asset: authenticate the admin before reading.
        return HTMLResponse(admin_template)

    @app.get('/assets/app.js')
    def ui_script():
        return Response((Path(__file__).parent/'ui.js').read_bytes(),media_type='application/javascript')

    @app.get('/assets/style.css')
    def ui_style():
        return Response((Path(__file__).parent/'style.css').read_bytes(),media_type='text/css')
    return app
