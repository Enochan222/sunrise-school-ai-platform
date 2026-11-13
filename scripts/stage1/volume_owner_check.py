#!/usr/bin/env python3
"""Local-only safe permission initialization of a NEW empty project DB volume.

Executed by Docker in a networkless ephemeral helper container with only the
one explicitly prechecked, project-owned named volume mounted at /target.
Refuses nonempty targets. No recursive chown, no chmod 777, no deletes.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import secrets


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('init','write-probe'),required=True)
    p.add_argument('--uid',type=int,required=True)
    p.add_argument('--gid',type=int,required=True)
    args=p.parse_args()
    if args.uid<=0 or args.gid<=0 or args.uid>65534 or args.gid>65534:
        p.error('Pinned SurrealDB UID/GID must be verified non-root numeric identities')
    target=Path('/target')
    if not target.is_dir() or target.is_symlink() or target.resolve()!=target:
        p.error('Not the isolated mounted volume root')
    if args.mode=='init':
        if os.geteuid()!=0:
            p.error('New-volume ownership setup only in a temporary root helper')
        if list(target.iterdir()):
            p.error('Refuse ownership changes on nonempty or reused volume')
        os.chown(target,args.uid,args.gid)
    else:
        if os.geteuid()!=args.uid or os.getegid()!=args.gid:
            p.error('Write probe is not executing as exact SurrealDB UID/GID')
        marker=target/('sunrise-s1-permission-probe-'+secrets.token_hex(12))
        with marker.open('xb') as stream:
            stream.write(b'new volume ownership check')
            stream.flush()
            os.fsync(stream.fileno())
        require=marker.read_bytes()==b'new volume ownership check'
        marker.unlink()
        if not require:
            p.error('Permission probe bytes not durable and read back')
        if list(target.iterdir()):
            p.error('Fresh empty volume contains unexpected files after probe')


if __name__=='__main__':
    main()
