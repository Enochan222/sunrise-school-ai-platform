#!/usr/bin/env python3
"""WP01 dynamic boundary test from an independent synthetic observer.

IMPLEMENTED_UNTESTED. Requires a fresh, separately captured Docker runtime
manifest from runtime_identity.py. NEVER guesses port numbers or uses 8000
when the actual published SurrealDB HostPort is 18080. This remains an ingress
probe, not authorization for public deployment.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
from ipaddress import ip_address
import json
from pathlib import Path
import re
import socket
import sys

SHA40=re.compile(r'^[0-9a-f]{40}$')
SHA64=re.compile(r'^[0-9a-f]{64}$')


def verify_private_address(value):
    address=ip_address(value)
    if not address.is_private or address.is_loopback or address.is_link_local or address.is_unspecified:
        raise ValueError('Private isolated numeric IP required, no public targets')
    return str(address)


def verify_manifest(path,context,project,expected_source_sha,expected_source_tree):
    if Path(path).is_symlink():raise ValueError('Runtime identity symlink forbidden')
    raw=Path(path).read_bytes()
    if len(raw)>1<<20:raise ValueError('Oversize runtime identity document')
    document=json.loads(raw)
    if (document.get('type')!='SUNRISE_S1_A_DOCKER_RUNTIME_IDENTITY_UNREVIEWED'
            or document.get('context')!=context or document.get('project')!=project
            or document.get('source_commit')!=expected_source_sha
            or document.get('source_tree')!=expected_source_tree
            or document.get('native_source_commit')!='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
            or document.get('native_source_tree')!='2d101001de594c7d6a0e4aaeb8e85ac4c52980af'
            or not SHA64.fullmatch(str(document.get('compose_sha256','')))
            or not SHA64.fullmatch(str(document.get('on_patch_sha256','')))):
        raise ValueError('Wrong/stale source revision, context, patch, compose or project identity')
    for key in ('surreal_namespace','surreal_database','on_namespace','on_database'):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(document.get(key,''))):
            raise ValueError('Namespace/database identity incomplete')
    services=document.get('services')
    if not isinstance(services,dict) or set(services)!={'open_notebook','surrealdb'}:
        raise ValueError('Missing or ambiguous Compose services')
    ports=[]
    for service,identity in services.items():
        if (identity.get('status')!='running' or
                not SHA64.fullmatch(str(identity.get('image_id','')).removeprefix('sha256:')) or
                not re.fullmatch(r'[a-f0-9]{64}',str(identity.get('container_id','')))
                or not isinstance(identity.get('published_ports'),list)):
            raise ValueError('Docker service identity unverified or not running')
        for binding in identity['published_ports']:
            port=binding.get('host_port')
            bind=binding.get('host_ip')
            if not isinstance(port,int) or not 0<port<65536:
                raise ValueError('HostPort is missing, stale or invalid')
            if not isinstance(bind,str):raise ValueError('Missing published bind address')
            ip_address(bind)  # No DNS/synthetic misleading address.
            if '/' not in binding.get('container_port',''):
                raise ValueError('ContainerPort protocol unspecified')
            ports.append((service,identity['container_id'],bind,port,binding['container_port']))
    if len(ports)!=len(set((p[3],p[4]) for p in ports)):
        raise ValueError('Ambiguous duplicate published port')
    return document,ports,hashlib.sha256(raw).hexdigest()


def probe(ip,port,timeout):
    try:
        with socket.create_connection((ip,port),timeout=timeout):
            return 'EXTERNAL_TCP_ACCEPTED_FAIL'
    except (socket.timeout,TimeoutError,ConnectionRefusedError,OSError) as exc:
        return type(exc).__name__


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runtime-identity',required=True,type=Path)
    p.add_argument('--context',required=True);p.add_argument('--project',required=True)
    p.add_argument('--source-sha',required=True);p.add_argument('--source-tree',required=True)
    p.add_argument('--observer-id',required=True)
    p.add_argument('--target-private-ip',required=True)
    p.add_argument('--timeout',type=float,default=3)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    import os
    if os.getenv('VAULT_OBSERVER_ISOLATED_CONFIRM')!='YES':
        p.error('Independent observer network is not attested')
    if not all(SHA40.fullmatch(x) for x in (args.source_sha,args.source_tree)):
        p.error('Expected fixed Git SHA/tree required')
    if not args.observer_id or not 0<args.timeout<=10:p.error('Invalid observer identity/timeout')
    ip=verify_private_address(args.target_private_ip)
    document,mappings,source_hash=verify_manifest(
        args.runtime_identity,args.context,args.project,args.source_sha,args.source_tree)
    results=[]
    for service,container_id,host_ip,host_port,container_port in mappings:
        outcome=probe(ip,host_port,args.timeout)
        results.append({'service':service,'container_id':container_id,
                        'host_ip':host_ip,'host_port':host_port,
                        'container_port':container_port,'outcome':outcome})
    if not mappings:
        status='PARTIAL'  # no published ports does NOT independently prove firewall isolation
    else:
        status='FAIL' if any(x['outcome']=='EXTERNAL_TCP_ACCEPTED_FAIL' for x in results) else 'PARTIAL'
    # Connection refused is not a complete authenticated ingress+service proof.
    evidence={'created_utc':datetime.now(timezone.utc).isoformat(),
              'runtime_identity_sha256':source_hash,
              'source_commit':args.source_sha,'source_tree':args.source_tree,
              'context':args.context,'project':args.project,'observer_id':args.observer_id,
              'target_private_ip':ip,'observations':results,
              'status':status,'classification':'NETWORK_PROBE_ONLY_NOT_AT_PASS'}
    target=args.out.absolute()
    if target.exists():p.error('Evidence output must be new')
    target.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    # Exit 2 explicitly prevents TCP-negative observations being mistaken for AT PASS.
    raise SystemExit(1 if status=='FAIL' else 2)


if __name__=='__main__':main()
