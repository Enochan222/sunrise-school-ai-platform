#!/usr/bin/env python3
"""Strict dual-physical A/ON/Native Docker and verified TLS identity capture.

IMPLEMENTED_UNTESTED; read-only on exact exclusive synthetic project.
No secrets, Docker Env/Args, credentials or response content in output.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
from urllib.parse import urlsplit

COMMIT_RE=re.compile(r'^[0-9a-f]{40}$')
SHA64=re.compile(r'^[0-9a-f]{64}$')
EXPECTED_SERVICES={'a_db','on_db','native'}
EXPECTED_MOUNTS={'a_db':'/mydata','on_db':'/mydata','native':'/app/data'}
EXPECTED_PRIVATE_NETWORKS={'a_db':'a_db_private','on_db':'on_db_private',
                           'native':'on_db_private'}
EXPECTED_NATIVE_COMMIT='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
EXPECTED_NATIVE_TREE='2d101001de594c7d6a0e4aaeb8e85ac4c52980af'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def require_explicit_env(keys):
    for key in keys:
        if not os.getenv(key):
            raise ValueError('Required private identity/credential absent: '+key)


def command(args,timeout=30):
    result=subprocess.run(args,check=True,capture_output=True,
                          text=True,timeout=timeout)
    return result.stdout


def git_identity(repo_root):
    root=Path(repo_root).resolve()
    sha=command(['git','-C',str(root),'rev-parse','HEAD']).strip()
    tree=command(['git','-C',str(root),'rev-parse','HEAD^{tree}']).strip()
    require(COMMIT_RE.fullmatch(sha) and COMMIT_RE.fullmatch(tree),
            'Exact tested Git identity unavailable')
    return sha,tree


def parse_gateway_origin(url):
    u=urlsplit(url)
    require(u.scheme=='https' and u.hostname in ('127.0.0.1','localhost')
            and u.port and u.path in ('','/') and not u.username and not u.password
            and not u.query and not u.fragment,
            'Gateway must be verified loopback HTTPS only')
    return u


def tls_gateway_identity(url,ca_file):
    address=parse_gateway_origin(url)
    ca=Path(ca_file)
    require(ca.is_file() and not ca.is_symlink() and ca.stat().st_size<=1<<20,
            'Pinned private Gateway TLS CA is missing/oversized/symlinked')
    tls=ssl.create_default_context(cafile=str(ca))
    tls.check_hostname=True
    tls.verify_mode=ssl.CERT_REQUIRED
    connection=http.client.HTTPSConnection(address.hostname,address.port,
                                           timeout=8,context=tls)
    try:
        connection.request('GET','/health',headers={'Accept':'application/json'})
        reply=connection.getresponse()
        require(reply.status==200,'Verified TLS Gateway health not HTTP 200')
        require(connection.sock is not None,'Cannot inspect Gateway TLS peer')
        peer=connection.sock.getpeercert(binary_form=True)
        require(isinstance(peer,bytes) and len(peer)>128,
                'Actual Gateway certificate identity unobservable')
        raw=reply.read(65537)
        require(len(raw)<=65536,'Gateway health exceeded size bound')
        record=json.loads(raw)
    finally:
        connection.close()
    require(record.get('gateway')=='running'
            and re.fullmatch(r'[a-f0-9]{32}',str(record.get('gateway_instance','')))
            and re.fullmatch(r'[a-f0-9]{64}',str(record.get('maintenance_path_sha256','')))
            and isinstance(record.get('mutations_in_flight'),int),
            'Observed HTTPS endpoint not authoritative A Gateway process')
    return {'instance_id':record['gateway_instance'],
            'maintenance_path_sha256':record['maintenance_path_sha256'],
            'health_url':url.rstrip('/')+'/health','origin':url.rstrip('/'),
            'tls_verified':True,'tls_peer_sha256':hashlib.sha256(peer).hexdigest(),
            'tls_ca_sha256':hashlib.sha256(ca.read_bytes()).hexdigest(),
            'maintenance':record.get('maintenance'),
            'mutations_in_flight':record['mutations_in_flight']}


def load_containers(context,project):
    require(re.fullmatch(r'sunrise-s1-[a-z0-9-]{8,40}',project) is not None,
            'Exact exclusive synthetic Docker project required')
    run=lambda *args:command(['docker','--context',context,*args])
    raw=run('ps','--all','--no-trunc',
            '--filter','label=com.docker.compose.project='+project,
            '--format','{{json .}}')
    rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    require(rows,'Selected project has no Docker containers')
    identities=json.loads(run('inspect',*[row['ID'] for row in rows]))
    result={}
    network_ids={}
    for item in identities:
        labels=item.get('Config',{}).get('Labels',{})
        service=labels.get('com.docker.compose.service')
        require(labels.get('com.docker.compose.project')==project
                and service in EXPECTED_SERVICES and service not in result,
                'Unexpected/duplicate/nonproject container')
        image=item.get('Image')
        require(isinstance(image,str) and re.fullmatch(r'sha256:[a-f0-9]{64}',image),
                'Container does not refer to immutable image')
        state=item.get('State',{}).get('Status')
        require(state=='running','Source physical service not running')
        ports=item.get('NetworkSettings',{}).get('Ports') or {}
        publishes=[]
        for target,mappings in ports.items():
            if mappings is None:continue
            require(len(mappings)==1 and target in ('8000/tcp','5055/tcp'),
                    'Unexpected or ambiguous service published port')
            binding=mappings[0]
            require(binding.get('HostIp')=='127.0.0.1',
                    'Service published beyond pinned loopback')
            port=int(binding['HostPort'])
            require(1024<=port<=65535,'Unsafe mapped loopback host port')
            publishes.append({'container_port':target,'host_ip':'127.0.0.1',
                              'host_port':port})
        expected_target={'a_db':'8000/tcp','on_db':'8000/tcp','native':'5055/tcp'}[service]
        require(len(publishes)==1 and publishes[0]['container_port']==expected_target,
                'Physical service not using exactly one dynamic loopback mapping')
        mounts=[m for m in item.get('Mounts',[])
                if m.get('Destination')==EXPECTED_MOUNTS[service]]
        require(len(mounts)==1 and mounts[0].get('Type')=='volume'
                and mounts[0].get('Name')==project+'_'+(
                    {'a_db':'a_db_data','on_db':'on_db_data','native':'native_data'}[service]),
                'Wrong or foreign persistent volume')
        network=item.get('NetworkSettings',{}).get('Networks') or {}
        expected_name=project+'_'+EXPECTED_PRIVATE_NETWORKS[service]
        require(set(network)=={expected_name},
                'Cross-engine network sharing, unexpected bridge or foreign network')
        network_id=network[expected_name].get('NetworkID')
        require(isinstance(network_id,str) and len(network_id)>=12,
                'Service private network identity absent')
        if expected_name in network_ids:
            require(network_ids[expected_name]==network_id,
                    'Native/on_db network identity inconsistent')
        network_ids[expected_name]=network_id
        image_info=json.loads(run('image','inspect',image))
        require(len(image_info)==1 and image_info[0].get('Id')==image,
                'Actual immutable image not inspectable')
        digests=image_info[0].get('RepoDigests') or []
        require(isinstance(digests,list) and all(
            isinstance(d,str) and re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}',d)
            for d in digests),'Malformed source image registry digests')
        user=item.get('Config',{}).get('User','')
        declared=image_info[0].get('Config',{}).get('User','')
        verified_primary=None
        if service in ('a_db','on_db'):
            require(re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',user or '') is not None,
                    'DB runtime effective user not attested nonroot')
            require(len(digests)==1,
                    'DB image has ambiguous registry provenance')
            image_digest=digests[0].rsplit('@',1)[-1]
            verifier=Path(__file__).parent/'verify_surreal_image_user.py'
            identity=subprocess.run(['python',str(verifier),
                '--context',context,'--image',image,'--digest',image_digest],
                capture_output=True,text=True,timeout=120)
            require(identity.returncode==0 and
                    re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',
                                 identity.stdout.strip()) is not None,
                    'Cannot derive effective primary GID from image itself')
            verified_primary=identity.stdout.strip()
            require(user==verified_primary,
                    'DB container UID/GID differs from digest-attested image primary identity')
        result[service]={'container_id':item['Id'],'image_id':image,
                         'image_name':item.get('Config',{}).get('Image'),
                         'image_repo_digests':digests,'image_os':image_info[0].get('Os'),
                         'image_arch':image_info[0].get('Architecture'),
                         'container_user':user,'image_declared_user':declared,
                         'image_verified_primary_user':verified_primary,
                         'status':state,
                         'persistent_volume':mounts[0]['Name'],
                         'mount_destination':EXPECTED_MOUNTS[service],
                         'network_name':expected_name,'network_id':network_id,
                         'published_ports':publishes}
    require(set(result)==EXPECTED_SERVICES,'Required dual DB/Native services missing')
    require(result['a_db']['container_id']!=result['on_db']['container_id']
            and result['a_db']['persistent_volume']!=result['on_db']['persistent_volume']
            and result['a_db']['network_id']!=result['on_db']['network_id'],
            'A and ON physical engine isolation not proven')
    for name,net_id in network_ids.items():
        network=json.loads(run('network','inspect',net_id))
        require(len(network)==1 and network[0].get('Id')==net_id
                and network[0].get('Name')==name
                and network[0].get('Internal') is True
                and network[0].get('Labels',{}).get('com.docker.compose.project')==project,
                'Private physical Docker network attestation failed')
    require(len({s['published_ports'][0]['host_port'] for s in result.values()})==3,
            'Dynamic physical service endpoints collide')
    return result


def require_dual_rpc_ready(context,services,namespace):
    require_explicit_env(('A_SURREAL_USER','A_SURREAL_PASSWORD','ON_SURREAL_USER',
        'ON_SURREAL_PASSWORD','ON_GRAPH_VIEWER_USER','ON_GRAPH_VIEWER_PASSWORD',
        'A_SURREAL_NAMESPACE','A_SURREAL_DATABASE','ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE'))
    helper=Path(__file__).parent/'dual_db_readiness.py'
    ports={k:services[k]['published_ports'][0]['host_port'] for k in ('a_db','on_db')}
    a='ws://127.0.0.1:'+str(ports['a_db'])+'/rpc'
    on='ws://127.0.0.1:'+str(ports['on_db'])+'/rpc'
    tested=subprocess.run(['python',str(helper),'--a-url',a,'--on-url',on],
                          capture_output=True,text=True,timeout=90)
    require(tested.returncode==0,'Two distinct root/VIEWER RPC readiness not verified')
    readback=json.loads(tested.stdout)
    require(readback.get('dual_physical_engines')=='RPC_READY'
            and readback.get('graph_viewer_read_only')=='PASS'
            and readback.get('cross_engine_root_denied') is True,
            'Root/Viewer/school DB proof incomplete')
    return {'a_url':a,'on_url':on,'authenticated':True,
            'separate_root_secrets':True,'on_viewer_read_only':True,
            'on_viewer_user_sha256':hashlib.sha256(
                os.environ['ON_GRAPH_VIEWER_USER'].encode()).hexdigest()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--context',required=True)
    p.add_argument('--project',required=True)
    p.add_argument('--source-root',required=True,type=Path)
    p.add_argument('--gateway-url',required=True)
    p.add_argument('--gateway-ca-file',required=True,type=Path)
    p.add_argument('--compose-file',required=True,type=Path)
    p.add_argument('--on-patch-sha256',required=True)
    for name in ('surreal_namespace','surreal_database','on_namespace','on_database'):
        p.add_argument('--'+name.replace('_','-'),required=True)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')=='YES'
            and os.getenv('VAULT_EXCLUSIVE_SYNTHETIC_PROJECT')=='YES',
            'Only exclusive synthetic runtime identity may be captured')
    require(re.fullmatch('[A-Za-z0-9_.-]{1,64}',args.context) is not None,
            'Explicit Docker context invalid')
    require(SHA64.fullmatch(args.on_patch_sha256) is not None,
            'Pinned Native A-only patch provenance missing')
    require(args.compose_file.is_file() and not args.compose_file.is_symlink(),
            'Private source Compose manifest missing')
    destination=args.out.absolute()
    require(not destination.exists(),'Runtime identity overwrite refused')
    sha,tree=git_identity(args.source_root)
    services=load_containers(args.context,args.project)
    namespace={'surreal_namespace':args.surreal_namespace,
               'surreal_database':args.surreal_database,
               'on_namespace':args.on_namespace,'on_database':args.on_database}
    require(namespace=={'surreal_namespace':os.getenv('A_SURREAL_NAMESPACE'),
                        'surreal_database':os.getenv('A_SURREAL_DATABASE'),
                        'on_namespace':os.getenv('ON_GRAPH_NAMESPACE'),
                        'on_database':os.getenv('ON_GRAPH_DATABASE')},
            'A and ON DB namespace/database identity inconsistent')
    gateway=tls_gateway_identity(args.gateway_url,args.gateway_ca_file)
    rpc=require_dual_rpc_ready(args.context,services,namespace)
    record={'type':'SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED',
            'captured_utc':datetime.now(timezone.utc).isoformat(),
            'context':args.context,'project':args.project,
            'source_commit':sha,'source_tree':tree,
            'native_source_commit':EXPECTED_NATIVE_COMMIT,
            'native_source_tree':EXPECTED_NATIVE_TREE,
            'compose_sha256':hashlib.sha256(args.compose_file.read_bytes()).hexdigest(),
            'on_patch_sha256':args.on_patch_sha256,
            **namespace,'services':services,'gateway':gateway,'dual_rpc':rpc,
            'classification':'IDENTITY_CAPTURE_NOT_TEST_RESULT'}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x',encoding='utf-8') as stream:
        json.dump(record,stream,sort_keys=True,indent=2)
        stream.write('\n')


if __name__=='__main__':main()
