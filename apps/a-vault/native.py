"""Strict allowlist adapter to pinned Open Notebook v1.15.1 private native HTTP.

No browser receives raw native credentials or URLs. No unsafe native retry or vector search.
"""
import hashlib
import hmac
import httpx


class NativeUnavailable(Exception): pass
class NativeOwnershipError(Exception): pass


class Native:
    def __init__(self,base_url,secret,transport=None):
        self.base=base_url.rstrip('/')
        self.secret=secret
        self.transport=transport

    async def _request(self,method,path,**kwargs):
        # Only fixed path templates constructed by this module are permitted.
        headers={'Authorization':f'Bearer {self.secret}','Accept':'application/json'}
        async with httpx.AsyncClient(base_url=self.base,timeout=20,transport=self.transport,trust_env=False) as client:
            try:
                r=await client.request(method,path,headers=headers,**kwargs)
                r.raise_for_status()
                if kwargs.get('stream'):
                    raise NativeUnavailable('Streaming is intentionally disabled')
                return r
            except (httpx.RequestError,httpx.HTTPStatusError) as e:
                raise NativeUnavailable('Native Open Notebook request unavailable or rejected') from e

    async def create_notebook(self,name):
        r=await self._request('POST','/api/notebooks',json={'name':name,'description':'Sunrise A synthetic private notebook'})
        data=r.json()
        if not isinstance(data,dict) or not str(data.get('id','')).startswith('notebook:'):
            raise NativeUnavailable('Native notebook receipt invalid')
        return str(data['id'])

    async def upload_pdf(self,nb_id,data,filename,title):
        fields={'type':'upload','notebooks':'["'+nb_id+'"]','title':title,'embed':'false',
                'transformations':'[]','delete_source':'false','async_processing':'true'}
        r=await self._request('POST','/api/sources',data=fields,files={'file':(filename,data,'application/pdf')})
        payload=r.json()
        if not str(payload.get('id','')).startswith('source:'):
            raise NativeUnavailable('Native source receipt invalid')
        return payload

    async def source(self,source_id):
        if not source_id.startswith('source:') or '/' in source_id or '?' in source_id or '#' in source_id:
            raise NativeOwnershipError('Invalid source id')
        return (await self._request('GET',f'/api/sources/{source_id}')).json()

    async def ensure_owned(self,source_id,notebook_id):
        source=await self.source(source_id)
        linked=source.get('notebooks')
        if not isinstance(linked,list) or linked!=[notebook_id]:
            raise NativeOwnershipError('Native source does not have exactly one expected notebook owner')
        if source.get('id')!=source_id:
            raise NativeOwnershipError('Native source identity mismatched')
        return source

    async def original(self,source_id,expected_sha):
        r=await self._request('GET',f'/api/sources/{source_id}/download')
        data=r.content
        if len(data)>25*1024*1024 or not hmac.compare_digest(hashlib.sha256(data).hexdigest(),expected_sha):
            raise NativeOwnershipError('Native original hash does not match immutable receipt')
        return data

    async def search(self,nb_id,term,limit=20):
        # NOT ENABLED: pinned native text_search triggers unsafe vector fallback on overflow.
        # Do not issue even type=text native /search request prior to verified A-only fix.
        raise NativeUnavailable('Text search disabled until native no-vector fallback is runtime verified')
