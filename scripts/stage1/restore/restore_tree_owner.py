#!/usr/bin/env python3
"""Verify and re-own ONLY a newly created isolated restored DB volume.

No chmod, no recursive blind chown, no source/project volume mounting.
Every file must match a previously cryptographically verified cold manifest
before applying the original pinned nonroot runtime user. Run on a sealed,
isolated target with the exact named new target volume mounted at /target.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat


def require(condition,reason):
    if not condition:raise RuntimeError(reason)


def sha_file(path):
    digest=hashlib.sha256()
    with path.open('rb') as src:
        while True:
            chunk=src.read(1<<20)
            if not chunk:break
            digest.update(chunk)
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('chown','nonroot-probe'),required=True)
    p.add_argument('--root',choices=('a_db','on_db'),required=True)
    p.add_argument('--uid',type=int,required=True)
    p.add_argument('--gid',type=int,required=True)
    p.add_argument('--manifest',default='/proof/target-owner-manifest.json')
    args=p.parse_args()
    require(0<args.uid<=65534 and 0<args.gid<=65534,'Invalid nonroot pinned runtime user')
    target=Path('/target')
    require(target.is_dir() and not target.is_symlink() and target.resolve()==target,
            'Target must be exact isolated mount')
    doc=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    require(doc.get('format')=='sunrise-a-dual-db-cold-bundle-v2'
            and doc.get('topology')=='DUAL_PHYSICAL_SURREALDB',
            'Target restore manifest not exact dual-engine evidence')
    prefix=args.root+'/'
    expect={Path(name[len(prefix):]):info for name,info in doc.get('files',{}).items()
            if name.startswith(prefix)}
    require(expect and all(not name.is_absolute() and '..' not in name.parts
                           for name in expect),'Missing or unsafe target root inventory')
    actual={}
    directories=[target]
    for path in target.rglob('*'):
        kind=path.lstat().st_mode
        relative=path.relative_to(target)
        if stat.S_ISDIR(kind):
            directories.append(path)
        elif stat.S_ISREG(kind) and not path.is_symlink():
            actual[relative]=path
        else:
            raise RuntimeError('Unsafe symlink/device/socket in isolated target')
    require(set(actual)==set(expect),'Target volume inventory has missing/foreign files')
    for relative,path in actual.items():
        info=expect[relative]
        require(info.get('bytes')==path.stat().st_size
                and info.get('sha256')==sha_file(path),
                'Restored target bytes do not match verified recovery point')
    if args.mode=='chown':
        require(os.geteuid()==0,'Fresh target ownership setup requires temporary root verifier')
        for path in actual.values():
            os.chown(path,args.uid,args.gid,follow_symlinks=False)
        for directory in reversed(directories):
            os.chown(directory,args.uid,args.gid,follow_symlinks=False)
    else:
        require(os.geteuid()==args.uid and os.getegid()==args.gid,
                'Actual target DB process user not verified')
        marker=target/('sunrise-write-check-'+secrets.token_hex(12))
        with marker.open('xb') as out:
            out.write(b'S1 isolated target write probe')
            out.flush()
            os.fsync(out.fileno())
        require(marker.read_bytes()==b'S1 isolated target write probe',
                'Nonroot DB volume read/write mismatch')
        marker.unlink()
    for path in list(actual.values())+directories:
        require(path.stat().st_uid==args.uid and path.stat().st_gid==args.gid,
                'Restored volume remains inaccessible to pinned nonroot DB UID/GID')


if __name__=='__main__':
    main()
