#!/usr/bin/env python3
"""WP08 isolated Docker restore runner; IMPLEMENTED_UNTESTED.

Uses the existing A cold tar manifest/restore_isolated instead of a second
backup engine. Source Docker project and volumes are NEVER changed or cleaned.
Target project must be new and isolated; no published host TCP ports, Native UI,
public DB/Worker, real school data or external providers are permitted.

Any failure leaves new TARGET project frozen for operator inspection. It never
silently rolls back or removes source/target volumes.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from a_cold_backup import BackupInvalid,restore_isolated,verify
from runtime_identity import git_identity
from dual_inventory_runner import both

HEX40=re.compile(r'^[a-f0-9]{40}$')
HEX64=re.compile(r'^[a-f0-9]{64}$')
PROJECT=re.compile(r'^sunrise-s1-restore-[a-z0-9-]{8,45}$')


def run(args,env=None,timeout=180):
    outcome=subprocess.run(args,text=True,capture_output=True,timeout=timeout,env=env)
    if outcome.returncode:
        raise BackupInvalid('Isolated Docker operation failed; command status '+str(outcome.returncode))
    return outcome.stdout


def docker(context,*args,env=None):
    return run(['docker','--context',context,*args],env=env)


def compose(args,*arguments,env=None):
    return docker(args.context,'compose','-p',args.project,'-f',str(args.compose_file),
                  *arguments,env=env)


def target_clean(args):
    containers=docker(args.context,'ps','--all','-q','--filter',
                      'label=com.docker.compose.project='+args.project)
    volumes=docker(args.context,'volume','ls','-q','--filter',
                   'label=com.docker.compose.project='+args.project)
    if containers.strip() or volumes.strip():
        raise BackupInvalid('Target Compose project/volumes already exist: never overwrite')
    if args.workdir.exists():
        raise BackupInvalid('Target restore staging path already exists')
    for leaf in ('a_db_data','on_db_data','native_data'):
        volume=args.project+'_'+leaf
        attempt=subprocess.run(['docker','--context',args.context,
            'volume','inspect',volume],capture_output=True,text=True,timeout=30)
        if attempt.returncode==0:
            raise BackupInvalid('Foreign or old target named volume exists: '+leaf)


def load_identity(args,manifest):
    raw=args.source_runtime_identity.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest.get('runtime_identity_sha256'):
        raise BackupInvalid('Runtime identity different from cold recovery point')
    identity=json.loads(raw)
    if (identity.get('type')!='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'
            or identity.get('source_commit')!=manifest['source_commit']
            or identity.get('source_tree')!=manifest['source_tree']
            or manifest.get('external_key_escrow_reference')!=args.key_escrow_reference
            or identity.get('project')==args.project):
        raise BackupInvalid('Foreign source identity or target collision')
    service=identity.get('services')
    if not isinstance(service,dict) or set(service)!={'a_db','on_db','native'}:
        raise BackupInvalid('Missing exact physically independent source images')
    if (service['a_db'].get('container_id')==service['on_db'].get('container_id') or
            service['a_db'].get('network_id')==service['on_db'].get('network_id') or
            service['a_db'].get('persistent_volume')==service['on_db'].get('persistent_volume')):
        raise BackupInvalid('Source did not contain independently isolated physical DBs')
    for name in ('a_db','on_db','native'):
        if not re.fullmatch(r'sha256:[a-f0-9]{64}',str(service[name].get('image_id',''))):
            raise BackupInvalid('Unverified immutable container image ID')
    if not args.key_escrow_reference.startswith('offline-escrow:'):
        raise BackupInvalid('External private escrow reference required')
    return identity


def restore_env(identity):
    env=os.environ.copy()
    services=identity['services']
    env['A_DB_RESTORE_IMAGE']=services['a_db']['image_id']
    env['ON_DB_RESTORE_IMAGE']=services['on_db']['image_id']
    env['ON_RESTORE_IMAGE']=services['native']['image_id']
    for service,prefix in (('a_db','A'),('on_db','ON')):
        user=services[service].get('container_user','')
        if not re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',user):
            raise BackupInvalid('Pinned physical DB nonroot user not attested')
        env[prefix+'_RESTORE_UID'],env[prefix+'_RESTORE_GID']=user.split(':')
    required=('A_SURREAL_USER','A_SURREAL_PASSWORD','A_SURREAL_NAMESPACE',
              'A_SURREAL_DATABASE','ON_SURREAL_USER','ON_SURREAL_PASSWORD',
              'OPEN_NOTEBOOK_PASSWORD','OPEN_NOTEBOOK_ENCRYPTION_KEY',
              'ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE')
    if any(not env.get(k) for k in required):
        raise BackupInvalid('Separate physical restore secrets or DB identities missing')
    if env['A_SURREAL_PASSWORD']==env['ON_SURREAL_PASSWORD']:
        raise BackupInvalid('Restored physical DBs cannot share root credentials')
    if (identity.get('surreal_namespace')!=env['A_SURREAL_NAMESPACE']
            or identity.get('surreal_database')!=env['A_SURREAL_DATABASE']
            or identity.get('on_namespace')!=env['ON_GRAPH_NAMESPACE']
            or identity.get('on_database')!=env['ON_GRAPH_DATABASE']):
        raise BackupInvalid('Wrong root namespace/database bindings for restored image')
    return env

def container_id(args,service,env):
    raw=compose(args,'ps','--all','-q',service,env=env).strip().splitlines()
    if len(raw)!=1 or not re.fullmatch(r'[a-f0-9]{64}',raw[0]):
        raise BackupInvalid('Expected one new isolated '+service+' container')
    return raw[0]


def transfer_into_volume(args,service,root,path,env):
    cid=container_id(args,service,env)
    # Docker cp into the target's declared named volume mount, while stopped.
    docker(args.context,'cp',str(root)+os.sep+'.',f'{cid}:{path}')
    # Roundtrip through the target container's actual volume mount.
    verify_dir=args.workdir/('volume-check-'+service)
    verify_dir.mkdir()
    docker(args.context,'cp',f'{cid}:{path}/.',str(verify_dir))
    for original in sorted(root.rglob('*')):
        if original.is_symlink():raise BackupInvalid('Restored symlink prohibited')
        if original.is_file():
            relative=original.relative_to(root)
            copy=verify_dir/relative
            if not copy.is_file() or copy.is_symlink() or (
                hashlib.sha256(copy.read_bytes()).hexdigest()!=hashlib.sha256(original.read_bytes()).hexdigest()):
                raise BackupInvalid('Independent Docker volume restore bytes differ: '+str(relative))


def inspect_isolation(args,env):
    images={'a_db':env['A_DB_RESTORE_IMAGE'],'on_db':env['ON_DB_RESTORE_IMAGE'],
            'native':env['ON_RESTORE_IMAGE']}
    mounts={'a_db':('/mydata','a_db_data'),
            'on_db':('/mydata','on_db_data'),
            'native':('/app/data','native_data')}
    networks={'a_db':'a_db_private','on_db':'on_db_private','native':'on_db_private'}
    observed={}
    for service in ('a_db','on_db','native'):
        cid=container_id(args,service,env)
        info=json.loads(docker(args.context,'inspect',cid))[0]
        if info.get('Id')!=cid or info.get('Image')!=images[service]:
            raise BackupInvalid('Target service immutable image identity mismatch')
        if info['Config']['Labels'].get('com.docker.compose.project')!=args.project:
            raise BackupInvalid('Foreign restore container')
        if any(x for x in info.get('HostConfig',{}).get('PortBindings',{}).values() if x):
            raise BackupInvalid('Isolated restored A/ON/Native publishes a TCP port')
        mount,leaf=mounts[service]
        found=[m for m in info.get('Mounts',[]) if m.get('Destination')==mount]
        if (len(found)!=1 or found[0].get('Type')!='volume'
                or found[0].get('Name')!=args.project+'_'+leaf):
            raise BackupInvalid('Wrong or reused target physical DB/native volume')
        expected_network=args.project+'_'+networks[service]
        network=info.get('NetworkSettings',{}).get('Networks') or {}
        if set(network)!={expected_network}:
            raise BackupInvalid('Target physical DB cross-engine network exposure')
        observed[service]=network[expected_network].get('NetworkID')
        if service in ('a_db','on_db') and info['Config'].get('User')!=(
                env['A_RESTORE_UID']+':'+env['A_RESTORE_GID'] if service=='a_db'
                else env['ON_RESTORE_UID']+':'+env['ON_RESTORE_GID']):
            raise BackupInvalid('Target physical DB running as wrong UID/GID')
    if observed['a_db']==observed['on_db'] or observed['on_db']!=observed['native']:
        raise BackupInvalid('Restored A/ON physical network trust-domain collision')


def restore_new_target_db_owner(args,env,root,manifest):
    """Only target new volumes; check exact restored files BEFORE chown or write."""
    if root not in ('a_db','on_db'):
        raise BackupInvalid('Unexpected target ownership operation')
    leaf=root+'_data'
    volume=args.project+'_'+leaf
    raw=json.loads(docker(args.context,'volume','inspect',volume))
    if (len(raw)!=1 or raw[0].get('Name')!=volume
            or raw[0].get('Labels',{}).get('com.docker.compose.project')!=args.project
            or raw[0].get('Labels',{}).get('com.docker.compose.volume')!=leaf):
        raise BackupInvalid('Non-project target DB volume cannot be adjusted')
    prefix='A' if root=='a_db' else 'ON'
    uid,gid=env[prefix+'_RESTORE_UID'],env[prefix+'_RESTORE_GID']
    helper=str(Path(__file__).parent/'restore_tree_owner.py')
    image=env['ON_RESTORE_IMAGE']
    for mode,user in (('chown','0:0'),('nonroot-probe',uid+':'+gid)):
        docker(args.context,'run','--rm','--network','none','--read-only',
               '--security-opt','no-new-privileges','--cap-drop','ALL',
               '--user',user,
               '-v',volume+':/target:rw',
               '-v',str(args.workdir)+':/proof:ro',
               '-v',helper+':/helper.py:ro',
               '--entrypoint','/app/.venv/bin/python',image,'/helper.py',
               '--mode',mode,'--root',root,'--uid',uid,'--gid',gid)


def runtime_inventory(args,env):
    return both(args.context,args.project,env['ON_RESTORE_IMAGE'])


def report(args,values):
    file=args.workdir/'restore-evidence-redacted.json'
    if file.exists():
        raise BackupInvalid('Evidence file exists, refusing to overwrite')
    file.write_text(json.dumps(values,sort_keys=True,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--source-runtime-identity',type=Path,required=True)
    p.add_argument('--key-escrow-reference',required=True)
    p.add_argument('--context',required=True)
    p.add_argument('--project',required=True)
    p.add_argument('--compose-file',type=Path,default=Path(__file__).parent/'compose.isolated.yml')
    p.add_argument('--workdir',type=Path,required=True)
    p.add_argument('--source-sha',required=True);p.add_argument('--source-tree',required=True)
    args=p.parse_args()
    if (os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or
            os.getenv('VAULT_ISOLATED_RESTORE_ALLOWED')!='YES'):
        p.error('Exclusive synthetic isolated restore not authorized')
    if not PROJECT.fullmatch(args.project) or not args.workdir.is_absolute():
        p.error('New scoped target project and absolute staging location required')
    trusted_compose=Path(__file__).parent/'compose.isolated.yml'
    if (not args.context or not args.compose_file.is_file() or args.compose_file.is_symlink()
            or args.compose_file.resolve()!=trusted_compose.resolve()):
        p.error('Only repository-owned immutable isolated Restore Compose is allowed')
    manifest=verify(args.bundle,compare_keys=True)
    if (manifest.get('recovery_point_id') is None or
            manifest.get('source_commit')!=args.source_sha or
            manifest.get('source_tree')!=args.source_tree):
        p.error('Not a confirmed consistent cold recovery-point candidate')
    local_sha,local_tree=git_identity(ROOT)
    if local_sha!=args.source_sha or local_tree!=args.source_tree:
        p.error('Checkout does not match bundled source code')
    identity=load_identity(args,manifest)
    env=restore_env(identity)
    target_clean(args)
    result=restore_isolated(args.bundle,args.workdir)
    # No source project or source Docker volume is ever mounted in the target.
    # Restore proof file is local to the new, staged target and contains only
    # cryptographic file metadata. Never write the escrow secret to this file.
    (args.workdir/'target-owner-manifest.json').write_text(
        json.dumps(manifest,sort_keys=True)+'\n',encoding='utf-8')
    compose(args,'create','--no-recreate','a_db','on_db','native',env=env)
    inspect_isolation(args,env)
    transfer_into_volume(args,'a_db',args.workdir/'a_db','/mydata',env)
    transfer_into_volume(args,'on_db',args.workdir/'on_db','/mydata',env)
    transfer_into_volume(args,'native',args.workdir/'native','/app/data',env)
    for root in ('a_db','on_db'):
        restore_new_target_db_owner(args,env,root,manifest)
    # Start both isolated DB engines, NOT Native UI/Worker.
    compose(args,'start','a_db','on_db',env=env)
    reference=json.loads((args.workdir/'gateway'/'db-inventory.json').read_text())
    restored=None
    for _ in range(30):
        try:
            restored=runtime_inventory(args,env)
            break
        except (OSError,BackupInvalid,subprocess.SubprocessError,RuntimeError):
            import time
            time.sleep(2)
    if (restored is None or restored!=reference or
            restored.get('distinct_engines') is not True
            or restored.get('distinct_private_networks') is not True):
        raise BackupInvalid('Both physical A and ON DB record counts/hashes not independently restored')
    summary={'utc':datetime.now(timezone.utc).isoformat(),
        'recovery_point':manifest['recovery_point_id'],
        'source_commit':args.source_sha,'source_tree':args.source_tree,
        'target_project':args.project,'target_context':args.context,
        'original_file_inventory_sha256':hashlib.sha256(
            json.dumps(manifest['files'],sort_keys=True).encode()).hexdigest(),
        'db_inventories_equal':True,'native_worker_running':False,
        'gateway_exposed':False,'classification':'ISOLATED_DB_RESTORE_VERIFIED_NATIVE_NOT_STARTED',
        'formal_AT05':'NOT_RUN','owner_UAT':'NOT_RUN'}
    report(args,summary)
    print(json.dumps({'classification':summary['classification'],
                      'evidence':str(args.workdir/'restore-evidence-redacted.json')},sort_keys=True))


if __name__=='__main__':main()
