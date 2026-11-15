"""D-owned local signed observer contract negatives, without Docker/network."""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from acceptance import security_at as security


def test_missing_secret_probe_rejects_invalid_baseline(monkeypatch):
    for name in list(security.os.environ):
        if name.startswith('VAULT_'):
            monkeypatch.delenv(name, raising=False)
    with pytest.raises(AssertionError, match='baseline'):
        security.negative_startups()


def test_missing_secret_probe_checks_each_attributable_failure(monkeypatch, tmp_path):
    from argon2 import PasswordHasher
    values={'VAULT_ADMIN_PASSWORD_HASH':PasswordHasher().hash('synthetic-password'),
            'VAULT_SESSION_SECRET':'s'*48, 'VAULT_ENCRYPTION_KEY':'e'*48,
            'VAULT_SCHOOL_ID':'synthetic-school', 'VAULT_ACTOR_ID':'synthetic-admin',
            'VAULT_NATIVE_URL':'http://127.0.0.1:12345',
            'VAULT_NATIVE_PASSWORD':'synthetic-native-password',
            'VAULT_SURREAL_USER':'synthetic-user', 'VAULT_SURREAL_PASSWORD':'p'*48,
            'VAULT_MAINTENANCE_FILE':str(tmp_path/'freeze')}
    for name in list(security.os.environ):
        if name.startswith('VAULT_'):
            monkeypatch.delenv(name, raising=False)
    for name,value in values.items():
        monkeypatch.setenv(name,value)
    security.negative_startups()


def test_missing_secret_probe_rejects_unrelated_process_error(monkeypatch):
    monkeypatch.setattr(security.subprocess,'run',lambda *a,**k: SimpleNamespace(returncode=0))
    class FailedChild:
        returncode=1
        def wait(self, timeout):
            return self.returncode
        def communicate(self, timeout):
            return b'', b'unrelated import failure'
        def poll(self):
            return self.returncode
    monkeypatch.setattr(security.subprocess,'Popen',lambda *a,**k: FailedChild())
    with pytest.raises(AssertionError, match='not attributable'):
        security.negative_startups()


def fixture(tmp_path,monkeypatch):
    key=Ed25519PrivateKey.generate()
    public=key.public_key().public_bytes_raw()
    monkeypatch.setenv('VAULT_EXTERNAL_OBSERVER_PUBKEY_BASE64',base64.b64encode(public).decode())
    sha='a'*40;tree='b'*40
    identity={'external_target':{'private_ip':'192.168.55.2','host_identity_sha256':'c'*64},
              'gateway':{'instance_id':'f'*32}}
    mappings=[('a_db','d'*64,'127.0.0.1',33321,'8000/tcp'),
              ('on_db','e'*64,'127.0.0.1',33322,'8000/tcp'),
              ('native','f'*64,'127.0.0.1',33323,'5055/tcp')]
    monkeypatch.setattr(security,'verify_manifest',lambda *args:(identity,mappings,'9'*64))
    rows=[{'service':s,'container_id':c,'published_host_ip':bind,
           'published_host_port':port,'container_port':internal,
           'target_host_identity_verified':True,'outcome':'CONNECTION_REFUSED'}
          for s,c,bind,port,internal in mappings]
    payload={'type':'SUNRISE_S1_EXTERNAL_PORT_DENIAL_V1',
             'source_commit':sha,'source_tree':tree,'runtime_identity_sha256':'9'*64,
             'context':'test','project':'sunrise-s1-synthetic',
             'target_private_ip':'192.168.55.2','target_host_identity_sha256':'c'*64,
             'gateway_instance_id':'f'*32,'observer_independent':True,
             'observer_network_isolated':True,'target_host_identity_verified':True,
             'observer_id':'synthetic-independent-observer',
             'observed_utc':datetime.now(timezone.utc).isoformat(),
             'observations':rows}
    args=SimpleNamespace(runtime_identity=tmp_path/'identity.json',context='test',
         project='sunrise-s1-synthetic',source_sha=sha,source_tree=tree,
         target_private_ip='192.168.55.2',observer_evidence=tmp_path/'signed-observer.json')
    def sign(data):
        sig=key.sign(json.dumps(data,sort_keys=True,separators=(',',':')).encode())
        args.observer_evidence.write_text(json.dumps({'payload':data,
            'signature_ed25519':base64.b64encode(sig).decode()}))
    return args,payload,sign,identity


def test_signed_real_target_external_evidence_accepted_only_as_candidate(tmp_path,monkeypatch):
    args,payload,sign,_=fixture(tmp_path,monkeypatch)
    sign(payload)
    result=security.verify_external_denial_evidence(args)
    assert result['physical_services']==['a_db','native','on_db']
    assert result['external_network_status']=='SIGNED_REAL_TARGET_OBSERVER_DENIED'


@pytest.mark.parametrize('field,bad',[
    ('target_private_ip','192.168.55.99'),
    ('source_commit','f'*40),
    ('runtime_identity_sha256','0'*64),
    ('observer_independent',False),
    ('observer_network_isolated',False),
    ('target_host_identity_verified',False),
    ('observed_utc','2020-01-01T00:00:00+00:00'),
    ('observations',[]),
])
def test_false_network_denial_claims_rejected(tmp_path,monkeypatch,field,bad):
    args,payload,sign,_=fixture(tmp_path,monkeypatch)
    sign({**payload,field:bad})
    with pytest.raises((AssertionError,ValueError)):
        security.public_port_denials(args)


def test_unsigned_and_wrong_host_identity_rejected(tmp_path,monkeypatch):
    args,payload,sign,identity=fixture(tmp_path,monkeypatch)
    sign(payload)
    identity['external_target']['host_identity_sha256']='0'*64
    with pytest.raises((AssertionError,ValueError)):
        security.public_port_denials(args)
    identity['external_target']['host_identity_sha256']='c'*64
    sign(payload)
    doc=json.loads(args.observer_evidence.read_text());doc['signature_ed25519']=base64.b64encode(b'0'*64).decode()
    args.observer_evidence.write_text(json.dumps(doc))
    with pytest.raises(Exception):security.public_port_denials(args)


def test_missing_target_binding_rejected(tmp_path,monkeypatch):
    args,payload,sign,identity=fixture(tmp_path,monkeypatch)
    sign(payload)
    identity.pop('external_target')
    with pytest.raises(AssertionError,match='external target host'):
        security.public_port_denials(args)
