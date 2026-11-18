"""Executable security/contract tests; hosted provider evidence is separate."""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import time
import uuid

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from cloud_app import Config, Provider, build_app, extract_pdf, MAX_PDF, COOKIE

ACTOR = "1f6bd435-b937-4c24-bf80-889c2351e53d"
SESSION = "47b06338-c866-4015-b202-df190b727676"
HOST = "https://sunrise-cloud-test.vercel.app"
URL = "https://abcdefghijklmnopqrst.supabase.co"


@pytest.fixture
def cfg():
    return Config(URL,"sb_publishable_"+"p"*40,"sb_secret_"+"s"*40,
        base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),ACTOR,
        "synthetic-owner@sunrise.invalid",(HOST,))


def pdf(text="Synthetic fractions: one half plus one quarter"):
    data=io.BytesIO();doc=canvas.Canvas(data);doc.drawString(40,700,text);doc.save();return data.getvalue()


def test_actual_pdf_parser_reads_text_and_rejects_empty_and_malformed():
    assert "fractions" in extract_pdf(pdf())
    with pytest.raises(HTTPException): extract_pdf(b"%PDF-broken\n%%EOF")
    empty=io.BytesIO();doc=canvas.Canvas(empty);doc.showPage();doc.save()
    with pytest.raises(HTTPException): extract_pdf(empty.getvalue())


def test_isolated_pdf_worker_recovers_vendor_dependencies_without_site_initialization(monkeypatch):
    import cloud_app
    run=cloud_app.subprocess.run
    def without_site(command,**kwargs):
        return run([*command[:2],'-S',*command[2:]],**kwargs)
    monkeypatch.setattr(cloud_app.subprocess,'run',without_site)
    assert 'fractions' in extract_pdf(pdf())


@pytest.mark.parametrize("field,value",[("url","https://attacker.example"),("admin_id","not-a-uuid"),
 ("master_key","short"),("origins",("http://public.example",)),("service_key","short")])
def test_missing_or_unsafe_configuration_fails_closed(cfg,field,value):
    from dataclasses import replace
    with pytest.raises(ValueError): replace(cfg,**{field:value}).validate()


@pytest.mark.asyncio
@pytest.mark.parametrize('body',[{'code':403,'message':'session revoked'},{'code':'PT403'},['unexpected'],None])
async def test_provider_denial_shapes_remain_denied_without_server_error(cfg,body):
    provider=Provider(cfg,httpx.MockTransport(lambda request:httpx.Response(403,json=body)))
    with pytest.raises(HTTPException) as error:
        await provider.auth('GET','user',token='synthetic-revoked-token')
    assert error.value.status_code==403


@pytest.mark.asyncio
async def test_jwt_signature_issuer_audience_mfa_and_fresh_user(cfg):
    private=ec.generate_private_key(ec.SECP256R1())
    jwk=json.loads(jwt.algorithms.ECAlgorithm.to_jwk(private.public_key()));jwk.update(kid="synthetic-key",alg="ES256")
    seen=[]
    def transport(request):
        seen.append(request)
        if request.url.path.endswith("jwks.json"):return httpx.Response(200,json={"keys":[jwk]})
        if request.url.path.endswith("/user"):return httpx.Response(200,json={"id":ACTOR})
        raise AssertionError("Unexpected provider request")
    provider=Provider(cfg,httpx.MockTransport(transport))
    claims={"sub":ACTOR,"session_id":SESSION,"iss":URL+"/auth/v1","aud":"authenticated","exp":int(time.time())+300,"iat":int(time.time()),"aal":"aal2"}
    def token(changes=None,key=private):return jwt.encode({**claims,**(changes or {})},key,algorithm="ES256",headers={"kid":"synthetic-key"})
    assert (await provider.claims(token()))["sub"]==ACTOR
    assert seen[-1].headers["authorization"].startswith("Bearer ")
    assert cfg.service_key not in str(seen[-1].headers)
    for changes in ({"iss":"https://attacker.example"},{"aud":"wrong"},{"exp":int(time.time())-1},{"aal":"aal1"},{"sub":str(uuid.uuid4())},{"session_id":"bad"}):
        with pytest.raises(HTTPException): await provider.claims(token(changes))
    with pytest.raises(HTTPException):await provider.claims(token(key=ec.generate_private_key(ec.SECP256R1())))


