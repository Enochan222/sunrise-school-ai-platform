#!/usr/bin/env python3
"""WP08 A-only synthetic consistent COLD capture coordinator. IMPLEMENTED_UNTESTED.

Reuses scripts/stage1/a_cold_backup.py bundle format. This utility may stop the
explicitly selected *exclusive synthetic* ON/SurrealDB Docker project when
run in the future; it is NOT being executed during the code-only sprint.
Requires a single-process private Gateway with host-visible maintenance flag.
Never cleans up source volumes/containers or resumes services automatically
after an unknown crash. No production or student data.
"""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from a_cold_backup import build, BackupInvalid
from surreal_store import RPC,SurrealConfig
from runtime_identity import git_identity,load_containers

HEX64=re.compile(r'^[a-f0-9]{64}$')


def utc():
    return datetime.now(timezone.utc).isoformat()


def run(args):
    return subprocess.run(args,capture_output=True,text=True,check=True,timeout=90).stdout


def docker(context,*args):
    return run(['docker','--context',context,*args])


def require_image_digest(context,image_id,digest):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',digest):
        raise BackupInvalid('Immutable registry digest required')
    raw=docker(context,'image','inspect',image_id,'--format','{{json .RepoDigests}}')
    repos=json.loads(raw)
    if not isinstance(repos,list) or not any(str(value).endswith('@'+digest) for value in repos):
        raise BackupInvalid('Image digest is not proven for inspected immutable image')


def check_manifest(args):
    manifest=json.loads(args.runtime_identity.read_text())
    if (manifest.get('type')!='SUNRISE_S1_A_DOCKER_RUNTIME_IDENTITY_UNREVIEWED'
            or manifest.get('context')!=args.context or
            manifest.get('project')!=args.project or
            manifest.get('services')!=load_containers(args.context,args.project)):
        raise BackupInvalid('Live Compose identity differs from runtime manifest')
    if manifest.get('source_commit')!=args.source_sha or manifest.get('source_tree')!=args.source_tree:
        raise BackupInvalid('Git provenance differs')
    if not HEX64.fullmatch(manifest.get('compose_sha256','')):
        raise BackupInvalid('Unverified Compose source hash')
    if hashlib.sha256(args.compose_file.read_bytes()).hexdigest()!=manifest['compose_sha256']:
        raise BackupInvalid('Compose changed since runtime identity capture')
    if manifest.get('on_namespace')!=os.environ.get('SURREAL_NAMESPACE','open_notebook') or (
        manifest.get('on_database')!=os.environ.get('SURREAL_DATABASE','open_notebook')):
        raise BackupInvalid('Pinned Native DB identity mismatch')
    require_image_digest(args.context,manifest['services']['surrealdb']['image_id'],
                         args.surreal_image_digest)
    return manifest


