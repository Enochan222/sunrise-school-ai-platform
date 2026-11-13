#!/usr/bin/env python3
"""WP00/WP01 private Docker/Compose runtime identity capture. IMPLEMENTED_UNTESTED.

Run on the *exclusive synthetic Docker host* during later test phase only.
Inspects one explicitly selected Docker context and Compose project. Does not
start, stop, create, remove or modify containers. No credentials in output.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

COMMIT_RE=re.compile(r'^[0-9a-f]{40}$')
EXPECTED_SERVICES={'surrealdb','open_notebook'}
EXPECTED_NATIVE_COMMIT='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
EXPECTED_NATIVE_TREE='2d101001de594c7d6a0e4aaeb8e85ac4c52980af'


def command(args):
    # No shell, env-supplied docker context; collect no inspect Env/Secret arrays.
    result=subprocess.run(args,check=True,capture_output=True,text=True,timeout=30)
    return result.stdout


def git_identity(repo_root):
    repo=str(Path(repo_root).resolve())
    sha=command(['git','-C',repo,'rev-parse','HEAD']).strip()
    tree=command(['git','-C',repo,'rev-parse','HEAD^{tree}']).strip()
    if not COMMIT_RE.fullmatch(sha) or not COMMIT_RE.fullmatch(tree):
        raise ValueError('Unverifiable Git identity')
    return sha,tree


def load_containers(context,project):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,70}',project):
        raise ValueError('Unsafe or missing exclusive Compose project')
    # Docker ps --format emits line-delimited JSON; use stable container IDs.
    raw=command(['docker','--context',context,'ps','--all','--no-trunc',
                 '--filter','label=com.docker.compose.project='+project,'--format','{{json .}}'])
    entries=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if not entries:raise RuntimeError('No containers for selected Compose project')
    ids=[x['ID'] for x in entries]
    containers=json.loads(command(['docker','--context',context,'inspect',*ids]))
    result={}
    for container in containers:
        labels=container.get('Config',{}).get('Labels',{})
        if labels.get('com.docker.compose.project')!=project:
            raise RuntimeError('Unowned container in runtime manifest')
        service=labels.get('com.docker.compose.service')
        if not service or service in result or service not in EXPECTED_SERVICES:
            raise RuntimeError('Unexpected, duplicate or missing expected service')
        image=container.get('Image')
        if not isinstance(image,str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',image):
            raise RuntimeError('Missing immutable image identifier')
        ports=container.get('NetworkSettings',{}).get('Ports') or {}
        exposed=[]
        for container_port,published in sorted(ports.items()):
            if published is None:continue
            if len(published)!=1:raise RuntimeError('Ambiguous published port binding')
            bind=published[0]
            port=int(bind['HostPort'])
            if not 1<=port<=65535:raise RuntimeError('Invalid host port')
            host_ip=bind['HostIp']
            if not host_ip:raise RuntimeError('Missing host bind IP')
            exposed.append({'container_port':container_port,'host_ip':host_ip,'host_port':port})
        expected_mount={'surrealdb':'/mydata','open_notebook':'/app/data'}[service]
        mounts=container.get('Mounts',[])
        matches=[m for m in mounts if m.get('Destination')==expected_mount]
        if (len(matches)!=1 or matches[0].get('Type')!='volume'
                or not isinstance(matches[0].get('Name'),str)
                or not matches[0]['Name'].startswith(project+'_')):
            raise RuntimeError('Missing/foreign/non-named persistent volume at '+expected_mount)
        inspected=json.loads(command(['docker','--context',context,'image','inspect',image]))
        if len(inspected)!=1 or inspected[0].get('Id')!=image:
            raise RuntimeError('Immutable image identity could not be verified')
        image_object=inspected[0]
        digests=image_object.get('RepoDigests') or []
        if not isinstance(digests,list) or any(
                not isinstance(x,str) or not re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}',x)
                for x in digests):
            raise RuntimeError('Image registry digest provenance malformed')
        result[service]={'container_id':container['Id'],'image_id':image,
                         'image_name':container.get('Config',{}).get('Image'),
                         'image_repo_digests':digests,
                         'image_os':image_object.get('Os'),
                         'image_arch':image_object.get('Architecture'),
                         'status':container.get('State',{}).get('Status'),
                         'persistent_volume':matches[0]['Name'],
                         'mount_destination':expected_mount,
                         'published_ports':exposed}
    if set(result)!=EXPECTED_SERVICES:
        raise RuntimeError('Compose services do not match expected pinned A-only runtime')
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--context',required=True);p.add_argument('--project',required=True)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--compose-file',type=Path,required=True)
    p.add_argument('--on-patch-sha256',required=True)
    p.add_argument('--surreal-namespace',required=True)
    p.add_argument('--surreal-database',required=True)
    p.add_argument('--on-namespace',required=True)
    p.add_argument('--on-database',required=True)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Exclusive synthetic source runtime not authorized')
    if not re.fullmatch('[A-Za-z0-9_.-]{1,64}',args.context):
        p.error('Explicit safe Docker context required')
    if not re.fullmatch('[0-9a-f]{64}',args.on_patch_sha256):
        p.error('Exact pinned ON patch provenance required')
    for name in ('surreal_namespace','surreal_database','on_namespace','on_database'):
        if not re.fullmatch('[A-Za-z0-9_-]{1,100}',getattr(args,name)):
            p.error('Invalid database identity')
    if not args.compose_file.is_file() or args.compose_file.is_symlink():
        p.error('Private compose source required')
    destination=args.out.absolute()
    if destination.exists():p.error('Identity output MUST NOT overwrite a prior record')
    sha,tree=git_identity(args.source_root)
    containers=load_containers(args.context,args.project)
    record={'type':'SUNRISE_S1_A_DOCKER_RUNTIME_IDENTITY_UNREVIEWED',
            'captured_utc':datetime.now(timezone.utc).isoformat(),
            'context':args.context,'project':args.project,
            'source_commit':sha,'source_tree':tree,
            'native_source_commit':EXPECTED_NATIVE_COMMIT,'native_source_tree':EXPECTED_NATIVE_TREE,
            'compose_sha256':hashlib.sha256(args.compose_file.read_bytes()).hexdigest(),
            'on_patch_sha256':args.on_patch_sha256,
            'surreal_namespace':args.surreal_namespace,'surreal_database':args.surreal_database,
            'on_namespace':args.on_namespace,'on_database':args.on_database,
            'services':containers,'classification':'IDENTITY_CAPTURE_NOT_TEST_RESULT'}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x',encoding='utf-8') as out:
        json.dump(record,out,sort_keys=True,indent=2)
        out.write('\n')


if __name__=='__main__':main()