class FakeProvider:
    """Policy-unit fixture only; real PostgreSQL tests below prove RPC behavior."""
    def __init__(self): self.calls=[];self.valid=True;self.revoked=False
    async def claims(self,token,mfa=True):
        if not self.valid:raise HTTPException(401,"Expired")
        return {"sub":ACTOR,"session_id":SESSION,"aal":"aal2"}
    async def rpc(self,name,state=None,**args):
        self.calls.append((name,state,args))
        if self.revoked:raise HTTPException(403,"Session revoked")
        if name=="vault_auth_session":return True
        if name=="vault_session":return {"school_id":state["school_id"],"csrf_token":state["csrf"],"available_schools":[state["school_id"]]}
        if name=="vault_list_shells":return {"shells":[]}
        raise AssertionError(name)


def authenticated_client(cfg,provider):
    app=build_app(cfg,provider)
    client=TestClient(app,base_url=HOST)
    state={"token":"synthetic-unit-token","session_id":SESSION,"school_id":cfg.schools[0],"csrf":"synthetic-csrf","pending":False}
    encoded=cfg.crypto("session-v1").encrypt(json.dumps(state).encode()).decode()
    client.cookies.set(COOKIE,encoded,domain="sunrise-cloud-test.vercel.app")
    return client


def test_unauthed_html_redirects_and_api_denies_without_leaking_content(cfg):
    app=build_app(cfg,FakeProvider())
    with TestClient(app,base_url=HOST,follow_redirects=False) as client:
        assert client.get("/admin").status_code==303
        assert client.get("/admin").headers["location"]=="/auth/login"
        assert client.get("/vault/v1/shells").status_code==401
        assert client.get("/api/notebooks").status_code==404
        response=client.get("/auth/login")
        assert "Cloud 合成試用" in response.text
        assert "HttpOnly" in response.headers["set-cookie"] and "Secure" in response.headers["set-cookie"]
        assert "no-store" in response.headers["cache-control"]


@pytest.mark.parametrize("headers",[{"host":"attacker.example"},{"origin":"https://attacker.example"},{"origin":"null"},
 {"origin":"http://sunrise-cloud-test.vercel.app"},{"sec-fetch-site":"cross-site"}])
def test_host_origin_fetch_site_denied(cfg,headers):
    provider=FakeProvider();client=authenticated_client(cfg,provider)
    assert client.post("/auth/logout",headers={"x-csrf-token":"synthetic-csrf",**headers}).status_code==403
    assert not any(name not in ("vault_auth_session",) for name,_,_ in provider.calls)


def test_csrf_forged_cookie_and_revocation_denied(cfg):
    provider=FakeProvider();client=authenticated_client(cfg,provider)
    assert client.post("/vault/v1/shells",json={"academic_year":"2026-2027","grade":"中一","subject":"數學","curriculum_stream":"合成"}).status_code==403
    provider.revoked=True
    assert client.get("/vault/v1/shells").status_code==403
    client.cookies.clear();client.cookies.set(COOKIE,"forged")
    assert client.get("/vault/v1/shells").status_code==401


def test_login_refreshes_overwritten_tab_challenge_without_weakening_csrf(cfg):
    import re
    class LoginProvider(FakeProvider):
        def __init__(self):super().__init__();self.logins=0
        async def auth(self,method,path,token=None,body=None):
            assert method=='POST' and path=='token?grant_type=password'
            self.logins+=1;return {'access_token':'unit-token'}
        async def rpc(self,name,state=None,**args):
            if name=='vault_open_session':return {'school_id':cfg.schools[0],'csrf_token':'session-csrf'}
            return await super().rpc(name,state,**args)
    provider=LoginProvider();client=TestClient(build_app(cfg,provider),base_url=HOST)
    first=client.get('/auth/login');old=re.search(r'name="csrf" value="([^"]+)"',first.text).group(1)
    client.get('/auth/login')
    assert client.post('/auth/login',headers={'Origin':HOST},data={'password':'unit','csrf':old}).status_code==403
    assert provider.logins==0
    assert client.get('/auth/login-csrf',headers={'Origin':'https://attacker.example'}).status_code==403
    challenge=client.get('/auth/login-csrf',headers={'Sec-Fetch-Site':'same-origin'})
    assert challenge.status_code==200 and 'HttpOnly' in challenge.headers['set-cookie']
    response=client.post('/auth/login',headers={'Origin':HOST},data={'password':'unit','csrf':challenge.json()['csrf_token']})
    assert response.status_code==200 and response.json()['next']=='/admin'
    assert provider.logins==1


