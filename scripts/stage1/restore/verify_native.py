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
import sys
import urllib.request
from websockets.sync.client import connect

ID=re.compile(r'^(source|notebook):[A-Za-z0-9_-]{1,128}$')
HEX=re.compile(r'^[a-f0-9]{64}$')


def owned_identity_digest(identities):
    """Order-independent digest for the verified SourceOwner/native graph.

    SurrealQL SELECT without ORDER BY has no stable row ordering across DB
    restart or isolated restore. Duplicate source ownership fails closed.
    """
    if not isinstance(identities,list) or len(identities)>10000:
        raise RuntimeError('Invalid owned source identity inventory')
    seen=set()
    for row in identities:
        if (not isinstance(row,tuple) or len(row)!=3 or
                not isinstance(row[0],str) or not row[0].startswith('source:') or
                not isinstance(row[1],str) or not row[1].startswith('notebook:') or
                not isinstance(row[2],str) or not HEX.fullmatch(row[2]) or
                row[0] in seen):
            raise RuntimeError('Duplicate/malformed SourceOwner graph identity')
        seen.add(row[0])
    canonical=json.dumps(sorted(identities),ensure_ascii=False,
                         separators=(',',':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def sql(query,ns,db):
    if os.environ.get('SURREAL_URL')!='ws://on_db:8000/rpc':
        raise RuntimeError('Native verifier may query only the ON physical graph DB')
    with connect('ws://on_db:8000/rpc',subprotocols=['json'],open_timeout=5) as ws:
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
    # The SourceOwner/Shell snapshot came from an independently verified A
    # container on the physically separate A private network over a host pipe.
    # A root secrets are NEVER available inside this Native/ON verifier.
    if os.getenv('A_SURREAL_PASSWORD') or os.getenv('VAULT_SURREAL_PASSWORD'):
        raise RuntimeError('A root leaked into Native graph verification container')
    raw=sys.stdin.read((4<<20)+1)
    if len(raw.encode('utf-8'))>4<<20:
        raise RuntimeError('A owner pipe evidence is unbounded')
    snapshot=json.loads(raw)
    if snapshot.get('classification')!='PRIVATE_A_OWNER_SNAPSHOT_NOT_ACCEPTANCE':
        raise RuntimeError('Independent physical A SourceOwner snapshot missing')
    owners=snapshot.get('source_owner')
    shells=snapshot.get('content_shell')
    if (not isinstance(owners,list) or not isinstance(shells,list)
            or not 0<len(owners)<=10000 or len(shells)>10000):
        raise RuntimeError('A SourceOwner/Shell proof missing, empty or unbounded')
    on_ns=os.environ['ON_GRAPH_NAMESPACE']
    on_db=os.environ['ON_GRAPH_DATABASE']
    shell_index={(r['school_id'],r['shell_id']):r for r in shells}
    identities=[]
    rights_versions=[]
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
        expected_initial=hashlib.sha256(json.dumps(
            [source,owner.get('sha256')],ensure_ascii=False,
            separators=(',',':'),sort_keys=True).encode('utf-8')).hexdigest()
        if (not HEX.fullmatch(str(owner.get('sha256',''))) or
            owner.get('version')!=1 or
            owner.get('initial_version_id')!=expected_initial or
            not owner.get('license') or not owner.get('retention') or
            not owner.get('original_name') or
            owner.get('original_mime_type')!='application/pdf' or
            not owner.get('rights_owner_actor_id') or
            owner.get('approved_sharing') is not False or
            owner.get('ai_usage_allowed') is not False or
            owner.get('ai_usage') is not False):
            raise RuntimeError('Rights/immutable initial version/original hash incorrect')
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
        identities.append((source,notebook,owner['sha256']))
        rights_versions.append((source,owner['sha256'],owner['version'],
            owner['initial_version_id'],owner['license'],owner['retention'],
            owner['rights_owner_actor_id'],owner['original_name'],
            owner['original_mime_type'],owner['approved_sharing'],
            owner['ai_usage_allowed'],owner['ai_usage']))
        searched+=1
    result={'classification':'NATIVE_OWNER_READBACK_NOT_FORMAL_AT',
            'source_owner_count':len(owners),'shell_count':len(shells),
            'verified_original_count':searched,
            'owned_source_graph_hash':owned_identity_digest(identities),
            'rights_retention_initial_version_sha256':hashlib.sha256(json.dumps(
                sorted(rights_versions),ensure_ascii=False,
                separators=(',',':')).encode('utf-8')).hexdigest(),
            'rights_retention_initial_version_count':len(rights_versions),
            'text_only_patch_attested':True,'external_ai_egress_test':'NOT_RUN'}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
