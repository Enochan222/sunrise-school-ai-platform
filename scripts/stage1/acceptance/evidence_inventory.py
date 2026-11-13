#!/usr/bin/env python3
"""WP09 verified Codex evidence-inventory candidate, hardened by Builder B.

Codex handoff original sha256:
3306d5d62524804a49b0fde75616b3ba0f66806a6fec3bbf6ad1e5ddf7aa2e69
Original is INVENTORY_ONLY_NOT_ACCEPTANCE; this implementation adds actual
checkout Git SHA/tree verification, sensitive evidence rejection and bounded
file inventory. It does NOT run AT cases, assert their results or sign evidence.
IMPLEMENTED_UNTESTED.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

GIT40=re.compile(r'^[a-f0-9]{40}$')
SAFE_TYPES={'.json','.txt','.log','.md','.csv'}
MAX_FILE=2<<20
MAX_TOTAL=20<<20
RISK_PATTERNS=(
    re.compile(r'(?i)authorization\s*[:=]\s*(?:bearer|basic)\s+\S+'),
    re.compile(r'(?i)(?:set-)?cookie\s*[:=]\s*\S+'),
    re.compile(r'(?i)(?:password|secret|private_key|api_key|token)\s*[:=]\s*["\']?\S{5,}'),
    re.compile(r'(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b')
)


class UnsafeEvidence(ValueError):
    pass


def git_ids(path):
    def git(arg):
        result=subprocess.run(['git','-C',str(path), 'rev-parse',arg],
            capture_output=True,text=True,check=True,timeout=10)
        return result.stdout.strip()
    return git('HEAD'),git('HEAD^{tree}')


def inventory(repo_root,source_sha,source_tree,root):
    if not GIT40.fullmatch(source_sha) or not GIT40.fullmatch(source_tree):
        raise UnsafeEvidence('Full immutable source SHA/tree required')
    actual_sha,actual_tree=git_ids(repo_root)
    if (actual_sha,actual_tree)!=(source_sha,source_tree):
        raise UnsafeEvidence('Operator supplied Git SHA/tree differs from checkout')
    root=Path(root).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():raise UnsafeEvidence('Not a real evidence directory')
    files=[];total=0
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise UnsafeEvidence('Evidence symlink forbidden')
        mode=path.lstat().st_mode
        if stat.S_ISDIR(mode):continue
        if not stat.S_ISREG(mode) or path.suffix.lower() not in SAFE_TYPES:
            raise UnsafeEvidence('Unknown/binary/unreviewed evidence file')
        size=path.stat().st_size;total+=size
        if size>MAX_FILE or total>MAX_TOTAL:raise UnsafeEvidence('Unbounded evidence')
        raw=path.read_bytes()
        try:text=raw.decode('utf-8')
        except UnicodeDecodeError as e:raise UnsafeEvidence('Non-UTF8 evidence') from e
        if any(pattern.search(text) for pattern in RISK_PATTERNS):
            raise UnsafeEvidence('Evidence contains possible credentials; block publication')
        files.append({'path':path.relative_to(root).as_posix(),'bytes':size,
                      'sha256':hashlib.sha256(raw).hexdigest()})
    if not files:raise UnsafeEvidence('Empty evidence inventory cannot prove a test')
    return {'classification':'INVENTORY_ONLY_NOT_ACCEPTANCE',
            'status':'IMPLEMENTED_UNTESTED',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha':source_sha,'source_tree':source_tree,
            'files':files}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-sha',required=True)
    parser.add_argument('--source-tree',required=True)
    parser.add_argument('--repo-root',required=True,type=Path)
    parser.add_argument('--evidence-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.absolute()
    evidence_root=args.evidence_dir.resolve(strict=True)
    if output.exists() or output.is_relative_to(evidence_root):
        parser.error('Output must be new and outside evidence directory')
    report=inventory(args.repo_root,args.source_sha,args.source_tree,args.evidence_dir)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,sort_keys=True,indent=2)
        stream.write('\n')


if __name__=='__main__':main()