def test_body_limit_including_chunked_request(cfg):
    with TestClient(build_app(cfg,FakeProvider()),base_url=HOST) as client:
        assert client.post("/auth/login",content=b"x"*(MAX_PDF+65537)).status_code==413
        assert client.post("/auth/login",content=iter([b"x"*(MAX_PDF+65537)])).status_code==413


def test_account_page_and_canonical_ui_have_no_public_credentials(cfg):
    provider=FakeProvider();client=authenticated_client(cfg,provider)
    assert "更改密碼" in client.get("/admin").text
    page=client.get("/account/password")
    assert page.status_code==200 and "current_password" in page.text and "minlength=\"12\"" in page.text
    for path in ("/auth/login","/auth/activate","/assets/cloud-auth.js","/admin"):
        text=client.get(path).text
        assert cfg.master_key not in text and cfg.service_key not in text
    text=client.get("/assets/cloud-auth.js").text
    assert "localStorage" not in text and "sessionStorage" not in text


def test_owner_recovery_requires_token_then_mfa_before_password_mutation(cfg):
    class RecoveryProvider(FakeProvider):
        def __init__(self):super().__init__();self.auth_calls=[]
        async def claims(self,token,mfa=True):
            if mfa and token!='mfa-token':raise HTTPException(401,'MFA required')
            return {'sub':ACTOR,'session_id':SESSION,'aal':'aal2' if token=='mfa-token' else 'aal1'}
        async def auth(self,method,path,token=None,body=None):
            self.auth_calls.append((method,path,token,body))
            if path=='verify':return {'access_token':'recovery-token'}
            if path=='user' and method=='GET':return {'id':ACTOR,'factors':[{'id':SESSION,'factor_type':'totp','status':'verified'}]}
            if path.endswith('/challenge'):return {'id':'challenge'}
            if path.endswith('/verify'):return {'access_token':'mfa-token'}
            if path=='user' and method=='PUT':
                assert token=='mfa-token';return {}
            if path.startswith('logout'):return {}
            raise AssertionError((method,path))
        async def rpc(self,name,state=None,**args):
            if name=='vault_open_session':return {'school_id':cfg.schools[0],'csrf_token':'post-mfa-csrf'}
            return await super().rpc(name,state,**args)
    provider=RecoveryProvider();client=TestClient(build_app(cfg,provider),base_url=HOST)
    normal=authenticated_client(cfg,FakeProvider())
    assert normal.get('/account/recovery-password').status_code==403
    assert normal.post('/account/recovery-password',headers={'Origin':HOST,'X-CSRF-Token':'synthetic-csrf'},
        data={'new_password':'long synthetic password','confirm_password':'long synthetic password'}).status_code==403
    client.get('/auth/activate');csrf=client.get('/auth/activation-csrf').json()['csrf_token']
    response=client.post('/auth/activate',headers={'Origin':HOST,'X-CSRF-Token':csrf},data={'activation_code':'a'*64})
    assert response.status_code==200 and response.json()['next']=='/auth/mfa'
    assert client.get('/account/recovery-password').status_code==401
    assert not any(method=='PUT' for method,_,_,_ in provider.auth_calls)
    state=client.get('/auth/mfa/state').json()
    response=client.post('/auth/mfa/verify',headers={'Origin':HOST,'X-CSRF-Token':state['csrf_token']},data={'factor_id':SESSION,'code':'123456'})
    assert response.status_code==200 and response.json()['next']=='/account/recovery-password'
    assert client.get('/account/recovery-password').status_code==200
    body={'new_password':'long synthetic password','confirm_password':'long synthetic password'}
    assert client.post('/account/recovery-password',headers={'Origin':HOST},data=body).status_code==403
    response=client.post('/account/recovery-password',headers={'Origin':HOST,'X-CSRF-Token':'post-mfa-csrf'},data=body)
    assert response.status_code==200 and response.json()['next']=='/auth/login'
    assert client.get('/vault/v1/shells').status_code==401
    assert sum(method=='PUT' for method,_,_,_ in provider.auth_calls)==1


