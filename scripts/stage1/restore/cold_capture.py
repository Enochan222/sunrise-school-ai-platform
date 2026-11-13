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
from runtime_identity import git_identity,load_containers,tls_gateway_identity
from dual_inventory_runner import both,read_a_owner_snapshot,native_readback

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
    if (manifest.get('type')!='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'
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
    if manifest.get('on_namespace')!=os.environ.get('ON_GRAPH_NAMESPACE') or (
        manifest.get('on_database')!=os.environ.get('ON_GRAPH_DATABASE')):
        raise BackupInvalid('Pinned Native DB identity mismatch')
    for physical in ('a_db','on_db'):
        require_image_digest(args.context,manifest['services'][physical]['image_id'],
                             args.surreal_image_digest)
    gateway=manifest.get('gateway')
    if (not isinstance(gateway,dict) or
            not re.fullmatch(r'[a-f0-9]{32}',str(gateway.get('instance_id',''))) or
            gateway.get('health_url')!=gateway.get('origin','')+'/health' or
            gateway.get('tls_verified') is not True or
            gateway.get('maintenance_path_sha256')!=hashlib.sha256(
                str(args.maintenance_file).encode('utf-8')).hexdigest()):
        raise BackupInvalid('Gateway instance or write-freeze path was not recorded correctly')
    return manifest


def check_gateway_frozen(args):
    if not args.maintenance_file.is_file():
        raise BackupInvalid('Gateway write-freeze flag absent')
    manifest=json.loads(args.runtime_identity.read_text(encoding='utf-8'))
    first=manifest.get('gateway',{})
    observed=tls_gateway_identity(first.get('origin',''),
                                  os.environ['VAULT_GATEWAY_CA_FILE'])
    if (observed.get('maintenance') is not True
            or observed.get('mutations_in_flight')!=0
            or any(observed.get(key)!=first.get(key) for key in (
                'instance_id','maintenance_path_sha256',
                'tls_peer_sha256','tls_ca_sha256','origin'))):
        raise BackupInvalid('TLS Gateway identity or consistent write-freeze not proven')

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
    native=SurrealConfig(os.environ['ON_GRAPH_WS_URL'],os.environ['ON_SURREAL_USER'],
        os.environ['ON_SURREAL_PASSWORD'],os.environ['ON_GRAPH_NAMESPACE'],
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
    return both(args.context,args.project,identity['services']['native']['image_id'])


def native_readback_at_freeze(args,identity):
    snapshot=read_a_owner_snapshot(
        args.context,args.project,identity['services']['native']['image_id'])
    proof_source=(Path(__file__).parent/'verify_native.py').read_text(encoding='utf-8')
    proof=native_readback(args.context,identity['services']['native']['container_id'],
                          snapshot,proof_source)
    if (proof.get('text_only_patch_attested') is not True
            or not isinstance(proof.get('source_owner_count'),int)
            or proof['source_owner_count']<1
            or proof.get('verified_original_count')!=proof['source_owner_count']
            or proof.get('rights_retention_initial_version_count')!=proof['source_owner_count']):
        raise BackupInvalid('Physical A/ON SourceOwner graph/original readback missing')
    return proof

def stop_project(args,identity):
    ids={service:value['container_id'] for service,value in identity['services'].items()}
    # Stop only the pinned, already inspected isolated Compose project.
    # Stop ALL relays first, then Native/DB. Leaving a published relay while
    # freezing recovery point would keep a foreign host access path alive.
    run(['docker','--context',args.context,'compose','-p',args.project,
         '-f',str(args.compose_file),'stop','--timeout','30',
         'native_relay','on_relay','a_relay','native','on_db','a_db'])
    for service,container_id in ids.items():
        inspected=json.loads(docker(args.context,'inspect',container_id))[0]
        if inspected.get('State',{}).get('Running') is not False:
            raise BackupInvalid('Synthetic service did not stop: '+service)
        if inspected.get('Id')!=container_id:
            raise BackupInvalid('Container identity changed after stop')
        relay=identity['services'][service].get('host_relay')
        if not isinstance(relay,dict):
            raise BackupInvalid('Host relay identity missing from recovery point')
        relay_id=relay.get('relay_container_id')
        if not isinstance(relay_id,str) or not re.fullmatch(r'[a-f0-9]{64}',relay_id):
            raise BackupInvalid('Invalid saved relay container identity')
        relay_info=json.loads(docker(args.context,'inspect',relay_id))[0]
        if (relay_info.get('Id')!=relay_id
                or relay_info.get('State',{}).get('Running') is not False):
            raise BackupInvalid('Host relay still running or replaced after cold stop')


def copy_volumes(args,identity,staging,inventory,native_readback):
    # docker cp can read a known stopped container's volume-mounted path.
    mapping={'a_db':('a_db','/mydata/.'),
             'on_db':('on_db','/mydata/.'),
             'native':('native','/app/data/.')}
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
    if os.getenv('VAULT_GATEWAY_SINGLE_PROCESS_CONFIRM')!='YES':
        p.error('Snapshot barrier only supports explicitly confirmed single-process Gateway')
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
            'exclusive_synthetic_host':True,'a_and_on_and_native_stopped':True,
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
