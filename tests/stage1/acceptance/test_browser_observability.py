"""Phase A pure-Python browser observability regressions; NOT Chromium E2E."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[3]
MODULE=ROOT/'scripts/stage1/browser_observability.py'


def load():
    spec=importlib.util.spec_from_file_location('stage1_browser_observability',MODULE)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('url,expected',[
    ('https://127.0.0.1:8765/auth/login','/auth/login'),
    ('https://127.0.0.1:8765/vault/v1/shells/secret-value/materials/source:SECRET/download',
     '/vault/v1/shells/{shell}/materials/{source}/download'),
    ('https://127.0.0.1:8765/admin?password=SECRET','/admin'),
    ('https://127.0.0.1:8765/unknown/SECRET?token=SECRET','/other'),
])
def test_path_redaction_never_exposes_secret_identifiers(url,expected):
    module=load()
    result=module.safe_path(url)
    assert result==expected
    assert 'SECRET' not in result and 'secret-value' not in result


def test_bounded_event_history_does_not_store_payloads_or_browser_errors():
    module=load()
    events=module.Events(max_events=3)
    for i in range(8):
        events.stage('S1B-SHELL')
        events.http('POST','https://localhost:8765/vault/v1/shells/private-key?token=SECRET',409)
    assert len(events.entries)<=3
    assert 'SECRET' not in str(events.entries)
    assert 'private-key' not in str(events.entries)


@pytest.mark.parametrize('kind,category',[
    ('browser_executable_missing','BROWSER_BINARY_MISSING'),
    ('net::ERR_CERT_AUTHORITY_INVALID','TLS_CERTIFICATE'),
    ('strict-mode selector timeout','SELECTOR_TIMEOUT'),
    ('pageerror','JAVASCRIPT_FAILURE'),
    ('requestfailed','REQUEST_FAILURE'),
    ('cookie rejected','COOKIE'),
    ('csrf rejected','CSRF'),
])
def test_failure_classification_scrubs_raw_exception_text(kind,category):
    module=load()
    assert module.classify_failure(kind)==category


def test_http_auth_classification_does_not_silence_401_403():
    module=load()
    assert module.http_category('/auth/login',401)=='LOGIN_AUTH_401'
    assert module.http_category('/auth/login',403)=='LOGIN_CSRF_403'
    assert module.http_category('/vault/v1/shells',401)=='HTTP_401'
    assert module.http_category('/vault/v1/shells',403)=='HTTP_403'
    assert module.http_category('/vault/v1/shells',503)=='HTTP_5XX'


def test_same_origin_blocks_loopback_port_swap_and_external():
    module=load()
    origin='https://127.0.0.1:8765'
    assert module.same_origin(origin+'/auth/login',origin)
    assert not module.same_origin('https://127.0.0.1:8766/admin',origin)
    assert not module.same_origin('https://evil.example/auth/login',origin)
    assert not module.same_origin('http://127.0.0.1:8765/admin',origin)


def test_worker_polling_empty_and_http_failures_are_explicit():
    module=load()
    assert module.worker_status([], 'expected-hash', 'expected-title')=='PENDING'
    assert module.worker_status([{'sha256':'expected-hash','title':'expected-title',
                                  'state':'FAILED','source_id':'source:one'}],
                                'expected-hash','expected-title')=='FAILED'
    assert module.worker_status([{'sha256':'expected-hash','title':'expected-title',
                                  'state':'READY','source_id':'source:one'}],
                                'expected-hash','expected-title')=='READY'
    with pytest.raises(module.BrowserContractError):
        module.worker_status([{'sha256':'expected-hash','title':'expected-title','state':'READY'},
                              {'sha256':'expected-hash','title':'expected-title','state':'READY'}],
                             'expected-hash','expected-title')


@pytest.mark.parametrize('status,location,accepted',[
    (303,'/admin',True),
    (200,'/admin',False),   # JSON API is NOT an HTML form redirect
    (302,'/admin',False),   # wrong redirect semantics
    (307,'/admin',False),
    (303,'https://attacker.invalid/admin',False),
    (303,'//attacker.invalid/admin',False),
    (303,'/admin?token=secret',False),
    (303,'/auth/login',False),
    (303,'/admin#redirect',False),
    (303,'',False),
    (True,'/admin',False),
])
def test_admin_html_login_must_redirect_303_to_relative_admin(status,location,accepted):
    module=load()
    assert module.valid_admin_login_redirect(status,location) is accepted