@pytest.fixture(scope="module")
def pg():
    dsn=os.environ.get("CLOUD_TEST_DSN")
    if not dsn:pytest.skip("CLOUD_TEST_DSN required; hosted PostgreSQL proof is separate")
    import psycopg
    conn=psycopg.connect(dsn,autocommit=True)
    bootstrap="""
do $$begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon;end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated;end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role;end if;
end $$;
create schema auth;create schema storage;create schema extensions;
create extension pgcrypto with schema extensions;
create function auth.role() returns text language sql as $$select current_setting('request.jwt.claim.role',true)$$;
create table auth.users(id uuid primary key,email text);
create table auth.sessions(id uuid primary key,user_id uuid references auth.users(id),aal text,not_after timestamptz);
create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(bucket_id text references storage.buckets(id),name text);
"""
    conn.execute(bootstrap)
    migration=(Path(__file__).parent/"supabase/migrations/20261117101415_stage1_cloud_vault.sql").read_text()
    conn.execute(migration)
    conn.execute("insert into auth.users(id) values(%s)",(ACTOR,))
    conn.execute("insert into auth.sessions values(%s,%s,'aal2',null)",(SESSION,ACTOR))
    conn.execute("insert into vault_private.admins(user_id,schools) values(%s,%s)",(ACTOR,["synthetic-cloud-stage1","synthetic-cloud-negative"]))
    conn.execute("set request.jwt.claim.role='service_role'")
    yield conn
    conn.close()


def rpc_db(conn,name,_server=True,**args):
    from psycopg import sql
    params={"p_actor":ACTOR,"p_session":SESSION,**args}
    query=sql.SQL("select public.{}({})").format(sql.Identifier(name),sql.SQL(",").join(sql.SQL("{}=>%s").format(sql.Identifier(k)) for k in params))
    with conn.transaction():
        if _server:
            conn.execute("set local role service_role")
        return conn.execute(query,list(params.values())).fetchone()[0]


def test_real_pg_atomic_idempotency_scope_archive_and_revocation(pg):
    import psycopg
    from psycopg.types.json import Jsonb
    school="synthetic-cloud-stage1"
    active=rpc_db(pg,"vault_open_session",p_school=school)
    common={"p_school":school,"p_csrf":active["csrf_token"]}
    payload={"academic_year":"2026-2027","grade":"中一","subject":"數學","curriculum_stream":"合成"}
    first=rpc_db(pg,"vault_create_shell",**common,p_key="same-operation",p_payload=Jsonb(payload))
    second=rpc_db(pg,"vault_create_shell",**common,p_key="same-operation",p_payload=Jsonb(payload))
    assert first["created"] and not second["created"] and first["notebook_id"]==second["notebook_id"]
    with pytest.raises(psycopg.Error) as error:
        rpc_db(pg,"vault_create_shell",**common,p_key="same-operation",p_payload=Jsonb({**payload,"subject":"中文"}))
    assert error.value.sqlstate=="PT409"
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_create_shell",**common,p_key="missing-fields",p_payload=Jsonb({"one":"x","two":"x","three":"x","four":"x"}))
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_search",**common,p_shell=first["shell_id"],p_query=" ",p_limit=20)
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_search",**common,p_shell=first["shell_id"],p_query="分數",p_limit=None)
    changed=rpc_db(pg,"vault_switch_school",**common,p_new_school="synthetic-cloud-negative")
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_list_shells",**common)
    foreign={"p_school":changed["school_id"],"p_csrf":changed["csrf_token"]}
    with pytest.raises(psycopg.Error) as error:rpc_db(pg,"vault_get_shell",**foreign,p_shell=first["shell_id"])
    assert error.value.sqlstate=="PT404"
    active=rpc_db(pg,"vault_switch_school",**foreign,p_new_school=school);common["p_csrf"]=active["csrf_token"]
    rpc_db(pg,"vault_archive_shell",**common,p_shell=first["shell_id"])
    assert rpc_db(pg,"vault_get_shell",**common,p_shell=first["shell_id"])["archived"]
    pg.execute("update auth.sessions set aal='aal1' where id=%s",(SESSION,))
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_list_shells",**common)
    pg.execute("update auth.sessions set aal='aal2',not_after=now()-interval '1second' where id=%s",(SESSION,))
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_list_shells",**common)
    pg.execute("update auth.sessions set not_after=null where id=%s",(SESSION,))


