#!/usr/bin/env python3
"""A-only WP04 exact-ACK Source reconciliation. IMPLEMENTED_UNTESTED.

ONLY for a trusted operator in an exclusive synthetic private runtime. No
POST /api/sources is ever issued. Source IDs cannot be inferred from title,
filename, payload SHA or nonunique Native metadata. If Native create lost ACK
before receipt persistence, this intentionally fails closed/quarantines.
"""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native,NativeUnavailable,checked_id
from surreal_store import SurrealConfig,SurrealStore
from store import Indeterminate


def when():
    return datetime.now(timezone.utc).isoformat()


async def reconcile(args):
    cfg=SurrealConfig(*(os.environ[k] for k in (
        'VAULT_SURREAL_WS_URL','VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
        'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE')))
    journal=SurrealStore(cfg,args.actor_id)
    op=journal._operation(args.school_id,args.key,'material',args.shell_id,actor_id=args.actor_id)
    if not op or op.get('actor_id')!=args.actor_id or op.get('status') not in (
            'PENDING','QUARANTINED','COMMITTED'):
        raise Indeterminate('Material operation missing or state unrecognised')
    source_id=op.get('native_source_id')
    metadata=op.get('metadata')
    if not source_id or not isinstance(metadata,dict) or not metadata:
        # Critical: Pinned Native Source create has NO proven immutable unique
        # creation marker, therefore an unknown ACK is NOT safely recoverable.
        raise Indeterminate('UNRECOVERABLE_WITHOUT_NATIVE_SOURCE_RECEIPT: quarantine, no second POST')
    checked_id(source_id,'source')
    shell=journal.shell(args.school_id,args.shell_id)
    if (not shell or shell.get('notebook_id')!=args.notebook_id or
            shell.get('archived') or not args.school_id.startswith('synthetic-')):
        raise Indeterminate('Foreign/archived A shell; recovery forbidden')
    native=Native(args.native_url,os.environ['OPEN_NOTEBOOK_PASSWORD'],
                  text_only_verified=False,max_download_bytes=args.max_pdf_bytes)
    source=await native.ensure_owned(source_id,args.notebook_id)
    raw=await native.original(source_id,metadata['sha256'])
    if hashlib.sha256(raw).hexdigest()!=metadata['sha256']:
        raise Indeterminate('Native original PDF differs from durable operation')
    current=journal.material(source_id,args.shell_id,args.school_id)
    if op['status']=='COMMITTED':
        if (not current or current.get('sha256')!=metadata['sha256']
                or current.get('initial_version_id') is None):
            raise Indeterminate('Committed material missing trustworthy SourceOwner')
        return {'result':'ALREADY_COMMITTED_VERIFIED','source_id_hash':hashlib.sha256(source_id.encode()).hexdigest()}
    if current:
        raise Indeterminate('SourceOwner exists before matching operation commit; quarantine')
    journal.finish_material(args.school_id,args.shell_id,args.key,source_id,
        metadata['title'],metadata['sha256'],metadata['original_name'],
        metadata['license'],metadata['retention'],actor_id=args.actor_id)
    done=journal.material(source_id,args.shell_id,args.school_id)
    if not done or done.get('sha256')!=metadata['sha256']:
        raise Indeterminate('SourceOwner completion uncertain, no second POST')
    return {'result':'RECOVERED_FROM_EXACT_DURABLE_NATIVE_RECEIPT',
            'source_id_hash':hashlib.sha256(source_id.encode()).hexdigest(),
            'original_sha256':metadata['sha256'],'worker_state':'NOT_VERIFIED'}


def main():
    p=argparse.ArgumentParser()
    for name in ('school-id','shell-id','notebook-id','actor-id','key'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--native-url',default='http://127.0.0.1:5055')
    p.add_argument('--max-pdf-bytes',type=int,default=8*1024*1024)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if (os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or
            os.getenv('VAULT_OPERATOR_RECONCILE_ALLOWED')!='YES' or
            not os.getenv('OPEN_NOTEBOOK_PASSWORD') or
            args.actor_id!=os.getenv('VAULT_ACTOR_ID')):
        p.error('Exclusive operator authorization/actor identity missing')
    from urllib.parse import urlsplit
    url=urlsplit(args.native_url)
    if url.scheme!='http' or url.hostname not in ('127.0.0.1','localhost','::1') or url.path not in ('','/'):
        p.error('Native origin must be exclusive loopback only')
    report={'utc':when(),'kind':'A_EXACT_RECEIPT_MATERIAL_RECONCILIATION',
            'status':'NOT_RUN','formal_acceptance':'NOT_RUN'}
    try:
        report.update(asyncio.run(reconcile(args)))
        report['status']='RECONCILED_NOT_AT_PASS'
    except Exception as e:
        report['status']='QUARANTINED_FAIL_CLOSED'
        report['error_type']=type(e).__name__
        raise
    finally:
        if args.out.exists():p.error('Evidence destination must be new')
        args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
