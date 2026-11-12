"""Actual httpx adapter transport contract tests. No real Open Notebook/SurrealDB."""
import asyncio
import hashlib
import pathlib
import sys
import json
import httpx
import pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'apps'/'a-vault'))
from native import Native,NativeOwnershipError,NativeUnavailable


def run(coro):return asyncio.run(coro)


def test_native_http_create_upload_retrieve_download_exact_contract():
    requests=[];raw=b'%PDF-1.4\nsynthetic\n%%EOF'
    def handler(req):
        requests.append(req)
        assert req.headers['authorization']=='Bearer synthetic-native-secret'
        assert req.url.host=='127.0.0.1'
        if req.method=='POST' and req.url.path=='/api/notebooks':
            assert req.read().decode().find('Sunrise Math')>=0
            return httpx.Response(200,json={'id':'notebook:123'})
        if req.method=='POST' and req.url.path=='/api/sources':
            body=req.read()
            assert b'embed' in body and b'false' in body
            assert b'notebook:123' in body and b'synthetic.pdf' in body
            assert b'async_processing' in body
            return httpx.Response(200,json={'id':'source:123'})
        if req.method=='GET' and req.url.path=='/api/sources/source:123':
            return httpx.Response(200,json={'id':'source:123','notebooks':['notebook:123']})
        if req.method=='GET' and req.url.path=='/api/sources/source:123/download':
            return httpx.Response(200,content=raw)
        return httpx.Response(404)
    n=Native('http://127.0.0.1:8001','synthetic-native-secret',transport=httpx.MockTransport(handler))
    assert run(n.create_notebook('Sunrise Math'))=='notebook:123'
    assert run(n.upload_pdf('notebook:123',raw,'synthetic.pdf','Source'))['id']=='source:123'
    assert run(n.ensure_owned('source:123','notebook:123'))['id']=='source:123'
    assert run(n.original('source:123',hashlib.sha256(raw).hexdigest()))==raw
    assert len(requests)==4


def test_native_unreachable_fails_closed():
    def handler(req):raise httpx.ConnectError('offline')
    n=Native('http://127.0.0.1:8001','synthetic-native-secret',transport=httpx.MockTransport(handler))
    with pytest.raises(NativeUnavailable):run(n.create_notebook('name'))


def test_native_wrong_owner_blocks():
    def handler(req):return httpx.Response(200,json={'id':'source:own','notebooks':['notebook:other']})
    n=Native('http://127.0.0.1:8001','synthetic-native-secret',transport=httpx.MockTransport(handler))
    with pytest.raises(NativeOwnershipError):run(n.ensure_owned('source:own','notebook:expected'))


def test_native_vector_search_never_invokes_transport():
    called=[]
    def handler(req):called.append(req);return httpx.Response(200,json={'results':[]})
    n=Native('http://127.0.0.1:8001','synthetic-native-secret',transport=httpx.MockTransport(handler))
    with pytest.raises(NativeUnavailable):run(n.search('notebook:expected','中文'))
    assert [req.url.path for req in called] == ["/api/sunrise-patch-status"]


def test_native_original_hash_failure_rejects_bytes():
    def handler(req):return httpx.Response(200,content=b'foreign pdf bytes')
    n=Native('http://127.0.0.1:8001','synthetic-native-secret',transport=httpx.MockTransport(handler))
    with pytest.raises(NativeOwnershipError):run(n.original('source:own','0'*64))