@pytest.mark.parametrize("role",["anon","authenticated"])
def test_real_pg_public_rpc_and_private_table_bypass_denied(pg,role):
    import psycopg
    pg.execute("set role "+role)
    try:
        with pytest.raises(psycopg.Error):pg.execute("select * from vault_private.sources")
        with pytest.raises(psycopg.Error):rpc_db(pg,"vault_open_session",_server=False,p_school="synthetic-cloud-stage1")
    finally:pg.execute("reset role")


def test_real_pg_upload_receipt_immutable_index_and_foreign_source_denial(pg):
    import psycopg
    from psycopg.types.json import Jsonb
    active=rpc_db(pg,"vault_open_session",p_school="synthetic-cloud-stage1")
    common={"p_school":active["school_id"],"p_csrf":active["csrf_token"]}
    payload={"academic_year":"2026-2027","grade":"中一","subject":"數學","curriculum_stream":"合成"}
    shell=rpc_db(pg,"vault_create_shell",**common,p_key="source-math",p_payload=Jsonb(payload))
    foreign=rpc_db(pg,"vault_create_shell",**common,p_key="source-science",p_payload=Jsonb({**payload,"subject":"科學"}))
    metadata={"title":"合成分數教材","license":"自製測試","retention":"試用","original_name":"synthetic.pdf","sha256":"a"*64}
    source=rpc_db(pg,"vault_reserve_source",**common,p_shell=shell["shell_id"],p_key="source-once",p_metadata=Jsonb(metadata))
    repeat=rpc_db(pg,"vault_reserve_source",**common,p_shell=shell["shell_id"],p_key="source-once",p_metadata=Jsonb(metadata))
    assert repeat["source_id"]==source["source_id"] and source["created"] and not repeat["created"]
    assert source["notebook_id"]==shell["notebook_id"] and source["state"]=="PENDING"
    for target,data in [(foreign["shell_id"],metadata),(shell["shell_id"],{**metadata,"title":"Different"})]:
        with pytest.raises(psycopg.Error) as error:rpc_db(pg,"vault_reserve_source",**common,p_shell=target,p_key="source-once",p_metadata=Jsonb(data))
        assert error.value.sqlstate=="PT409"
    with pytest.raises(psycopg.Error) as error:rpc_db(pg,"vault_finish_source",**common,p_shell=shell["shell_id"],p_source=source["source_id"],p_text="分數 fractions",p_cipher_sha="b"*64)
    assert error.value.sqlstate=="PT409"
    pg.execute("insert into storage.objects(bucket_id,name) values('sunrise-a-originals',%s)",(source["original_path"],))
    ready=rpc_db(pg,"vault_finish_source",**common,p_shell=shell["shell_id"],p_source=source["source_id"],p_text="分數 fractions",p_cipher_sha="b"*64)
    assert ready["state"]=="READY" and ready["version"]==1
    assert len(rpc_db(pg,"vault_search",**common,p_shell=shell["shell_id"],p_query="分數")["results"])==1
    assert rpc_db(pg,"vault_search",**common,p_shell=foreign["shell_id"],p_query="分數")["results"]==[]
    with pytest.raises(psycopg.Error) as error:rpc_db(pg,"vault_source",**common,p_shell=foreign["shell_id"],p_source=source["source_id"])
    assert error.value.sqlstate=="PT404"
    with pytest.raises(psycopg.Error) as error:rpc_db(pg,"vault_finish_source",**common,p_shell=shell["shell_id"],p_source=source["source_id"],p_text="tampered index",p_cipher_sha="b"*64)
    assert error.value.sqlstate=="PT409"
    rpc_db(pg,"vault_archive_shell",**common,p_shell=shell["shell_id"])
    assert rpc_db(pg,"vault_source",**common,p_shell=shell["shell_id"],p_source=source["source_id"])["state"]=="READY"
    with pytest.raises(psycopg.Error):rpc_db(pg,"vault_reserve_source",**common,p_shell=shell["shell_id"],p_key="archive-write",p_metadata=Jsonb(metadata))


