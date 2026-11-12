"""Native search contract: an ENV flag cannot bypass live patched-runtime proof.

These use an HTTPX transport double. Real runtime remains NOT_RUN.
"""
import asyncio
import inspect
import json
import pathlib
import sys
import httpx
import pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'apps'/'a-vault'))
from native import Native, NativeUnavailable


def make_native(handler):
    kwargs={'transport':httpx.MockTransport(handler)}
    if 'text_only_verified' in inspect.signature(Native).parameters:
        kwargs['text_only_verified']=True
    return Native('http://127.0.0.1:5055','synthetic-private-password',**kwargs)


def test_wrong_runtime_patch_marker_blocks_search_post():
    called=[]
    def handler(req):
        called.append(req.url.path)
        return httpx.Response(200,json={'marker':'unpatched','text_only':False})
    native=make_native(handler)
    with pytest.raises(NativeUnavailable):
        asyncio.run(native.search('notebook:only','繁體中文'))
    assert called == ['/api/sunrise-patch-status']


def test_patch_attestation_and_single_notebook_text_only_contract():
    called=[]
    def handler(req):
        called.append(req.url.path)
        if req.url.path.endswith('patch-status'):
            return httpx.Response(200,json={'marker':'sunrise-a-text-only-no-vector-v1','text_only':True})
        payload=json.loads(req.read())
        assert req.url.path=='/api/search'
        assert payload['type']=='text'
        assert payload['notebook_ids']==['notebook:only']
        assert payload['search_notes'] is False
        return httpx.Response(200,json={'search_type':'text','results':[{'parent_id':'source:one'}]})
    native=make_native(handler)
    result=asyncio.run(native.search('notebook:only','繁體中文'))
    assert result[0]['parent_id']=='source:one'
    assert called==['/api/sunrise-patch-status','/api/search']
