#!/usr/bin/env python3
"""WP04 real Native graph Link/Unlink + A ownership source-only probe.

IMPLEMENTED_UNTESTED. MUTATES ONLY a dedicated disposable synthetic source
whose A SourceOwner is first verified. Requires exclusive operator approval,
pinned patch attestation and SurrealDB v2. Never run on live student materials.
This is NOT a replacement for school A/B Gateway authorization negatives.
"""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native,checked_id
from surreal_store import SurrealConfig,SurrealStore,RPC


def utc():
    return datetime.now(timezone.utc).isoformat()


def configure():
    names=('VAULT_SURREAL_WS_URL','VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
           'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE')
    if any(not os.environ.get(name) for name in names):
        raise ValueError('Isolated synthetic A database required')
    return SurrealConfig(*(os.environ[name] for name in names))


def native_graph_authority():
    """Independent read-only ON graph RPC connection, never the A journal handle.

    The operator must provide a signed-off private runtime identity manifest
    from Docker inspection. Environment names are intentionally independent:
    A_URL and ON_URL may alias the same host but cannot be assumed equivalent.
    """
    names=('ON_GRAPH_WS_URL','ON_GRAPH_USER','ON_GRAPH_PASSWORD',
           'ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE','ON_GRAPH_IDENTITY_FILE')
    if any(not os.environ.get(n) for n in names):
        raise RuntimeError('Native Graph DB identity missing; mutation denied')
    identity=json.loads(Path(os.environ['ON_GRAPH_IDENTITY_FILE']).read_text())
    wanted={k:os.environ[k] for k in ('ON_GRAPH_WS_URL','ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE')}
    expected={'ws_url':wanted['ON_GRAPH_WS_URL'],'namespace':wanted['ON_GRAPH_NAMESPACE'],
              'database':wanted['ON_GRAPH_DATABASE']}
    if (identity.get('native_graph')!=expected or
            identity.get('source_commit')!='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
            or identity.get('source_tree')!='2d101001de594c7d6a0e4aaeb8e85ac4c52980af'
            or identity.get('attested_exclusive_synthetic') is not True
            or not identity.get('container_id') or not identity.get('image_digest')):
        raise RuntimeError('Unattested Native DB endpoint/namespace/database/source identity')
    a=configure()
    a_identity={'ws_url':a.ws_url,'namespace':a.namespace,'database':a.database}
    if identity.get('a_journal')!=a_identity:
        raise RuntimeError('A Journal physical DB identity disagrees with runtime manifest')
    native=SurrealConfig(os.environ['ON_GRAPH_WS_URL'],os.environ['ON_GRAPH_USER'],
                         os.environ['ON_GRAPH_PASSWORD'],
                         os.environ['ON_GRAPH_NAMESPACE'],os.environ['ON_GRAPH_DATABASE']).validate()
    # No SurrealStore(native) here: its migration is A-owned and must not alter ON schema.
    return RPC(native)


def native_edges(graph_rpc,source_id):
    # Pinned ON graph: source -reference-> notebook; the Surreal reference.in
    # endpoint is the source, out is the notebook.
    key=checked_id(source_id,'source').split(':',1)[1]
    results=graph_rpc.query(
        'SELECT in,out FROM reference WHERE in=type::thing("source",$source_key);',
        {'source_key':key})
    rows=results[-1] if results else None
    if not isinstance(rows,list):
        raise RuntimeError('Native graph edge readback malformed')
    return rows


def require_exact_edge(graph_rpc,source_id,notebook_id,expected):
    rows=native_edges(graph_rpc,source_id)
    if len(rows)!=expected:
        raise RuntimeError('Native edge cardinality violates expected count')
    for row in rows:
        if not isinstance(row,dict) or str(row.get('in'))!=source_id or str(row.get('out'))!=notebook_id:
            raise RuntimeError('Native reference.in/out direction or owner incorrect')


