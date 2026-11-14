#!/usr/bin/env python3
"""TRUE SurrealDB v2 A journal/Notebook crash marker probe. No doubles or SQLite.

Run only on isolated synthetic Docker host with private Surreal + pinned Native.
A crash subprocess creates an actual ON Notebook and dies BEFORE A mapping commit.
Recovered mapping must equal exact marker ID. Never retry native creation.
This is a candidate script, NOT_RUN until its JSON evidence exists.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from surreal_store import SurrealStore,SurrealConfig,SurrealUnavailable
from store import Conflict,Indeterminate
from native import Native
from wp03_races import first_reservation_races,native_lost_ack
from executed_runtime_provenance import inspect as inspect_runtime,guard as guard_runtime,resolve_native_endpoint


def now():return datetime.now(timezone.utc).isoformat()


def cfg():
    names=['VAULT_SURREAL_WS_URL','VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
           'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE']
    if not all(os.getenv(n) for n in names):
        print('RUNTIME_NOT_RUN: missing separate synthetic A SurrealDB configuration',file=sys.stderr)
        raise SystemExit(69)
    return SurrealConfig(os.environ[names[0]],os.environ[names[1]],os.environ[names[2]],
                         os.environ[names[3]],os.environ[names[4]])


async def recover_native(store,school,key,details,secret,native_endpoint):
    op=store.operation(school,key,'shell')
    if not op or op.get('status') not in ('PENDING','QUARANTINED'):
        raise AssertionError('Recovery operation not pending in A SurrealDB')
    n=Native(native_endpoint,secret)
    matches=await n.find_notebooks_by_marker(op['marker'])
    if len(matches)!=1:
        raise AssertionError('Cannot uniquely reconcile native marker')
    reservation={'shell_id':op['shell_id'],'school_id':school,**details}
    return store.complete_shell(school,key,reservation,matches[0])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime-identity',type=Path,
                        default=os.getenv('VAULT_RUNTIME_IDENTITY_FILE'))
    parser.add_argument('--source-sha',default=os.getenv('VAULT_FIXED_SOURCE_SHA'))
    parser.add_argument('--source-tree',default=os.getenv('VAULT_FIXED_SOURCE_TREE'))
    args=parser.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        print('RUNTIME_NOT_RUN: synthetic Docker runtime confirmation required',file=sys.stderr)
        raise SystemExit(69)
    if args.runtime_identity is None:
        parser.error('Exact external runtime identity required for real journal execution')
    runtime_sha=inspect_runtime(ROOT,args.runtime_identity,args.source_sha,args.source_tree)
    native_endpoint=resolve_native_endpoint(ROOT,args.runtime_identity,args.source_sha,args.source_tree,runtime_sha)
    # Resolve ON secret ONCE before any optional Native side effect. Never log its value.
    secret = os.environ.get('OPEN_NOTEBOOK_PASSWORD') or None
    configuration=cfg();school='synthetic-a-'+secrets.token_hex(5)
    actor='synthetic-actor';key='ackcrash_'+secrets.token_hex(8)
    details={'academic_year':'2026','grade':'P4','subject':'Mathematics','curriculum_stream':'synthetic'}
    log={'start_utc':now(),'at_id':'S1-AT06',
         'source_commit':args.source_sha,'source_tree':args.source_tree,
         'runtime_identity_sha256':runtime_sha,
         'category':'NATIVE_SURREALDB_REAL_RUNTIME',
         'staging_database':configuration.database,'school':school,'actor':actor,
         'results':{},'s1_at01_15':'NOT_RUN'}
    try:
        journal=SurrealStore(configuration,actor)
        reservation,fresh=journal.start_shell(school,key,details)
        assert fresh and reservation['creation_marker'].startswith('sunrise-a-op-v1:')
        log['results']['fresh_first_reservation_races']=first_reservation_races(configuration,actor,secret,native_endpoint)
        # Validate actual nested first-write outcomes; no successful empty/malformed data.
        race_modes={'same_key_same_body','different_key_same_scope','same_key_different_body'}
        races=log['results']['fresh_first_reservation_races']
        if not isinstance(races,dict) or set(races)!=race_modes:
            raise AssertionError('Missing or malformed first-reservation races')
        for mode in race_modes:
            entry=races[mode]
            if not isinstance(entry,dict) or not isinstance(entry.get('outcomes'),dict):
                raise AssertionError('Missing nested first-reservation evidence: '+mode)
            outcomes=entry['outcomes']
            if (outcomes.get('FRESH')!=1 or outcomes.get('REPLAY',0)!=0 or
                    sum(outcomes.values())!=8 or entry.get('durable_operations')!=1 or
                    entry.get('durable_scope_claims')!=1):
                raise AssertionError('Fresh first-claim did not prove durable uniqueness: '+mode)
            expected_native=1 if secret else 0
            if (entry.get('durable_shells')!=expected_native or
                    entry.get('native_create_posts')!=expected_native):
                raise AssertionError('Fresh first-claim native evidence incomplete: '+mode)
        log['results']['real_surrealdb_unique_operation_reservation']='PASS'
        # Different-body 409 before any native side effect.
        try:
            journal.start_shell(school,key,{**details,'grade':'P5'})
        except Conflict:pass
        else:raise AssertionError('Different body same key was accepted')
        log['results']['different_body_conflict']='PASS'
        # Concurrent exact idempotency key: should never issue another reservation.
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks=[pool.submit(lambda:journal.start_shell(school,key,details)) for _ in range(16)]
            for task in tasks:
                try: task.result()
                except Indeterminate: continue
                raise AssertionError('Concurrent same-key created fresh reservation')
        log['results']['same_key_concurrent_no_second_reservation']='PASS'
        op=journal.operation(school,key,'shell')
        assert op['shell_id']==reservation['shell_id']
        if not secret:
            for name in ('real_native_crash_after_create_before_journal_commit',
                         'real_native_lost_ack_tcp','marker_reconciliation_unique_mapping',
                         'same_key_replay_original_notebook','cross_school_shell_negative'):
                log['results'][name]='NOT_RUN'
            log['native_gate']='NOT_RUN'
            log['status']='PARTIAL'
        else:
            # The child runs real Native API POST and immediately terminates, skipping
            # any A mapping update. Forced process death models gateway crash precisely
            # between native success and journal commit; not a simulated DB response.
            code='''import asyncio,os,sys
from native import Native
async def run():
 n=Native(os.environ['VAULT_VERIFIED_NATIVE_ENDPOINT'],os.environ['OPEN_NOTEBOOK_PASSWORD'])
 await n.create_notebook('SYNTHETIC CRASH WINDOW NOTEBOOK',marker=os.environ['VAULT_TEST_MARKER'])
asyncio.run(run())
os._exit(97)
'''
            env=dict(os.environ,VAULT_TEST_MARKER=reservation['creation_marker'],
                     OPEN_NOTEBOOK_PASSWORD=secret,VAULT_VERIFIED_NATIVE_ENDPOINT=native_endpoint)
            child=subprocess.run([sys.executable,'-c',code],cwd=str(ROOT/'apps/a-vault'),
                                  env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)
            if child.returncode!=97:
                raise RuntimeError('Native create crash child failed before committed boundary')
            # Independent fresh DB connection proves restart/readback, not use of process memory.
            restarted=SurrealStore(configuration,actor)
            recovered=asyncio.run(recover_native(restarted,school,key,details,secret,native_endpoint))
            assert recovered['notebook_id'].startswith('notebook:')
            same,new=restarted.start_shell(school,key,details)
            assert new is False and same['notebook_id']==recovered['notebook_id']
            assert restarted.shell('synthetic-foreign-school',recovered['shell_id']) is None
            lost_ack=native_lost_ack(configuration,actor,secret,native_endpoint)
            if (not isinstance(lost_ack,dict) or
                    lost_ack.get('native_create_posts')!=1 or
                    lost_ack.get('client_received_post_ack') is not False or
                    lost_ack.get('persisted_mapping_count')!=1 or
                    not isinstance(lost_ack.get('original_notebook_sha256'),str) or
                    not re.fullmatch(r'[a-f0-9]{64}',lost_ack['original_notebook_sha256'])):
                raise AssertionError('Lost-ACK recovery evidence missing/invalid')
            log['results']['real_native_lost_ack_tcp']=lost_ack
            log['results']['real_native_crash_after_create_before_journal_commit']='PASS'
            log['results']['marker_reconciliation_unique_mapping']='PASS'
            log['results']['same_key_replay_original_notebook']='PASS'
            log['results']['cross_school_shell_negative']='PASS'
            log['notebook_id_sha256']=hashlib.sha256(recovered['notebook_id'].encode()).hexdigest()
            log['native_gate']='PASS'
            guard_runtime(ROOT,args.runtime_identity,args.source_sha,args.source_tree,runtime_sha)
            log['status']='PASS'
    except Exception as error:
        log['status']='FAIL'
        log['error_type']=type(error).__name__
        log['error']='Synthetic DB/Native invariant failed; review private runner logs'
        raise
    finally:
        log['end_utc']=now()
        dest=Path(os.environ.get('VAULT_JOURNAL_EVIDENCE','journal-runtime-redacted.json'))
        dest.write_text(json.dumps(log,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'status':log.get('status'),'results':log['results'],
                          'evidence':str(dest)},ensure_ascii=False))
    if log['status']=='PARTIAL':
        raise SystemExit(2)  # DB-only results do not satisfy mandatory Native gate.
    if log['status']!='PASS':
        raise SystemExit(1)

if __name__=='__main__':
    main()
