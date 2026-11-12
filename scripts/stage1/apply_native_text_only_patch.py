#!/usr/bin/env python3
"""One-purpose A-only patch for Open Notebook v1.15.1 pinned source.

Run against a CLEAN checkout at the verified pinned commit/tree before docker build.
No patch is applied to a different upstream, and no native code is silently updated.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

PIN_COMMIT = '5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
PIN_TREE = '2d101001de594c7d6a0e4aaeb8e85ac4c52980af'
REL = Path('open_notebook/domain/notebook.py')

START = '        if "position overflow" in str(e):\n'
END = '        logger.error(f"Error performing text search: {str(e)}")\n'
REPLACEMENT = '''        if "position overflow" in str(e):
            # Sunrise Stage 1 [A]: never turn text/BM25 failures into vector/AI calls.
            logger.error("Sunrise text-only search highlight overflow; vector fallback disabled")
            raise DatabaseOperationError("Text search highlight position overflow; no vector fallback") from e
'''


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args):
    result = subprocess.run(['git', '-C', str(repo), *args],
                            text=True, capture_output=True, check=True)
    return result.stdout.strip()


def verified_checkout(root: Path):
    if git(root, 'rev-parse', 'HEAD') != PIN_COMMIT:
        raise RuntimeError('Pinned Open Notebook commit mismatch — refusing to modify')
    if git(root, 'rev-parse', 'HEAD^{tree}') != PIN_TREE:
        raise RuntimeError('Pinned Open Notebook git tree mismatch — refusing to modify')
    if git(root, 'status', '--porcelain', '--untracked-files=no'):
        raise RuntimeError('Open Notebook checkout is dirty — refusing to modify')


def modify_text(text: str) -> str:
    tree = ast.parse(text)
    found = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == 'text_search']
    if len(found) != 1:
        raise RuntimeError('Expected exactly one native text_search function')
    fn = found[0]
    # Restrict replacement to text_search function only; maintain normal text/BM25 behavior.
    lines = text.splitlines(keepends=True)
    prior = ''.join(lines[:fn.lineno-1]); within = ''.join(lines[fn.lineno-1:fn.end_lineno]); after = ''.join(lines[fn.end_lineno:])
    if within.count(START) != 1 or within.count(END) != 2:
        raise RuntimeError('Pinned native text_search overflow structure changed unexpectedly')
    start = within.index(START)
    end = within.index(END, start)
    old_branch = within[start:end]
    if 'return await vector_search(' not in old_branch:
        raise RuntimeError('Pinned vector fallback branch missing — fail closed')
    changed = prior + within[:start] + REPLACEMENT + within[end:] + after
    ast.parse(changed)
    if changed.count('Sunrise Stage 1 [A]: never turn text/BM25') != 1:
        raise RuntimeError('Patch marker missing')
    return changed


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    root=args.source_root.resolve()
    verified_checkout(root)
    path=root/REL
    before=path.read_bytes()
    after=modify_text(before.decode('utf-8')).encode('utf-8')
    if args.verify_only:
        print(json.dumps({'source':'PINNED_SOURCE_VERIFIED','pin_commit':PIN_COMMIT,
                         'pin_tree':PIN_TREE,'source_sha256':sha256(before),
                         'would_patch_sha256':sha256(after)},sort_keys=True))
        return
    path.write_bytes(after)
    print(json.dumps({'patch':'A_ONLY_TEXT_FALLBACK_DISABLED', 'pin_commit':PIN_COMMIT,
                      'pin_tree':PIN_TREE,'before_sha256':sha256(before),
                      'after_sha256':sha256(after),'file':str(REL)},sort_keys=True))

if __name__=='__main__':
    main()
