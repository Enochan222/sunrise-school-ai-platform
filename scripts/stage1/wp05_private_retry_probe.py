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
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native


def stamp():
    return datetime.now(timezone.utc).isoformat()


async def probe(args):
    native=Native(args.native_url,os.environ['OPEN_NOTEBOOK_PASSWORD'],
                  text_only_verified=True,max_download_bytes=args.max_pdf_bytes)
    return await native.retry_failed_owned_source(args.source_id,args.notebook_id,args.expected_sha256,
                                                 operator_authorized=True)


def main():
    parser=argparse.ArgumentParser(description='Exclusive synthetic only; failed-job retry, not stage acceptance')
    parser.add_argument('--source-id',required=True)
    parser.add_argument('--notebook-id',required=True)
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
    if not re.fullmatch(r'[a-f0-9]{64}',args.expected_sha256):
        raise ValueError('Expected original PDF SHA-256 invalid')
    evidence={'start_utc':stamp(),'category':'PINNED_NATIVE_FAILED_JOB_RETRY',
              'source_id_sha256':hashlib.sha256(args.source_id.encode()).hexdigest(),
              'notebook_id_sha256':hashlib.sha256(args.notebook_id.encode()).hexdigest(),
              'original_sha256':args.expected_sha256,'result':'NOT_RUN',
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
