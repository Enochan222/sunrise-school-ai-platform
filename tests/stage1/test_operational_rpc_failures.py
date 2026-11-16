"""Operational outage regressions: safe HTTP failure, phase evidence, no replay."""
import json
import logging
import asyncio
from pathlib import Path
import sys

import pytest
import httpx
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'apps/a-vault'))
import surreal_store
from config import Settings
from surreal_store import RPC, SurrealConfig, SurrealUnavailable
from vault_app import build_app
from native import Native, NativeUnavailable


@pytest.fixture
def app(tmp_path):
    return build_app(Settings(
        admin_hash=PasswordHasher().hash('synthetic-outage-password'),
        session_secret='s' * 60, encryption_key='e' * 60,
        school_id='synthetic-a', actor_id='synthetic-admin',
        sqlite_file=str(tmp_path / 'outage.sqlite3'),
        native_url='http://127.0.0.1:5055',
        native_password='synthetic-native-password-2026',
        store_backend='synthetic_sqlite'), native=object())


def login(client):
    from html.parser import HTMLParser
    class Form(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'input' and attrs.get('name') == 'csrf':
                self.csrf = attrs['value']
    form = Form()
    form.feed(client.get('/auth/login').text)
    return client.post('/auth/login', data={
        'csrf': form.csrf, 'password': 'synthetic-outage-password'})


@pytest.mark.parametrize('operation', ['list', 'credentials', 'login'])
def test_db_outage_is_safe_503_without_retry_or_cookie(app, monkeypatch, operation):
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(1)
        raise SurrealUnavailable('PRIVATE_PASSWORD SELECT private_table;')
    with TestClient(app, raise_server_exceptions=False) as client:
        if operation != 'login':
            assert login(client).status_code == 200
        if operation == 'list':
            monkeypatch.setattr(app.state.store, 'list_shells', unavailable)
            response = client.get('/vault/v1/shells')
        elif operation == 'credentials':
            monkeypatch.setattr(app.state.store, 'session', unavailable)
            response = client.get('/auth/me')
        else:
            monkeypatch.setattr(app.state.store, 'add_session', unavailable)
            response = login(client)
            assert 'sunrise_a_sid' not in response.cookies
        assert response.status_code == 503
        assert response.json() == {'detail': 'A database unavailable; operation outcome unconfirmed'}
        assert response.headers['cache-control'] == 'no-store'
        assert 'PRIVATE_PASSWORD' not in response.text
        assert 'private_table' not in response.text
        assert len(calls) == 1  # An uncertain write must never be replayed.


@pytest.mark.parametrize('failure_phase', ['connect', 'signin', 'use', 'query'])
def test_rpc_failure_records_phase_without_payload_or_retry(monkeypatch, caplog, failure_phase):
    sockets = []
    class Socket:
        def __enter__(self):
            if failure_phase == 'connect':
                raise TimeoutError('PRIVATE_PASSWORD handshake')
            return self
        def __exit__(self, *args):
            return False
        def send(self, data):
            self.last = json.loads(data)
        def recv(self, **kwargs):
            if self.last['method'] == failure_phase:
                raise TimeoutError('PRIVATE_PASSWORD payload')
            return json.dumps({'id': self.last['id'], 'result': None})
    def connect(*args, **kwargs):
        sockets.append(Socket())
        return sockets[-1]
    monkeypatch.setattr(surreal_store, 'connect', connect)
    cfg = SurrealConfig('ws://127.0.0.1:8000/rpc', 'synthetic-root',
                        'PRIVATE_PASSWORD' * 3, 'synthetic_ns', 'synthetic_db')
    with caplog.at_level(logging.WARNING, logger='surreal_store'):
        with pytest.raises(SurrealUnavailable):
            RPC(cfg).query('CREATE private_table CONTENT $secret;', {'secret': 'PRIVATE_PAYLOAD'})
    assert len(sockets) == 1
    assert f'phase={failure_phase}' in caplog.text
    assert 'elapsed_ms=' in caplog.text
    for private in ['PRIVATE_PASSWORD', 'PRIVATE_PAYLOAD', 'private_table', 'synthetic-root', 'synthetic_ns']:
        assert private not in caplog.text


@pytest.mark.parametrize('failure', ['read_timeout', 'write_timeout', 'http_503'])
def test_native_failure_diagnostics_do_not_leak_or_replay(caplog, failure):
    calls = []
    def transport(request):
        calls.append(request)
        if failure == 'read_timeout':
            raise httpx.ReadTimeout('PRIVATE_TRANSPORT_MESSAGE', request=request)
        if failure == 'write_timeout':
            raise httpx.WriteTimeout('PRIVATE_TRANSPORT_MESSAGE', request=request)
        return httpx.Response(503, text='PRIVATE_RESPONSE')
    native = Native('http://127.0.0.1:5055', 'PRIVATE_NATIVE_SECRET_2026',
                    transport=httpx.MockTransport(transport))
    with caplog.at_level(logging.WARNING, logger='native'):
        with pytest.raises(NativeUnavailable):
            asyncio.run(native._request('POST', '/api/sources/PRIVATE_SOURCE_ID',
                                        json={'private': 'PRIVATE_BODY'}))
    assert len(calls) == 1
    assert 'endpoint=source' in caplog.text
    assert 'elapsed_ms=' in caplog.text
    for private in ['PRIVATE_TRANSPORT_MESSAGE', 'PRIVATE_RESPONSE', 'PRIVATE_NATIVE_SECRET_2026',
                    'PRIVATE_SOURCE_ID', 'PRIVATE_BODY']:
        assert private not in caplog.text
