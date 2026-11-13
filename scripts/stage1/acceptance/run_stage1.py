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

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/'scripts/stage1'
AT_DIR=STAGE/'acceptance'
RUN_ORDER=('S1-AT01','S1-AT02','S1-AT03','S1-AT04','S1-AT06',
           'S1-AT07','S1-AT08','S1-AT09','S1-AT10','S1-AT11',
           'S1-AT14','S1-AT15','S1-AT05','S1-AT12','S1-AT13')
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
    if not script.resolve().is_relative_to(STAGE.resolve()) or not script.is_file():
        raise IncompleteAT('Unrecognised or missing real Stage1 case implementation')
    cmd=[sys.executable,str(script)]
    if at_id:cmd.extend(['--at-id',at_id])
    cmd.extend(pairs(flags))
    env=os.environ.copy()
    if env_override:env.update(env_override)
    if has_out:cmd.extend(['--out',str(destination)])
    proc=subprocess.run(cmd,cwd=str(ROOT),env=env,capture_output=True,
                        text=True,timeout=1500)
    detail={'command_path':str(script.relative_to(ROOT)),
            'command_arguments_redacted':sorted(flags),
            'exit_code':proc.returncode,
            'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest(),
            'stderr_sha256':hashlib.sha256(proc.stderr.encode()).hexdigest(),
            'started_output_utc':timestamp()}
    if proc.returncode!=0:raise IncompleteAT('Case failed; exit code '+str(proc.returncode))
    return detail


def read_json(path):
    if not path.is_file() or path.stat().st_size>4<<20:
        raise IncompleteAT('Missing or unbounded case evidence file')
    return json.loads(path.read_text(encoding='utf-8'))


def test_result(at,report):
    if at=='S1-AT01':
        required=('admin_login_and_private_session','surreal_durable_native_notebook_unique',
            'same_key_replay_and_body_conflict','native_pdf_upload_original_sha',
            'worker_extracted_synthetic_pdf','server_scoped_text_only_search',
            'original_pdf_hash_and_authorization','archive_non_destructive','logout_session_revocation')
        return (report.get('result')=='PARTIAL_PASSED_WITH_UNRUN_GATES' and
                all(report.get('results',{}).get(key)=='PASS' for key in required))
    if at=='S1-AT06':
        r=report.get('results',{})
        return (report.get('status')=='PASS' and report.get('native_gate')=='PASS'
            and all(r.get(x)=='PASS' for x in (
                'real_surrealdb_unique_operation_reservation','different_body_conflict',
                'same_key_concurrent_no_second_reservation',
                'real_native_crash_after_create_before_journal_commit',
                'marker_reconciliation_unique_mapping','same_key_replay_original_notebook'))
            and isinstance(r.get('real_native_lost_ack_tcp'),dict)
            and r['real_native_lost_ack_tcp'].get('native_create_posts')==1
            and r['real_native_lost_ack_tcp'].get('client_received_post_ack') is False)
    if at=='S1-AT11':
        return (report.get('status')=='PASS' and
                all(report.get(k)=='PASS' for k in
                    ('native_unlink','native_link_and_duplicate','original_hash_preserved')))
    return report.get('status')=='PASS' and report.get('at_id')==at


def run_regular(at,config,output):
    script,kind=CASES[at]
    evidence=output/(at+'.json')
    opts=config.get('case_flags',{}).get(at)
    env={}
    if kind=='journal':
        env['VAULT_JOURNAL_EVIDENCE']=str(evidence)
    detail=subprocess_case(script,opts,evidence,
        at_id=at if kind in ('security','http') else None,
        env_override=env,has_out=kind!='journal')
    result=read_json(evidence)
    if not test_result(at,result):
        raise IncompleteAT('Real case result incomplete or wrong classification '+at)
    return detail,hashlib.sha256(evidence.read_bytes()).hexdigest()


def run_restore(config,output):
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
    if (final.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
            or final.get('db_inventories_equal') is not True
            or final.get('native_readback',{}).get('text_only_patch_attested') is not True):
        raise IncompleteAT('Independent restore and source-owner verification not proven')
    target=output/'S1-AT05.json'
    target.write_text(json.dumps({'at_id':'S1-AT05','status':'PASS',
        'source_commit':final.get('source_commit'),
        'source_tree':final.get('source_tree'),
        'cold_bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
        'restore_evidence_sha256':hashlib.sha256((workdir/'native-readback-evidence.json').read_bytes()).hexdigest(),
        'target_project':final.get('target_project'),'utc':timestamp()},indent=2)+'\n')
    return {'steps':[first,second,third]},hashlib.sha256(target.read_bytes()).hexdigest()


