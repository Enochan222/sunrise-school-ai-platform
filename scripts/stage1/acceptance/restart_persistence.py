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
import secrets
import subprocess
import sys
import time
import httpx

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1/restore'))
from cold_capture import check_manifest,check_gateway_frozen,drain,inventory_at_freeze,stop_project,native_readback_at_freeze
from runtime_identity import git_identity,tls_gateway_identity
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from executed_runtime_provenance import inspect as inspect_runtime,guard as guard_runtime


def compose(args,*rest):
    out=subprocess.run(['docker','--context',args.context,'compose','-p',args.project,
        '-f',str(args.compose_file),*rest],capture_output=True,text=True,timeout=120)
    if out.returncode:
        raise RuntimeError('Verified Compose restart failed with exit '+str(out.returncode))


def verify_gateway_after_restart(args,identity,client):
    # Strictly bound to the CA and Gateway instance, never log cookie or secret.
    gateway=identity['gateway']
    actual=tls_gateway_identity(gateway['origin'],os.environ['VAULT_GATEWAY_CA_FILE'])
    if any(actual.get(k)!=gateway.get(k) for k in ('origin','instance_id','tls_peer_sha256','tls_ca_sha256')):
        raise RuntimeError('Post-restart Gateway TLS identity differs')
    password=os.environ.get('VAULT_TEST_ADMIN_PASSWORD')
    if not password or not re.fullmatch(r'[a-f0-9]{64}',args.probe_sha256):
        raise RuntimeError('Synthetic Gateway probe credentials/hash missing')
    me=client.get('/auth/me')
    if me.status_code!=200 or not str(me.json().get('school_id','')).startswith('synthetic-'):
        raise RuntimeError('Pre-restart authenticated session did not persist')
    path=f'/vault/v1/shells/{args.probe_shell}/materials/{args.probe_source}/download'
    response=client.get(path)
    if response.status_code!=200 or hashlib.sha256(response.content).hexdigest()!=args.probe_sha256:
        raise RuntimeError('Post-restart Gateway owned Native original mismatch')



def main():
    p=argparse.ArgumentParser()
    for name in ('context','project','source-sha','source-tree','surreal-image-digest','probe-shell','probe-source','probe-sha256'):
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
    runtime_sha=inspect_runtime(ROOT,args.runtime_identity,sha,tree)
    identity=check_manifest(args)
    from real_admin_journey import login
    password=os.environ.get('VAULT_TEST_ADMIN_PASSWORD')
    if not password:
        raise RuntimeError('Synthetic Gateway probe password missing')
    client=httpx.Client(base_url=identity['gateway']['origin'],
        verify=os.environ['VAULT_GATEWAY_CA_FILE'], timeout=35,
        trust_env=False,follow_redirects=False)
    login(client,password)  # session must remain valid across the restart
    # One unique probe-owned barrier; leave it active on any failed restart.
    nonce=secrets.token_hex(16)
    marker='SUNRISE_A_RESTART_WRITE_FREEZE '+nonce+'\n'
    with args.maintenance_file.open('x') as freeze:
        freeze.write(marker)
    record={'at_id':'S1-AT04','status':'NOT_RUN','start_utc':datetime.now(timezone.utc).isoformat(),
            'source_commit':sha,'source_tree':tree,'project':args.project,
            'runtime_identity_sha256':runtime_sha}
    try:
        check_gateway_frozen(args)
        drain(args)
        before_readback=native_readback_at_freeze(args,identity)
        drain(args)
        before=inventory_at_freeze(args,identity)
        stop_project(args,identity)
        compose(args,'start','a_db','on_db','a_relay','on_relay')
        after=None
        for _ in range(30):
            try:
                after=inventory_at_freeze(args,identity)
                break
            except (OSError,RuntimeError,subprocess.CalledProcessError):
                time.sleep(2)
        if (after is None or before!=after or
                after.get('distinct_engines') is not True):
            raise RuntimeError('Two physical DB journal/index inventories changed during restart')
        compose(args,'start','native','native_relay')
        after_readback=None
        for _ in range(30):
            try:
                after_readback=native_readback_at_freeze(args,identity)
                break
            except (OSError,RuntimeError,subprocess.CalledProcessError):
                time.sleep(2)
        if after_readback is None or after_readback!=before_readback:
            raise RuntimeError('Native Worker/SourceOwner/Original Graph changed after restart')
        check_gateway_frozen(args)
        check_manifest(args)  # Re-inspect live Docker identities and relay ports.
        record['before_inventory_sha256']=hashlib.sha256(
            json.dumps(before,sort_keys=True).encode()).hexdigest()
        record['after_inventory_sha256']=hashlib.sha256(
            json.dumps(after,sort_keys=True).encode()).hexdigest()
        record['native_readback_before_after_equal']=True
        guard_runtime(ROOT,args.runtime_identity,sha,tree,runtime_sha)
        # Only unfreeze the exact flag created by THIS successful check.
        # Any error (including identity mismatch) leaves it frozen.
        if args.maintenance_file.read_text(encoding='utf-8')!=marker:
            raise RuntimeError('Another operator changed restart write-freeze')
        args.maintenance_file.unlink()
        try:
            verify_gateway_after_restart(args,identity,client)
            check_manifest(args)
        except Exception:
            # Restore this run's freeze on failed post-release connectivity.
            with args.maintenance_file.open('x') as freeze:
                freeze.write(marker)
            raise
        record['checks']={k:'PASS' for k in ('live_runtime_identity_after_restart',
            'gateway_authenticated_session','gateway_owned_native_original_sha',
            'freeze_released_after_checks')}
        record['own_restart_freeze_released_after_pass']=True
        record['status']='PASS'
    except Exception as e:
        record['status']='FAIL';record['error_type']=type(e).__name__
        raise
    finally:
        client.close()
        record['end_utc']=datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'at_id':record['at_id'],'status':record['status'],
                      'restart_freeze_held':args.maintenance_file.exists(),
                      'released_only_after_verified_pass':record.get('own_restart_freeze_released_after_pass') is True}))


if __name__=='__main__':main()
