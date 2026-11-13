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
    target=Path(path)
    if target.is_symlink() or not target.is_file() or target.stat().st_size>1<<20:
        raise ValueError('Missing/unbounded/symlinked runtime identity')
    raw=target.read_bytes()
    document=json.loads(raw)
    if (document.get('type')!='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'
            or document.get('context')!=context or document.get('project')!=project
            or document.get('source_commit')!=expected_source_sha
            or document.get('source_tree')!=expected_source_tree
            or document.get('native_source_commit')!='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
            or document.get('native_source_tree')!='2d101001de594c7d6a0e4aaeb8e85ac4c52980af'
            or not SHA64.fullmatch(str(document.get('compose_sha256','')))
            or not SHA64.fullmatch(str(document.get('on_patch_sha256','')))):
        raise ValueError('Wrong dual physical source SHA/tree/project/patch identity')
    gateway=document.get('gateway',{})
    if (gateway.get('tls_verified') is not True
            or not SHA64.fullmatch(str(gateway.get('tls_peer_sha256','')))
            or not SHA64.fullmatch(str(gateway.get('tls_ca_sha256','')))
            or not str(gateway.get('origin','')).startswith('https://')):
        raise ValueError('Verified Gateway TLS identity missing')
    root=document.get('dual_rpc',{})
    if (root.get('authenticated') is not True
            or root.get('separate_root_secrets') is not True
            or root.get('on_viewer_read_only') is not True):
        raise ValueError('Two authenticated root engines and scoped ON Viewer not proven')
    for key in ('surreal_namespace','surreal_database','on_namespace','on_database'):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(document.get(key,''))):
            raise ValueError('Physical namespace/database missing')
    services=document.get('services')
    if not isinstance(services,dict) or set(services)!={'a_db','on_db','native'}:
        raise ValueError('Missing physical A/ON/Native services')
    if (services['a_db'].get('container_id')==services['on_db'].get('container_id')
            or services['a_db'].get('network_id')==services['on_db'].get('network_id')
            or services['a_db'].get('persistent_volume')==services['on_db'].get('persistent_volume')):
        raise ValueError('A/ON physical engine identity collision')
    ports=[]
    for service,identity in services.items():
        if (identity.get('status')!='running'
                or not SHA64.fullmatch(str(identity.get('image_id','')).removeprefix('sha256:'))
                or not re.fullmatch(r'[a-f0-9]{64}',str(identity.get('container_id','')))
                or not isinstance(identity.get('published_ports'),list)
                or len(identity['published_ports'])!=1
                or not str(identity.get('persistent_volume','')).startswith(project+'_')):
            raise ValueError('Non-project or unverified immutable physical service')
        if service in ('a_db','on_db') and not re.fullmatch(
                r'[1-9][0-9]*:[1-9][0-9]*',str(identity.get('container_user',''))):
            raise ValueError('Source DB is not verifiably nonroot')
        for binding in identity['published_ports']:
            port=binding.get('host_port')
            bind=binding.get('host_ip')
            target=binding.get('container_port')
            if (type(port) is not int or not 1024<=port<=65535
                    or bind!='127.0.0.1'
                    or target!=('5055/tcp' if service=='native' else '8000/tcp')):
                raise ValueError('Unattested or externally exposed private service')
            ports.append((service,identity['container_id'],bind,port,target))
    if len(set(x[3] for x in ports))!=3:
        raise ValueError('Duplicate/ambiguous dynamic physical host port')
    a, on=services['a_db']['published_ports'][0],services['on_db']['published_ports'][0]
    if (root.get('a_url')!='ws://127.0.0.1:'+str(a['host_port'])+'/rpc'
            or root.get('on_url')!='ws://127.0.0.1:'+str(on['host_port'])+'/rpc'):
        raise ValueError('Dual physical authenticated endpoint identity changed')
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
