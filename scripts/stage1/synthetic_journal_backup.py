"""Synthetic SQLite journal-only snapshot helper. NOT formal WP08 A restore.

Open Notebook SurrealDB, native original files, encryption keys, indexes, and worker
are NOT included. Used solely to prepare an isolated test verification pattern.
"""
import argparse
import hashlib
import sqlite3
from pathlib import Path


def journal_backup(source,destination):
    src=Path(source);dest=Path(destination)
    if not src.is_file() or src.resolve()==dest.resolve():
        raise ValueError('Missing source database or unsafe identical destination')
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError('Never overwrite existing backup')
    with sqlite3.connect(f'file:{src}?mode=ro',uri=True) as db:
        with sqlite3.connect(dest) as target:db.backup(target)
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def restore_isolated(backup,destination,expected_sha):
    src=Path(backup);dest=Path(destination)
    if not src.is_file() or dest.exists():raise ValueError('Restore destination must be absent')
    if hashlib.sha256(src.read_bytes()).hexdigest()!=expected_sha:
        raise ValueError('Backup SHA-256 mismatch; restore refused')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(f'file:{src}?mode=ro',uri=True) as db:
        with sqlite3.connect(dest) as target:db.backup(target)
    with sqlite3.connect(dest) as verify:
        check=verify.execute('PRAGMA integrity_check').fetchone()[0]
        if check!='ok':raise RuntimeError('Restored SQLite journal corrupt')
        counts={table:verify.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
            for table in ('shells','operations','materials','material_operations')}
    return counts


if __name__=='__main__':
    p=argparse.ArgumentParser(description='Synthetic SQLite-only backup/restore; NOT native A restore')
    p.add_argument('action',choices=['snapshot','restore'])
    p.add_argument('source');p.add_argument('destination');p.add_argument('--sha256')
    opts=p.parse_args()
    if opts.action=='snapshot':print('BACKUP_SHA256',journal_backup(opts.source,opts.destination))
    elif not opts.sha256:p.error('--sha256 required for restore')
    else:print('RESTORED_SQLITE_COUNTS',restore_isolated(opts.source,opts.destination,opts.sha256))
