#!/usr/bin/env python3
"""WP05 private Native failed-only retry probe · IMPLEMENTED_UNTESTED.

Requires a pinned/patch-attested ON v1.15.1, exclusive synthetic worker and
operator consent. Never routed to the browser. No automatic retry/replay.
This script does not prove processing completion, Worker restart, or zero egress.
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
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native,checked_id
from surreal_store import SurrealConfig,SurrealStore


def stamp():
    return datetime.now(timezone.utc).isoformat()


def verified_source_owner(args):
    # Operator knowledge of a Source ID is NEVER equivalent to authorization.
    env=('VAULT_SURREAL_WS_URL','VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
         'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE','VAULT_ACTOR_ID')
    if any(not os.getenv(name) for name in env):
        raise ValueError('Private A Journal identity missing')
    if not args.school_id.startswith('synthetic-') or not args.actor_id:
        raise ValueError('Trusted synthetic school and actor required')
    if args.actor_id!=os.environ['VAULT_ACTOR_ID']:
        raise ValueError('Operator actor does not match authenticated A actor')
    journal=SurrealStore(SurrealConfig(*(os.environ[n] for n in env[:5])),args.actor_id)
    shell=journal.shell(args.school_id,args.shell_id)
    owner=journal.material(args.source_id,args.shell_id,args.school_id)
    # A SourceOwner alone does not prove the authenticated operator owns the
    # committed upload operation. Pin the same source and actor in its journal.
    ops=journal.query(
        'SELECT source_id,actor_id,school_id,shell_id,status FROM vault_operation '
        'WHERE kind="material" AND source_id=$source AND school_id=$school '
        'AND shell_id=$shell AND actor_id=$actor LIMIT 2;',
        source=args.source_id,school=args.school_id,
        shell=args.shell_id,actor=args.actor_id)
    committed=ops[-1] if ops else None
    if not isinstance(committed,list) or len(committed)!=1 or (
            committed[0].get('status')!='COMMITTED' or
            committed[0].get('source_id')!=args.source_id):
        raise ValueError('Unique committed material journal/actor is not proven')
    if (not shell or not owner or shell.get('archived') or
        shell.get('notebook_id')!=args.notebook_id or
        owner.get('notebook_id')!=args.notebook_id or
        owner.get('school_id')!=args.school_id or
        owner.get('shell_id')!=args.shell_id or
        owner.get('source_id')!=args.source_id or
        owner.get('sha256')!=args.expected_sha256 or
        owner.get('created_by_actor_id')!=args.actor_id or
        owner.get('rights_owner_actor_id')!=args.actor_id or
        owner.get('approved_sharing') is not False or
        owner.get('ai_usage_allowed') is not False or
        owner.get('state') in ('QUARANTINED','REVOKED','UNCONFIRMED') or
        not owner.get('initial_version_id') or
        not owner.get('license') or not owner.get('retention')):
        raise ValueError('A SourceOwner, rights, archive or version gate denied')
    return {'shell_id':shell['shell_id'],'source_id':owner['source_id']}


async def probe(args):
    verified_source_owner(args)
    native=Native(args.native_url,os.environ['OPEN_NOTEBOOK_PASSWORD'],
                  text_only_verified=True,max_download_bytes=args.max_pdf_bytes)
    return await native.retry_failed_owned_source(args.source_id,args.notebook_id,args.expected_sha256,
                                                 operator_authorized=True)


def main():
    parser=argparse.ArgumentParser(description='Exclusive synthetic only; failed-job retry, not stage acceptance')
    parser.add_argument('--source-id',required=True)
    parser.add_argument('--notebook-id',required=True)
    parser.add_argument('--school-id',required=True)
    parser.add_argument('--shell-id',required=True)
    parser.add_argument('--actor-id',required=True)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--native-url',default='http://127.0.0.1:5055')
    parser.add_argument('--max-pdf-bytes',type=int,default=8*1024*1024)
    parser.add_argument('--out',type=Path,default=Path('wp05-retry-redacted.json'))
    args=parser.parse_args()
    if (os.environ.get('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or
            os.environ.get('VAULT_PRIVATE_RETRY_ALLOWED')!='YES' or
            not os.environ.get('OPEN_NOTEBOOK_PASSWORD')):
        print('RUNTIME_NOT_RUN: explicit private synthetic retry authorization missing',file=sys.stderr)
        raise SystemExit(69)
    parsed=urlsplit(args.native_url)
    if (parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1')
            or parsed.username or parsed.password or parsed.path not in ('','/')):
        raise ValueError('Retry operator Native API must be local loopback only')
    checked_id(args.source_id,'source');checked_id(args.notebook_id,'notebook')
    if not re.fullmatch(r'[a-f0-9]{64}',args.expected_sha256):
        raise ValueError('Expected original PDF SHA-256 invalid')
    evidence={'start_utc':stamp(),'category':'PINNED_NATIVE_FAILED_JOB_RETRY',
              'source_id_sha256':hashlib.sha256(args.source_id.encode()).hexdigest(),
              'notebook_id_sha256':hashlib.sha256(args.notebook_id.encode()).hexdigest(),
              'original_sha256':args.expected_sha256,
              'actor_id_sha256':hashlib.sha256(args.actor_id.encode()).hexdigest(),
              'result':'NOT_RUN',
              'worker_restart':'NOT_RUN','zero_external_ai_egress':'NOT_RUN',
              'S1_AT05_15':'NOT_RUN'}
    try:
        receipt=asyncio.run(probe(args))
        if receipt.get('state')!='RETRY_SUBMITTED_NOT_COMPLETED':
            raise RuntimeError('Retry status unconfirmed')
        evidence['result']='RETRY_SUBMITTED_NOT_COMPLETED'
        evidence['new_command_id_sha256']=hashlib.sha256(receipt['new_command_id'].encode()).hexdigest()
    except Exception as exc:
        evidence['result']='FAIL';evidence['error_type']=type(exc).__name__
        evidence['error']='Private native failed-only retry or ownership/hash invariant failed'
        raise
    finally:
        evidence['end_utc']=stamp()
        args.out.write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'result':evidence['result'],'evidence':str(args.out)}))


if __name__=='__main__':
    main()
