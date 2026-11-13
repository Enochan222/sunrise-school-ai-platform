#!/usr/bin/env python3
"""Executable S1-AT01..15 candidate orchestrator. IMPLEMENTED_UNTESTED.

NO test, container, HTTP, backup, restore or UAT executes when this source is
authored. Later execution needs exact SHA/tree + operator-supplied isolated
synthetic scenario config; runner has fixed script allowlist and NEVER shells
out to arbitrary user-defined commands. PASS here means local case evidence
candidate, NEVER Owner/Reviewer approval or R01.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if __package__:
    from .evidence_inventory import verify_clean_source
else:
    from evidence_inventory import verify_clean_source

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/'scripts/stage1'
AT_DIR=STAGE/'acceptance'
# Exercise the real HTTP journey before cold capture, but do not adjudicate
# AT01 until AT04, AT05, AT15 and a genuine Chromium journey have completed.
RUN_ORDER=('S1-AT02','S1-AT03','S1-AT06',
           'S1-AT07','S1-AT08','S1-AT09','S1-AT10','S1-AT11',
           'S1-AT14','S1-AT15','S1-AT04','S1-AT05',
           'S1-AT12','S1-AT01','S1-AT13')
CASES={
    'S1-AT01':(STAGE/'real_admin_journey.py','journey'),
    'S1-AT02':(AT_DIR/'security_at.py','security'),
    'S1-AT03':(AT_DIR/'http_boundaries.py','http'),
    'S1-AT04':(AT_DIR/'restart_persistence.py','generic'),
    'S1-AT06':(STAGE/'surreal_journal_smoke.py','journal'),
    'S1-AT07':(AT_DIR/'security_at.py','security'),
    'S1-AT08':(AT_DIR/'security_at.py','security'),
    'S1-AT09':(AT_DIR/'security_at.py','security'),
    'S1-AT10':(AT_DIR/'http_boundaries.py','http'),
    'S1-AT11':(STAGE/'wp04_native_graph_probe.py','generic'),
    'S1-AT14':(AT_DIR/'http_boundaries.py','http'),
    'S1-AT15':(AT_DIR/'http_boundaries.py','http'),
}


class IncompleteAT(RuntimeError):
    pass


class CaseFailure(IncompleteAT):
    def __init__(self, reason, detail):
        super().__init__(reason)
        self.detail=detail


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def git_id(arg):
    return subprocess.run(['git','-C',str(ROOT),'rev-parse',arg],
                          check=True,capture_output=True,text=True,timeout=12).stdout.strip()


def pairs(values):
    """Scenario JSON is only data for fixed CLI argument slots, never a shell."""
    if not isinstance(values,dict):raise IncompleteAT('Case flags missing')
    out=[]
    for key,value in values.items():
        if not re.fullmatch(r'--[a-z][a-z0-9-]{1,50}',key) or key=='--out':
            raise IncompleteAT('Unsafe/unsupported case argument key')
        if not isinstance(value,(str,int,float)) or len(str(value))>3000:
            raise IncompleteAT('Missing, oversized or non-scalar case argument')
        out.extend([key,str(value)])
    return out


def subprocess_case(script,flags,destination,*,at_id=None,env_override=None,has_out=True):
    if (not script.resolve().is_relative_to(STAGE.resolve())
            or not script.is_file() or script.is_symlink()):
        raise IncompleteAT('Unrecognised or missing real Stage1 case implementation')
    cmd=[sys.executable,str(script)]
    if at_id:cmd.extend(['--at-id',at_id])
    cmd.extend(pairs(flags))
    env=os.environ.copy()
    if env_override:env.update(env_override)
    if has_out:cmd.extend(['--out',str(destination)])
    try:
        proc=subprocess.run(cmd,cwd=str(ROOT),env=env,capture_output=True,
                            text=True,timeout=1500)
        stdout,stderr=proc.stdout,proc.stderr
        exit_code=proc.returncode
        timed_out=False
    except subprocess.TimeoutExpired as error:
        stdout=error.stdout or b''
        stderr=error.stderr or b''
        if isinstance(stdout,bytes):stdout=stdout.decode('utf-8',errors='replace')
        if isinstance(stderr,bytes):stderr=stderr.decode('utf-8',errors='replace')
        exit_code=124
        timed_out=True
    detail={'command_path':str(script.relative_to(ROOT)),
            # Never put operator-supplied positional values or secrets in evidence.
            'command_arguments_redacted':sorted(flags),
            'exit_code':exit_code,'timed_out':timed_out,
            'stdout_sha256':hashlib.sha256(stdout.encode()).hexdigest(),
            'stderr_sha256':hashlib.sha256(stderr.encode()).hexdigest(),
            'completed_utc':timestamp()}
    if timed_out or exit_code!=0:
        raise CaseFailure('Case execution did not complete successfully',detail)
    return detail


def read_json(path):
    if not path.is_file() or path.stat().st_size>4<<20:
        raise IncompleteAT('Missing or unbounded case evidence file')
    return json.loads(path.read_text(encoding='utf-8'))


def sha256_file(path):
    """Hash cold restore archives without loading an unbounded tar into RAM."""
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            chunk=stream.read(1024*1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def test_result(at,report):
    if at=='S1-AT01':
        required=('admin_login_and_private_session','surreal_durable_native_notebook_unique',
            'same_key_replay_and_body_conflict','native_pdf_upload_original_sha',
            'worker_extracted_synthetic_pdf','server_scoped_text_only_search',
            'original_pdf_hash_and_authorization','archive_non_destructive','logout_session_revocation')
        # The existing real_admin_journey.py explicitly reports a PARTIAL
        # journey with three NOT_RUN gates. A partial smoke must NEVER become
        # a formal AT01 PASS merely because its component assertions passed.
        return (report.get('result')=='FULL_NATIVE_UI_HTTP_JOURNEY_PASS' and
                report.get('formal_s1_at01_15')=='S1-AT01_CANDIDATE_EXECUTED' and
                all(report.get('results',{}).get(key)=='PASS' for key in required)
                and all(report.get('results',{}).get(key)=='PASS' for key in (
                    'gateway_restart_persistence','same_gateway_two_school_idor_negative',
                    'independent_backup_restore','browser_admin_journey')))
    if at=='S1-AT06':
        r=report.get('results')
        if not isinstance(r,dict):
            return False
        lost=r.get('real_native_lost_ack_tcp')
        races=r.get('fresh_first_reservation_races')
        if not isinstance(lost,dict) or not isinstance(races,dict):
            return False
        # Require three genuinely fresh concurrent claims, not merely
        # retries against an already-reserved scope.
        modes={'same_key_same_body','different_key_same_scope','same_key_different_body'}
        if set(races)!=modes:
            return False
        for mode in modes:
            entry=races[mode]
            if not isinstance(entry,dict):
                return False
            outcomes=entry.get('outcomes')
            if (not isinstance(outcomes,dict)
                    or not set(outcomes).issubset(
                        {'FRESH','REPLAY','CONFLICT','INDETERMINATE'})
                    or any(type(v) is not int or v<0 for v in outcomes.values())
                    or outcomes.get('FRESH')!=1 or outcomes.get('REPLAY',0)!=0
                    or sum(outcomes.values())!=8
                    or any(type(entry.get(k)) is not int or entry[k]!=1
                           for k in ('durable_operations','durable_scope_claims',
                                     'durable_shells','native_create_posts'))):
                return False
        return (report.get('status')=='PASS' and report.get('native_gate')=='PASS'
            and all(r.get(x)=='PASS' for x in (
                'real_surrealdb_unique_operation_reservation','different_body_conflict',
                'same_key_concurrent_no_second_reservation',
                'real_native_crash_after_create_before_journal_commit',
                'marker_reconciliation_unique_mapping','same_key_replay_original_notebook',
                'cross_school_shell_negative'))
            and type(lost.get('native_create_posts')) is int
            and lost['native_create_posts']==1
            and lost.get('client_received_post_ack') is False
            and type(lost.get('persisted_mapping_count')) is int
            and lost['persisted_mapping_count']==1
            and isinstance(lost.get('original_notebook_sha256'),str)
            and re.fullmatch(r'[a-f0-9]{64}',lost['original_notebook_sha256']) is not None
            and isinstance(report.get('notebook_id_sha256'),str)
            and re.fullmatch(r'[a-f0-9]{64}',report['notebook_id_sha256']) is not None)
    if at=='S1-AT15':
        return (report.get('at_id')=='S1-AT15'
            and report.get('status')=='PASS'
            and report.get('classification')=='REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED'
            and all(report.get('checks',{}).get(key)=='PASS' for key in (
                'school_a_access','school_a_denies_school_b_shell',
                'school_a_denies_school_b_materials',
                'school_a_denies_school_b_original_download',
                'forged_school_header_denied','csrf_rotated_on_switch',
                'school_b_access','school_b_denies_school_a_shell')))
    if at=='S1-AT11':
        return (report.get('status')=='PASS' and
                all(report.get(k)=='PASS' for k in
                    ('native_unlink','native_link_and_duplicate','original_hash_preserved')))
    return report.get('status')=='PASS' and report.get('at_id')==at


def verify_report_binding(at,record,source_sha,source_tree,identity_sha=None):
    if not isinstance(record,dict):
        raise IncompleteAT('Malformed executed case evidence: '+at)
    # C-owned probes that cannot emit this contract are NOT_RUN until adapted.
    if (record.get('source_commit')!=source_sha or
            record.get('source_tree')!=source_tree):
        raise IncompleteAT('Case source revision not independently attested: '+at)
    if identity_sha and record.get('runtime_identity_sha256')!=identity_sha:
        raise IncompleteAT('Wrong physical runtime/Gateway identity in case: '+at)
    if record.get('status') in ('NOT_RUN','PARTIAL','IMPLEMENTED_UNTESTED'):
        raise IncompleteAT('Partial evidence is not formal PASS: '+at)


def pinned_runtime_identity(config, source_sha, source_tree):
    flags=config.get('case_flags',{}).get('S1-AT01',{})
    path=flags.get('--runtime-identity')
    if not isinstance(path,str) or not Path(path).is_file():
        raise IncompleteAT('Pinned runtime identity evidence missing')
    manifest=read_json(Path(path))
    if (manifest.get('type')!='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'
            or manifest.get('source_commit')!=source_sha
            or manifest.get('source_tree')!=source_tree
            or set(manifest.get('services',{}))!={'a_db','on_db','native'}
            or manifest.get('gateway',{}).get('tls_verified') is not True):
        raise IncompleteAT('Runtime identity is not exact canonical dual-DB Gateway')
    return manifest,sha256_file(Path(path))


def run_regular(at,config,output,source_sha,source_tree):
    script,kind=CASES[at]
    evidence=output/(at+'.json')
    flags=config.get('case_flags',{}).get(at)
    if not isinstance(flags,dict):
        raise IncompleteAT('Missing fixed real scenario: '+at)
    flags=dict(flags)
    for key,value in (('--source-sha',source_sha),('--source-tree',source_tree)):
        if flags.get(key,value)!=value:
            raise IncompleteAT('Scenario attempts different tested revision')
    if kind in ('security','http') or at=='S1-AT04':
        flags.update({'--source-sha':source_sha,'--source-tree':source_tree})
    env={'VAULT_FIXED_SOURCE_SHA':source_sha,'VAULT_FIXED_SOURCE_TREE':source_tree}
    if kind=='journal':
        env['VAULT_JOURNAL_EVIDENCE']=str(evidence)
    detail=subprocess_case(script,flags,evidence,
        at_id=at if kind in ('security','http') else None,
        env_override=env,has_out=kind!='journal')
    result=read_json(evidence)
    if not test_result(at,result):
        raise IncompleteAT('Actual case result incomplete or wrong classification '+at)
    # Every case, including C-owned journal/graph, must emit source binding.
    # Provenance unknown is a blocked case, not an inferred success.
    verify_report_binding(at,result,source_sha,source_tree)
    if kind in ('security','http','generic','journal'):
        _,identity_sha=pinned_runtime_identity(config,source_sha,source_tree)
        verify_report_binding(at,result,source_sha,source_tree,identity_sha)
    return detail,sha256_file(evidence)

def run_admin_preflight(config, output, source_sha, source_tree):
    """Create actual synthetic material before cold capture; NEVER label this full AT01."""
    diagnostic=output/'S1-AT01-native.json'
    flags=config.get('case_flags',{}).get('S1-AT01')
    if not isinstance(flags,dict) or any(
            flags.get(k,expected)!=expected for k,expected in (
                ('--source-sha',source_sha),('--source-tree',source_tree))):
        raise IncompleteAT('Native Admin source identity missing or inconsistent')
    flags={**flags,'--source-sha':source_sha,'--source-tree':source_tree}
    step=subprocess_case(STAGE/'real_admin_journey.py',flags,diagnostic)
    result=read_json(diagnostic)
    required=('admin_login_and_private_session','surreal_durable_native_notebook_unique',
              'same_key_replay_and_body_conflict','native_pdf_upload_original_sha',
              'worker_extracted_synthetic_pdf','server_scoped_text_only_search',
              'original_pdf_hash_and_authorization','archive_non_destructive',
              'logout_session_revocation')
    if (result.get('result')!='PARTIAL_PASSED_WITH_UNRUN_GATES'
            or result.get('source_commit')!=source_sha
            or result.get('source_tree')!=source_tree
            or result.get('formal_s1_at01_15')!='NOT_RUN'
            or any(result.get('results',{}).get(name)!='PASS' for name in required)):
        raise IncompleteAT('Real native Admin preflight incomplete; never synthesize component PASS')
    return step,hashlib.sha256(diagnostic.read_bytes()).hexdigest()


def run_browser_before_cold_capture(config,output,source_sha,source_tree):
    """Run real Chromium while source Gateway/Worker remain alive."""
    flags=config.get('browser_flags')
    admin=config.get('case_flags',{}).get('S1-AT01')
    if not isinstance(flags,dict) or not isinstance(admin,dict):
        raise IncompleteAT('Real browser and Admin identity scenarios required')
    for key in ('--gateway','--context','--project','--runtime-identity'):
        if not flags.get(key) or flags[key]!=admin.get(key):
            raise IncompleteAT('Browser does not target same Admin runtime identity')
    if flags.get('--gateway-ca-file')!=admin.get('--ca-file'):
        raise IncompleteAT('Browser and Admin HTTPS CA mismatch')
    if any(flags.get(k,v)!=v for k,v in (
            ('--source-sha',source_sha),('--source-tree',source_tree))):
        raise IncompleteAT('Browser source revision differs')
    flags={**flags,'--source-sha':source_sha,'--source-tree':source_tree}
    path=output/'S1-AT01-browser.json'
    step=subprocess_case(STAGE/'browser_admin_journey.py',flags,path)
    result=read_json(path)
    _,identity_sha=pinned_runtime_identity(config,source_sha,source_tree)
    if (result.get('runtime_identity_sha256')!=identity_sha
            or result.get('at_id')!='S1-AT01-BROWSER'
            or result.get('source_commit')!=source_sha
            or result.get('source_tree')!=source_tree
            or result.get('status')!='PASS'):
        raise IncompleteAT('Real Chromium did not pass before source cold stop')
    return step,hashlib.sha256(path.read_bytes()).hexdigest()


def run_full_at01(config,output,source_sha,source_tree,case_reports,preflight):
    """Bind independent actual restart/restore/school tests and real Chromium probe."""
    if preflight is None:
        raise IncompleteAT('Missing actual native journey preflight')
    dependent=('S1-AT04','S1-AT05','S1-AT15')
    records={}
    for at in dependent:
        if case_reports.get(at,{}).get('status')!='PASS':
            raise IncompleteAT('AT01 prerequisite was not executed and passed: '+at)
        record=read_json(output/(at+'.json'))
        if record.get('at_id')!=at or record.get('status')!='PASS':
            raise IncompleteAT('AT01 prerequisite evidence not a real PASS: '+at)
        if at in ('S1-AT04','S1-AT05','S1-AT15') and (
                record.get('source_commit')!=source_sha
                or record.get('source_tree')!=source_tree):
            raise IncompleteAT('AT01 dependent evidence refers to different source revision')
        records[at]=record
    at15=records['S1-AT15']
    runtime,identity_sha=pinned_runtime_identity(config,source_sha,source_tree)
    if (not test_result('S1-AT15',at15)
            or at15.get('runtime_identity_sha256')!=identity_sha
            or not isinstance(at15.get('gateway_tls_peer_sha256'),str)
            or not re.fullmatch(r'[a-f0-9]{64}',at15['gateway_tls_peer_sha256'])
            or at15['gateway_tls_peer_sha256']!=runtime.get('gateway',{}).get('tls_peer_sha256')):
        raise IncompleteAT('AT15 executed same-Gateway two-school IDOR evidence invalid')
    raw=read_json(output/'S1-AT01-native.json')
    ui_path=output/'S1-AT01-browser.json'
    if not ui_path.is_file():
        raise IncompleteAT('Real Chromium evidence missing before source cold capture')
    ui=read_json(ui_path)
    ui_checks=('real_browser_login_and_server_school','real_browser_shell_create',
        'real_browser_pdf_upload_and_worker_status','real_browser_scoped_text_search',
        'real_browser_original_pdf_download','real_browser_archive',
        'real_browser_logout_revocation','no_uncaught_browser_script_errors')
    if (ui.get('status')!='PASS' or ui.get('at_id')!='S1-AT01-BROWSER'
            or ui.get('source_commit')!=source_sha
            or ui.get('source_tree')!=source_tree
            or ui.get('runtime_identity_sha256')!=identity_sha
            or any(ui.get('checks',{}).get(k)!='PASS' for k in ui_checks)):
        raise IncompleteAT('Actual browser Admin journey missing or wrong revision')
    results={**raw['results'],
             'gateway_restart_persistence':'PASS',
             'same_gateway_two_school_idor_negative':'PASS',
             'independent_backup_restore':'PASS',
             'browser_admin_journey':'PASS'}
    record={'at_id':'S1-AT01','status':'PASS',
        'source_commit':source_sha,'source_tree':source_tree,
        'result':'FULL_NATIVE_UI_HTTP_JOURNEY_PASS',
        'formal_s1_at01_15':'S1-AT01_CANDIDATE_EXECUTED',
        'results':results,'evidence_dependencies':{
           'real_native_http_sha256':hashlib.sha256(
                (output/'S1-AT01-native.json').read_bytes()).hexdigest(),
           'real_browser_sha256':hashlib.sha256(ui_path.read_bytes()).hexdigest(),
           **{at:hashlib.sha256((output/(at+'.json')).read_bytes()).hexdigest()
              for at in dependent}},
        'utc':timestamp(),'owner_UAT':'NOT_RUN','R01':'NOT_APPROVED'}
    if not test_result('S1-AT01',record):
        raise IncompleteAT('AT01 full candidate does not satisfy mandatory independent gates')
    evidence=output/'S1-AT01.json'
    evidence.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return {'real_http_preflight':preflight[0],
            'browser_evidence_sha256':hashlib.sha256(ui_path.read_bytes()).hexdigest(),
            'independent_cases':list(dependent)},hashlib.sha256(evidence.read_bytes()).hexdigest()


def run_restore(config,output,source_sha,source_tree):
    capture=STAGE/'restore/cold_capture.py'
    restore=STAGE/'restore/isolated_restore.py'
    start=STAGE/'restore/start_verified_native.py'
    steps=config.get('restore_flags')
    if not isinstance(steps,dict):raise IncompleteAT('Restore scenario absent')
    bundle=output/'synthetic-a-cold.tar'
    first=subprocess_case(capture,steps['capture'],bundle,has_out=True)
    if not bundle.is_file():raise IncompleteAT('Cold stopped Volume bundle not created')
    restore_flags={**steps['restore'],'--bundle':str(bundle)}
    second=subprocess_case(restore,restore_flags,output/'ignored.json',has_out=False)
    native_flags={**steps['native'],'--bundle':str(bundle)}
    third=subprocess_case(start,native_flags,output/'ignored-native.json',has_out=False)
    workdir=Path(restore_flags['--workdir'])
    final=read_json(workdir/'native-readback-evidence.json')
    native=final.get('native_readback',{})
    _,expected_runtime_sha=pinned_runtime_identity(config,source_sha,source_tree)
    if (final.get('source_runtime_identity_sha256')!=expected_runtime_sha
            or final.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
            or final.get('source_commit')!=source_sha
            or final.get('source_tree')!=source_tree
            or final.get('target_project')!=restore_flags.get('--project')
            or final.get('db_inventories_equal') is not True
            or final.get('independent_target_verified') is not True
            or final.get('restored_volume_count')!=3
            or set(final.get('restored_services',[]))!={'a_db','on_db','native'}
            or final.get('native_owner_identity_matches_before_after') is not True
            or native.get('text_only_patch_attested') is not True
            or not isinstance(native.get('source_owner_count'),int)
            or native['source_owner_count']<1
            or native.get('verified_original_count')!=native['source_owner_count']
            or not native.get('owned_source_graph_hash')
            or not isinstance(native.get('rights_retention_initial_version_sha256'),str)
            or re.fullmatch(r'[a-f0-9]{64}',
                native['rights_retention_initial_version_sha256']) is None
            or native.get('rights_retention_initial_version_count')!=native['source_owner_count']):
        raise IncompleteAT('Independent restore and source-owner verification not proven')
    target=output/'S1-AT05.json'
    target.write_text(json.dumps({'at_id':'S1-AT05','status':'PASS',
        'source_commit':final.get('source_commit'),
        'source_tree':final.get('source_tree'),
        'cold_bundle_sha256':sha256_file(bundle),
        'restore_evidence_sha256':hashlib.sha256((workdir/'native-readback-evidence.json').read_bytes()).hexdigest(),
        'target_project':final.get('target_project'),'utc':timestamp()},indent=2)+'\n')
    return {'steps':[first,second,third]},hashlib.sha256(target.read_bytes()).hexdigest()


def validate_restore_rights(config,output,source_sha,source_tree):
    workdir=Path(config['restore_flags']['restore']['--workdir'])
    result=read_json(workdir/'native-readback-evidence.json')
    native=result.get('native_readback',{})
    if result.get('source_commit')!=source_sha or result.get('source_tree')!=source_tree:
        raise IncompleteAT('Post-restore rights/version/original data not verified')
    _,expected_runtime_sha=pinned_runtime_identity(config,source_sha,source_tree)
    if (result.get('source_runtime_identity_sha256')!=expected_runtime_sha
            or result.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
            or result.get('source_commit')!=source_sha
            or result.get('source_tree')!=source_tree
            or result.get('native_owner_identity_matches_before_after') is not True
            or result.get('db_inventories_equal') is not True
            or result.get('independent_target_verified') is not True
            or result.get('restored_volume_count')!=3
            or set(result.get('restored_services',[]))!={'a_db','on_db','native'}
            or not isinstance(native.get('source_owner_count'),int)
            or native['source_owner_count']<1
            or native.get('verified_original_count')!=native['source_owner_count']
            or not native.get('owned_source_graph_hash')
            or not isinstance(native.get('rights_retention_initial_version_sha256'),str)
            or re.fullmatch(r'[a-f0-9]{64}',
                native['rights_retention_initial_version_sha256']) is None
            or native.get('rights_retention_initial_version_count')!=native['source_owner_count']):
        raise IncompleteAT('Post-restore rights/version/original data not verified')
    record=output/'S1-AT12.json'
    record.write_text(json.dumps({'at_id':'S1-AT12','status':'PASS',
        'source_commit':source_sha,'source_tree':source_tree,
        'rights_retention_initial_version_original_checked_by_native_readback':True,
        'utc':timestamp()},indent=2)+'\n')
    return ({'depends_on':'S1-AT05 verified Native owner/readback'},
            hashlib.sha256(record.read_bytes()).hexdigest())


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',required=True,type=Path)
    p.add_argument('--source-sha',required=True);p.add_argument('--source-tree',required=True)
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--selected',default=','.join(RUN_ORDER))
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Owner no-testing gate must be lifted and isolated synthetic runtime explicitly confirmed')
    verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.output_dir)
    selected=args.selected.split(',')
    if len(selected)!=len(set(selected)) or any(at not in RUN_ORDER for at in selected):
        p.error('Unknown/duplicate formal Stage1 AT IDs')
    config=read_json(args.config)
    if args.output_dir.exists():p.error('Output directory must be new; never overwrite evidence')
    args.output_dir.mkdir(parents=True)
    verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.output_dir)
    report={'classification':'STAGE1_AT_CANDIDATE_NOT_OWNER_ACCEPTANCE',
            'source_sha':args.source_sha,'source_tree':args.source_tree,
            'created_utc':timestamp(),'selected':selected,
            'cases':{at:{'status':'NOT_RUN'} for at in RUN_ORDER},
            'aggregate':'NOT_RUN','tests_executed':0,'owner_UAT':'NOT_RUN','R01':'NOT_APPROVED'}
    try:
        preflight=None
        if 'S1-AT01' in selected:
            report['cases']['S1-AT01']={'status':'RUNNING_NATIVE_PREFLIGHT',
                'start_utc':timestamp()}
            try:
                preflight=run_admin_preflight(config,args.output_dir,args.source_sha,args.source_tree)
                report['cases']['S1-AT01']['status']='PENDING_INDEPENDENT_GATES'
            except Exception as exc:
                report['cases']['S1-AT01']={'status':'FAIL',
                    'error_type':type(exc).__name__,'end_utc':timestamp()}
                raise
        browser_preflight=None
        for at in RUN_ORDER:
            if at not in selected:continue
            verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.output_dir)
            report['cases'][at]={'status':'RUNNING','start_utc':timestamp()}
            try:
                if at=='S1-AT01':
                    steps,digest=run_full_at01(config,args.output_dir,
                        args.source_sha,args.source_tree,report['cases'],preflight)
                elif at in CASES:
                    steps,digest=run_regular(at,config,args.output_dir,args.source_sha,args.source_tree)
                elif at=='S1-AT05':
                    if 'S1-AT01' in selected:
                        if (report['cases']['S1-AT04']['status']!='PASS'
                                or report['cases']['S1-AT15']['status']!='PASS'):
                            raise IncompleteAT('Chromium must follow real restart and school negatives')
                        browser_preflight=run_browser_before_cold_capture(
                            config,args.output_dir,args.source_sha,args.source_tree)
                    steps,digest=run_restore(config,args.output_dir,args.source_sha,args.source_tree)
                elif at=='S1-AT12':
                    steps,digest=validate_restore_rights(config,args.output_dir,args.source_sha,args.source_tree)
                elif at=='S1-AT13':
                    mandatory=set(RUN_ORDER)-{'S1-AT13'}
                    if set(selected)!=set(RUN_ORDER) or any(
                            report['cases'][a]['status']!='PASS' for a in mandatory):
                        raise IncompleteAT('AT13 requires all prior 14 actually PASS')
                    # Actual local regression is an independent command, not
                    # the current runner's own self-reported PASS tally.
                    regression=AT_DIR/'regression.py'
                    reg_out=args.output_dir/'regression.json'
                    params={'--repo-root':str(ROOT),'--source-sha':args.source_sha,
                            '--source-tree':args.source_tree}
                    regression_step=subprocess_case(regression,params,reg_out)
                    r=read_json(reg_out)
                    if (r.get('status')!='PASS' or r.get('tests_executed',0)<1
                            or r.get('source_sha')!=args.source_sha
                            or r.get('source_tree')!=args.source_tree
                            or r.get('exit_code')!=0):
                        raise IncompleteAT('Actual regression missing')
                    mandatory=set(RUN_ORDER)-{'S1-AT13'}
                    # S1-AT13 is a *full-scope* regression/release-scope check.
                    # Never let a selected subset or NOT_RUN gate satisfy it.
                    if set(selected)!=set(RUN_ORDER) or any(
                            report['cases'][a]['status']!='PASS' for a in mandatory):
                        raise IncompleteAT('AT13 requires all other 14 real AT cases PASS on same SHA')
                    verified_restore=Path(config['restore_flags']['restore']['--workdir'])/'native-readback-evidence.json'
                    if Path(config['case_flags'][at]['--restore-evidence']).resolve()!=verified_restore.resolve():
                        raise IncompleteAT('AT13 restore evidence path differs from AT05')
                    _,runtime_hash=pinned_runtime_identity(config,args.source_sha,args.source_tree)
                    aggregate={'source_sha':args.source_sha,'source_tree':args.source_tree,
                               'runtime_identity_sha256':runtime_hash,
                               'restore_evidence_sha256':sha256_file(verified_restore),
                               'case_evidence_sha256':{case:report['cases'][case]['evidence_sha256']
                                    for case in sorted(mandatory)},
                               'aggregate':'ALL_SELECTED_PASS',
                               'covered_at_ids':sorted(mandatory),
                               'tests_executed':r['tests_executed']}
                    summary=args.output_dir/'regression-summary.json'
                    summary.write_text(json.dumps(aggregate)+'\n')
                    options=config['case_flags'][at]
                    options={**options,'--source-sha':args.source_sha,
                             '--source-tree':args.source_tree,
                             '--repo-root':str(ROOT),'--regression-evidence':str(summary)}
                    steps=subprocess_case(AT_DIR/'release_manifest.py',options,args.output_dir/(at+'.json'))
                    detail=read_json(args.output_dir/(at+'.json'))
                    verify_report_binding(at,detail,args.source_sha,args.source_tree)
                    if detail.get('status')!='PASS':
                        raise IncompleteAT('A-only source manifest release gate failed')
                    steps={'regression':regression_step,'release':steps}
                    digest=hashlib.sha256((args.output_dir/(at+'.json')).read_bytes()).hexdigest()
                else:raise IncompleteAT('AT has no executable source')
                verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.output_dir)
                report['cases'][at]={'status':'PASS','steps':steps,
                    'evidence_sha256':digest,'end_utc':timestamp()}
                report['tests_executed']+=1
            except Exception as exc:
                report['cases'][at]={'status':'FAIL','error_type':type(exc).__name__,
                    'failure_detail':getattr(exc,'detail',None),
                    'end_utc':timestamp()}
                raise
        verify_clean_source(ROOT,args.source_sha,args.source_tree,output=args.output_dir)
        all_pass=all(report['cases'][at]['status']=='PASS' for at in selected)
        full_coverage=(len(selected)==len(RUN_ORDER) and set(selected)==set(RUN_ORDER))
        # A successful subset is diagnostic evidence, not the full 15-AT gate.
        report['aggregate']=(
            'ALL_15_LOCAL_CASES_PASS_REVIEW_PENDING' if all_pass and full_coverage
            else 'SELECTED_CASES_PASS_NOT_FULL_STAGE' if all_pass
            else 'FAIL')
        report['formal_acceptance']='REVIEW_PENDING' if all_pass and full_coverage else 'NOT_RUN'
    except Exception:
        report['aggregate']='FAIL'
        raise
    finally:
        report['finished_utc']=timestamp()
        report['source_integrity_final']=('PASS' if report.get('aggregate') in (
            'ALL_15_LOCAL_CASES_PASS_REVIEW_PENDING','SELECTED_CASES_PASS_NOT_FULL_STAGE')
            else 'NOT_CONFIRMED')
        (args.output_dir/'stage1-at-run.json').write_text(
            json.dumps(report,sort_keys=True,indent=2)+'\n')
    # Selected-subset success is useful diagnostic evidence, never a successful
    # formal acceptance CLI exit. Exit 2 makes missing ATs machine-visible.
    raise SystemExit(0 if report['aggregate']=='ALL_15_LOCAL_CASES_PASS_REVIEW_PENDING'
                     else 2 if report['aggregate']=='SELECTED_CASES_PASS_NOT_FULL_STAGE'
                     else 1)


if __name__=='__main__':main()
