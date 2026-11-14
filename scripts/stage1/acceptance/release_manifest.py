#!/usr/bin/env python3
"""S1-AT13 A-only source/runtime freeze and regression/restore evidence gate.

IMPLEMENTED_UNTESTED. Read-only git/runtime/evidence check, never changes
formal Stage Registry or Owner decisions. Reviewer still determines PASS.
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

if __package__:
    from .evidence_inventory import verify_clean_source
else:
    from evidence_inventory import verify_clean_source

if __package__:
    from .run_stage1 import verify_browser_evidence
else:
    from run_stage1 import verify_browser_evidence

RELEASE_STATES=('SOURCE_IMPLEMENTED','NON_NATIVE_TESTS_PASSED',
 'NATIVE_RUNTIME_PASSED','INDEPENDENT_RESTORE_PASSED','S1_AT01_15_PASSED',
 'INDEPENDENT_REVIEW_PASSED','OWNER_UAT_PASSED','R01_APPROVED',
 'PR14_MERGED','STAGE2_HANDOFF_READY')

ALLOWED=('apps/a-vault/','scripts/stage1/','tests/stage1/',
         'docs/stage1/evidence/','docs/stage1/uat/')


def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,
        capture_output=True,text=True,timeout=20).stdout.strip()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',required=True,type=Path)
    p.add_argument('--source-sha',required=True)
    p.add_argument('--source-tree',required=True)
    p.add_argument('--base-sha',required=True)
    p.add_argument('--runtime-identity',required=True,type=Path)
    p.add_argument('--restore-evidence',required=True,type=Path)
    p.add_argument('--regression-evidence',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Only isolated synthetic release-candidate audit')
    output=args.out.absolute()
    if output.exists():p.error('Evidence output must be new')
    verify_clean_source(args.repo_root,args.source_sha,args.source_tree,output=output)
    result={'at_id':'S1-AT13','status':'NOT_RUN',
            'start_utc':datetime.now(timezone.utc).isoformat()}
    try:
        head=git(args.repo_root,'rev-parse','HEAD')
        tree=git(args.repo_root,'rev-parse','HEAD^{tree}')
        verify_clean_source(args.repo_root,args.source_sha,args.source_tree,output=output)
        changed=git(args.repo_root,'diff','--name-only',
                    args.base_sha+'..'+args.source_sha).splitlines()
        if not changed or any(not path.startswith(ALLOWED) for path in changed):
            raise RuntimeError('Non-A source/Workflow/Governance changes found')
        if args.runtime_identity.is_symlink() or args.runtime_identity.stat().st_size>1<<20:
            raise RuntimeError('Unbounded or symlinked runtime manifest')
        runtime=json.loads(args.runtime_identity.read_text())
        if (runtime.get('source_commit')!=head or runtime.get('source_tree')!=tree or
            runtime.get('native_source_commit')!='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239' or
            not runtime.get('on_patch_sha256')
            or runtime.get('type')!='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'
            or set(runtime.get('services',{}))!={'a_db','on_db','native'}
            or runtime.get('dual_rpc',{}).get('on_viewer_read_only') is not True
            or runtime.get('gateway',{}).get('tls_verified') is not True):
            raise RuntimeError('Pinned runtime/image/patch provenance missing')
        for identity in runtime.get('services',{}).values():
            if not re.fullmatch(r'sha256:[a-f0-9]{64}',str(identity.get('image_id',''))):
                raise RuntimeError('Mutable or unverified runtime image')
        if (args.restore_evidence.is_symlink() or args.regression_evidence.is_symlink()
                or not args.restore_evidence.is_file() or not args.regression_evidence.is_file()
                or args.restore_evidence.stat().st_size>4<<20
                or args.regression_evidence.stat().st_size>4<<20):
            raise RuntimeError('Missing or unbounded restore/regression evidence')
        restored=json.loads(args.restore_evidence.read_text())
        regression=json.loads(args.regression_evidence.read_text())
        if (restored.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
                or restored.get('source_commit')!=head
                or restored.get('source_tree')!=tree
                or restored.get('source_runtime_identity_sha256')!=hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest()
                or restored.get('independent_target_verified') is not True
                or restored.get('db_inventories_equal') is not True
                or restored.get('restored_volume_count')!=3
                or set(restored.get('restored_services',[]))!={'a_db','on_db','native'}
                or restored.get('native_readback',{}).get('text_only_patch_attested') is not True):
            raise RuntimeError('Required independent restore source/result absent')
        if (regression.get('source_sha')!=head or regression.get('source_tree')!=tree
                or regression.get('aggregate')!='ALL_SELECTED_PASS'
                or regression.get('tests_executed',0)<1
                or set(regression.get('covered_at_ids',[]))==set()
                or set(regression.get('covered_at_ids',[]))!={f'S1-AT{x:02}' for x in range(1,16)}-{'S1-AT13'}
                or regression.get('runtime_identity_sha256')!=hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest()
                or regression.get('restore_evidence_sha256')!=hashlib.sha256(args.restore_evidence.read_bytes()).hexdigest()
                or not isinstance(regression.get('case_evidence_sha256'),dict)
                or set(regression['case_evidence_sha256'])!=set(regression['covered_at_ids'])
                or any(re.fullmatch(r'[a-f0-9]{64}',str(x)) is None for x in regression['case_evidence_sha256'].values())):
            raise RuntimeError('Regressions not actually executed at exact SHA')
        # An arbitrary list of case hashes is not evidence. Verify the exact
        # 14 case artifacts next to the runner-created regression summary.
        folder=args.regression_evidence.parent.resolve()
        if folder.is_relative_to(args.repo_root.resolve()):
            raise RuntimeError('Release case evidence cannot contaminate source')
        for at,digest in regression['case_evidence_sha256'].items():
            path=folder/(at+'.json')
            if path.is_symlink() or not path.is_file() or path.stat().st_size>4<<20:
                raise RuntimeError('Required executed case file is missing: '+at)
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:
                raise RuntimeError('Stale or overwritten case evidence: '+at)
            evidence=json.loads(raw)
            if (evidence.get('at_id')!=at or evidence.get('status')!='PASS'
                    or evidence.get('source_commit')!=head
                    or evidence.get('source_tree')!=tree):
                raise RuntimeError('Case not executed at fixed source: '+at)
            if at=='S1-AT01':
                if (evidence.get('result')!='FULL_NATIVE_UI_HTTP_JOURNEY_PASS'
                        or evidence.get('formal_s1_at01_15')!='S1-AT01_CANDIDATE_EXECUTED'):
                    raise RuntimeError('AT01 was not the complete real UI/Native journey')
                deps=evidence.get('evidence_dependencies',{})
                names={'real_native_http_sha256':'S1-AT01-native.json',
                       'real_browser_sha256':'S1-AT01-browser.json',
                       **{x:x+'.json' for x in ('S1-AT04','S1-AT05','S1-AT15')}}
                if not isinstance(deps,dict) or set(deps)!=set(names):
                    raise RuntimeError('AT01 missing independent dependency set')
                for name,file in names.items():
                    artifact=folder/file
                    if (artifact.is_symlink() or not artifact.is_file()
                            or artifact.stat().st_size>4<<20
                            or hashlib.sha256(artifact.read_bytes()).hexdigest()!=deps[name]):
                        raise RuntimeError('AT01 dependency hash does not match actual artifact')
                at15=json.loads((folder/'S1-AT15.json').read_bytes())
                browser=json.loads((folder/names['real_browser_sha256']).read_bytes())
                identity_sha=hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest()
                required_school_checks=(
                    'school_a_access','school_a_denies_school_b_shell',
                    'school_a_denies_school_b_materials',
                    'school_a_denies_school_b_original_download',
                    'forged_school_header_denied','csrf_rotated_on_switch',
                    'school_b_access','school_b_denies_school_a_shell')
                if (at15.get('at_id')!='S1-AT15'
                        or at15.get('classification')!='REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED'
                        or at15.get('status')!='PASS'
                        or at15.get('source_commit')!=head
                        or at15.get('source_tree')!=tree
                        or at15.get('runtime_identity_sha256')!=identity_sha
                        or not re.fullmatch(r'[a-f0-9]{64}',str(at15.get('gateway_tls_peer_sha256','')))
                        or at15['gateway_tls_peer_sha256']!=runtime.get('gateway',{}).get('tls_peer_sha256')
                        or any(at15.get('checks',{}).get(key)!='PASS' for key in required_school_checks)
                        ):
                    raise RuntimeError('Executed AT15 school IDOR runtime evidence absent')
                try:
                    verify_browser_evidence(browser,head,tree,identity_sha,runtime['gateway'])
                except (ValueError,TypeError,RuntimeError) as error:
                    raise RuntimeError('Full supported-engine Browser evidence absent') from error
            if at=='S1-AT05':
                if evidence.get('restore_evidence_sha256')!=hashlib.sha256(args.restore_evidence.read_bytes()).hexdigest():
                    raise RuntimeError('AT05 did not cite this actual independent restore')
        verify_clean_source(args.repo_root,args.source_sha,args.source_tree,output=output)
        # Distinct gates are never inferred from one another or silently signed.
        gate_states={name:'NOT_RUN' for name in RELEASE_STATES}
        gate_states['SOURCE_IMPLEMENTED']='CANDIDATE_REQUIRES_REVIEW'
        gate_states['NON_NATIVE_TESTS_PASSED']='LOCAL_EXECUTION_RECORDED_UNREVIEWED'
        result.update({'status':'PASS','release_gate_states':gate_states,
                       'classification':'S1_AT13_SOURCE_REGRESSION_CANDIDATE_NOT_R01',
                       'source_commit':head,'source_tree':tree,
                       'changed_count':len(changed),
                       'changed_paths_sha256':hashlib.sha256('\n'.join(changed).encode()).hexdigest(),
                       'runtime_identity_sha256':hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest(),
                       'restore_evidence_sha256':hashlib.sha256(args.restore_evidence.read_bytes()).hexdigest()})
    except Exception as error:
        result.update({'status':'FAIL','error_type':type(error).__name__})
        raise
    finally:
        result['end_utc']=datetime.now(timezone.utc).isoformat()
        with output.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(result,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
