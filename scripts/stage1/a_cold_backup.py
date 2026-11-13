#!/usr/bin/env python3
"""WP08 candidate: immutable A-only COLD snapshot bundle + isolated restore.

Precondition: an operator independently stops and exports the exclusive synthetic
Docker stack and supplies its *offline staging copy*. This utility DOES NOT
stop containers, export live RocksDB or assert consistency of a running DB.
It preserves the SurrealDB volume (journal/indexes), native original-file
volume and private Gateway persistent metadata. Encryption keys stay OUTSIDE
this archive; only their SHA-256 identities are recorded for restore checks.

This is NOT a completed WP08 runtime restore, nor a production backup tool.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile
from datetime import datetime, timezone

MAX_FILE_BYTES = 1 << 30  # 1 GiB; purposefully bounded for synthetic WP08
MAX_TOTAL_BYTES = 4 << 30
REQUIRED_ROOTS = ('surreal', 'native', 'gateway')
FORMAT = 'sunrise-a-cold-bundle-v1'
UPSTREAM = '5e285b7a2e435895c4ee99ad7e4b8d2af64c3239'
HEX64 = re.compile(r'^[0-9a-f]{64}$')


class BackupInvalid(ValueError):
    pass


def key_identities():
    result = {}
    for var in ('OPEN_NOTEBOOK_ENCRYPTION_KEY', 'VAULT_ENCRYPTION_KEY'):
        secret = os.environ.get(var)
        if not secret or len(secret) < 32:
            raise BackupInvalid('Missing/weak required external key: ' + var)
        result[var] = hashlib.sha256(secret.encode('utf-8')).hexdigest()
    return result


def validate_cold_attestation(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not all(data.get(key) is True for key in
            ('exclusive_synthetic_host', 'native_and_db_stopped', 'offline_volume_copy')):
        raise BackupInvalid('Operator-attested exclusive offline export required')
    for key in ('docker_project', 'host_identity', 'snapshot_utc'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise BackupInvalid('Incomplete offline operator attestation: '+key)
    return {k: data[k] for k in ('docker_project','host_identity','snapshot_utc')}


def safe_members(folder):
    base = Path(folder)
    if not base.is_dir() or base.is_symlink():
        raise BackupInvalid('Offline staging directory must be a real directory')
    members=[];total=0
    for root in REQUIRED_ROOTS:
        part=base/root
        if not part.is_dir() or part.is_symlink():
            raise BackupInvalid('Missing/offline snapshot is a symlink: '+root)
        for path in sorted(part.rglob('*')):
            # Never resolve/follow untrusted volume symlinks, sockets or devices.
            mode=path.lstat().st_mode
            if stat.S_ISDIR(mode):continue
            if not stat.S_ISREG(mode) or path.is_symlink():
                raise BackupInvalid('Special path/symlink prohibited in cold snapshot')
            relative=path.relative_to(base).as_posix()
            size=path.stat().st_size
            total+=size
            if size>MAX_FILE_BYTES or total>MAX_TOTAL_BYTES:
                raise BackupInvalid('Synthetic snapshot size limit exceeded')
            members.append((relative,path,size))
    if not any(name.startswith('surreal/') for name,_,_ in members):
        raise BackupInvalid('SurrealDB data volume not included')
    if not any(name.startswith('native/') for name,_,_ in members):
        raise BackupInvalid('Native originals volume not included')
    return members


def build(offline_dir,output,attestation_path,source_sha,source_tree,image_digest):
    if not re.fullmatch(r'[0-9a-f]{40}',source_tree) or not re.fullmatch(r'[0-9a-f]{40}',source_sha):
        raise BackupInvalid('Exact source SHA/tree required')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image_digest):
        raise BackupInvalid('Verified immutable Surreal image digest required')
    offline=Path(offline_dir).resolve();dest=Path(output).absolute()
    if dest.exists() or offline==dest or offline in dest.parents:
        raise BackupInvalid('Destination must be new and outside offline snapshot')
    if os.environ.get('VAULT_BACKUP_EXCLUSIVE_COLD') != 'YES':
        raise BackupInvalid('Explicit cold-volume snapshot confirmation required')
    attestation=validate_cold_attestation(attestation_path)
    members=safe_members(offline)
    manifest={'format':FORMAT, 'created_utc':datetime.now(timezone.utc).isoformat(),
        'stage':'A_ONLY_SYNTHETIC', 'upstream_commit':UPSTREAM,
        'source_commit':source_sha,'source_tree':source_tree,
        'surreal_image_digest':image_digest,'cold_operator_attestation':attestation,
        'required_external_key_sha256':key_identities(),'files':{}}
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Temporary artifact is outside input dir; never leave a misleading final archive.
    with tempfile.NamedTemporaryFile(dir=dest.parent,prefix='.wp08-',suffix='.tar',delete=False) as tmp:
        temp=Path(tmp.name)
    try:
        with tarfile.open(temp,'w') as tar:
            for name,path,size in members:
                before=path.stat()
                digest=hashlib.sha256()
                with path.open('rb') as f:
                    while chunk:=f.read(1<<20):digest.update(chunk)
                after=path.stat()
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise BackupInvalid('Cold snapshot mutated while hashing')
                info=tarfile.TarInfo('payload/'+name)
                info.size=size;info.mode=0o600;info.uid=info.gid=0;info.mtime=0
                with path.open('rb') as stream:tar.addfile(info,stream)
                check=path.stat()
                if (check.st_size,check.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise BackupInvalid('Cold snapshot mutated while archiving')
                manifest['files'][name]={'bytes':size,'sha256':digest.hexdigest()}
            raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode('utf-8')
            meta=tarfile.TarInfo('manifest.json');meta.size=len(raw);meta.mode=0o600
            meta.uid=meta.gid=0;meta.mtime=0
            tar.addfile(meta,io.BytesIO(raw))
        # Re-verify archive contents, not just successful tar creation.
        verify(temp,compare_keys=False)
        os.chmod(temp,0o600)
        os.replace(temp,dest)
        return {'bundle_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
                'files':len(members),'result':'COLD_BUNDLE_CREATED_NOT_RUNTIME_RESTORE'}
    finally:
        if temp.exists():temp.unlink()


def _member_path(name):
    p=PurePosixPath(name)
    if not name or name.startswith('/') or '..' in p.parts or '\\' in name:
        raise BackupInvalid('Archive path traversal rejected')
    if p.parts[0]!='payload' or len(p.parts)<3 or p.parts[1] not in REQUIRED_ROOTS:
        raise BackupInvalid('Unexpected archive member')
    return '/'.join(p.parts[1:])


def verify(path,compare_keys=True):
    with tarfile.open(path,'r:') as tar:
        members=tar.getmembers()
        if len(members)<2 or sum(x.name=='manifest.json' for x in members)!=1:
            raise BackupInvalid('Missing or repeated manifest')
        meta=tar.extractfile('manifest.json')
        if not meta or tar.getmember('manifest.json').size>(8<<20):
            raise BackupInvalid('Invalid manifest')
        manifest=json.load(meta)
        if not isinstance(manifest,dict) or manifest.get('format')!=FORMAT or manifest.get('upstream_commit')!=UPSTREAM:
            raise BackupInvalid('Wrong backup format or pinned source')
        expected=manifest.get('files')
        if not isinstance(expected,dict):raise BackupInvalid('Missing backup inventory')
        if compare_keys and manifest.get('required_external_key_sha256')!=key_identities():
            raise BackupInvalid('Wrong/missing external key identity; restore refused')
        found=set();total=0
        for item in members:
            if item.name=='manifest.json':continue
            if not item.isfile() or item.issym() or item.islnk() or item.size>MAX_FILE_BYTES:
                raise BackupInvalid('Unsafe archive member')
            name=_member_path(item.name)
            if name in found or name not in expected:raise BackupInvalid('Unexpected/duplicated file')
            found.add(name);total+=item.size
            if total>MAX_TOTAL_BYTES:raise BackupInvalid('Oversize archive')
            expected_info=expected[name]
            if not isinstance(expected_info,dict) or expected_info.get('bytes')!=item.size or not HEX64.fullmatch(str(expected_info.get('sha256',''))):
                raise BackupInvalid('Inventory mismatch')
            digest=hashlib.sha256();source=tar.extractfile(item)
            if source is None:raise BackupInvalid('Unreadable archive member')
            while chunk:=source.read(1<<20):digest.update(chunk)
            if digest.hexdigest()!=expected_info['sha256']:
                raise BackupInvalid('Archive content corrupted')
        if found!=set(expected):raise BackupInvalid('Missing archive inventory file')
        return manifest


def restore_isolated(path,new_destination):
    manifest=verify(path,compare_keys=True)  # reject before creating any output
    destination=Path(new_destination).absolute()
    if destination.exists():raise BackupInvalid('Restore destination MUST NOT exist')
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.wp08-restore-',dir=destination.parent))
    try:
        with tarfile.open(path,'r:') as tar:
            for item in tar.getmembers():
                if item.name=='manifest.json':continue
                name=_member_path(item.name)
                output=staging/name
                output.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(item) as inp,output.open('xb') as out:
                    shutil.copyfileobj(inp,out,length=1<<20)
                os.chmod(output,0o600)
        # Check actually written files after extraction: corrupt output => abort staging.
        for name,info in manifest['files'].items():
            if hashlib.sha256((staging/name).read_bytes()).hexdigest()!=info['sha256']:
                raise BackupInvalid('Restored file hash differs')
        os.replace(staging,destination)
        return {'result':'ISOLATED_OFFLINE_COPY_NOT_DB_RESTORE_VERIFIED',
                'files':len(manifest['files'])}
    finally:
        if staging.exists():shutil.rmtree(staging)


def main():
    p=argparse.ArgumentParser(description='A-only synthetic cold snapshot preparation (NOT runtime WP08 acceptance)')
    sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('bundle');b.add_argument('--offline-dir',required=True)
    b.add_argument('--out',required=True);b.add_argument('--attestation',required=True)
    b.add_argument('--code-sha',required=True);b.add_argument('--code-tree',required=True)
    b.add_argument('--surreal-image-digest',required=True)
    v=sub.add_parser('verify');v.add_argument('bundle')
    r=sub.add_parser('restore-isolated');r.add_argument('bundle');r.add_argument('--dest',required=True)
    args=p.parse_args()
    if args.action=='bundle':result=build(args.offline_dir,args.out,args.attestation,args.code_sha,args.code_tree,args.surreal_image_digest)
    elif args.action=='verify':
        obj=verify(args.bundle);result={'result':'INTEGRITY_VERIFIED_NOT_RUNTIME_RESTORE','files':len(obj['files'])}
    else:result=restore_isolated(args.bundle,args.dest)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
