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


def load_identity(args,manifest):
    raw=args.source_runtime_identity.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest.get('runtime_identity_sha256'):
        raise BackupInvalid('Runtime identity different from cold recovery point')
    identity=json.loads(raw)
    if (identity.get('type')!='SUNRISE_S1_A_DOCKER_RUNTIME_IDENTITY_UNREVIEWED'
            or identity.get('source_commit')!=manifest['source_commit']
            or identity.get('source_tree')!=manifest['source_tree']
            or manifest.get('external_key_escrow_reference')!=args.key_escrow_reference
            or identity.get('project')==args.project):
        raise BackupInvalid('Foreign source identity or target collision')
    service=identity.get('services')
    if not isinstance(service,dict) or set(service)!={'surrealdb','open_notebook'}:
        raise BackupInvalid('Missing exact source images')
    for name in ('surrealdb','open_notebook'):
        if not re.fullmatch(r'sha256:[a-f0-9]{64}',str(service[name].get('image_id',''))):
            raise BackupInvalid('Unverified immutable container image ID')
    if not args.key_escrow_reference.startswith('offline-escrow:'):
        raise BackupInvalid('External private escrow reference required')
    return identity


def restore_env(identity):
    env=os.environ.copy()
    env['SURREAL_RESTORE_IMAGE']=identity['services']['surrealdb']['image_id']
    env['ON_RESTORE_IMAGE']=identity['services']['open_notebook']['image_id']
    required=('SURREAL_USER','SURREAL_PASSWORD','OPEN_NOTEBOOK_PASSWORD',
              'OPEN_NOTEBOOK_ENCRYPTION_KEY','ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE',
              'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE')
    if any(not env.get(k) for k in required):
        raise BackupInvalid('Restore secrets or namespace bindings absent')
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
    for service in ('surrealdb','open_notebook'):
        cid=container_id(args,service,env)
        info=json.loads(docker(args.context,'inspect',cid))[0]
        if info['Config']['Labels'].get('com.docker.compose.project')!=args.project:
            raise BackupInvalid('Target resource belongs to another project')
        if any(x for x in info.get('HostConfig',{}).get('PortBindings',{}).values() if x):
            raise BackupInvalid('Restore target publishes private port: REFUSE START')
        networks=info.get('NetworkSettings',{}).get('Networks') or {}
        if len(networks)!=1 or not all(args.project in key for key in networks):
            raise BackupInvalid('Restore target has unexpected/bridged Docker network')


def runtime_inventory(args,env):
    code=(Path(__file__).parent/'db_inventory.py').read_text(encoding='utf-8')
    # "compose run" uses a transient private utility container with Python
    # entrypoint; never starts Native worker/UI, no port published.
    raw=compose(args,'run','--rm','--no-deps','-T','--entrypoint','python',
                'open_notebook','-c',code,env=env)
    data=json.loads(raw)
    if data.get('classification')!='DB_INVENTORY_ONLY_NOT_ACCEPTANCE':
        raise BackupInvalid('Restore DB verification source not authoritative')
    return data


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
    if not args.context or not args.compose_file.is_file() or args.compose_file.is_symlink():
        p.error('Explicit Docker context and private Compose file required')
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
    compose(args,'create','--no-recreate','surrealdb','open_notebook',env=env)
    inspect_isolation(args,env)
    transfer_into_volume(args,'surrealdb',args.workdir/'surreal','/mydata',env)
    transfer_into_volume(args,'open_notebook',args.workdir/'native','/app/data',env)
    # Start the *private* DB only. Native UI/Worker remain stopped until
    # DB, ownership, index, graph and original files have been independently reviewed.
    compose(args,'start','surrealdb',env=env)
    reference=json.loads((args.workdir/'gateway'/'db-inventory.json').read_text())
    restored=runtime_inventory(args,env)
    if restored!=reference:
        raise BackupInvalid('Isolated A/ON DB record counts, identity or canonical hashes differ')
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
