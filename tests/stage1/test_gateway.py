"""Real FastAPI ASGI integration tests; fake Native only, never Native Runtime PASS."""
import hashlib
import io
import json
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import pytest
from argon2 import PasswordHasher
from reportlab.pdfgen import canvas

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'apps'/'a-vault'))
from config import Settings
from native import Native,NativeUnavailable,NativeOwnershipError
from vault_app import build_app


class NativeFixture:
    """No SurrealDB, worker, or native HTTP; suitable only for Gateway contract tests."""
    def __init__(self,lose_ack=False):
        self.lock=threading.Lock();self.notebooks=[];self.sources={};self.lose_ack=lose_ack
    async def create_notebook(self,name):
        with self.lock:
            value=f'notebook:{len(self.notebooks)+1}'
            self.notebooks.append((value,name))
        if self.lose_ack:raise NativeUnavailable('simulated acknowledgement loss AFTER commit')
        return value
    async def upload_pdf(self,notebook_id,data,filename,title):
        source_id=f'source:{len(self.sources)+1}'
        self.sources[source_id]={'id':source_id,'notebooks':[notebook_id],'bytes':data,'title':title}
        return {'id':source_id,'status':'new'}
    async def ensure_owned(self,source_id,notebook_id):
        src=self.sources[source_id]
        if src['notebooks']!=[notebook_id]:raise NativeOwnershipError('foreign link')
        return src
    async def original(self,source_id,digest):
        content=self.sources[source_id]['bytes']
        if hashlib.sha256(content).hexdigest()!=digest:raise NativeOwnershipError('hash mismatch')
        return content
    async def search(self,*args):raise NativeUnavailable('Unsafe vector fallback blocked')


def cfg(tmp_path,school='school-a'):
    return Settings(admin_hash=PasswordHasher().hash('only-synthetic-secret'),
        session_secret='s'*60,encryption_key='e'*60,school_id=school,actor_id='a-owner',
        sqlite_file=str(tmp_path/'synthetic-journal.db'),native_url='http://127.0.0.1:8001',
        native_password='private-test-password',store_backend='synthetic_sqlite')


def auth(client):
    resp=client.get('/auth/login')
    assert resp.status_code==200
    import itsdangerous
    # Test extracts hidden login CSRF from HTML (exactly what an authorized browser receives)
    from html.parser import HTMLParser
    class Parser(HTMLParser):
        csrf=None
        def handle_starttag(self,tag,attrs):
            d=dict(attrs)
            if tag=='input' and d.get('name')=='csrf':self.csrf=d['value']
    parser=Parser();parser.feed(resp.text)
    out=client.post('/auth/login',data={'password':'only-synthetic-secret','csrf':parser.csrf})
    assert out.status_code==200,out.text
    return {'X-CSRF-Token':out.json()['csrf_token']}


def pdf_bytes():
    f=io.BytesIO()
    p=canvas.Canvas(f);p.drawString(40,770,'Synthetic math lesson - no school data');p.save()
    return f.getvalue()


@pytest.fixture
def env(tmp_path):
    backend=NativeFixture()
    app=build_app(cfg(tmp_path),native=backend)
    with TestClient(app) as c:
        yield c,backend,app


def create(c,headers,year='2026'):
    body={'academic_year':year,'grade':'P4','subject':'Math','curriculum_stream':'HK'}
    return c.post('/vault/v1/shells',json=body,headers={**headers,'Idempotency-Key':'unique-operation'})


def test_requires_real_configuration(tmp_path):
    base=cfg(tmp_path)
    from dataclasses import replace
    for modification in [dict(admin_hash='abc'),dict(session_secret='short'),dict(encryption_key=''),
        dict(native_url='https://example.com'),dict(native_password='root'),dict(school_id=''),
        dict(service_issuer='foo')]:
        with pytest.raises(ValueError):build_app(replace(base,**modification))



def test_formal_surreal_gateway_rejects_missing_maintenance_at_startup(tmp_path):
    """Validate formal configuration before opening a Surreal connection."""
    from dataclasses import replace
    base=cfg(tmp_path)
    with pytest.raises(ValueError,match='VAULT_MAINTENANCE_FILE'):
        replace(base,store_backend='surreal').validate()


@pytest.mark.parametrize('bad_path',[
    'relative/maintenance.lock',
    'missing-parent',
])
def test_maintenance_path_invalid_configuration_fails_closed(tmp_path,bad_path):
    from dataclasses import replace
    candidate = str(tmp_path/'nonexistent'/'maintenance.lock') if bad_path=='missing-parent' else bad_path
    with pytest.raises(ValueError,match='Maintenance flag'):
        replace(cfg(tmp_path),maintenance_file=candidate).validate()


