"""WP07 UI candidate-to-Gateway contract regression · IMPLEMENTED_UNTESTED.

Source-only authoring during Owner's coding-only sprint; DO NOT claim PASS
until this file is run on a reviewer-approved exact tested SHA.
"""
from html.parser import HTMLParser
from dataclasses import replace
from pathlib import Path
import sys

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
import pytest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'apps/a-vault'
sys.path.insert(0,str(APP))
from config import Settings
from vault_app import build_app


class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs={}
        self.ids=set()
        self.scripts=[]
    def handle_starttag(self,tag,attrs):
        attributes=dict(attrs)
        if attributes.get('id'):self.ids.add(attributes['id'])
        if tag=='input' and attributes.get('name'):
            self.inputs[attributes['name']]=attributes
        if tag=='script':self.scripts.append(attributes)


def settings(tmp_path):
    return Settings(admin_hash=PasswordHasher().hash('synthetic-ui-secret'),
        session_secret='s'*60,encryption_key='e'*60,school_id='synthetic-a',
        actor_id='synthetic-admin',sqlite_file=str(tmp_path/'wp07-fixture.sqlite3'),
        native_url='http://127.0.0.1:5055',native_password='synthetic-native-password-2026',
        store_backend='synthetic_sqlite')


@pytest.fixture
def client(tmp_path):
    with TestClient(build_app(settings(tmp_path),native=object())) as c:
        yield c


def login_form(client):
    response=client.get('/auth/login')
    assert response.status_code==200
    parser=Controls();parser.feed(response.text)
    return response,parser


def test_login_is_gateway_generated_not_public_unreplaced_template(client):
    response,controls=login_form(client)
    assert '__SUNRISE_LOGIN_CSRF__' not in response.text
    assert controls.inputs['csrf']['value']
    assert controls.inputs['password']['type']=='password'
    assert response.headers['cache-control']=='no-store'
    assert response.cookies.get('sunrise_a_login_csrf')
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'strict' in response.headers['set-cookie'].lower()
    assert '管理員登入' in response.text
    assert len(controls.scripts)==1
    assert controls.scripts[0].get('src')=='/assets/app.js'
    assert client.get('/templates/login.html').status_code==404


def test_login_supports_json_and_html_303_without_changing_auth(client):
    response,controls=login_form(client)
    csrf=controls.inputs['csrf']['value']
    denied=client.post('/auth/login',data={'csrf':'invalid','password':'synthetic-ui-secret'})
    assert denied.status_code==403
    accepted=client.post('/auth/login',headers={'Accept':'application/json'},
        data={'csrf':csrf,'password':'synthetic-ui-secret'})
    assert accepted.status_code==200 and accepted.json()['authenticated'] is True
    assert client.get('/auth/me').json()['school_id']=='synthetic-a'
    assert client.get('/admin').status_code==200

    # Native HTML form users must still receive the original server redirect.
    response,controls=login_form(client)
    redirected=client.post('/auth/login',headers={'Accept':'text/html'},follow_redirects=False,
        data={'csrf':controls.inputs['csrf']['value'],'password':'synthetic-ui-secret'})
    assert redirected.status_code==303
    assert redirected.headers['location']=='/admin'


def test_private_admin_csp_assets_dom_ids_and_no_inline_js(client):
    assert client.get('/admin').status_code==401
    response,controls=login_form(client)
    client.post('/auth/login',headers={'Accept':'application/json'},
        data={'csrf':controls.inputs['csrf']['value'],'password':'synthetic-ui-secret'})
    admin=client.get('/admin')
    assert admin.status_code==200 and admin.headers['cache-control']=='no-store'
    assert "script-src 'self'" in admin.headers['content-security-policy']
    assert "style-src 'self'" in admin.headers['content-security-policy']
    parser=Controls();parser.feed(admin.text)
    required={'workspace','active-school','pending','reconcile','logout',
        'create','upload','search','shells','shell-meta','materials','search-results',
        'archive','detail','refresh-materials','refresh-shells','notice','retry-session'}
    assert required.issubset(parser.ids)
    assert len(parser.scripts)==1 and parser.scripts[0].get('src')=='/assets/app.js'
    assert client.get('/api/sources').status_code==404
    js=client.get('/assets/app.js')
    css=client.get('/assets/style.css')
    assert js.status_code==200 and css.status_code==200
    assert "textContent" in js.text and "replaceChildren" in js.text
    assert "innerHTML" not in js.text and "localStorage" not in js.text
    assert "Idempotency-Key" in js.text and "credentials: 'same-origin'" in js.text
    assert '#detail' in css.text and '.dashboard' in css.text


def test_session_logout_revokes_admin_route(client):
    response,controls=login_form(client)
    client.post('/auth/login',headers={'Accept':'application/json'},
        data={'csrf':controls.inputs['csrf']['value'],'password':'synthetic-ui-secret'})
    token=client.get('/auth/me').json()['csrf_token']
    assert client.post('/auth/logout').status_code==403
    out=client.post('/auth/logout',headers={'X-CSRF-Token':token})
    assert out.status_code==200
    assert client.get('/admin').status_code==401



def test_trusted_two_school_switch_is_server_held_and_rotates_csrf(tmp_path):
    cfg=replace(settings(tmp_path),
        school_allowlist=('synthetic-a','synthetic-b'))
    with TestClient(build_app(cfg,native=object())) as client:
        response,controls=login_form(client)
        accepted=client.post('/auth/login',headers={'Accept':'application/json'},
            data={'csrf':controls.inputs['csrf']['value'],
                  'password':'synthetic-ui-secret'})
        assert accepted.status_code==200
        before=client.get('/auth/me').json()
        assert before['school_id']=='synthetic-a'
        assert set(before['available_schools'])=={'synthetic-a','synthetic-b'}
        assert client.get('/auth/me',
            headers={'X-School-ID':'synthetic-b'}).json()['school_id']=='synthetic-a'
        ui=client.get('/admin')
        assert ui.status_code==200
        html=Controls();html.feed(ui.text)
        assert {'switch-school','school-choice','switch-school-submit'}.issubset(html.ids)
        bad=client.post('/auth/school',
            headers={'X-CSRF-Token':before['csrf_token']},json={'school_id':'evil'})
        assert bad.status_code==403
        assert client.get('/auth/me').json()['school_id']=='synthetic-a'
        changed=client.post('/auth/school',
            headers={'X-CSRF-Token':before['csrf_token']},json={'school_id':'synthetic-b'})
        assert changed.status_code==200
        switched=client.get('/auth/me').json()
        assert switched['school_id']=='synthetic-b'
        assert switched['csrf_token']!=before['csrf_token']
        assert client.post('/auth/school',
            headers={'X-CSRF-Token':before['csrf_token']},
            json={'school_id':'synthetic-a'}).status_code==403
        assert client.get('/auth/me',
            headers={'X-School-ID':'synthetic-a'}).json()['school_id']=='synthetic-b'
        assert client.get('/vault/v1/shells').json()=={'shells':[]}
        assert client.post('/auth/logout',
            headers={'X-CSRF-Token':switched['csrf_token']}).status_code==200
        assert client.get('/admin').status_code==401


def test_unapproved_school_allowlist_fails_app_start(tmp_path):
    cfg=replace(settings(tmp_path),
        school_allowlist=('synthetic-b',))
    with pytest.raises(ValueError):
        build_app(cfg,native=object())
