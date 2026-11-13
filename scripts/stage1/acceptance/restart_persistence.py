#!/usr/bin/env python3
"""WP09 S1-AT04 real DB/Worker restart and source persistence. IMPLEMENTED_UNTESTED.

One exclusive synthetic Compose project only. Does not reset volumes, delete
resources, migrate data or print secrets. Write freeze stays active on failure.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1/restore'))
from cold_capture import check_manifest,check_gateway_frozen,drain,inventory_at_freeze,stop_project
from runtime_identity import git_identity


def compose(args,*rest):
    out=subprocess.run(['docker','--context',args.context,'compose','-p',args.project,
        '-f',str(args.compose_file),*rest],capture_output=True,text=True,timeout=120)
    if out.returncode:
        raise RuntimeError('Verified Compose restart failed with exit '+str(out.returncode))


def main():
    p=argparse.ArgumentParser()
    for name in ('context','project','source-sha','source-tree','surreal-image-digest'):
        p.add_argument('--'+name,required=True)
    for name in ('runtime-identity','compose-file','maintenance-file','out'):
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--drain-timeout',type=int,default=120)
    args=p.parse_args()
    if (os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or
            os.getenv('VAULT_EXCLUSIVE_RESTART_ALLOWED')!='YES'):
        p.error('Exclusive synthetic restart approval missing')
    sha,tree=git_identity(ROOT)
    if (sha,tree)!=(args.source_sha,args.source_tree):
        p.error('Exact tested revision mismatch')
    if args.out.exists():p.error('Evidence cannot overwrite prior run')
    identity=check_manifest(args)
    # Conditional creation, no existing recovery/capture flag is replaced.
    with args.maintenance_file.open('x') as f:
        f.write('SUNRISE_A_RESTART_WRITE_FREEZE\n')
    record={'at_id':'S1-AT04','status':'NOT_RUN','start_utc':datetime.now(timezone.utc).isoformat(),
            'source_commit':sha,'source_tree':tree,'project':args.project}
    try:
        check_gateway_frozen(args)
        drain(args)
        before=inventory_at_freeze(args,identity)
        stop_project(args,identity)
        compose(args,'start','surrealdb')
        compose(args,'start','open_notebook')
        after=None
        for _ in range(30):
            try:
                after=inventory_at_freeze(args,identity)
                break
            except (OSError,RuntimeError,subprocess.CalledProcessError):
                time.sleep(2)
        if after is None or before!=after:
            raise RuntimeError('DB/worker restart did not preserve A+ON journal, source and index inventory')
        record['before_inventory_sha256']=hashlib.sha256(
            json.dumps(before,sort_keys=True).encode()).hexdigest()
        record['after_inventory_sha256']=hashlib.sha256(
            json.dumps(after,sort_keys=True).encode()).hexdigest()
        record['status']='PASS'
    except Exception as e:
        record['status']='FAIL';record['error_type']=type(e).__name__
        raise
    finally:
        record['end_utc']=datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    # Keep maintenance in place; operator explicitly reviews and releases.
    print(json.dumps({'at_id':record['at_id'],'status':record['status'],
                      'maintenance_flag_held':True}))


if __name__=='__main__':main()