def test_formal_surreal_maintenance_configured_before_gateway_open(tmp_path):
    from dataclasses import replace
    path=tmp_path/'maintenance.lock'
    configured=replace(cfg(tmp_path),
        store_backend='surreal',maintenance_file=str(path),
        surreal_ws_url='ws://127.0.0.1:8000/rpc',
        surreal_user='synthetic_test_user',
        surreal_password='synthetic-private-db-password-at-least-24',
        surreal_namespace='sunrise_a',surreal_database='synthetic')
    assert configured.validate().maintenance_file==str(path)
    assert not path.exists()  # startup validation never creates freeze flag


def test_maintenance_symlink_and_directory_rejected(tmp_path):
    from dataclasses import replace
    real=tmp_path/'real.lock'
    real.touch()
    link=tmp_path/'alias.lock'
    link.symlink_to(real)
    for path in (link,tmp_path):
        with pytest.raises(ValueError,match='Maintenance flag'):
            replace(cfg(tmp_path),maintenance_file=str(path)).validate()


def test_gateway_health_attests_configured_maintenance_path_and_freeze(tmp_path):
    from dataclasses import replace
    flag=tmp_path/'maintenance.lock'
    settings=replace(cfg(tmp_path),maintenance_file=str(flag))
    with TestClient(build_app(settings,native=NativeFixture())) as client:
        before=client.get('/health')
        assert before.status_code==200
        body=before.json()
        assert body['gateway']=='running'
        assert body['maintenance'] is False
        assert body['maintenance_path_sha256']==hashlib.sha256(
            str(flag).encode('utf-8')).hexdigest()
        assert len(body['gateway_instance'])==32
        assert body['mutations_in_flight']==0
        flag.write_text('synthetic freeze test',encoding='utf-8')
        frozen=client.get('/health')
        assert frozen.status_code==200
        assert frozen.json()['maintenance'] is True
        assert frozen.json()['gateway_instance']==body['gateway_instance']
        assert frozen.json()['maintenance_path_sha256']==body['maintenance_path_sha256']
        assert client.get('/auth/login').status_code==503
        flag.unlink()
        assert client.get('/auth/login').status_code==200


def test_login_session_logout_and_no_docs(env):
    c,_,_=env
    assert c.get('/vault/v1/shells').status_code==401
    assert c.get('/openapi.json').status_code==404
    assert c.get('/docs').status_code==404
    assert 'Sunrise A Vault' in c.get('/auth/login').text
    headers=auth(c)
    assert c.get('/auth/me').json()['school_id']=='school-a'
    assert c.get('/admin').status_code==200
    assert c.get('/assets/app.js').status_code==200
    assert c.get('/vault/v1/shells').status_code==200
    assert c.post('/auth/logout').status_code==403
    assert c.post('/auth/logout',headers=headers).status_code==200
    assert c.get('/vault/v1/shells').status_code==401


def test_login_bad_password_and_login_csrf(env):
    c,_,_=env
    assert c.post('/auth/login',data={'password':'whatever','csrf':'not-signed'}).status_code==403
    c.get('/auth/login')
    assert c.post('/auth/login',data={'password':'whatever','csrf':'bad'}).status_code==403


def test_rate_limit(env):
    c,_,_=env
    for _ in range(8): c.post('/auth/login',data={'password':'bad','csrf':'bad'})
    assert c.post('/auth/login',data={'password':'bad','csrf':'bad'}).status_code==429


def test_shell_create_replay_and_conflict(env):
    c,n,_=env;headers=auth(c)
    assert create(c,{}).status_code==403
    first=create(c,headers)
    assert first.status_code==201,first.text
    assert first.json()['notebook_id']=='notebook:1'
    second=create(c,headers)
    assert second.status_code==200 and second.json()['shell_id']==first.json()['shell_id']
    assert len(n.notebooks)==1
    conflict=create(c,headers,year='2027')
    assert conflict.status_code==409
    shell=c.get('/vault/v1/shells').json()['shells']
    assert len(shell)==1 and shell[0]['school_id']=='school-a'
    assert c.get('/vault/v1/shells/'+shell[0]['shell_id']).status_code==200
    assert c.get('/vault/v1/shells/other').status_code==404


def test_ack_loss_never_duplicated_even_after_restart(tmp_path):
    n=NativeFixture(lose_ack=True)
    config=cfg(tmp_path)
    with TestClient(build_app(config,native=n)) as c:
        headers=auth(c)
        assert create(c,headers).status_code==503
        assert create(c,headers).status_code==503
        assert len(n.notebooks)==1
    n.lose_ack=False
    with TestClient(build_app(config,native=n)) as c:
        headers=auth(c)
        assert create(c,headers).status_code==503
        assert len(n.notebooks)==1
    # Explicit limitation: the committed ON notebook exists but is not safely adopted.


