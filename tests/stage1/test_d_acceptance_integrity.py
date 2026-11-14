"""D-owned offline fail-closed regression tests; NEVER native acceptance."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stage1/acceptance'))
import evidence_inventory as inv
import evidence_bundle as bundle
import run_stage1 as runner
import release_manifest as release


def git(repo, *parts):
    return subprocess.run(['git','-C',str(repo),*parts],check=True,
                          capture_output=True,text=True).stdout.strip()


@pytest.fixture
def clean_repo(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    git(root,'init','-q')
    git(root,'config','user.name','Synthetic D Unit Test')
    git(root,'config','user.email','synthetic@example.invalid')
    (root/'scripts/stage1').mkdir(parents=True)
    (root/'scripts/stage1'/'app.py').write_text('VALUE = 1\n')
    git(root,'add','.')
    git(root,'commit','-qm','synthetic baseline')
    return root,git(root,'rev-parse','HEAD'),git(root,'rev-parse','HEAD^{tree}')


def test_clean_source_requires_real_git_and_outside_evidence(clean_repo,tmp_path):
    repo,sha,tree=clean_repo
    assert inv.verify_clean_source(repo,sha,tree,output=tmp_path/'out.json')['source_sha']==sha
    with pytest.raises(inv.UnsafeEvidence,match='outside source'):
        inv.verify_clean_source(repo,sha,tree,output=repo/'ignored-output.json')
    with pytest.raises(inv.UnsafeEvidence):
        inv.verify_clean_source(repo,'a'*40,tree)


@pytest.mark.parametrize('mode',['modified','staged','untracked','ignored_executable','drift'])
def test_dirty_source_or_revision_drift_blocks(clean_repo,mode):
    repo,sha,tree=clean_repo
    source=repo/'scripts/stage1/app.py'
    if mode=='modified':source.write_text('VALUE = 2\n')
    elif mode=='staged':
        source.write_text('VALUE = 3\n');git(repo,'add','.')
    elif mode=='untracked':(repo/'unexpected.py').write_text('pass\n')
    elif mode=='ignored_executable':
        (repo/'.gitignore').write_text('scripts/stage1/hidden.py\n')
        git(repo,'add','.gitignore');git(repo,'commit','-qm','ignore dangerous source')
        sha=git(repo,'rev-parse','HEAD');tree=git(repo,'rev-parse','HEAD^{tree}')
        (repo/'scripts/stage1/hidden.py').write_text('print("hidden")\n')
    else:
        source.write_text('VALUE=99\n');git(repo,'add','.')
        git(repo,'commit','-qm','revision moved')
    with pytest.raises(inv.UnsafeEvidence):inv.verify_clean_source(repo,sha,tree)


def test_git_archive_not_commit_provenance(tmp_path):
    root=tmp_path/'extracted';root.mkdir()
    with pytest.raises(inv.UnsafeEvidence):inv.verify_clean_source(root,'a'*40,'b'*40)


def test_at01_untested_component_not_formal_pass():
    assert not runner.test_result('S1-AT01',{
        'result':'PARTIAL_PASSED_WITH_UNRUN_GATES',
        'results':{'same_gateway_two_school_idor_negative':'PASS'}})


AT15_NEGATIVES=('school_a_access','school_a_denies_school_b_shell',
    'school_a_denies_school_b_materials','school_a_denies_school_b_original_download',
    'forged_school_header_denied','csrf_rotated_on_switch',
    'school_b_access','school_b_denies_school_a_shell')


def test_at15_requires_all_real_same_gateway_school_negative_checks():
    good={'at_id':'S1-AT15','status':'PASS',
          'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
          'checks':{key:'PASS' for key in AT15_NEGATIVES}}
    assert runner.test_result('S1-AT15',good)
    for key in AT15_NEGATIVES:
        bad={**good,'checks':{**good['checks'],key:'NOT_RUN'}}
        assert not runner.test_result('S1-AT15',bad)
    for bad in ({'at_id':'S1-AT03'},{'status':'NOT_RUN'},
                {'classification':'UNRELATED_TEST'}):
        assert not runner.test_result('S1-AT15',{**good,**bad})


def test_at01_requires_executed_bound_at15_not_a_second_gateway(tmp_path):
    reports={x:{'status':'PASS'} for x in ('S1-AT04','S1-AT05','S1-AT15')}
    for case in reports:
        (tmp_path/(case+'.json')).write_text(json.dumps({
            'at_id':case,'status':'PASS','source_commit':'a'*40,'source_tree':'b'*40}))
    runtime={'type':'SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED',
             'source_commit':'a'*40,'source_tree':'b'*40,
             'services':{x:{} for x in ('a_db','on_db','native')},
             'gateway':{'tls_verified':True,'tls_peer_sha256':'e'*64,'tls_ca_sha256':'f'*64}}
    path=tmp_path/'runtime.json';path.write_text(json.dumps(runtime))
    config={'case_flags':{'S1-AT01':{'--runtime-identity':str(path)}}}
    with pytest.raises(runner.IncompleteAT,match='AT15 executed same-Gateway'):
        runner.run_full_at01(config,tmp_path,'a'*40,'b'*40,reports,('preflight','sha'))

def test_mismatched_case_revision_or_runtime_rejected():
    good={'source_commit':'a'*40,'source_tree':'b'*40,'status':'PASS',
          'runtime_identity_sha256':'c'*64}
    runner.verify_report_binding('S1-AT02',good,'a'*40,'b'*40,'c'*64)
    for changed in ({'source_commit':'d'*40},{'source_tree':'d'*40},
                    {'status':'NOT_RUN'},{'runtime_identity_sha256':'d'*64}):
        with pytest.raises(runner.IncompleteAT):
            runner.verify_report_binding('S1-AT02',{**good,**changed},
                                         'a'*40,'b'*40,'c'*64)


def test_three_volume_restore_evidence_mandatory(tmp_path):
    work=tmp_path/'restored';work.mkdir()
    good={'classification':'ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS',
          'source_commit':'a'*40,'source_tree':'b'*40,
          'db_inventories_equal':True,'independent_target_verified':True,
          'restored_volume_count':3,'restored_services':['a_db','on_db','native'],
          'native_owner_identity_matches_before_after':True,
          'native_readback':{'source_owner_count':1,'verified_original_count':1,
              'owned_source_graph_hash':'d'*64,
              'rights_retention_initial_version_sha256':'e'*64,
              'rights_retention_initial_version_count':1}}
    record=work/'native-readback-evidence.json';record.write_text(json.dumps(good))
    runtime={'type':'SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED',
             'source_commit':'a'*40,'source_tree':'b'*40,
             'services':{'a_db':{},'on_db':{},'native':{}},
             'gateway':{'tls_verified':True}}
    identity=tmp_path/'identity.json';identity.write_text(json.dumps(runtime))
    good['source_runtime_identity_sha256']=hashlib.sha256(identity.read_bytes()).hexdigest()
    record.write_text(json.dumps(good))
    config={'case_flags':{'S1-AT01':{'--runtime-identity':str(identity)}},
            'restore_flags':{'restore':{'--workdir':str(work)}}}
    runner.validate_restore_rights(config,tmp_path,'a'*40,'b'*40)
    assert json.loads((tmp_path/'S1-AT12.json').read_text())['source_tree']=='b'*40
    (tmp_path/'S1-AT12.json').unlink()
    for field,bad in [('restored_volume_count',1),('restored_services',['on_db','native']),
                      ('independent_target_verified',False)]:
        record.write_text(json.dumps({**good,field:bad}))
        with pytest.raises(runner.IncompleteAT):
            runner.validate_restore_rights(config,tmp_path,'a'*40,'b'*40)


def test_bundle_refuses_inside_checkout_and_dirty_source(clean_repo,tmp_path):
    repo,sha,tree=clean_repo
    evidence=tmp_path/'external';evidence.mkdir()
    (evidence/'case.json').write_text('{"status":"NOT_RUN"}')
    args=SimpleNamespace(repo_root=repo,source_sha=sha,source_tree=tree,
                         evidence_dir=evidence,output=tmp_path/'candidate.zip')
    result=bundle.create(args)
    assert result['classification'].endswith('NOT_ACCEPTANCE')
    assert bundle.verify(args.output)['classification']=='ARCHIVE_INTEGRITY_VERIFIED_MANUAL_REVIEW_REQUIRED'
    args.output=repo/'in_checkout.zip'
    with pytest.raises(inv.UnsafeEvidence):bundle.create(args)


def test_release_states_never_collapse_into_r01():
    assert len(release.RELEASE_STATES)==10
    assert release.RELEASE_STATES[-1]=='STAGE2_HANDOFF_READY'
    assert release.RELEASE_STATES[-3]=='R01_APPROVED'


def test_release_manifest_keeps_all_higher_gates_unapproved(clean_repo,tmp_path,monkeypatch):
    """Synthetic fixture checks *evidence contract*, not actual Stage 1 runtime."""
    repo,base_sha,_=clean_repo
    changed=repo/'scripts/stage1/app.py'
    changed.write_text('VALUE = 123\n')
    git(repo,'add','.');git(repo,'commit','-qm','synthetic allowed A change')
    sha=git(repo,'rev-parse','HEAD');tree=git(repo,'rev-parse','HEAD^{tree}')
    artifacts=tmp_path/'artifacts';artifacts.mkdir()
    runtime={'type':'SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED',
             'source_commit':sha,'source_tree':tree,
             'native_source_commit':'5e285b7a2e435895c4ee99ad7e4b8d2af64c3239',
             'on_patch_sha256':'a'*64,'dual_rpc':{'on_viewer_read_only':True},
             'gateway':{'tls_verified':True,'tls_peer_sha256':'e'*64,'tls_ca_sha256':'f'*64},
             'services':{name:{'image_id':'sha256:'+letter*64}
                         for name,letter in [('a_db','b'),('on_db','c'),('native','d')]}}
    run_path=artifacts/'identity.json'
    run_path.write_text(json.dumps(runtime))
    restore={'classification':'ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS',
             'source_commit':sha,'source_tree':tree,'independent_target_verified':True,
             'restored_volume_count':3,'restored_services':['a_db','on_db','native'],
             'db_inventories_equal':True,
             'source_runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest(),
             'native_readback':{'text_only_patch_attested':True}}
    restore_path=artifacts/'restore.json'
    restore_path.write_text(json.dumps(restore))
    ids={f'S1-AT{i:02}' for i in range(1,16)}-{'S1-AT13'}
    extra={'real_native_http_sha256':'S1-AT01-native.json',
           'real_browser_sha256':'S1-AT01-browser.json',
           **{x:x+'.json' for x in ('S1-AT04','S1-AT05','S1-AT15')}}
    # This is a *unit-only synthetic fixture*: contents deliberately do not
    # represent real executed Gateway/restore evidence.
    (artifacts/'S1-AT01-native.json').write_text('{"formal_s1_at01_15":"NOT_RUN"}')
    (artifacts/'S1-AT01-browser.json').write_text(json.dumps({
        'status':'PASS','at_id':'S1-AT01-BROWSER',
        'classification':'SYNTHETIC_LOCAL_BROWSER_JOURNEY_CANDIDATE',
        'source_commit':sha,'source_tree':tree,'gateway_scheme':'https',
        'gateway_tls_peer_sha256':'e'*64,'browser_engine':'chromium',
        'chromium_version':'141.0.0.0','playwright_package_version':'1.65.1',
        'checks':{key:'PASS' for key in runner.BROWSER_CHECKS},
        'runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest()}))
    for at in sorted(ids-{'S1-AT01'}):
        data={'at_id':at,'status':'PASS','source_commit':sha,'source_tree':tree}
        if at=='S1-AT04':
            data.update({'runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest(),
                         'native_readback_before_after_equal':True,
                         'checks':{key:'PASS' for key in ('live_runtime_identity_after_restart',
                           'gateway_authenticated_session','gateway_owned_native_original_sha',
                           'gateway_checks_passed_after_freeze_release')}})
        if at=='S1-AT15':
            data.update({'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
                         'runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest(),
                         'gateway_tls_peer_sha256':'e'*64,
                         'checks':{key:'PASS' for key in AT15_NEGATIVES}})
        if at=='S1-AT05':
            data['restore_evidence_sha256']=hashlib.sha256(restore_path.read_bytes()).hexdigest()
        (artifacts/(at+'.json')).write_text(json.dumps(data))
    deps={name:hashlib.sha256((artifacts/file).read_bytes()).hexdigest()
          for name,file in extra.items()}
    (artifacts/'S1-AT01.json').write_text(json.dumps({
        'at_id':'S1-AT01','status':'PASS','source_commit':sha,'source_tree':tree,
        'result':'FULL_NATIVE_UI_HTTP_JOURNEY_PASS',
        'formal_s1_at01_15':'S1-AT01_CANDIDATE_EXECUTED',
        'evidence_dependencies':deps}))
    hashes={at:hashlib.sha256((artifacts/(at+'.json')).read_bytes()).hexdigest()
            for at in ids}
    evidence={'source_sha':sha,'source_tree':tree,'aggregate':'ALL_SELECTED_PASS',
              'tests_executed':18,'covered_at_ids':sorted(ids),
              'case_evidence_sha256':hashes,
              'runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest(),
              'restore_evidence_sha256':hashlib.sha256(restore_path.read_bytes()).hexdigest()}
    regression=artifacts/'summary.json';regression.write_text(json.dumps(evidence))
    out=artifacts/'at13.json'
    argv=['release_manifest.py','--repo-root',str(repo),'--source-sha',sha,
          '--source-tree',tree,'--base-sha',base_sha,'--runtime-identity',str(run_path),
          '--restore-evidence',str(restore_path),'--regression-evidence',str(regression),
          '--out',str(out)]
    monkeypatch.setenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM','YES')
    monkeypatch.setattr(sys,'argv',argv)
    release.main()
    result=json.loads(out.read_text())
    assert result['status']=='PASS'
    assert result['classification']=='S1_AT13_SOURCE_REGRESSION_CANDIDATE_NOT_R01'
    assert result['release_gate_states']['R01_APPROVED']=='NOT_RUN'
    assert result['release_gate_states']['OWNER_UAT_PASSED']=='NOT_RUN'
    assert result['release_gate_states']['S1_AT01_15_PASSED']=='NOT_RUN'
    assert result['release_gate_states']['PR14_MERGED']=='NOT_RUN'
    # A valid SHA256 of unrelated stale proof is not acceptance.
    regression.write_text(json.dumps({**evidence,'restore_evidence_sha256':'0'*64}))
    out=artifacts/'reject.json';monkeypatch.setattr(sys,'argv',argv[:-1]+[str(out)])
    with pytest.raises(RuntimeError,match='Regressions not actually executed'):
        release.main()
    assert json.loads(out.read_text())['status']=='FAIL'
    # A hash listing can no longer conceal missing, replaced, or fake case bytes.
    regression.write_text(json.dumps(evidence))
    (artifacts/'S1-AT15.json').write_text('{"status":"NOT_RUN"}')
    out=artifacts/'tampered.json';monkeypatch.setattr(sys,'argv',argv[:-1]+[str(out)])
    with pytest.raises(RuntimeError,match='Stale or overwritten case evidence|AT01 dependency hash'):
        release.main()
    assert json.loads(out.read_text())['status']=='FAIL'
    # Even a consistently re-hashed AT15 PASS is not proof of the IDOR negatives.
    wrong={'at_id':'S1-AT15','status':'PASS','source_commit':sha,
           'source_tree':tree,'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
           'runtime_identity_sha256':hashlib.sha256(run_path.read_bytes()).hexdigest(),
           'gateway_tls_peer_sha256':'e'*64,
           'checks':{'school_a_access':'PASS'}}
    at15_path=artifacts/'S1-AT15.json';at15_path.write_text(json.dumps(wrong))
    at01_path=artifacts/'S1-AT01.json';at01=json.loads(at01_path.read_text())
    at01['evidence_dependencies']['S1-AT15']=hashlib.sha256(at15_path.read_bytes()).hexdigest()
    at01_path.write_text(json.dumps(at01))
    evidence['case_evidence_sha256']['S1-AT15']=hashlib.sha256(at15_path.read_bytes()).hexdigest()
    evidence['case_evidence_sha256']['S1-AT01']=hashlib.sha256(at01_path.read_bytes()).hexdigest()
    regression.write_text(json.dumps(evidence))
    out=artifacts/'unrelated_at15.json';monkeypatch.setattr(sys,'argv',argv[:-1]+[str(out)])
    with pytest.raises(RuntimeError,match='Executed AT15 school IDOR'):
        release.main()
    assert json.loads(out.read_text())['status']=='FAIL'


def test_at15_rejects_unrelated_pass_even_if_hashes_updated():
    """AT15 PASS label alone cannot satisfy same-Gateway negative contract."""
    good={'at_id':'S1-AT15','status':'PASS',
          'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
          'checks':{key:'PASS' for key in AT15_NEGATIVES}}
    assert runner.test_result('S1-AT15',good)
    assert not runner.test_result('S1-AT15',{**good,'checks':{'school_a_access':'PASS'}})
