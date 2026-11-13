#!/usr/bin/env python3
"""WP08 gated native startup and private integrity readback. IMPLEMENTED_UNTESTED.

Must follow isolated_restore.py with matching exact project, context and SHA.
Leaves Gateway stopped. NEVER publishes an ON/DB port or starts a public entry.
No cleanup of source or target resources, even on failure.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1/restore'))
from isolated_restore import compose,container_id,inspect_isolation,restore_env,load_identity
from a_cold_backup import verify,BackupInvalid


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
    if (previous.get('classification')!='ISOLATED_DB_RESTORE_VERIFIED_NATIVE_NOT_STARTED'
            or previous.get('source_commit')!=args.source_sha
            or previous.get('source_tree')!=args.source_tree
            or previous.get('target_project')!=args.project
            or previous.get('target_context')!=args.context
            or previous.get('db_inventories_equal') is not True):
        p.error('Target has not passed isolated DB inventory gate')
    inspect_isolation(args,env)
    compose(args,'start','open_notebook',env=env)
    cid=container_id(args,'open_notebook',env)
    proof=(Path(__file__).parent/'verify_native.py').read_text()
    last=None
    for _ in range(25):
        try:
            # Executing this readback within the private stopped-volume target
            # proves local native source/owner hashes WITHOUT a public port.
            result=subprocess.run(['docker','--context',args.context,'exec',
                '-e','VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES',cid,'python','-c',proof],
                capture_output=True,text=True,timeout=75)
            if result.returncode==0:
                output=json.loads(result.stdout)
                if output.get('classification')!='NATIVE_OWNER_READBACK_NOT_FORMAL_AT':
                    raise BackupInvalid('Unexpected Native verify result')
                break
            last='Native private readback returned '+str(result.returncode)
        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
            last=type(exc).__name__
        time.sleep(2)
    else:
        raise BackupInvalid('Native source/graph/original readback not proven: '+str(last))
    summary={**previous,
        'native_worker_running':True,
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