def test_no_arbitrary_school_header(env):
    c,_,_=env;headers=auth(c)
    created=create(c,{**headers,'X-School-ID':'school-b'})
    assert created.status_code==201
    assert created.json()['school_id']=='school-a'


def test_cross_school_rejects_even_id_known(tmp_path):
    backend=NativeFixture()
    with TestClient(build_app(cfg(tmp_path,'school-a'),native=backend)) as a:
        h=auth(a);own=create(a,h).json()['shell_id']
    with TestClient(build_app(cfg(tmp_path,'school-b'),native=backend)) as b:
        auth(b)
        assert b.get('/vault/v1/shells/'+own).status_code==404
        assert b.get('/vault/v1/shells').json()['shells']==[]
        assert b.get(f'/vault/v1/shells/{own}/materials').status_code==404


def test_pdf_upload_owner_verified_hash_download_and_archive(env):
    c,n,_=env;headers=auth(c)
    shell=create(c,headers).json()['shell_id'];pdf=pdf_bytes()
    form={'title':'Synthetic Algebra','license':'synthetic','retention':'test-only'}
    received=c.post(f'/vault/v1/shells/{shell}/materials',headers={**headers,'Idempotency-Key':'upload1'},data=form,files={'file':('math.pdf',pdf,'application/pdf')})
    assert received.status_code==201,received.text
    replay=c.post(f'/vault/v1/shells/{shell}/materials',headers={**headers,'Idempotency-Key':'upload1'},data=form,files={'file':('math.pdf',pdf,'application/pdf')})
    assert replay.status_code==200 and replay.json()['source_id']==received.json()['source_id']
    source=received.json()['source_id']
    assert received.json()['sha256']==hashlib.sha256(pdf).hexdigest()
    listing=c.get(f'/vault/v1/shells/{shell}/materials')
    assert len(listing.json()['materials'])==1
    down=c.get(f'/vault/v1/shells/{shell}/materials/{source}/download')
    assert down.status_code==200 and down.content==pdf
    n.sources[source]['notebooks']=['notebook:foreign']
    assert c.get(f'/vault/v1/shells/{shell}/materials/{source}/download').status_code==403
    n.sources[source]['notebooks']=['notebook:1']
    assert c.post(f'/vault/v1/shells/{shell}/archive',headers=headers).status_code==200
    assert c.post(f'/vault/v1/shells/{shell}/materials',headers={**headers,'Idempotency-Key':'upload2'},data=form,files={'file':('math.pdf',pdf,'application/pdf')}).status_code==409


def test_search_fails_closed_native_no_vector(env):
    c,_,_=env;h=auth(c);s=create(c,h).json()['shell_id']
    r=c.post(f'/vault/v1/shells/{s}/search',json={'query':'繁體中文'},headers=h)
    assert r.status_code==503 and 'results' not in r.text
    assert c.post(f'/vault/v1/shells/{s}/search',json={'query':'繁體中文'}).status_code==403


def test_pdf_invalid_rejected_before_native_call(env):
    c,n,_=env;h=auth(c);s=create(c,h).json()['shell_id']
    for filename,body in [('x.pdf',b'not pdf'),('../path.pdf',pdf_bytes()),('x.txt',pdf_bytes())]:
        r=c.post(f'/vault/v1/shells/{s}/materials',headers=h,data={'title':'x','license':'synthetic','retention':'test'},files={'file':(filename,body,'application/pdf')})
        assert r.status_code==422,r.text
    assert not n.sources


def test_invalid_service_bearer_denied(env):
    c,_,_=env
    assert c.get('/vault/v1/shells',headers={'Authorization':'Bearer bad'}).status_code==401


def test_origin_and_frame_denied(env):
    c,_,_=env;h=auth(c)
    assert c.post('/vault/v1/shells',headers={**h,'Origin':'https://attacker.example','Idempotency-Key':'origin-check'},json={'academic_year':'2026','grade':'P4','subject':'Math','curriculum_stream':'HK'}).status_code==403
    assert c.get('/health').headers['x-frame-options']=='DENY'
    assert c.get('/health').json()['release']=='NOT_APPROVED'


def test_native_adapter_construction_no_public_url(tmp_path):
    with pytest.raises(ValueError):build_app(__import__('dataclasses').replace(cfg(tmp_path),native_url='http://169.254.169.254'))


def test_persist_shell_after_process_restart(tmp_path):
    n=NativeFixture();config=cfg(tmp_path)
    with TestClient(build_app(config,native=n)) as c:
        h=auth(c);shell=create(c,h).json()['shell_id']
    with TestClient(build_app(config,native=n)) as c:
        auth(c)
        assert c.get('/vault/v1/shells/'+shell).status_code==200
        assert c.get('/vault/v1/shells').json()['shells'][0]['shell_id']==shell


