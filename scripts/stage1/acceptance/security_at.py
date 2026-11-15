#!/usr/bin/env python3
"""WP09 A Stage AT02/07/08/09 security probes. IMPLEMENTED_UNTESTED.

Destructive raw Native requests are NOT sent if a port is reachable. Security
failures always fail closed. External observer proof + Docker identity +
Gateway route denial required; local loopback-only does not satisfy HTTPS AT07.
"""
import argparse
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from datetime import datetime,timezone,timedelta
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
from runtime_identity import tls_gateway_identity
from acceptance.evidence_inventory import verify_clean_source


def ensure(condition,reason):
    if not condition:raise AssertionError(reason)


def negative_startups():
    import tempfile
    base=os.environ.copy()
    base['VAULT_STORE_BACKEND']='surreal'
    # A failure caused by some other missing setting proves nothing about the
    # secret under test. Validate the exact baseline without opening a DB.
    baseline=subprocess.run([sys.executable,'-c','from config import from_env; from_env()'],
        cwd=str(ROOT/'apps/a-vault'),env=base,stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
    ensure(baseline.returncode==0,'Gateway secret probe baseline configuration invalid')
    errors={'VAULT_NATIVE_PASSWORD':'VAULT_NATIVE_PASSWORD',
            'VAULT_ENCRYPTION_KEY':'VAULT_ENCRYPTION_KEY',
            'VAULT_SESSION_SECRET':'VAULT_SESSION_SECRET',
            'VAULT_SURREAL_PASSWORD':'Missing/unsafe A database password',
            'VAULT_SURREAL_USER':'Missing/unsafe A database user'}
    for key,expected_error in errors.items():
        env=base.copy()
        env.pop(key,None)
        # Never execute a process on an already occupied fixed port.
        with tempfile.TemporaryDirectory() as tmp:
            child=subprocess.Popen([sys.executable,'-m','uvicorn','server:app',
                '--host','127.0.0.1','--port','0','--no-access-log'],
                cwd=str(ROOT/'apps/a-vault'),env=env,
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                try:_,error=child.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    raise AssertionError('Unsafe config unexpectedly started serving with missing '+key)
                ensure(child.returncode!=0 and expected_error.encode() in error,
                       'Missing '+key+' rejection was not attributable to that setting')
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
    physical,_,_=verify_manifest(args.runtime_identity,args.context,args.project,
                                 args.source_sha,args.source_tree)
    for service,prefix in (('a_db','A_SURREAL'),('on_db','ON_SURREAL')):
        user=physical['services'][service]['container_user'].split(':')
        baseline[prefix+'_IMAGE_UID']=user[0]
        baseline[prefix+'_IMAGE_GID']=user[1]
    first=subprocess.run(fixed,env=baseline,capture_output=True,text=True,timeout=30)
    if first.returncode!=0:
        raise RuntimeError('Baseline pinned private Compose config cannot be proven')
    tested=[]
    for key in ('OPEN_NOTEBOOK_PASSWORD','OPEN_NOTEBOOK_ENCRYPTION_KEY',
                'A_SURREAL_USER','A_SURREAL_PASSWORD',
                'ON_SURREAL_USER','ON_SURREAL_PASSWORD',
                'ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE'):
        altered=baseline.copy();altered.pop(key,None)
        result=subprocess.run(fixed,env=altered,capture_output=True,text=True,timeout=30)
        # An unrelated Docker outage is not proof of secret fail-start.
        if result.returncode==0 or key not in (result.stdout+result.stderr):
            raise AssertionError('Native Compose missing-'+key+' startup gate not demonstrable')
        tested.append(key)
    return tested



def native_process_secret_fail_start(args):
    """Run the *attested image entrypoint* on an isolated, networkless process.

    A Docker Compose --quiet config rejection alone does not prove Native
    process safety. Baseline entrypoint must exec /bin/true; each missing
    secret must exit with the specific patched-entrypoint error. No API,
    Worker, SurrealDB or external network starts during these probes.
    """
    identity,_,_=verify_manifest(args.runtime_identity,args.context,args.project,
                                 args.source_sha,args.source_tree)
    image=identity['services']['native']['image_id']
    required=('OPEN_NOTEBOOK_PASSWORD','OPEN_NOTEBOOK_ENCRYPTION_KEY',
              'SURREAL_USER','SURREAL_PASSWORD')
    runtime_env=os.environ.copy()
    if not runtime_env.get('ON_SURREAL_USER') or not runtime_env.get('ON_SURREAL_PASSWORD'):
        raise RuntimeError('Private ON physical engine root secrets missing')
    runtime_env['SURREAL_USER']=runtime_env['ON_SURREAL_USER']
    runtime_env['SURREAL_PASSWORD']=runtime_env['ON_SURREAL_PASSWORD']
    if any(not runtime_env.get(k) for k in required):
        raise RuntimeError('Pinned Native process smoke requires operator secrets in private env')
    base=['docker','--context',args.context,'run','--rm','--network','none',
          '--security-opt','no-new-privileges','--pids-limit','64',
          '--entrypoint','/app/scripts/docker-entrypoint.sh',
          '-e','OPEN_NOTEBOOK_PASSWORD_FILE=',
          '-e','OPEN_NOTEBOOK_ENCRYPTION_KEY_FILE=',
          '-e','OPEN_NOTEBOOK_ENABLE_DOCLING=false',
          '-e','OPEN_NOTEBOOK_ENABLE_CRAWL4AI=false']
    for key in required:
        base.extend(['-e',key])
    # -e KEY inherits a value from the local operator env, NEVER its text in
    # command arguments. The Docker image is pinned to the exact identity.
    def invoke(key=None,value=None):
        cmd=base.copy()
        if key:
            cmd.extend(['-e',key+'='+value])
        cmd.extend([image,'/bin/true'])
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=90,
                            env=runtime_env)
        return proc.returncode,proc.stdout+proc.stderr
    status,output=invoke()
    if status!=0 or 'Starting Open Notebook.' not in output:
        raise AssertionError('Baseline attested Native entrypoint did not run successfully')
    completed=[]
    for key in required:
        status,output=invoke(key,'')
        if status!=78 or 'SUNRISE_NATIVE_SECRET_FAIL_START: '+key not in output:
            raise AssertionError('Pinned Native process did not fail-start missing '+key)
        completed.append(key)
    for key,value in (('OPEN_NOTEBOOK_PASSWORD','password'),
                      ('OPEN_NOTEBOOK_ENCRYPTION_KEY','changeme'),
                      ('SURREAL_PASSWORD','root:root')):
        status,output=invoke(key,value)
        if status!=78 or 'SUNRISE_NATIVE_SECRET_FAIL_START: '+key not in output:
            raise AssertionError('Pinned Native process accepted example secret '+key)
    return {'image_id':image,'baseline_entrypoint':'PASS',
            'missing_secret_rejected':completed,
            'weak_example_secret_rejected':True,
            'network':'none','native_api_worker_started':False}



def verify_external_denial_evidence(args):
    """Consume *signed real-observer* evidence bound to a real target host.

    An arbitrary RFC1918 IP or three TCP timeouts are not security proof.
    No arbitrary network probes are issued by the acceptance consumer.
    """
    identity,mappings,identity_sha=verify_manifest(args.runtime_identity,args.context,
                                         args.project,args.source_sha,args.source_tree)
    target=identity.get('external_target')
    ensure(isinstance(target,dict) and
           target.get('private_ip')==verify_private_address(args.target_private_ip) and
           isinstance(target.get('host_identity_sha256'),str) and
           len(target['host_identity_sha256'])==64 and
           all(x in '0123456789abcdef' for x in target['host_identity_sha256']),
           'C runtime identity must independently bind actual external target host')
    document=getattr(args,'observer_evidence',None)
    ensure(document and document.is_file() and not document.is_symlink()
           and document.stat().st_size<=1<<16,
           'Signed independent observer evidence missing')
    envelope=json.loads(document.read_text(encoding='utf-8'))
    ensure(isinstance(envelope,dict) and set(envelope)=={'payload','signature_ed25519'}
           and isinstance(envelope['payload'],dict),'Malformed signed observer evidence')
    payload=envelope['payload']
    trust=os.getenv('VAULT_EXTERNAL_OBSERVER_PUBKEY_BASE64')
    ensure(bool(trust),'Independently pinned observer public key absent')
    try:
        key=base64.b64decode(trust,validate=True)
        signature=base64.b64decode(envelope['signature_ed25519'],validate=True)
        ensure(len(key)==32 and len(signature)==64,'Invalid observer signing key')
        Ed25519PublicKey.from_public_bytes(key).verify(signature,
            json.dumps(payload,sort_keys=True,separators=(',',':')).encode('utf-8'))
    except (ValueError,TypeError,KeyError) as error:
        raise AssertionError('Observer signature verification failed') from error
    expected={'type':'SUNRISE_S1_EXTERNAL_PORT_DENIAL_V1',
              'source_commit':args.source_sha,'source_tree':args.source_tree,
              'runtime_identity_sha256':identity_sha,
              'context':args.context,'project':args.project,
              'target_private_ip':target['private_ip'],
              'target_host_identity_sha256':target['host_identity_sha256'],
              'gateway_instance_id':identity['gateway'].get('instance_id'),
              'observer_independent':True,
              'observer_network_isolated':True,
              'target_host_identity_verified':True}
    ensure(all(payload.get(k)==v for k,v in expected.items()),
           'Observer target/physical runtime/source binding mismatch')
    ensure(isinstance(payload.get('observer_id'),str) and len(payload['observer_id'])>=12,
           'Independent observer identity missing')
    observed=payload.get('observed_utc')
    ensure(isinstance(observed,str),'Observer UTC missing')
    try:
        when=datetime.fromisoformat(observed.replace('Z','+00:00'))
        ensure(when.tzinfo is not None and when.utcoffset()==timedelta(0),
               'Only UTC observer evidence accepted')
        age=datetime.now(timezone.utc)-when
        ensure(timedelta(seconds=-30)<=age<=timedelta(minutes=10),
               'External observer evidence stale or future-dated')
    except ValueError as error:
        raise AssertionError('Invalid observer UTC') from error
    observations=payload.get('observations')
    ensure(isinstance(observations,list) and len(observations)==len(mappings),
           'Missing physical service port observations')
    intended={(service,container,bind,port,internal)
              for service,container,bind,port,internal in mappings}
    measured=set()
    for row in observations:
        ensure(isinstance(row,dict) and row.get('outcome') in
               ('CONNECTION_REFUSED','CONNECTION_TIMED_OUT') and
               row.get('target_host_identity_verified') is True,
               'External observer result cannot prove denial')
        item=(row.get('service'),row.get('container_id'),row.get('published_host_ip'),
              row.get('published_host_port'),row.get('container_port'))
        ensure(item in intended and item not in measured,
               'Port observation does not match the exact Docker service')
        measured.add(item)
    ensure(measured==intended,'Incomplete independent published port coverage')
    return {'external_network_status':'SIGNED_REAL_TARGET_OBSERVER_DENIED',
            'observer_evidence_sha256':hashlib.sha256(document.read_bytes()).hexdigest(),
            'runtime_identity_sha256':identity_sha,
            'observer_utc':observed,'observer_id':payload['observer_id'],
            'physical_services':sorted(x[0] for x in measured)}


def public_port_denials(args):
    """Legacy name retained; now rejects unbound RFC1918/private-IP guesses."""
    return verify_external_denial_evidence(args)


def gateway_negative(args,at):
    base=urlsplit(args.gateway)
    ensure(base.scheme=='https' and base.hostname in ('127.0.0.1','localhost')
           and base.port and not base.username and not base.password
           and base.path in ('','/') and not base.query and not base.fragment,
           'All security ATs require exactly pinned loopback HTTPS Gateway')
    identity,_,_=verify_manifest(args.runtime_identity,args.context,args.project,
                                 args.source_sha,args.source_tree)
    gateway=identity['gateway']
    ensure(set(identity.get('services',{}))=={'a_db','on_db','native'}
           and identity.get('dual_rpc',{}).get('on_viewer_read_only') is True
           and identity.get('dual_rpc',{}).get('separate_root_secrets') is True,
           'Independent dual DB and read-only graph viewer missing')
    ca=args.gateway_ca_file
    ensure(ca.is_file() and not ca.is_symlink() and ca.stat().st_size<=1<<20,
           'Exact independent Gateway CA material required')
    ensure(hashlib.sha256(ca.read_bytes()).hexdigest()==gateway.get('tls_ca_sha256')
           and args.gateway.rstrip('/')==gateway.get('origin'),
           'AT Gateway origin/CA differs from captured physical runtime')
    verified=tls_gateway_identity(args.gateway,ca)
    ensure(verified.get('tls_peer_sha256')==gateway.get('tls_peer_sha256')
           and verified.get('instance_id')==gateway.get('instance_id'),
           'Actual HTTPS TLS peer/Gateway identity changed after capture')
    with httpx.Client(base_url=args.gateway,verify=str(ca),trust_env=False,
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
        if at=='S1-AT07':
            ensure(os.environ.get('VAULT_COOKIE_SECURE','').lower()=='true',
                   'Actual Gateway secure-cookie launch setting not attested')
            login=c.get('/auth/login')
            ensure(login.status_code==200,'Real login page unavailable')
            cookies=login.headers.get_list('set-cookie')
            ensure(any('Secure' in value and 'HttpOnly' in value and
                       'SameSite=strict' in value for value in cookies),
                   'Real login CSRF cookie lacks HTTPS/HttpOnly/SameSite')
            no_csrf=c.post('/auth/login',data={'password':'synthetic-invalid','csrf':'missing'})
            ensure(no_csrf.status_code==403,'Missing login CSRF not rejected')
            unauthorized=c.post('/auth/school',json={'school_id':'synthetic-other'})
            ensure(unauthorized.status_code in (401,403),
                   'Missing session / school CSRF unexpectedly accepted')
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
    p.add_argument('--owner-attestation',type=Path)  # required for AT07
    p.add_argument('--gateway-ca-file',required=True,type=Path)
    for key in ('runtime-identity','context','project','source-sha','source-tree',
                'target-private-ip','out'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--observer-evidence',type=Path)
    args=p.parse_args()
    args.runtime_identity=Path(args.runtime_identity)
    args.out=Path(args.out)
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Exclusive synthetic runtime confirmation required')
    # AT08 executes local fail-start processes and networkless image probes.
    # It must not require a nonexistent external observer declaration. Network
    # acceptance cases still require the independent observer and signed proof.
    if args.at_id!='S1-AT08' and os.getenv('VAULT_OBSERVER_ISOLATED_CONFIRM')!='YES':
        p.error('External synthetic observer attestation required')
    verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.out)
    report={'at_id':args.at_id,'status':'NOT_RUN',
            'source_commit':args.source_sha,'source_tree':args.source_tree,
            'started_utc':datetime.now(timezone.utc).isoformat()}
    try:
        if args.at_id=='S1-AT08':
            negative_startups()
            tested=native_compose_secret_preflight(args)
            identity,_,identity_sha=verify_manifest(args.runtime_identity,args.context,
                args.project,args.source_sha,args.source_tree)
            report['runtime_identity_sha256']=identity_sha
            report['gateway_secret_fail_start']='PASS'
            report['pinned_native_compose_required_secrets']=tested
            report['direct_native_process_missing_secret_test']=native_process_secret_fail_start(args)
            report['status']='PASS'
        else:
            report['private_ports']=public_port_denials(args)
            report['runtime_identity_sha256']=report['private_ports']['runtime_identity_sha256']
            report.update(gateway_negative(args,args.at_id))
        if args.at_id=='S1-AT07':
            if not args.owner_attestation:
                raise RuntimeError('Signed independent Owner full-volume data review required for AT07')
            audit_path=args.out.with_name(args.out.stem+'-admin-audit.json')
            if audit_path.exists():
                raise RuntimeError('Admin audit evidence overwrite refused')
            script=Path(__file__).parent/'admin_data_audit.py'
            fixed=[sys.executable,str(script),
                '--gateway',args.gateway,'--gateway-ca-file',str(args.gateway_ca_file),
                '--runtime-identity',str(args.runtime_identity),
                '--owner-attestation',str(args.owner_attestation),
                '--context',args.context,'--project',args.project,
                '--source-sha',args.source_sha,'--source-tree',args.source_tree,
                '--out',str(audit_path)]
            attempt=subprocess.run(fixed,cwd=str(ROOT),capture_output=True,
                                   text=True,timeout=480)
            if attempt.returncode!=0:
                raise RuntimeError('Independent AT07 Admin/data audit failed; see isolated evidence')
            audited=json.loads(audit_path.read_text(encoding='utf-8'))
            if (audited.get('status')!='PASS'
                    or audited.get('at_id')!='S1-AT07-AUDIT'
                    or audited.get('source_commit')!=args.source_sha
                    or audited.get('source_tree')!=args.source_tree
                    or audited.get('signed_data_scope',{}).get('signature_verified') is not True
                    or any(audited.get('real_admin_session_audit',{}).get(k)!='PASS'
                           for k in ('admin_login_audit','trusted_school_switch_audit',
                                     'admin_logout_audit','session_revocation'))):
                raise RuntimeError('AT07 requires signed real audit and durable session evidence')
            report['unique_admin_full_login_audit']='PASS'
            report['real_student_data_absence_audit']='INDEPENDENT_SIGNED_FULL_VOLUME_REVIEW'
            report['audit_evidence_sha256']=hashlib.sha256(audit_path.read_bytes()).hexdigest()
        verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.out)
        report['status']='PASS'
    except Exception as error:
        report['status']='FAIL';report['error_type']=type(error).__name__
        raise
    finally:
        report['end_utc']=datetime.now(timezone.utc).isoformat()
        if args.out.exists():raise RuntimeError('Evidence overwrite refused')
        with args.out.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
