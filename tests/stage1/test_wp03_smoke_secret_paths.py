"""WP03 P0: execute main() both ways without a real DB/Native Runtime.

These are deterministic component contracts, not a Native PASS. Runner-only
integration tests remain mandatory under exact reviewed SHA.
"""
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/stage1/surreal_journal_smoke.py'
sys.path.insert(0, str(ROOT/'apps/a-vault'))
sys.path.insert(0, str(ROOT/'scripts/stage1'))


def fresh_module():
    spec = importlib.util.spec_from_file_location('wp03_smoke_under_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def races(secret, mode='good'):
    if mode=='exception':
        raise RuntimeError('Native race failed')
    if mode=='missing':
        return {}
    if mode=='incomplete_native':
        secret = None
    entries={}
    for kind in ('same_key_same_body','different_key_same_scope','same_key_different_body'):
        entries[kind]={'outcomes':{'FRESH':1,'CONFLICT':7},
                       'durable_operations':1,'durable_scope_claims':1,
                       'durable_shells':int(bool(secret)),'native_create_posts':int(bool(secret))}
    return entries


def prepare(monkeypatch,tmp_path,secret=None,race_mode='good',ack_mode='good',db_mode='good'):
    module=fresh_module()
    evidence=tmp_path/'journal.json'
    monkeypatch.setenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM','YES')
    monkeypatch.setenv('VAULT_JOURNAL_EVIDENCE',str(evidence))
    # Unit fixture only: runtime case attestation is separately exercised by
    # executable provenance regressions, never claimed as Native PASS.
    monkeypatch.setattr(sys,'argv',['surreal_journal_smoke.py',
        '--runtime-identity',str(tmp_path/'synthetic-runtime.json'),
        '--source-sha','a'*40,'--source-tree','b'*40])
    monkeypatch.setattr(module,'inspect_runtime',lambda *a: 'c'*64)
    monkeypatch.setattr(module,'guard_runtime',lambda *a: None)
    # Component-test-only endpoint: actual provenance rejects missing/wrong
    # source, stale Docker identity and non-loopback targets in separate tests.
    endpoint='http://127.0.0.1:65055'
    monkeypatch.setattr(module,'resolve_native_endpoint',lambda *a: endpoint)
    if secret is None:monkeypatch.delenv('OPEN_NOTEBOOK_PASSWORD',raising=False)
    else:monkeypatch.setenv('OPEN_NOTEBOOK_PASSWORD',secret)
    monkeypatch.setattr(module,'cfg',lambda: SimpleNamespace(database='synthetic-unique-journal'))
    calls={'races':[],'lost_ack':[],'subprocess':[],'recover':[],'db':0}

    class FakeStore:
        def __init__(self,cfg,actor):
            calls['db']+=1
            if db_mode=='initial_fail':raise RuntimeError('DB unavailable')
        def start_shell(self,school,key,payload):
            if payload.get('grade')=='P5':raise module.Conflict('Different body same key')
            # 16 other threads prove that no replay can create another notebook.
            if calls.get('recovered'):
                return {'notebook_id':'notebook:original','shell_id':'shell-unique'},False
            if calls.setdefault('created',False):
                raise module.Indeterminate('native operation pending')
            calls['created']=True
            return {'shell_id':'shell-unique','creation_marker':'sunrise-a-op-v1:'+'a'*64},True
        def operation(self,school,key,kind):
            return {'shell_id':'shell-unique'}
        def shell(self,school,shellid):
            return None  # foreign school denied
    monkeypatch.setattr(module,'SurrealStore',FakeStore)
    def race_runner(cfg,actor,loaded_secret,native_endpoint):
        assert native_endpoint==endpoint
        calls['races'].append(loaded_secret)
        return races(loaded_secret,race_mode)
    monkeypatch.setattr(module,'first_reservation_races',race_runner)
    def lost_ack(cfg,actor,loaded_secret,native_endpoint):
        assert native_endpoint==endpoint
        calls['lost_ack'].append(loaded_secret)
        if ack_mode=='exception':raise RuntimeError('TCP ACK dropped before native create')
        if ack_mode=='incomplete':return {'native_create_posts':0}
        return {'native_create_posts':1,'client_received_post_ack':False,
                'persisted_mapping_count':1,'original_notebook_sha256':'b'*64}
    monkeypatch.setattr(module,'native_lost_ack',lost_ack)
    def child(*args,**kwargs):
        calls['subprocess'].append(kwargs.get('env',{}).get('OPEN_NOTEBOOK_PASSWORD'))
        return SimpleNamespace(returncode=97)
    # Replace the smoke module's subprocess binding, NOT the shared stdlib
    # subprocess.run used by real Git SHA/tree/Runtime provenance checks.
    monkeypatch.setattr(module,'subprocess',
                        SimpleNamespace(run=child,DEVNULL=subprocess.DEVNULL))
    async def recovery(store,school,key,details,loaded_secret,native_endpoint):
        assert native_endpoint==endpoint
        calls['recover'].append(loaded_secret)
        calls['recovered']=True
        return {'notebook_id':'notebook:original','shell_id':'shell-unique'}
    monkeypatch.setattr(module,'recover_native',recovery)
    return module,evidence,calls


@pytest.mark.parametrize('password',[None,''])
def test_db_only_partial_never_native_pass(monkeypatch,tmp_path,password):
    m,file,c=prepare(monkeypatch,tmp_path,password)
    with pytest.raises(SystemExit) as stopped:
        m.main()
    assert stopped.value.code==2
    evidence=json.loads(file.read_text())
    assert evidence['status']=='PARTIAL'
    assert evidence['native_gate']=='NOT_RUN'
    assert evidence['results']['real_surrealdb_unique_operation_reservation']=='PASS'
    assert evidence['results']['different_body_conflict']=='PASS'
    assert evidence['results']['same_key_concurrent_no_second_reservation']=='PASS'
    for n in ('real_native_lost_ack_tcp','real_native_crash_after_create_before_journal_commit',
              'marker_reconciliation_unique_mapping','same_key_replay_original_notebook',
              'cross_school_shell_negative'):
        assert evidence['results'][n]=='NOT_RUN'
    assert c['races']==[None] and not c['lost_ack'] and not c['subprocess']
    assert 'notebook_id_sha256' not in evidence


def test_present_secret_both_native_flows_pass_after_evidence(monkeypatch,tmp_path):
    secret='synthetic-private-native-password-never-log'
    m,file,c=prepare(monkeypatch,tmp_path,secret)
    m.main()
    evidence=json.loads(file.read_text())
    assert evidence['status']=='PASS' and evidence['native_gate']=='PASS'
    assert c['races']==[secret] and c['lost_ack']==[secret]
    assert c['subprocess']==[secret] and c['recover']==[secret]
    assert evidence['results']['real_native_crash_after_create_before_journal_commit']=='PASS'
    assert evidence['results']['real_native_lost_ack_tcp']['native_create_posts']==1
    assert evidence['results']['real_native_lost_ack_tcp']['client_received_post_ack'] is False
    assert secret not in file.read_text()


@pytest.mark.parametrize('mode',['missing','incomplete_native','exception'])
def test_malformed_or_failing_nested_races_fail_closed(monkeypatch,tmp_path,mode):
    m,file,c=prepare(monkeypatch,tmp_path,'synthetic-secure-native-pass',race_mode=mode)
    with pytest.raises((AssertionError,RuntimeError)):
        m.main()
    evidence=json.loads(file.read_text())
    assert evidence['status']=='FAIL'
    assert evidence['error_type'] in ('AssertionError','RuntimeError')
    assert not c['subprocess'] and not c['lost_ack']


@pytest.mark.parametrize('ack_mode',['incomplete','exception'])
def test_lost_ack_unverifiable_native_never_pass(monkeypatch,tmp_path,ack_mode):
    m,file,c=prepare(monkeypatch,tmp_path,'synthetic-secure-native-pass',ack_mode=ack_mode)
    with pytest.raises((AssertionError,RuntimeError)):
        m.main()
    evidence=json.loads(file.read_text())
    assert evidence['status']=='FAIL' and 'real_native_lost_ack_tcp' not in evidence['results']
    assert len(c['subprocess'])==len(c['lost_ack'])==1


def test_database_failure_is_not_swallowed(monkeypatch,tmp_path):
    m,file,_=prepare(monkeypatch,tmp_path,None,db_mode='initial_fail')
    with pytest.raises(RuntimeError,match='DB unavailable'):
        m.main()
    evidence=json.loads(file.read_text())
    assert evidence['status']=='FAIL' and evidence['error_type']=='RuntimeError'
    assert evidence['results']=={}


def test_no_native_password_does_not_mask_bad_db_races(monkeypatch,tmp_path):
    m,file,_=prepare(monkeypatch,tmp_path,None,race_mode='exception')
    with pytest.raises(RuntimeError):m.main()
    evidence=json.loads(file.read_text())
    assert evidence['status']=='FAIL' and evidence['error_type']=='RuntimeError'

def test_child_stub_does_not_mutate_global_subprocess(monkeypatch,tmp_path):
    """The child is fake in this component case; real SHA/tree probes remain real."""
    original_run=subprocess.run
    module,_,_=prepare(monkeypatch,tmp_path,'synthetic-secret')
    assert subprocess.run is original_run
    assert module.subprocess.run([],env={}).returncode==97
    real=subprocess.run([sys.executable,'-c','print("GLOBAL_SUBPROCESS_INTACT")'],
                        capture_output=True,text=True,check=True,timeout=10)
    assert real.stdout.strip()=='GLOBAL_SUBPROCESS_INTACT'


def test_runtime_provenance_git_fail_closed_with_wp03_stub(monkeypatch,tmp_path):
    """Untrusted non-repository root MUST fail the real source verifier."""
    prepare(monkeypatch,tmp_path,'synthetic-secret')
    from executed_runtime_provenance import _git
    with pytest.raises(subprocess.CalledProcessError):
        _git(tmp_path,'HEAD')