def test_material_ack_loss_fails_closed_no_duplicate_after_restart(tmp_path):
    n=NativeFixture();config=cfg(tmp_path)
    with TestClient(build_app(config,native=n)) as c:
        h=auth(c);shell=create(c,h).json()['shell_id'];raw=pdf_bytes()
        class AckLossNative(NativeFixture):
            async def upload_pdf(self,notebook_id,data,filename,title):
                result=await super().upload_pdf(notebook_id,data,filename,title)
                raise NativeUnavailable('ACK lost after native source created')
        fail=AckLossNative();fail.notebooks=n.notebooks
    with TestClient(build_app(config,native=fail)) as c:
        h=auth(c)
        args={'headers':{**h,'Idempotency-Key':'upload-ack-lost'},'data':{'title':'x','license':'test','retention':'test'},
              'files':{'file':('synthetic.pdf',raw,'application/pdf')}}
        path=f'/vault/v1/shells/{shell}/materials'
        assert c.post(path,**args).status_code==503
        assert c.post(path,**args).status_code==503
        assert len(fail.sources)==1
    with TestClient(build_app(config,native=fail)) as c:
        h=auth(c);args['headers']['X-CSRF-Token']=h['X-CSRF-Token']
        assert c.post(path,**args).status_code==503
        assert len(fail.sources)==1


def test_service_token_verified_claims_and_scope(tmp_path):
    from dataclasses import replace
    import time,jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    pub=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    config=replace(cfg(tmp_path),service_public_key=pub,service_issuer='synthetic-issuer',service_audience='sunrise-a')
    with TestClient(build_app(config,native=NativeFixture())) as client:
        t=int(time.time());claims={'sub':'synthetic-service','school_id':'school-a','iss':'synthetic-issuer','aud':'sunrise-a',
            'iat':t,'nbf':t,'exp':t+120,'jti':'synthetic-token-id','scope':'vault.shell.read vault.materials.read'}
        def call(payload):
            token=jwt.encode(payload,key,algorithm='RS256')
            return client.get('/vault/v1/shells',headers={'Authorization':'Bearer '+token})
        assert call(claims).status_code==200
        assert call({**claims,'school_id':'school-b'}).status_code==403
        assert call({**claims,'scope':'vault.materials.write'}).status_code==403
        assert call({**claims,'exp':t+600}).status_code==403
        assert call({**claims,'iss':'other'}).status_code==401
        assert call({k:v for k,v in claims.items() if k!='jti'}).status_code==401
        # Admin-owned POST does not grant service right without corresponding scope
        token=jwt.encode(claims,key,algorithm='RS256')
        assert client.post('/vault/v1/shells',headers={'Authorization':'Bearer '+token,'Idempotency-Key':'1'},json={
            'academic_year':'2026','grade':'P4','subject':'Math','curriculum_stream':'HK'}).status_code==403


def test_browser_login_redirects_to_owner_ui(env):
    c,_,_=env
    page=c.get('/auth/login')
    from html.parser import HTMLParser
    class Parser(HTMLParser):
        csrf=None
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if tag=='input' and a.get('name')=='csrf':self.csrf=a['value']
    p=Parser();p.feed(page.text)
    response=c.post('/auth/login',headers={'Accept':'text/html'},data={'password':'only-synthetic-secret','csrf':p.csrf},follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='/admin'
    assert c.get('/admin').status_code==200


def test_ack_loss_new_key_cannot_bypass_quarantine(tmp_path):
    native=NativeFixture(lose_ack=True)
    with TestClient(build_app(cfg(tmp_path),native=native)) as c:
        h=auth(c);first=create(c,h)
        assert first.status_code==503
        second=c.post('/vault/v1/shells',json={'academic_year':'2026','grade':'P4','subject':'Math','curriculum_stream':'HK'},
                      headers={**h,'Idempotency-Key':'attempt-new-key'})
        assert second.status_code==409 and len(native.notebooks)==1


def test_pdf_upload_new_key_cannot_bypass_uncertain_result(tmp_path):
    class SourceAckLoss(NativeFixture):
        async def upload_pdf(self,nb,data,filename,title):
            await super().upload_pdf(nb,data,filename,title)
            raise NativeUnavailable('lost')
    n=SourceAckLoss()
    with TestClient(build_app(cfg(tmp_path),native=n)) as c:
        h=auth(c);s=create(c,h).json()['shell_id'];file=pdf_bytes()
        opts={'data':{'title':'Sample','license':'synthetic','retention':'testing'},'files':{'file':('f.pdf',file,'application/pdf')}}
        route=f'/vault/v1/shells/{s}/materials'
        assert c.post(route,headers={**h,'Idempotency-Key':'original-key'},**opts).status_code==503
        assert c.post(route,headers={**h,'Idempotency-Key':'another-key'},**opts).status_code==409
        assert len(n.sources)==1
