#!/usr/bin/env python3
"""WP09 local code regression executor at an immutable Git SHA. IMPLEMENTED_UNTESTED.

Do not invoke until Owner's no-testing gate is lifted. This is a real pytest
execution, not a hardcoded PASS count. No shell, no network, no GitHub Actions.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

if __package__:
    from .evidence_inventory import verify_clean_source
else:
    from evidence_inventory import verify_clean_source


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',required=True,type=Path)
    p.add_argument('--source-sha',required=True)
    p.add_argument('--source-tree',required=True)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if args.out.exists():p.error('Evidence already exists')
    verify_clean_source(args.repo_root,args.source_sha,args.source_tree,output=args.out)
    if not args.out.parent.resolve().is_dir():p.error('Existing external evidence directory required')
    import os
    if os.environ.get('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Only synthetic regression suite authorized')
    env=os.environ.copy()
    cmd=[sys.executable,'-m','pytest','-q','tests/stage1']
    proc=subprocess.run(cmd,cwd=str(args.repo_root),env=env,
        capture_output=True,text=True,timeout=600)
    verify_clean_source(args.repo_root,args.source_sha,args.source_tree,output=args.out)
    # Parse actual pytest end summary, never hardcode a count or an exit code.
    summary=re.findall(r'(\d+) passed',proc.stdout)
    count=int(summary[-1]) if summary else 0
    report={'classification':'ACTUAL_LOCAL_REGRESSION_NOT_NATIVE_AT',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha':args.source_sha,'source_tree':args.source_tree,
            'command':cmd,'exit_code':proc.returncode,
            'tests_executed':count,
            'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest(),
            'stderr_sha256':hashlib.sha256(proc.stderr.encode()).hexdigest(),
            'status':'PASS' if proc.returncode==0 and count>0 else 'FAIL'}
    with args.out.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(report,indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if report['status']=='PASS' else 1)


if __name__=='__main__':main()