def check_gateway_frozen(args):
    import urllib.request
    if not args.maintenance_file.is_file():
        raise BackupInvalid('Gateway maintenance flag absent')
    request=urllib.request.Request('http://127.0.0.1:8765/health',headers={'Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=3) as response:
        body=json.loads(response.read(1<<16))
    if (body.get('gateway')!='running' or body.get('maintenance') is not True
            or body.get('mutations_in_flight')!=0):
        raise BackupInvalid('Gateway still admits writes or has in-flight mutations')


def check_db_clean(cfg,required_tables,active_query):
    rpc=RPC(cfg)
    info=rpc.query('INFO FOR DB;')
    if not info or not isinstance(info[-1],dict):
        raise BackupInvalid('Cannot prove native DB table identity')
    tables=info[-1].get('tables')
    if not isinstance(tables,dict) or not set(required_tables).issubset(tables):
        raise BackupInvalid('Required DB tables absent: cannot prove worker drain')
    rows=rpc.query(active_query)
    result=rows[-1] if rows else None
    if not isinstance(result,list):
        raise BackupInvalid('Worker/journal active-state readback unverified')
    return len(result)


def drain(args):
    a=SurrealConfig(os.environ['VAULT_SURREAL_WS_URL'],os.environ['VAULT_SURREAL_USER'],
        os.environ['VAULT_SURREAL_PASSWORD'],os.environ['VAULT_SURREAL_NAMESPACE'],
        os.environ['VAULT_SURREAL_DATABASE']).validate()
    native=SurrealConfig(os.environ['ON_GRAPH_WS_URL'],os.environ['ON_GRAPH_USER'],
        os.environ['ON_GRAPH_PASSWORD'],os.environ['ON_GRAPH_NAMESPACE'],
        os.environ['ON_GRAPH_DATABASE']).validate()
    deadline=time.monotonic()+args.drain_timeout
    while time.monotonic()<deadline:
        check_gateway_frozen(args)
        in_flight=check_db_clean(a,{'vault_operation','source_owner','content_shell'},
            'SELECT id FROM vault_operation WHERE status="PENDING" LIMIT 1;')
        running=check_db_clean(native,{'source','reference','command'},
            'SELECT id FROM command WHERE status IN ["running","queued"] LIMIT 1;')
        if in_flight==0 and running==0:return
        time.sleep(2)
    raise BackupInvalid('Worker/Journals not drained at selected recovery point')


def inventory_at_freeze(args,identity):
    # Execute an additive *read-only* bounded inventory in the pinned ON
    # container, not via a publicly forwarded DB port. No secrets in command
    # flags: the container already has its private SURREAL_* env.
    image_script=(Path(__file__).parent/'db_inventory.py').read_text()
    native_container=identity['services']['open_notebook']['container_id']
    names={'VAULT_RUNTIME_SYNTHETIC_CONFIRM':'YES',
           'VAULT_SURREAL_NAMESPACE':os.environ['VAULT_SURREAL_NAMESPACE'],
           'VAULT_SURREAL_DATABASE':os.environ['VAULT_SURREAL_DATABASE'],
           'ON_GRAPH_NAMESPACE':os.environ['ON_GRAPH_NAMESPACE'],
           'ON_GRAPH_DATABASE':os.environ['ON_GRAPH_DATABASE']}
    env_flags=[]
    for name,value in names.items():
        env_flags.extend(['-e',name+'='+value])
    raw=docker(args.context,'exec',*env_flags,native_container,'python','-c',image_script)
    inventory=json.loads(raw)
    if inventory.get('classification')!='DB_INVENTORY_ONLY_NOT_ACCEPTANCE':
        raise BackupInvalid('Cannot prove A and Native DB inventory before stopping')
    return inventory


def native_readback_at_freeze(args,identity):
    # Prove every A SourceOwner against Native link and original PDF BEFORE
    # stop. This readback is allowed on the isolated worker host only.
    # Follow it with a fresh DB inventory (Native may touch last_viewed).
    code=(Path(__file__).parent/'verify_native.py').read_text(encoding='utf-8')
    cid=identity['services']['open_notebook']['container_id']
    raw=docker(args.context,'exec','-e','VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES',
               '-e','VAULT_SURREAL_NAMESPACE='+os.environ['VAULT_SURREAL_NAMESPACE'],
               '-e','VAULT_SURREAL_DATABASE='+os.environ['VAULT_SURREAL_DATABASE'],
               '-e','ON_GRAPH_NAMESPACE='+os.environ['ON_GRAPH_NAMESPACE'],
               '-e','ON_GRAPH_DATABASE='+os.environ['ON_GRAPH_DATABASE'],
               cid,'python','-c',code)
    proof=json.loads(raw)
    if (proof.get('classification')!='NATIVE_OWNER_READBACK_NOT_FORMAL_AT'
            or proof.get('text_only_patch_attested') is not True
            or not isinstance(proof.get('source_owner_count'),int)
            or proof.get('verified_original_count')!=proof['source_owner_count']):
        raise BackupInvalid('SourceOwner/Original Native pre-snapshot proof incomplete')
    return proof


def stop_project(args,identity):
    ids={service:value['container_id'] for service,value in identity['services'].items()}
    # Stop only the pinned, already inspected isolated Compose project.
    run(['docker','--context',args.context,'compose','-p',args.project,
         '-f',str(args.compose_file),'stop','--timeout','30',
         'open_notebook','surrealdb'])
    for service,container_id in ids.items():
        inspected=json.loads(docker(args.context,'inspect',container_id))[0]
        if inspected.get('State',{}).get('Running') is not False:
            raise BackupInvalid('Synthetic service did not stop: '+service)
        if inspected.get('Id')!=container_id:
            raise BackupInvalid('Container identity changed after stop')


def copy_volumes(args,identity,staging,inventory,native_readback):
    # docker cp can read a known stopped container's volume-mounted path.
    mapping={'surrealdb':('surreal','/mydata/.'),
             'open_notebook':('native','/app/data/.')}
    for service,(destination,path) in mapping.items():
        container_id=identity['services'][service]['container_id']
        target=staging/destination
        target.mkdir()
        docker(args.context,'cp',f'{container_id}:{path}',str(target))
        if not any(target.rglob('*')):
            raise BackupInvalid('Captured volume empty; cannot establish integrity')
    (staging/'gateway').mkdir()
    (staging/'gateway'/'db-inventory.json').write_text(json.dumps(inventory,sort_keys=True)+'\n')
    (staging/'gateway'/'native-pre-capture-readback.json').write_text(
        json.dumps(native_readback,sort_keys=True)+'\n')
    (staging/'gateway'/'cold-recovery-point.json').write_text(json.dumps({
        'recovery_point':args.recovery_point,
        'source_commit':args.source_sha,
        'source_tree':args.source_tree,
        'key_escrow_reference':args.key_escrow_reference,
        'native_source_commit':'5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
    },sort_keys=True)+'\n')


def main():
    p=argparse.ArgumentParser(description='Stop an exclusive synthetic A project and create a cold bundle')
    for field in ('context','project','recovery-point','source-sha','source-tree',
                  'surreal-image-digest','key-escrow-reference'):
        p.add_argument('--'+field,required=True)
    for field in ('runtime-identity','compose-file','maintenance-file','out'):
        p.add_argument('--'+field,required=True,type=Path)
    p.add_argument('--drain-timeout',type=int,default=120)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or (
        os.getenv('VAULT_EXCLUSIVE_COLD_CAPTURE')!='YES'):
        p.error('Exclusive synthetic cold capture not authorized')
    if not 10<=args.drain_timeout<=600:p.error('Bounded worker drain required')
    if args.out.exists() or not args.maintenance_file.is_absolute():
        p.error('New output and absolute maintenance flag required')
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,90}',args.recovery_point):
        p.error('Unique recovery point ID required')
    sha,tree=git_identity(ROOT)
    if sha!=args.source_sha or tree!=args.source_tree:p.error('Wrong source SHA/tree')
    if not args.key_escrow_reference.startswith('offline-escrow:'):
        p.error('Independent private offline key-escrow reference required')
    identity=check_manifest(args)
    if not args.maintenance_file.parent.is_dir():p.error('Maintenance directory unavailable')
    # Exclusive create: never replace an existing flag belonging to someone else.
    with args.maintenance_file.open('x') as f:
        f.write('SUNRISE_A_WRITE_FREEZE '+args.recovery_point+'\n')
    # Intentionally leave write freeze active on any failure after this point.
    check_gateway_frozen(args)
    drain(args)
    native_readback=native_readback_at_freeze(args,identity)
    # Recheck pending worker/journal states after the native readback:
    # a new change during verification invalidates the snapshot barrier.
    drain(args)
    inventory=inventory_at_freeze(args,identity)
    stop_project(args,identity)
    with tempfile.TemporaryDirectory(prefix='sunrise-a-cold-') as staging_text:
        staging=Path(staging_text)
        copy_volumes(args,identity,staging,inventory,native_readback)
        attestation=staging.parent/(staging.name+'-attestation.json')
        attestation.write_text(json.dumps({
            'exclusive_synthetic_host':True,'native_and_db_stopped':True,
            'offline_volume_copy':True,'docker_project':args.project,
            'host_identity':args.context,'snapshot_utc':utc()
        }))
        try:
            os.environ['VAULT_BACKUP_EXCLUSIVE_COLD']='YES'
            result=build(staging,args.out,attestation,args.source_sha,args.source_tree,
                         args.surreal_image_digest,
                         recovery_point_id=args.recovery_point,
                         key_escrow_reference=args.key_escrow_reference,
                         runtime_identity_sha256=hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest())
        finally:
            attestation.unlink(missing_ok=True)
    print(json.dumps({'status':'OFFLINE_COLD_BUNDLE_NOT_RESTORE_VERIFIED',
                      'source_project_remains_stopped_and_frozen':True,
                      'recovery_point':args.recovery_point,**result},sort_keys=True))


if __name__=='__main__':main()
