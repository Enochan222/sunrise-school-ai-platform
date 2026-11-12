"""Pinned API wire contract and fail-closed download/search tests (MockTransport, not native runtime)."""
import asyncio
import hashlib
import io
import json
import pathlib
import sys

import httpx
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]/'apps'/'a-vault'))
from native import Native, NativeOwnershipError, NativeUnavailable


def run(coro):
    return asyncio.run(coro)


def adapter(handler, *, verified=False, max_bytes=25*1024*1024):
    return Native('http://127.0.0.1:8001', 'synthetic-native-secret',
                  transport=httpx.MockTransport(handler), text_only_verified=verified,
                  max_download_bytes=max_bytes)


@pytest.mark.parametrize('notebook_id', [
    'notebook:', 'source:evil', 'notebook:a"],"notebook:evil', 'notebook:x/y',
    'notebook:x?y', 'notebook:x#fragment', 'notebook:x%2Fy', 'notebook:☃', None, '',
])
def test_upload_rejects_malformed_or_injected_notebook_without_request(notebook_id):
    requested = []
    def handler(req):
        requested.append(req)
        return httpx.Response(200, json={'id': 'source:1'})
    with pytest.raises(NativeOwnershipError):
        run(adapter(handler).upload_pdf(notebook_id, b'%PDF-1.4\n%%EOF', 'synthetic.pdf', 'Synthetic'))
    assert requested == []


def test_upload_notebook_list_uses_json_encoding_and_embedding_off():
    seen=[]
    def handler(req):
        seen.append(req.read())
        return httpx.Response(200, json={'id': 'source:234'})
    r=run(adapter(handler).upload_pdf('notebook:abc_123', b'%PDF-1.4\n%%EOF', 'test.pdf', 'title'))
    assert r['id']=='source:234'
    assert len(seen)==1
    body=seen[0]
    assert b'["notebook:abc_123"]' in body
    assert b'false' in body
    assert b'async_processing' in body


@pytest.mark.parametrize('source_id', ['notebook:1', 'source:', 'source:x/y', 'source:x#f', 'source:a?b', 'source:☃'])
def test_download_rejects_invalid_source_id_before_request(source_id):
    seen=[]
    def handler(req):
        seen.append(req)
        return httpx.Response(200, content=b'%PDF-1.4\n%%EOF')
    with pytest.raises(NativeOwnershipError):
        run(adapter(handler).original(source_id, '0'*64))
    assert seen==[]


def test_original_rejects_large_content_length_before_reading_stream():
    class GuardedBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError('must never consume oversized body')
            yield b'x'
    def handler(req):
        return httpx.Response(200, headers={'Content-Length': '100'}, stream=GuardedBody())
    with pytest.raises(NativeOwnershipError, match='exceeds'):
        run(adapter(handler, max_bytes=8).original('source:ok','0'*64))


def test_original_rejects_chunked_oversize_before_returning_any_bytes():
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b'%PDF-1.'
            yield b'4-more-bytes'
    def handler(req):return httpx.Response(200, stream=Chunks())
    with pytest.raises(NativeOwnershipError,match='exceeds'):
        run(adapter(handler,max_bytes=8).original('source:ok','0'*64))


def test_original_validates_sha_for_bounded_chunked_payload():
    content=b'%PDF-1.4\nsynthetic\n%%EOF'
    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield content[:5]
            yield content[5:]
    n=adapter(lambda req:httpx.Response(200,stream=Chunks()),max_bytes=200)
    assert run(n.original('source:ok',hashlib.sha256(content).hexdigest()))==content


def test_original_never_follows_redirect():
    n=adapter(lambda req:httpx.Response(302,headers={'Location':'https://attacker.invalid/secret'}))
    with pytest.raises(NativeUnavailable):run(n.original('source:ok','0'*64))


def test_text_search_requires_verified_native_patch_and_nonempty_notebook():
    seen=[]
    def handler(req):
        seen.append(req)
        return httpx.Response(200,json={'search_type':'text','results':[]})
    with pytest.raises(NativeUnavailable):run(adapter(handler).search('notebook:ok','繁體中文'))
    with pytest.raises(NativeOwnershipError):run(adapter(handler,verified=True).search('notebook:','繁體中文'))
    assert seen==[]


def test_text_search_uses_exact_single_scope_type_and_no_notes():
    seen=[]
    def handler(req):
        assert req.url.path=='/api/search'
        data=json.loads(req.content)
        seen.append(data)
        return httpx.Response(200,json={'search_type':'text','results':[{'parent_id':'source:expected','relevance':1.0}]})
    result=run(adapter(handler,verified=True).search('notebook:owned','小學數學',5))
    assert result[0]['parent_id']=='source:expected'
    assert seen==[{'query':'小學數學','type':'text','limit':5,'notebook_ids':['notebook:owned'],
                   'search_sources':True,'search_notes':False}]


@pytest.mark.parametrize('payload',[
    {'search_type':'vector','results':[]},
    {'search_type':'text','results':[{'parent_id':'source:good'},{'parent_id':'note:bad'}]},
    {'search_type':'text','results':[{'parent_id':'source:good'},{'parent_id':'source:good'}]*25},
    {'search_type':'text','results':'not-a-list'},
    {'search_type':'text','results':[{'parent_id':'source:foo/route'}]},
])
def test_text_search_rejects_unverifiable_results(payload):
    with pytest.raises(NativeUnavailable):
        run(adapter(lambda req:httpx.Response(200,json=payload),verified=True).search('notebook:owned','math',10))


def test_native_overflow_http_500_is_error_not_empty_results():
    with pytest.raises(NativeUnavailable):
        run(adapter(lambda req:httpx.Response(500,json={'detail':'position overflow'}),verified=True).search('notebook:owned','math'))
