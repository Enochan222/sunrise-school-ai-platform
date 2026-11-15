"""Independent Ed25519 host-target attestation component negatives.

Uses ephemeral synthetic keys and loopback fixtures solely within unit tests.
No real external observer, Mac host or Stage 1 security PASS is claimed.
"""
import base64
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import sys
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
import external_target_attestation as target


def signed_fixture(monkeypatch,tmp_path):
    key=Ed25519PrivateKey.generate()
    public=key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    monkeypatch.setenv('VAULT_EXTERNAL_OBSERVER_PUBKEY_BASE64',
                       base64.b64encode(public).decode())
    challenge='a1'*32
    monkeypatch.setenv('VAULT_EXTERNAL_HOST_CHALLENGE',challenge)
    monkeypatch.setattr(target,'measured_mac_private_ips',lambda: {'192.168.50.4'})
    payload={'type':'SUNRISE_S1_TARGET_HOST_ATTESTATION_V1',
        'source_commit':'a'*40,'source_tree':'b'*40,
        'context':'desktop-linux','project':'sunrise-s1-synthetic-private',
        'gateway_instance_id':'e'*32,
        'host_challenge_sha256':hashlib.sha256(bytes.fromhex(challenge)).hexdigest(),
        'observer_independent':True,'target_host_identity_verified':True,
        'authenticated_host_challenge_verified':True,
        'target_private_ip':'192.168.50.4',
        'target_host_identity_sha256':'f'*64,
        'observed_utc':datetime.now(timezone.utc).isoformat()}
    path=tmp_path/'observer.json'
    def save(payload,signer=key):
        raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
        path.write_text(json.dumps({'payload':payload,
            'signature_ed25519':base64.b64encode(signer.sign(raw)).decode()}))
    save(payload)
    return payload,path,save


def verify(path):
    return target.verify_attested_target(path,'a'*40,'b'*40,
                                         'desktop-linux','sunrise-s1-synthetic-private','e'*32)


def test_signed_host_attestation_binds_actual_mac_ip_and_challenge(monkeypatch,tmp_path):
    payload,path,save=signed_fixture(monkeypatch,tmp_path)
    assert verify(path)=={'private_ip':'192.168.50.4','host_identity_sha256':'f'*64}
    monkeypatch.setattr(target,'measured_mac_private_ips',lambda:{'192.168.50.5'})
    with pytest.raises(RuntimeError,match='actual Mac'):
        verify(path)


@pytest.mark.parametrize('field,value',[
    ('target_private_ip','192.168.50.5'),
    ('host_challenge_sha256','0'*64),
    ('source_tree','c'*40),
    ('gateway_instance_id','0'*32),
    ('observer_independent',False),
    ('target_host_identity_verified',False),
    ('authenticated_host_challenge_verified',False),
    ('target_host_identity_sha256','wrong'),
    ('observed_utc',(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()),
])
def test_signed_but_untrusted_or_stale_observer_claim_rejected(monkeypatch,tmp_path,field,value):
    payload,path,save=signed_fixture(monkeypatch,tmp_path)
    payload[field]=value
    save(payload)
    with pytest.raises(RuntimeError):
        verify(path)


def test_tampered_signature_rejected(monkeypatch,tmp_path):
    payload,path,save=signed_fixture(monkeypatch,tmp_path)
    envelope=json.loads(path.read_text())
    envelope['payload']['target_private_ip']='192.168.50.5'
    path.write_text(json.dumps(envelope))
    with pytest.raises(RuntimeError,match='signature'):
        verify(path)


def test_missing_pinned_key_refused(monkeypatch,tmp_path):
    payload,path,save=signed_fixture(monkeypatch,tmp_path)
    monkeypatch.delenv('VAULT_EXTERNAL_OBSERVER_PUBKEY_BASE64')
    with pytest.raises(RuntimeError,match='Pinned'):
        verify(path)
