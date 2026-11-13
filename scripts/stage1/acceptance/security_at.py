#!/usr/bin/env python3
"""WP09 A Stage AT02/07/08/09 security probes. IMPLEMENTED_UNTESTED.

Destructive raw Native requests are NOT sent if a port is reachable. Security
failures always fail closed. External observer proof + Docker identity +
Gateway route denial required; local loopback-only does not satisfy HTTPS AT07.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from urllib.parse import urlsplit
import httpx

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from wp01_network_boundary_probe import verify_manifest,verify_private_address


def ensure(condition,reason):
    if not condition:raise AssertionError(reason)


def negative_startups():
    import tempfile
    base=os.environ.copy()
    keys=('OPEN_NOTEBOOK_PASSWORD','VAULT_NATIVE_PASSWORD','VAULT_ENCRYPTION_KEY',
          'VAULT_SESSION_SECRET','VAULT_SURREAL_PASSWORD','VAULT_SURREAL_USER')
    for key in keys:
        env=base.copy()
        env.pop(key,None)
        env['VAULT_STORE_BACKEND']='surreal'
        # Never execute a process on an already occupied fixed port.
        with tempfile.TemporaryDirectory() as tmp:
            child=subprocess.Popen([sys.executable,'-m','uvicorn','server:app',
                '--host','127.0.0.1','--port','0','--no-access-log'],
                cwd=str(ROOT/'apps/a-vault'),env=env,
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                try:status=child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    raise AssertionError('Unsafe config unexpectedly started serving with missing '+key)
                ensure(status!=0,'Missing '+key+' incorrectly accepted at fail-start')
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:child.wait(timeout=3)
                    except subprocess.TimeoutExpired:child.kill()
    # Example secrets must also fail-start; no external services created.
    from argon2 import PasswordHasher
    sys.path.insert(0,str(ROOT/'apps/a-vault'))
    from config import Settings
    base_args=dict(admin_hash=PasswordHasher().hash('synthetic-only-acceptable'),
        session_secret='S'*48,encryption_key='E'*48,
        school_id='synthetic-a',actor_id='synthetic-admin',
        native_url='http://127.0.0.1:5055',native_password='long-private-test-secret',
        sqlite_file=':memory:',store_backend='synthetic_sqlite')
    for patch in ({'native_password':'password'},{'session_secret':'abc'},
                  {'encryption_key':'same','session_secret':'same'}):
        try: Settings(**{**base_args,**patch}).validate()
        except ValueError:continue
        raise AssertionError('Example/weak secret accepted')


def public_port_denials(args):
    identity,mappings,_=verify_manifest(args.runtime_identity,args.context,args.project,
                                         args.source_sha,args.source_tree)
    host=verify_private_address(args.target_private_ip)
    ensure(bool(mappings),'No genuine Docker Published Port mappings available to test')
    observed=[]
    for service,container,bind,port,internal in mappings:
        try:
            with socket.create_connection((host,port),timeout=3):
                raise AssertionError('Private '+service+' published HostPort reachable externally')
        except (socket.timeout,ConnectionRefusedError,OSError) as error:
            observed.append({'service':service,'published_host_port':port,
                'outcome':type(error).__name__})
    return observed


def gateway_negative(args,at):
    base=urlsplit(args.gateway)
    ensure(base.scheme in ('http','https'),'Gateway scheme invalid')
    if at=='S1-AT07':
        ensure(base.scheme=='https','Basic security AT07 requires verified HTTPS, not local HTTP')
    elif base.scheme=='http':
        ensure(base.hostname in ('127.0.0.1','localhost','::1'),'Unencrypted gateway is never remote')
    with httpx.Client(base_url=args.gateway,verify=True,trust_env=False,
                      follow_redirects=False,timeout=10) as c:
        # Authenticated API must never leak an anonymous school or Source.
        for path in ('/vault/v1/shells','/vault/v1/shells/foreign',
                     '/vault/v1/shells/foreign/materials','/admin'):
            response=c.get(path)
            ensure(response.status_code in (401,403,404),'Anonymous private data exposed')
        if at in ('S1-AT02','S1-AT09'):
            for path in ('/api/notebooks','/api/sources','/api/search','/api/notebooks/foo/sources/bar',
                         '/docs','/openapi.json','/events','/api/preview'):
                denied=c.get(path)
                ensure(denied.status_code in (401,403,404),'Raw Native API reached through Gateway')
            # Harmless invalid POST only: no id or source is ever created.
            for path in ('/api/notebooks','/api/search'):
                denied=c.post(path,json={'invalid':True})
                ensure(denied.status_code in (401,403,404),'Raw Native POST available')
        return {'gateway_https_verified':base.scheme=='https','anonymous_denied':True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--at-id',required=True,choices=['S1-AT02','S1-AT07','S1-AT08','S1-AT09'])
    p.add_argument('--gateway',required=True)
    for key in ('runtime-identity','context','project','source-sha','source-tree',
                'target-private-ip','out'):
        p.add_argument('--'+key,required=True)
    args=p.parse_args()
    args.runtime_identity=Path(args.runtime_identity)
    args.out=Path(args.out)
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or (
        os.getenv('VAULT_OBSERVER_ISOLATED_CONFIRM')!='YES'):
        p.error('External synthetic observer attestation required')
    report={'at_id':args.at_id,'status':'NOT_RUN','started_utc':datetime.now(timezone.utc).isoformat()}
    try:
        if args.at_id=='S1-AT08':
            negative_startups()
            report['missing_secrets_and_weak_sample_fail_start']=True
        else:
            report['private_ports']=public_port_denials(args)
            report.update(gateway_negative(args,args.at_id))
        report['status']='PASS'
    except Exception as error:
        report['status']='FAIL';report['error_type']=type(error).__name__
        raise
    finally:
        report['end_utc']=datetime.now(timezone.utc).isoformat()
        if args.out.exists():raise RuntimeError('Evidence overwrite refused')
        args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
