#!/usr/bin/env python3
"""WP08 gated native startup and private integrity readback. IMPLEMENTED_UNTESTED.

Must follow isolated_restore.py with matching exact project, context and SHA.
Leaves Gateway stopped. NEVER publishes an ON/DB port or starts a public entry.
No cleanup of source or target resources, even on failure.
"""
import argparse
from datetime import datetime,timezone
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1/restore'))
from isolated_restore import compose,container_id,inspect_isolation,restore_env,load_identity
from a_cold_backup import verify,BackupInvalid
from dual_inventory_runner import read_a_owner_snapshot,native_readback,both


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--source-runtime-identity',required=True,type=Path)
    p.add_argument('--key-escrow-reference',required=True)
    p.add_argument('--context',required=True);p.add_argument('--project',required=True)
    p.add_argument('--compose-file',required=True,type=Path)
    p.add_argument('--workdir',required=True,type=Path)
    p.add_argument('--source-sha',required=True);p.add_argument('--source-tree',required=True)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or (
        os.getenv('VAULT_ISOLATED_RESTORE_ALLOWED')!='YES'):
        p.error('Isolated source-only synthetic startup not authorized')
    manifest=verify(args.bundle)
    identity=load_identity(args,manifest)
    env=restore_env(identity)
    evidence=args.workdir/'restore-evidence-redacted.json'
    previous=json.loads(evidence.read_text())
    source_runtime_sha=hashlib.sha256(args.source_runtime_identity.read_bytes()).hexdigest()
    if (previous.get('classification')!='ISOLATED_DB_RESTORE_VERIFIED_NATIVE_NOT_STARTED'
            or previous.get('source_runtime_identity_sha256')!=source_runtime_sha
            or previous.get('independent_target_verified') is not True
            or previous.get('restored_volume_count')!=3
            or set(previous.get('restored_services',[]))!={'a_db','on_db','native'}
            or previous.get('source_commit')!=args.source_sha
            or previous.get('source_tree')!=args.source_tree
            or previous.get('target_project')!=args.project
            or previous.get('target_context')!=args.context
            or previous.get('db_inventories_equal') is not True):
        p.error('Target has not passed isolated DB inventory gate')
    target_before=inspect_isolation(args,env,running={'a_db','on_db'})
    if (previous.get('restored_target_volume_names')!=target_before['volumes']
            or previous.get('restored_target_container_ids')!=target_before['containers']
            or previous.get('restored_target_network_ids')!=target_before['network_ids']):
        raise BackupInvalid('Restored target identities changed since DB stage')
    compose(args,'start','native',env=env)
    if inspect_isolation(args,env,running={'a_db','on_db','native'})!=target_before:
        raise BackupInvalid('Restored target identity changed at Native startup')
    cid=container_id(args,'native',env)
    proof=(Path(__file__).parent/'verify_native.py').read_text(encoding='utf-8')
    last=None
    output=None
    for _ in range(25):
        try:
            source_owner=read_a_owner_snapshot(
                args.context,args.project,env['ON_RESTORE_IMAGE'])
            output=native_readback(args.context,cid,source_owner,proof)
            break
        except (OSError,ValueError,subprocess.TimeoutExpired,RuntimeError) as exc:
            last=type(exc).__name__
        time.sleep(2)
    if output is None:
        raise BackupInvalid('Independent A/ON Native original/graph readback unavailable: '+str(last))
    target_after=inspect_isolation(args,env,running={'a_db','on_db','native'})
    if target_after!=target_before:
        raise BackupInvalid('Restored independent target changed during Native readback')
    before=json.loads((args.workdir/'gateway'/'native-pre-capture-readback.json').read_text())
    identity_fields=('source_owner_count','shell_count','verified_original_count',
                     'owned_source_graph_hash','rights_retention_initial_version_sha256',
                     'rights_retention_initial_version_count',
                     'worker_scoped_search_positive_count','text_only_patch_attested')
    if not isinstance(output.get('worker_scoped_search_positive_count'),int) or (
            output['worker_scoped_search_positive_count']<1):
        raise BackupInvalid('Restored Worker/Scope/Search evidence missing')
    if (not isinstance(output.get('rights_retention_initial_version_sha256'),str)
            or len(output['rights_retention_initial_version_sha256'])!=64
            or output.get('rights_retention_initial_version_count')!=output.get('source_owner_count')):
        raise BackupInvalid('Native restored rights/version inventory incomplete')
    if (before.get('classification')!='NATIVE_OWNER_READBACK_NOT_FORMAL_AT'
            or any(before.get(key)!=output.get(key) for key in identity_fields)):
        raise BackupInvalid('Native original PDF/graph/source ownership differs from source recovery point')
    summary={**previous,
        'source_runtime_identity_sha256':source_runtime_sha,
        'independent_target_verified':target_after==target_before,
        'restored_volume_count':len(set(target_after['volumes'].values())),
        'restored_services':sorted(target_after['volumes']),
        'pre_capture_native_readback_sha256':hashlib.sha256(
            json.dumps(before,sort_keys=True).encode()).hexdigest(),
        'native_owner_identity_matches_before_after':True,
        'native_worker_running':True,
        'a_db_restored_nonroot':True,
        'on_db_restored_nonroot':True,
        'two_physical_dbs_restored':True,
        'native_readback':output,
        'native_started_utc':datetime.now(timezone.utc).isoformat(),
        'classification':'ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS',
        'formal_AT05':'NOT_RUN','gateway_exposed':False}
    out=args.workdir/'native-readback-evidence.json'
    if out.exists():p.error('Native evidence destination must be new')
    out.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'classification':summary['classification'],
                      'evidence':str(out),'stage1_acceptance':'NOT_RUN'}))


if __name__=='__main__':main()
