"""SurrealDB A journal contract checks; actual database test is a separate runtime gate."""
import importlib.util
import pathlib
import sys
from dataclasses import replace

import pytest
from argon2 import PasswordHasher

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from config import Settings
from native import Native,NativeOwnershipError,NativeUnavailable
from surreal_store import SCHEMA,SurrealConfig,SurrealStore,_record,_digest
from store import Indeterminate
import asyncio
import httpx


def test_real_backend_selected_by_default_and_missing_credentials_fails_start(tmp_path):
    cfg=Settings(admin_hash=PasswordHasher().hash('synthetic'),session_secret='S'*56,
        encryption_key='E'*56,school_id='synthetic-a',actor_id='admin',sqlite_file='',
        native_url='http://127.0.0.1:5055',native_password='synthetic-native-password')
    assert cfg.store_backend=='surreal'
    with pytest.raises(ValueError,match='database'):
        cfg.validate()
    assert replace(cfg,store_backend='synthetic_sqlite',sqlite_file=str(tmp_path/'synthetic.sqlite')).validate()


@pytest.mark.parametrize('url',["ws://example.com:8000/rpc","wss://surrealdb:8000/rpc",
    "ws://127.0.0.1:8000/sql","ws://root:password@127.0.0.1:8000/rpc"])
def test_surreal_only_private_socket_url(url):
    with pytest.raises(ValueError):
        SurrealConfig(url,'synthetic_user','long-random-synthetic-password-2026').validate()


def test_required_unique_indexes_and_op_tables():
    for table in ('content_shell','vault_operation','vault_scope_claim','source_owner','vault_session'):
        assert f'DEFINE TABLE IF NOT EXISTS {table} ' in SCHEMA
    for index in ('shell_scope_unique','shell_notebook_unique','op_key_unique','scope_key_unique','source_id_unique'):
        assert index in SCHEMA and 'UNIQUE' in SCHEMA
    assert 'IF NOT EXISTS' in SCHEMA


def test_transaction_identifiers_opaque_and_key_bound():
    assert _record('vault_operation','a','actor','shell','key') != _record('vault_operation','b','actor','shell','key')
    assert _record('content_shell','a','id').startswith('content_shell:')
    assert 'school-b' not in _record('content_shell','school-b','my-id')
    assert _digest({'a':1,'b':2})==_digest({'b':2,'a':1})


def test_native_marker_create_and_exact_readback():
    marker='sunrise-a-op-v1:'+'a'*64
    paths=[]
    def handler(request):
        paths.append(request.url.path)
        if request.url.path=='/api/notebooks' and request.method=='POST':
            assert request.read().decode().count(marker)==1
            return httpx.Response(200,json={'id':'notebook:single'})
        if request.url.path=='/api/notebooks':
            return httpx.Response(200,json=[{'id':'notebook:single','name':'do not use title','description':marker},
                                           {'id':'notebook:foreign','description':'another-marker'}])
        if request.url.path=='/api/notebooks/notebook:single':
            return httpx.Response(200,json={'id':'notebook:single','description':marker})
        return httpx.Response(404)
    n=Native('http://127.0.0.1:5055','synthetic-native-password',transport=httpx.MockTransport(handler))
    assert asyncio.run(n.create_notebook('Math',marker=marker))=='notebook:single'
    assert asyncio.run(n.find_notebooks_by_marker(marker))==['notebook:single']
    assert paths==['/api/notebooks','/api/notebooks','/api/notebooks/notebook:single']


def test_native_duplicate_marker_causes_quarantine_not_adoption():
    marker='sunrise-a-op-v1:'+'b'*64
    def handler(req):return httpx.Response(200,json=[{'id':'notebook:one','description':marker},
                                                     {'id':'notebook:two','description':marker}])
    n=Native('http://127.0.0.1:5055','synthetic-native-password',transport=httpx.MockTransport(handler))
    with pytest.raises(NativeOwnershipError):
        asyncio.run(n.find_notebooks_by_marker(marker))


def test_unknown_native_marker_is_not_title_search():
    marker='sunrise-a-op-v1:'+'c'*64
    def handler(req):return httpx.Response(200,json=[{'id':'notebook:one','name':marker,'description':'unrelated'}])
    n=Native('http://127.0.0.1:5055','synthetic-native-password',transport=httpx.MockTransport(handler))
    assert asyncio.run(n.find_notebooks_by_marker(marker))==[]


def test_live_surreal_not_misreported_as_pass_when_unavailable(monkeypatch):
    # Real integration executed only by explicit synthetic host script, not fake success.
    from pathlib import Path
    smoke=ROOT/'scripts/stage1/surreal_journal_smoke.py'
    assert smoke.is_file() and 'RUNTIME_NOT_RUN' in smoke.read_text()
    assert 'os._exit(97)' in smoke.read_text()