def test_real_pg_concurrent_lost_ack_retry_creates_one_notebook(pg):
    import concurrent.futures
    import psycopg
    from psycopg.types.json import Jsonb
    active=rpc_db(pg,"vault_open_session",p_school="synthetic-cloud-stage1")
    values={"p_school":active["school_id"],"p_csrf":active["csrf_token"],"p_key":"concurrent-ack",
        "p_payload":Jsonb({"academic_year":"2026-2027","grade":"中一","subject":"重試","curriculum_stream":"合成"})}
    def create(_):
        with psycopg.connect(pg.info.dsn,autocommit=True) as conn:
            conn.execute("set request.jwt.claim.role='service_role'")
            return rpc_db(conn,"vault_create_shell",**values)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        rows=list(executor.map(create,range(4)))
    assert len({r["shell_id"] for r in rows})==len({r["notebook_id"] for r in rows})==1
    assert sum(r["created"] for r in rows)==1


class SQLPolicyProvider(FakeProvider):
    """Real SQL policy with in-memory transport bytes, not hosted Storage proof."""
    def __init__(self,connection):
        super().__init__();self.connection=connection;self.blobs={};self.lose_ack=False;self.on_read=None
    async def rpc(self,name,state=None,**args):
        import psycopg
        from psycopg.types.json import Jsonb
        if state:args={"p_school":state["school_id"],"p_csrf":state["csrf"],**args}
        for key in ("p_payload","p_metadata"):
            if key in args:args[key]=Jsonb(args[key])
        try:return rpc_db(self.connection,name,**args)
        except psycopg.Error as error:
            if error.sqlstate and error.sqlstate.startswith("PT"):
                raise HTTPException(int(error.sqlstate[2:]),"SQL denied") from error
            raise
    async def put_original(self,path,payload):
        if path in self.blobs:raise HTTPException(409,"Already exists")
        self.blobs[path]=payload
        self.connection.execute("insert into storage.objects(bucket_id,name) values('sunrise-a-originals',%s)",(path,))
        if self.lose_ack:
            self.lose_ack=False
            raise HTTPException(503,"ACK lost after durable storage")
    async def original(self,path):
        payload=self.blobs[path]
        if self.on_read:
            callback=self.on_read;self.on_read=None;callback()
        return payload


def test_real_pg_http_pdf_flow_lost_storage_ack_integrity_and_revocation(pg,cfg):
    import hashlib
    active=rpc_db(pg,"vault_open_session",p_school=cfg.schools[0])
    provider=SQLPolicyProvider(pg)
    client=authenticated_client(cfg,provider)
    state={"token":"synthetic-unit-token","session_id":SESSION,"school_id":cfg.schools[0],"csrf":active["csrf_token"],"pending":False}
    client.cookies.set(COOKIE,cfg.crypto("session-v1").encrypt(json.dumps(state).encode()).decode(),domain="sunrise-cloud-test.vercel.app")
    headers={"X-CSRF-Token":state["csrf"],"Origin":HOST}
    payload={"academic_year":"2026-2027","grade":"中一","subject":"HTTP數學","curriculum_stream":"合成"}
    shell=client.post('/vault/v1/shells',json=payload,headers={**headers,'Idempotency-Key':'http-math'}).json()
    other=client.post('/vault/v1/shells',json={**payload,'subject':'HTTP科學'},headers={**headers,'Idempotency-Key':'http-science'}).json()
    root='/vault/v1/shells/'+shell['shell_id'];foreign='/vault/v1/shells/'+other['shell_id']
    content=pdf('Synthetic fractions and scoped download')
    digest=hashlib.sha256(content).hexdigest()
    upload=lambda:client.post(root+'/materials',headers={**headers,'Idempotency-Key':'http-source'},
        files={'file':('synthetic.pdf',content,'application/pdf')},data={'title':'合成分數教材','license':'自製測試','retention':'試用'})
    provider.lose_ack=True
    assert upload().status_code==503
    assert len(provider.blobs)==1
    response=upload();assert response.status_code==200
    source=response.json();assert source['state']=='READY' and source['sha256']==digest
    assert source['rights_owner_actor_id']==source['created_by_actor_id']==ACTOR
    assert source['ai_usage_allowed'] is False and source['approved_sharing'] is False
    assert source['initial_version_id']==hashlib.sha256(json.dumps([source['source_id'],digest],separators=(',',':')).encode()).hexdigest()
    assert source['original_mime_type']=='application/pdf'
    assert upload().json()['source_id']==source['source_id'] and len(provider.blobs)==1
    assert len(client.get(root+'/materials').json()['materials'])==1
    assert client.post(root+'/search',headers=headers,json={'query':'fractions'}).json()['total_count']==1
    assert client.post(foreign+'/search',headers=headers,json={'query':'fractions'}).json()['results']==[]
    download=root+'/materials/'+source['source_id']+'/download'
    assert client.get(foreign+'/materials/'+source['source_id']+'/download').status_code==404
    original=client.get(download)
    assert original.status_code==200 and original.content==content
    assert hashlib.sha256(original.content).hexdigest()==digest
    assert content not in next(iter(provider.blobs.values()))
    path=next(iter(provider.blobs));cipher=provider.blobs[path];provider.blobs[path]=b'corrupt'
    assert client.get(download).status_code==503
    provider.blobs[path]=cipher
    provider.on_read=lambda:pg.execute('delete from auth.sessions where id=%s',(SESSION,))
    denied=client.get(download);assert denied.status_code in (401,403) and content not in denied.content
    pg.execute("insert into auth.sessions values(%s,%s,'aal2',null)",(SESSION,ACTOR))
    provider.on_read=lambda:pg.execute('update vault_private.sources set shell_id=%s,notebook_id=%s where source_id=%s',
        (other['shell_id'],other['notebook_id'],source['source_id']))
    denied=client.get(download);assert denied.status_code in (403,404) and content not in denied.content