def validate_restore_rights(config,output):
    workdir=Path(config['restore_flags']['restore']['--workdir'])
    result=read_json(workdir/'native-readback-evidence.json')
    native=result.get('native_readback',{})
    if (result.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
            or not isinstance(native.get('source_owner_count'),int)
            or native['source_owner_count']<1
            or native.get('verified_original_count')!=native['source_owner_count']
            or not native.get('owned_source_graph_hash')):
        raise IncompleteAT('Post-restore rights/version/original data not verified')
    record=output/'S1-AT12.json'
    record.write_text(json.dumps({'at_id':'S1-AT12','status':'PASS',
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
    if (git_id('HEAD'),git_id('HEAD^{tree}'))!=(args.source_sha,args.source_tree):
        p.error('Exact tested Git source SHA/tree mismatch')
    selected=args.selected.split(',')
    if len(selected)!=len(set(selected)) or any(at not in RUN_ORDER for at in selected):
        p.error('Unknown/duplicate formal Stage1 AT IDs')
    config=read_json(args.config)
    if args.output_dir.exists():p.error('Output directory must be new; never overwrite evidence')
    args.output_dir.mkdir(parents=True)
    report={'classification':'STAGE1_AT_CANDIDATE_NOT_OWNER_ACCEPTANCE',
            'source_sha':args.source_sha,'source_tree':args.source_tree,
            'created_utc':timestamp(),'selected':selected,
            'cases':{at:{'status':'NOT_RUN'} for at in RUN_ORDER},
            'aggregate':'NOT_RUN','tests_executed':0,'owner_UAT':'NOT_RUN','R01':'NOT_APPROVED'}
    try:
        for at in RUN_ORDER:
            if at not in selected:continue
            report['cases'][at]={'status':'RUNNING','start_utc':timestamp()}
            try:
                if at in CASES:
                    steps,digest=run_regular(at,config,args.output_dir)
                elif at=='S1-AT05':
                    steps,digest=run_restore(config,args.output_dir)
                elif at=='S1-AT12':
                    steps,digest=validate_restore_rights(config,args.output_dir)
                elif at=='S1-AT13':
                    # Actual local regression is an independent command, not
                    # the current runner's own self-reported PASS tally.
                    regression=AT_DIR/'regression.py'
                    reg_out=args.output_dir/'regression.json'
                    params={'--repo-root':str(ROOT),'--source-sha':args.source_sha,
                            '--source-tree':args.source_tree}
                    regression_step=subprocess_case(regression,params,reg_out)
                    r=read_json(reg_out)
                    if r.get('status')!='PASS' or r.get('tests_executed',0)<1:
                        raise IncompleteAT('Actual regression missing')
                    prior={a:v for a,v in report['cases'].items() if a!=at}
                    aggregate={'source_sha':args.source_sha,'source_tree':args.source_tree,
                               'aggregate':'ALL_SELECTED_PASS' if all(
                                    v['status']=='PASS' for a,v in prior.items() if a in selected)
                               else 'FAIL',
                               'tests_executed':r['tests_executed']}
                    summary=args.output_dir/'regression-summary.json'
                    summary.write_text(json.dumps(aggregate)+'\n')
                    options=config['case_flags'][at]
                    options={**options,'--source-sha':args.source_sha,
                             '--source-tree':args.source_tree,
                             '--repo-root':str(ROOT),'--regression-evidence':str(summary)}
                    steps=subprocess_case(AT_DIR/'release_manifest.py',options,args.output_dir/(at+'.json'))
                    detail=read_json(args.output_dir/(at+'.json'))
                    if detail.get('status')!='PASS':
                        raise IncompleteAT('A-only source manifest release gate failed')
                    steps={'regression':regression_step,'release':steps}
                    digest=hashlib.sha256((args.output_dir/(at+'.json')).read_bytes()).hexdigest()
                else:raise IncompleteAT('AT has no executable source')
                report['cases'][at]={'status':'PASS','steps':steps,
                    'evidence_sha256':digest,'end_utc':timestamp()}
                report['tests_executed']+=1
            except Exception as exc:
                report['cases'][at]={'status':'FAIL','error_type':type(exc).__name__,
                    'end_utc':timestamp()}
                raise
        report['aggregate']='ALL_SELECTED_PASS' if all(
            report['cases'][at]['status']=='PASS' for at in selected) else 'FAIL'
    except Exception:
        report['aggregate']='FAIL'
        raise
    finally:
        report['finished_utc']=timestamp()
        (args.output_dir/'stage1-at-run.json').write_text(
            json.dumps(report,sort_keys=True,indent=2)+'\n')
    raise SystemExit(0 if report['aggregate']=='ALL_SELECTED_PASS' else 1)


if __name__=='__main__':main()
