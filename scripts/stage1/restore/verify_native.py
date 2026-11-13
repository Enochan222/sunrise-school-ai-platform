#!/usr/bin/env python3
"""WP08 post-start private Native data ownership readback. IMPLEMENTED_UNTESTED.

Only runs via docker exec inside the verified isolated ON container. No raw
Source content is printed, only counts and digests. Actual original PDF bytes,
Native graph edge, rights and source version are verified one by one.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import urllib.request
from websockets.sync.client import connect

ID=re.compile(r'^(source|notebook):[A-Za-z0-9_-]{1,128}$')
HEX=re.compile(r'^[a-f0-9]{64}$')


def sql(query,ns,db):
    if os.environ.get('SURREAL_URL')!='ws://surrealdb:8000/rpc':
        raise RuntimeError('Only isolated SurrealDB address accepted')
    with connect('ws://surrealdb:8000/rpc',subprotocols=['json'],open_timeout=5) as ws:
        number=0
        def rpc(method,params):
            nonlocal number
            number+=1
            ws.send(json.dumps({'id':number,'method':method,'params':params}))
            reply=json.loads(ws.recv(timeout=15))
            if reply.get('id')!=number or reply.get('error'):
                raise RuntimeError('Private SurrealDB query rejected')
            return reply['result']
        rpc('signin',[{'user':os.environ['SURREAL_USER'],'pass':os.environ['SURREAL_PASSWORD']}])
        rpc('use',[ns,db])
        result=rpc('query',[query,{}])
        if not isinstance(result,list) or len(result)!=1 or result[0].get('status')!='OK':
            raise RuntimeError('SourceOwner/reference integrity query failed')
        rows=result[0]['result']
        if not isinstance(rows,list) or len(rows)>10000:
            raise RuntimeError('Unbounded/malformed source inventory')
        return rows


def native(path,method='GET',body=None):
    secret=os.environ.get('OPEN_NOTEBOOK_PASSWORD')
    if not secret or len(secret)<16:raise RuntimeError('Missing restore Native password')
    url='http://127.0.0.1:5055'+path
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(url,method=method,data=data,headers={
        'Authorization':'Bearer '+secret,'Accept':'application/json',
        **({'Content-Type':'application/json'} if body is not None else {})})
    with urllib.request.urlopen(req,timeout=25) as response:
        if response.status!=200:raise RuntimeError('Unexpected native HTTP status')
        payload=response.read(26*1024*1024)
    if len(payload)>25*1024*1024:
        raise RuntimeError('Original/native response too large')
    if path.endswith('/download'):return payload
    return json.loads(payload)


def main():
    if os.environ.get('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        raise SystemExit(69)
    proof=native('/api/sunrise-patch-status')
    if proof.get('marker')!='sunrise-a-text-only-no-vector-v1' or proof.get('text_only') is not True:
        raise RuntimeError('Native no-vector patch identity unavailable')
    a_ns=os.environ['VAULT_SURREAL_NAMESPACE']
    a_db=os.environ['VAULT_SURREAL_DATABASE']
    on_ns=os.environ['ON_GRAPH_NAMESPACE']
    on_db=os.environ['ON_GRAPH_DATABASE']
    owners=sql('SELECT * FROM source_owner LIMIT 10001;',a_ns,a_db)
    shells=sql('SELECT * FROM content_shell LIMIT 10001;',a_ns,a_db)
    shell_index={(r['school_id'],r['shell_id']):r for r in shells}
    check_digest=hashlib.sha256()
    searched=0
    for owner in owners:
        source=owner.get('source_id')
        notebook=owner.get('notebook_id')
        if (not isinstance(source,str) or not ID.fullmatch(source) or not source.startswith('source:') or
            not isinstance(notebook,str) or not ID.fullmatch(notebook) or not notebook.startswith('notebook:')):
            raise RuntimeError('Invalid owner source/notebook identity')
        shell=shell_index.get((owner.get('school_id'),owner.get('shell_id')))
        if not shell or shell.get('notebook_id')!=notebook:
            raise RuntimeError('School/Shell/Notebook mapping inconsistent')
        if (not HEX.fullmatch(str(owner.get('sha256',''))) or
            not HEX.fullmatch(str(owner.get('initial_version_id',''))) or
            not owner.get('license') or not owner.get('retention') or
            owner.get('approved_sharing') is not False or
            owner.get('ai_usage_allowed') is not False):
            raise RuntimeError('Rights/version/original hash incorrect')
        # Native reference source(in) -> notebook(out), exactly one.
        links=sql('SELECT in,out FROM reference WHERE in=type::thing("source","'+source.split(':',1)[1]+'");',on_ns,on_db)
        if len(links)!=1 or str(links[0].get('in'))!=source or str(links[0].get('out'))!=notebook:
            raise RuntimeError('Native Graph reference authority mismatch')
        info=native('/api/sources/'+source)
        if info.get('id')!=source or info.get('notebooks')!=[notebook]:
            raise RuntimeError('Native Source owner readback mismatch')
        pdf=native('/api/sources/'+source+'/download')
        if hashlib.sha256(pdf).hexdigest()!=owner['sha256']:
            raise RuntimeError('Native original PDF hash differs after isolated restore')
        check_digest.update((source+'|'+notebook+'|'+owner['sha256']).encode())
        searched+=1
    result={'classification':'NATIVE_OWNER_READBACK_NOT_FORMAL_AT',
            'source_owner_count':len(owners),'shell_count':len(shells),
            'verified_original_count':searched,
            'owned_source_graph_hash':check_digest.hexdigest(),
            'text_only_patch_attested':True,'external_ai_egress_test':'NOT_RUN'}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