def test_password_only_trial_requires_both_explicit_app_and_synthetic_db_opt_in(pg,cfg):
    import re
    import psycopg
    from dataclasses import replace
    with pytest.raises(ValueError):replace(cfg,password_only_trial=True).validate()
    trial=replace(cfg,url='https://bnepekozzgymbvbjtltb.supabase.co',password_only_trial=True).validate()
    pg.execute("update auth.sessions set aal='aal1' where id=%s",(SESSION,))
    with pytest.raises(psycopg.Error):rpc_db(pg,'vault_open_session',p_school=cfg.schools[0])
    migration=(Path(__file__).parent/'supabase/migrations/20261118024322_password_only_synthetic_trial.sql').read_text()
    pg.execute("update auth.users set email='real@school.example' where id=%s",(ACTOR,))
    with pytest.raises(psycopg.Error):pg.execute(migration)
    pg.execute('rollback')
    pg.execute("update auth.users set email='synthetic@sunrise.invalid' where id=%s",(ACTOR,))
    pg.execute(migration)
    class PasswordTrialProvider(SQLPolicyProvider):
        async def claims(self,token,mfa=True):
            if mfa:raise HTTPException(401,'MFA required outside approved trial')
            return {'sub':ACTOR,'session_id':SESSION,'aal':'aal1'}
        async def auth(self,method,path,token=None,body=None):
            assert method=='POST' and path=='token?grant_type=password'
            return {'access_token':'synthetic-password-session'}
    provider=PasswordTrialProvider(pg)
    client=TestClient(build_app(trial,provider),base_url=HOST)
    assert client.get('/vault/v1/shells').status_code==401
    page=client.get('/auth/login');assert 'data-password-only-trial' in page.text
    csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
    response=client.post('/auth/login',headers={'Origin':HOST},data={'password':'fixed synthetic password','csrf':csrf})
    assert response.status_code==200 and response.json()=={'authenticated':True,'next':'/admin'}
    assert client.get('/vault/v1/shells').status_code==200
    assert '更改密碼' not in client.get('/admin').text
    assert client.get('/account/password').status_code==403
    csrf=client.get('/auth/me').json()['csrf_token']
    assert client.post('/vault/v1/shells',headers={'Origin':HOST},json={'academic_year':'2026','grade':'S1','subject':'test','curriculum_stream':'synthetic'}).status_code==403
    strict=TestClient(build_app(replace(trial,password_only_trial=False),provider),base_url=HOST)
    strict.cookies.update(client.cookies)
    assert strict.get('/vault/v1/shells').status_code==401
    pg.execute('update vault_private.admins set password_only_trial=false')
    assert client.get('/vault/v1/shells').status_code==403