async def workflow(args,record):
    notebook=checked_id(args.notebook_id,'notebook')
    source=checked_id(args.source_id,'source')
    native=Native(args.native_url,os.environ['OPEN_NOTEBOOK_PASSWORD'],
                  text_only_verified=True,max_download_bytes=args.max_pdf_bytes)
    proof=(await native._request('GET','/api/sunrise-patch-status')).json()
    if (not isinstance(proof,dict) or proof.get('marker')!='sunrise-a-text-only-no-vector-v1'
            or proof.get('text_only') is not True):
        raise RuntimeError('Full pinned-source patch attestation absent; mutation forbidden')
    graph_rpc=native_graph_authority()  # Must be verified before ANY mutation.
    journal=SurrealStore(configure(),os.environ['VAULT_ACTOR_ID'])
    owned=journal.material(source,args.shell_id,args.school_id)
    if (not owned or owned.get('notebook_id')!=notebook or owned.get('sha256')!=args.expected_sha256
            or not args.school_id.startswith('synthetic-')):
        raise RuntimeError('Not an exclusively owned synthetic SourceOwner; mutation forbidden')
    await native.ensure_owned(source,notebook)
    require_exact_edge(graph_rpc,source,notebook,1)
    original=await native.original(source,args.expected_sha256)
    record['before_original_sha256']=hashlib.sha256(original).hexdigest()
    was_unlinked=False
    try:
        await native._request('DELETE',f'/api/notebooks/{notebook}/sources/{source}')
        was_unlinked=True
        require_exact_edge(graph_rpc,source,notebook,0)
        detached=await native.source(source)
        if detached.get('notebooks')!=[]:
            raise RuntimeError('Native Source remains attached after unlink')
        record['native_unlink']='PASS'
        await native._request('POST',f'/api/notebooks/{notebook}/sources/{source}')
        await native.ensure_owned(source,notebook)
        require_exact_edge(graph_rpc,source,notebook,1)
        was_unlinked=False  # Clear only AFTER proving the restored edge exists.
        # Duplicate link request must not introduce a second reference edge.
        await native._request('POST',f'/api/notebooks/{notebook}/sources/{source}')
        await native.ensure_owned(source,notebook)
        require_exact_edge(graph_rpc,source,notebook,1)
        record['native_link_and_duplicate']='PASS'
        after=await native.original(source,args.expected_sha256)
        if after!=original:
            raise RuntimeError('Original content changed during native graph mutation')
        record['original_hash_preserved']='PASS'
    finally:
        if was_unlinked:
            # Best effort to recover the operator-owned synthetic source if a
            # negative test is interrupted; failures REQUIRE manual quarantine.
            try:
                await native._request('POST',f'/api/notebooks/{notebook}/sources/{source}')
                await native.ensure_owned(source,notebook)
                require_exact_edge(graph_rpc,source,notebook,1)
            except Exception as exc:
                record['recovery']='MANUAL_QUARANTINE_REQUIRED'
                record['recovery_error_type']=type(exc).__name__


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-id',required=True);parser.add_argument('--notebook-id',required=True)
    parser.add_argument('--shell-id',required=True);parser.add_argument('--school-id',required=True)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--native-url',default='http://127.0.0.1:5055')
    parser.add_argument('--max-pdf-bytes',type=int,default=8*1024*1024)
    parser.add_argument('--out',type=Path,default=Path('wp04-graph-redacted.json'))
    args=parser.parse_args()
    if (os.environ.get('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or
            os.environ.get('VAULT_EXCLUSIVE_GRAPH_MUTATION')!='YES' or
            not os.environ.get('OPEN_NOTEBOOK_PASSWORD') or
            not os.environ.get('VAULT_ACTOR_ID')):
        print('RUNTIME_NOT_RUN: exclusive synthetic graph mutation not authorized',file=sys.stderr)
        raise SystemExit(69)
    target=urlsplit(args.native_url)
    if (target.scheme!='http' or target.hostname not in ('127.0.0.1','localhost','::1')
            or target.username or target.password or target.path not in ('','/')):
        raise ValueError('Graph operator Native API must be a trusted loopback origin')
    record={'start_utc':utc(),'component':'WP04_NATIVE_LINK_UNLINK_AND_A_OWNER',
            'status':'NOT_RUN','original_sha256':args.expected_sha256,'formal_S1_AT':'NOT_RUN'}
    try:
        asyncio.run(workflow(args,record))
        if record.get('recovery')=='MANUAL_QUARANTINE_REQUIRED':
            raise RuntimeError('Graph recovery failed; manual quarantine required')
        record['status']='PASS'
    except Exception as exc:
        record['status']='FAIL';record['error_type']=type(exc).__name__
        record['error']='Native graph/ownership integrity check failed'
        raise
    finally:
        record['end_utc']=utc()
        args.out.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'status':record['status'],'evidence':str(args.out)}))


if __name__=='__main__':
    main()
