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
    result={'at_id':'S1-AT13','status':'NOT_RUN',
            'start_utc':datetime.now(timezone.utc).isoformat()}
    try:
        head=git(args.repo_root,'rev-parse','HEAD')
        tree=git(args.repo_root,'rev-parse','HEAD^{tree}')
        if (head,tree)!=(args.source_sha,args.source_tree):
            raise RuntimeError('Source identity mismatch')
        changed=git(args.repo_root,'diff','--name-only',
                    args.base_sha+'..'+args.source_sha).splitlines()
        if not changed or any(not path.startswith(ALLOWED) for path in changed):
            raise RuntimeError('Non-A source/Workflow/Governance changes found')
        runtime=json.loads(args.runtime_identity.read_text())
        if (runtime.get('source_commit')!=head or runtime.get('source_tree')!=tree or
            runtime.get('native_source_commit')!='5e285b7a2e435895c4ee99ad7e4b8d2af64c3239' or
            not runtime.get('on_patch_sha256')):
            raise RuntimeError('Pinned runtime/image/patch provenance missing')
        for identity in runtime.get('services',{}).values():
            if not re.fullmatch(r'sha256:[a-f0-9]{64}',str(identity.get('image_id',''))):
                raise RuntimeError('Mutable or unverified runtime image')
        restored=json.loads(args.restore_evidence.read_text())
        regression=json.loads(args.regression_evidence.read_text())
        if (restored.get('classification')!='ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS'
                or restored.get('source_commit')!=head or
                restored.get('native_readback',{}).get('text_only_patch_attested') is not True):
            raise RuntimeError('Required independent restore source/result absent')
        if (regression.get('source_sha')!=head or regression.get('source_tree')!=tree
                or regression.get('aggregate')!='ALL_SELECTED_PASS'
                or regression.get('tests_executed',0)<1):
            raise RuntimeError('Regressions not actually executed at exact SHA')
        result.update({'status':'PASS','changed_count':len(changed),
                       'changed_paths_sha256':hashlib.sha256('\n'.join(changed).encode()).hexdigest(),
                       'runtime_identity_sha256':hashlib.sha256(args.runtime_identity.read_bytes()).hexdigest(),
                       'restore_evidence_sha256':hashlib.sha256(args.restore_evidence.read_bytes()).hexdigest()})
    except Exception as error:
        result.update({'status':'FAIL','error_type':type(error).__name__})
        raise
    finally:
        result['end_utc']=datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
