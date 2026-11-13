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
    keys=('VAULT_NATIVE_PASSWORD','VAULT_ENCRYPTION_KEY',
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


def native_compose_secret_preflight(args):
    # Direct Native/Surreal runtime secret checks belong to the actual pinned
    # private Compose definition, not the A Gateway process. A missing ON
    # password never affects A Gateway startup by itself.
    if not args.native_compose_file or not args.native_compose_file.is_file():
        raise RuntimeError('Exact private Native Compose required for AT08')
    fixed=['docker','--context',args.context,'compose','-p',args.project,
           '-f',str(args.native_compose_file),'config','--quiet']
    baseline=os.environ.copy()
    first=subprocess.run(fixed,env=baseline,capture_output=True,text=True,timeout=30)
    if first.returncode!=0:
        raise RuntimeError('Baseline pinned private Compose config cannot be proven')
    tested=[]
    for key in ('OPEN_NOTEBOOK_PASSWORD','OPEN_NOTEBOOK_ENCRYPTION_KEY',
                'SURREAL_USER','SURREAL_PASSWORD'):
        altered=baseline.copy();altered.pop(key,None)
        result=subprocess.run(fixed,env=altered,capture_output=True,text=True,timeout=30)
        # An unrelated Docker outage is not proof of secret fail-start.
        if result.returncode==0 or key not in (result.stdout+result.stderr):
            raise AssertionError('Native Compose missing-'+key+' startup gate not demonstrable')
        tested.append(key)
    return tested


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
        # Bind HTTPS/loopback observer result to the actual private Gateway
        # instance captured alongside the Docker Compose project.
        manifest=json.loads(args.runtime_identity.read_text(encoding='utf-8'))
        instance=manifest.get('gateway',{}).get('instance_id')
        if not isinstance(instance,str) or len(instance)!=32:
            raise RuntimeError('Missing captured Gateway instance identity')
        health=c.get('/health')
        ensure(health.status_code==200,'Gateway health endpoint is unavailable')
        result=health.json()
        ensure(result.get('gateway')=='running' and
               result.get('gateway_instance')==instance,
               'Observed HTTP endpoint is not the attested private Gateway process')
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
            for path in ('/api/notebooks/synthetic-nonexistent',
                         '/api/notebooks/synthetic-nonexistent/sources/synthetic-nonexistent',
                         '/api/sources/synthetic-nonexistent'):
                denied=c.delete(path)
                ensure(denied.status_code in (401,403,404),'Raw Native DELETE available')
        return {'gateway_https_verified':base.scheme=='https',
                'gateway_instance_attested':True,'anonymous_denied':True,
                'raw_native_get_post_delete_negative':at in ('S1-AT02','S1-AT09')}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--at-id',required=True,choices=['S1-AT02','S1-AT07','S1-AT08','S1-AT09'])
    p.add_argument('--gateway',required=True)
    p.add_argument('--native-compose-file',type=Path)  # required only for AT08
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
            tested=native_compose_secret_preflight(args)
            report['gateway_secret_fail_start']='PASS'
            report['pinned_native_compose_required_secrets']=tested
            report['direct_native_process_missing_secret_test']='NOT_RUN'
            report['status']='PARTIAL_NEEDS_NATIVE_PROCESS_FAIL_START'
            # Compose variable interpolation is useful evidence, but cannot
            # prove that the pinned Native process rejects example passwords.
            raise SystemExit(2)
        else:
            report['private_ports']=public_port_denials(args)
            report.update(gateway_negative(args,args.at_id))
        if args.at_id=='S1-AT07':
            report['unique_admin_full_login_audit']='NOT_RUN'
            report['real_student_data_absence_audit']='NOT_RUN'
            report['status']='PARTIAL_NEEDS_INDEPENDENT_DATA_AND_ADMIN_AUDIT'
            raise SystemExit(2)
        report['status']='PASS'
    except Exception as error:
        report['status']='FAIL';report['error_type']=type(error).__name__
        raise
    finally:
        report['end_utc']=datetime.now(timezone.utc).isoformat()
        if args.out.exists():raise RuntimeError('Evidence overwrite refused')
        args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
