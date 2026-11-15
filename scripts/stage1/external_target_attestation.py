#!/usr/bin/env python3
"""Bind physical Mac host identity to a separately signed external observer.

Never invent an address/hash. An off-box verifier must attest an authenticated
host challenge using its own pinned Ed25519 signing key. The private key is
never accepted, stored, or produced by this application.
"""
from __future__ import annotations
import base64
from datetime import datetime,timezone,timedelta
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_SHA40=re.compile(r'[0-9a-f]{40}\Z')
_SHA64=re.compile(r'[0-9a-f]{64}\Z')


def measured_mac_private_ips():
    raw=subprocess.run(['ifconfig','-a'],capture_output=True,text=True,
                       check=True,timeout=12).stdout
    addresses=set()
    for match in re.finditer(r'(?m)^\S+:\s+flags=.*?(?=^\S+:\s+flags=|\Z)',
                             raw,flags=re.S|re.M):
        interface=match.group(0)
        if 'status: inactive' in interface:
            continue
        for addr in re.findall(r'(?m)^\s*inet\s+(\d+(?:\.\d+){3})\b',interface):
            parsed=ipaddress.ip_address(addr)
            if parsed.version==4 and parsed.is_private and not (
                    parsed.is_loopback or parsed.is_link_local or
                    parsed.is_unspecified or parsed.is_multicast):
                addresses.add(str(parsed))
    if not addresses:
        raise RuntimeError('No actually configured nonloopback private Mac host IPv4')
    return addresses


def verify_attested_target(path: Path,source_sha:str,source_tree:str,
                           context:str,project:str,gateway_instance:str):
    if (not isinstance(path,Path) or not path.is_file() or path.is_symlink()
            or not 0<path.stat().st_size<=65536):
        raise RuntimeError('Independent signed host-target attestation unavailable')
    trust=os.environ.get('VAULT_EXTERNAL_OBSERVER_PUBKEY_BASE64')
    challenge=os.environ.get('VAULT_EXTERNAL_HOST_CHALLENGE')
    if (not trust or not challenge or not re.fullmatch(r'[A-Fa-f0-9]{64}',challenge)
            or not _SHA40.fullmatch(source_sha or '')
            or not _SHA40.fullmatch(source_tree or '')):
        raise RuntimeError('Pinned external public key, host challenge or source binding absent')
    envelope=json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(envelope,dict) or
            set(envelope)!={'payload','signature_ed25519'} or
            not isinstance(envelope['payload'],dict)):
        raise RuntimeError('Malformed host target attestation envelope')
    payload=envelope['payload']
    try:
        pub=base64.b64decode(trust,validate=True)
        signature=base64.b64decode(envelope['signature_ed25519'],validate=True)
        if len(pub)!=32 or len(signature)!=64:
            raise ValueError('Unexpected observer key or signature length')
        Ed25519PublicKey.from_public_bytes(pub).verify(signature,
            json.dumps(payload,sort_keys=True,separators=(',',':')).encode())
    except Exception as error:
        raise RuntimeError('Independent target attestation signature invalid') from error
    expected={'type':'SUNRISE_S1_TARGET_HOST_ATTESTATION_V1',
              'source_commit':source_sha,'source_tree':source_tree,
              'context':context,'project':project,
              'gateway_instance_id':gateway_instance,
              'host_challenge_sha256':hashlib.sha256(bytes.fromhex(challenge)).hexdigest(),
              'observer_independent':True,'target_host_identity_verified':True,
              'authenticated_host_challenge_verified':True}
    if any(payload.get(key)!=value for key,value in expected.items()):
        raise RuntimeError('Observer did not attest exact authenticated host target')
    host_ip=payload.get('target_private_ip')
    if not isinstance(host_ip,str) or host_ip not in measured_mac_private_ips():
        raise RuntimeError('Signed observer IP does not match actual Mac host interface')
    host_digest=payload.get('target_host_identity_sha256')
    if not isinstance(host_digest,str) or not _SHA64.fullmatch(host_digest):
        raise RuntimeError('Independently attested host identity hash missing')
    stamp=payload.get('observed_utc')
    try:
        moment=datetime.fromisoformat(stamp.replace('Z','+00:00'))
        if moment.utcoffset()!=timedelta(0):
            raise ValueError('Not UTC')
        age=datetime.now(timezone.utc)-moment
        if not timedelta(seconds=-30)<=age<=timedelta(minutes=10):
            raise ValueError('Stale')
    except (TypeError,AttributeError,ValueError) as error:
        raise RuntimeError('Unsigned, stale or non-UTC host observation') from error
    return {'private_ip':host_ip,'host_identity_sha256':host_digest}
