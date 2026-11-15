"""D-only offline consumer tests. Synthetic fixtures are NOT browser evidence."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import run_stage1 as runner

SHA='a'*40
TREE='b'*40
IDENTITY='c'*64
PEER='d'*64
CA='e'*64
GATEWAY={'tls_verified':True,'tls_peer_sha256':PEER,'tls_ca_sha256':CA}


def browser(engine='chromium'):
    data={'at_id':'S1-AT01-BROWSER','status':'PASS',
          'classification':'SYNTHETIC_LOCAL_BROWSER_JOURNEY_CANDIDATE',
          'source_commit':SHA,'source_tree':TREE,
          'runtime_identity_sha256':IDENTITY,'gateway_scheme':'https',
          'gateway_tls_peer_sha256':PEER,'browser_engine':engine,
          'playwright_package_version':'1.65.1',
          'checks':{key:'PASS' for key in runner.BROWSER_CHECKS}}
    if engine=='chromium':data['chromium_version']='141.0.0.0'
    if engine=='firefox':
        data.update({'firefox_version':'159.0','browser_version':'159.0',
                     'browser_tls_verification':'STRICT',
                     'firefox_nss_profile':'ISOLATED_PERSISTENT',
                     'firefox_nss_ca_trust':'C,,',
                     'firefox_nss_ca_sha256':CA,
                     'firefox_profile_path_sha256':'1'*64,
                     'browser_executable_sha256':'2'*64,
                     'firefox_nss_profile_cleanup':'PASS'})
    return data


def accept(data):
    return runner.verify_browser_evidence(data,SHA,TREE,IDENTITY,GATEWAY)


def test_chromium_legacy_engine_and_complete_checks():
    assert accept(browser())=='chromium'


def test_firefox_real_engine_complete_strict_nss_evidence():
    assert accept(browser('firefox'))=='firefox'


@pytest.mark.parametrize('change',[
    ('browser_engine','webkit'),('browser_engine',None),('firefox_version',None),
    ('firefox_version','Firefox 159'),('firefox_version','160.0'),
    ('browser_version','160.0'),('browser_version',None),
    ('playwright_package_version','1.65.2'),
    ('browser_tls_verification','BYPASS'),('browser_tls_verification',None),
    ('firefox_nss_profile','SHARED'),('firefox_nss_profile',None),
    ('firefox_nss_ca_trust',''),('firefox_nss_ca_trust',None),
    ('firefox_nss_ca_sha256','0'*64),('firefox_nss_ca_sha256',None),
    ('firefox_profile_path_sha256',None),('firefox_profile_path_sha256','invalid'),
    ('browser_executable_sha256',None),('browser_executable_sha256','invalid'),
    ('firefox_nss_profile_cleanup','FAIL'),('firefox_nss_profile_cleanup',None),
    ('gateway_scheme','http'),('gateway_tls_peer_sha256','0'*64),
    ('source_commit','f'*40),('source_tree','f'*40),
    ('runtime_identity_sha256','f'*64),('status','PARTIAL'),
    ('classification','FIREFOX_LOGIN_POC_PASS'),
])
def test_firefox_rejects_unsupported_partial_stale_or_tls_bypass(change):
    data=browser('firefox')
    data[change[0]]=change[1]
    with pytest.raises(runner.IncompleteAT):accept(data)


@pytest.mark.parametrize('key',runner.BROWSER_CHECKS)
def test_firefox_requires_each_real_ui_journey_check(key):
    data=browser('firefox')
    data['checks'][key]='NOT_RUN'
    with pytest.raises(runner.IncompleteAT):accept(data)


def test_browser_preflight_is_not_full_at01_without_restore_and_at15(tmp_path):
    proof=browser('firefox')
    assert accept(proof)=='firefox'
    with pytest.raises(runner.IncompleteAT,match='prerequisite'):
        runner.run_full_at01({},tmp_path,SHA,TREE,{},(None,None))


def test_firefox_rejects_unverified_gateway_ca_even_if_browser_ca_matches():
    data=browser('firefox')
    bad_gateway={**GATEWAY,'tls_ca_sha256':'not-a-sha'}
    data['firefox_nss_ca_sha256']='not-a-sha'
    with pytest.raises(runner.IncompleteAT):
        runner.verify_browser_evidence(data,SHA,TREE,IDENTITY,bad_gateway)


def test_c_producer_fixture_does_not_require_nonexistent_flags():
    data=browser('firefox')
    for non_producer_field in ('browser_engine_verified','tls_strict_verified',
                               'nss_profile_isolated','nss_profile_cleanup_verified',
                               'nss_profile_ca_sha256'):
        assert non_producer_field not in data
    assert accept(data)=='firefox'


def test_rehashed_incomplete_firefox_artifact_is_still_rejected(tmp_path):
    # Rehashing a forged / partial file must not make the shared release
    # consumer validator accept it: a digest proves bytes, not their meaning.
    data=browser('firefox')
    data['firefox_nss_profile_cleanup']='FAIL'
    artifact=tmp_path/'S1-AT01-browser.json'
    artifact.write_text(json.dumps(data,sort_keys=True)+'\n')
    digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert digest==hashlib.sha256(artifact.read_bytes()).hexdigest()
    with pytest.raises(runner.IncompleteAT):
        accept(json.loads(artifact.read_bytes()))


@pytest.mark.parametrize(('scenario_engine','report_engine','accepted'),[
    (None,'firefox',False),
    ('firefox','firefox',True),
    ('chromium','chromium',True),
    ('firefox','chromium',False),
])
def test_scenario_requested_engine_bound_to_actual_browser_report(
        tmp_path,monkeypatch,scenario_engine,report_engine,accepted):
    """The real runner cannot accept a complete report from the wrong engine."""
    shared={'--gateway':'https://127.0.0.1:56789',
            '--context':'synthetic','--project':'synthetic',
            '--runtime-identity':'synthetic-identity.json'}
    flags={**shared,'--gateway-ca-file':'synthetic-ca.pem'}
    if scenario_engine is not None:
        flags['--browser-engine']=scenario_engine
    config={'browser_flags':flags,'case_flags':{'S1-AT01':{
        **shared,'--ca-file':'synthetic-ca.pem'}}}
    observed=[]

    def fake_case(script,passed_flags,destination):
        observed.append(passed_flags.copy())
        destination.write_text(json.dumps(browser(report_engine)))
        return {'exit_code':0}

    monkeypatch.setattr(runner,'subprocess_case',fake_case)
    monkeypatch.setattr(runner,'pinned_runtime_identity',
                        lambda *args: ({'gateway':GATEWAY},IDENTITY))
    if accepted:
        step,digest=runner.run_browser_before_cold_capture(config,tmp_path,SHA,TREE)
        assert step['exit_code']==0
        assert digest==hashlib.sha256((tmp_path/'S1-AT01-browser.json').read_bytes()).hexdigest()
    else:
        with pytest.raises(runner.IncompleteAT,match='Actual browser engine differs'):
            runner.run_browser_before_cold_capture(config,tmp_path,SHA,TREE)
    assert len(observed)==1
    assert observed[0].get('--browser-engine','chromium')==(
        scenario_engine if scenario_engine is not None else 'chromium')


@pytest.mark.parametrize('invalid',[None,'webkit','Firefox','',1])
def test_unsupported_requested_engine_fails_before_browser_launch(
        tmp_path,monkeypatch,invalid):
    shared={'--gateway':'https://127.0.0.1:56789',
            '--context':'synthetic','--project':'synthetic',
            '--runtime-identity':'synthetic-identity.json'}
    flags={**shared,'--gateway-ca-file':'synthetic-ca.pem','--browser-engine':invalid}
    config={'browser_flags':flags,'case_flags':{'S1-AT01':{
        **shared,'--ca-file':'synthetic-ca.pem'}}}
    def forbid_execution(*args,**kwargs):
        pytest.fail('Unsupported scenario engine reached browser execution')
    monkeypatch.setattr(runner,'subprocess_case',forbid_execution)
    with pytest.raises(runner.IncompleteAT,match='Unsupported requested browser engine'):
        runner.run_browser_before_cold_capture(config,tmp_path,SHA,TREE)
