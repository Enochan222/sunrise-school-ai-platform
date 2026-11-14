"""Repair C unit regressions; no Docker or acceptance claim."""
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import loopback_port_contract as relay
import run_stage1 as runner

def test_static_relay_ports_unique_and_valid():
 assert relay.validate_explicit_ports({'a_db':'50101','on_db':'50102','native':'50103'})=={'a_db':50101,'on_db':50102,'native':50103}
 for d in ({'a_db':'50101','on_db':'50101','native':'50103'}, {'a_db':'80','on_db':'50102','native':'50103'}, {'a_db':'50101','on_db':'50102','native':'0'}, {'a_db':'50101','on_db':'50102'}, {'a_db':'*','on_db':'50102','native':'50103'}):
  with pytest.raises(RuntimeError):relay.validate_explicit_ports(d)

def test_at04_consumer_rejects_prior_false_pass_and_missing_checks():
 old={'at_id':'S1-AT04','status':'PASS','native_readback_before_after_equal':True}
 assert not runner.test_result('S1-AT04',old)
 checks={'live_runtime_identity_after_restart':'PASS','gateway_authenticated_session':'PASS','gateway_owned_native_original_sha':'PASS','freeze_released_after_checks':'PASS'}
 assert runner.test_result('S1-AT04',{**old,'checks':checks})
 for k in checks:
  assert not runner.test_result('S1-AT04',{**old,'checks':{**checks,k:'FAIL'}})

def test_host_config_port_must_match_live_mapping():
 import test_loopback_port_contract as fixtures
 backend,live=fixtures.fixture()
 live['HostConfig']['PortBindings']['8000/tcp'][0]['HostPort']='48921'
 with pytest.raises(RuntimeError):relay.inspect_port_pair('a_db',backend,live,fixtures.PROJECT,fixtures.IMAGE)

def test_gateway_post_restart_probe_rejects_wrong_peer(monkeypatch):
 import restart_persistence as restart
 from types import SimpleNamespace
 gateway={'origin':'https://127.0.0.1:50000','instance_id':'a'*32,'tls_peer_sha256':'b'*64,'tls_ca_sha256':'c'*64}
 monkeypatch.setenv('VAULT_GATEWAY_CA_FILE','ca.pem')
 monkeypatch.setattr(restart,'tls_gateway_identity',lambda *_:{**gateway,'tls_peer_sha256':'d'*64})
 with pytest.raises(RuntimeError,match='TLS identity'):
  restart.verify_gateway_after_restart(SimpleNamespace(probe_sha256='a'*64),{'gateway':gateway},None)

@pytest.mark.parametrize('session_status,pdf_status,pdf_bytes',[(401,200,b'pdf'),(200,404,b'pdf'),(200,200,b'wrong')])
def test_gateway_restart_probe_rejects_lost_session_or_bad_original(monkeypatch,session_status,pdf_status,pdf_bytes):
 import hashlib
 import restart_persistence as restart
 from types import SimpleNamespace
 gateway={'origin':'https://127.0.0.1:50000','instance_id':'a'*32,'tls_peer_sha256':'b'*64,'tls_ca_sha256':'c'*64}
 monkeypatch.setenv('VAULT_GATEWAY_CA_FILE','ca.pem');monkeypatch.setenv('VAULT_TEST_ADMIN_PASSWORD','synthetic-secret')
 monkeypatch.setattr(restart,'tls_gateway_identity',lambda *_:gateway)
 class Response:
  def __init__(self,status,content=b''):self.status_code=status;self.content=content
  def json(self):return {'school_id':'synthetic-a'}
 class Client:
  def get(self,path):return Response(session_status) if path=='/auth/me' else Response(pdf_status,pdf_bytes)
 args=SimpleNamespace(probe_sha256=hashlib.sha256(b'pdf').hexdigest(),probe_shell='synthetic',probe_source='source:synthetic')
 with pytest.raises(RuntimeError):restart.verify_gateway_after_restart(args,{'gateway':gateway},Client())
