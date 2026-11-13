"""WP08 cold snapshot + isolated restore negative cases. IMPLEMENTED_UNTESTED.

All tests use generated synthetic temp files only. They are NOT runtime/real
SurrealDB evidence. These tests MUST NOT be run until coding-only gate lifts.
"""
import io
import json
import os
from pathlib import Path
import sys
import tarfile

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from a_cold_backup import BackupInvalid,build,verify,restore_isolated


@pytest.fixture
def cold_bundle(tmp_path,monkeypatch):
    monkeypatch.setenv('VAULT_BACKUP_EXCLUSIVE_COLD','YES')
    monkeypatch.setenv('OPEN_NOTEBOOK_ENCRYPTION_KEY','N'*48)
    monkeypatch.setenv('VAULT_ENCRYPTION_KEY','V'*48)
    offline=tmp_path/'input'
    for name in ('surreal','native','gateway'):
        (offline/name).mkdir(parents=True)
    (offline/'surreal'/'database.db').write_bytes(b'SYNTHETIC_SURREAL_DATA')
    (offline/'native'/'synthetic-original.pdf').write_bytes(b'%PDF-1.4\nSYNTHETIC\n%%EOF')
    (offline/'gateway'/'recovery.json').write_text('{"synthetic": true}')
    attest=tmp_path/'attestation.json'
    attest.write_text(json.dumps({'exclusive_synthetic_host':True,
        'native_and_db_stopped':True,'offline_volume_copy':True,
        'docker_project':'sunrise-s1-native-synthetic',
        'host_identity':'synthetic-docker-context',
        'snapshot_utc':'2026-11-14T00:00:00+00:00'}))
    out=tmp_path/'cold.tar'
    result=build(offline,out,attest,'a'*40,'b'*40,'sha256:'+'c'*64,
        recovery_point_id='synthetic_point_01',
        key_escrow_reference='offline-escrow:synthetic-test',
        runtime_identity_sha256='d'*64)
    assert result['files']==3
    assert verify(out)['recovery_point_id']=='synthetic_point_01'
    return out


def repack(source,target, *,skip=None,extra=None,corrupt=None):
    with tarfile.open(source,'r:') as original,tarfile.open(target,'w') as output:
        for member in original.getmembers():
            if member.name==skip:continue
            data=original.extractfile(member).read()
            if member.name==corrupt:data=b'CORRUPTED'+data
            clone=tarfile.TarInfo(member.name)
            clone.size=len(data)
            clone.mode=0o600
            output.addfile(clone,io.BytesIO(data))
        if extra is not None:
            name,data,kind=extra
            entry=tarfile.TarInfo(name)
            entry.size=len(data) if kind=='file' else 0
            entry.type=tarfile.REGTYPE if kind=='file' else tarfile.SYMTYPE
            if kind=='symlink':entry.linkname='../../unsafe'
            output.addfile(entry,io.BytesIO(data) if kind=='file' else None)


def test_corrupt_archive_rejected(cold_bundle,tmp_path):
    damaged=tmp_path/'damaged.tar'
    damaged.write_bytes(cold_bundle.read_bytes()[:200])
    with pytest.raises((BackupInvalid,tarfile.TarError,EOFError)):
        verify(damaged)


def test_original_file_missing_rejected(cold_bundle,tmp_path):
    target=tmp_path/'missing-original.tar'
    repack(cold_bundle,target,skip='payload/native/synthetic-original.pdf')
    with pytest.raises(BackupInvalid):
        verify(target)


@pytest.mark.parametrize('name,content,kind',[
    ('payload/native/../../outside.txt',b'EXPLOIT','file'),
    ('payload/native/duplicated-symlink',b'','symlink'),
    ('payload/native/synthetic-original.pdf',b'DUPLICATE','file')
])
def test_traversal_symlink_duplicate_members_rejected(cold_bundle,tmp_path,name,content,kind):
    target=tmp_path/'forged.tar'
    repack(cold_bundle,target,extra=(name,content,kind))
    with pytest.raises(BackupInvalid):
        verify(target)


def test_wrong_or_missing_external_key_rejected(cold_bundle,monkeypatch):
    monkeypatch.setenv('VAULT_ENCRYPTION_KEY','WRONG'*12)
    with pytest.raises(BackupInvalid):
        verify(cold_bundle,compare_keys=True)
    monkeypatch.delenv('OPEN_NOTEBOOK_ENCRYPTION_KEY')
    with pytest.raises(BackupInvalid):
        verify(cold_bundle,compare_keys=True)


def test_missing_archive_member_rejected(cold_bundle,tmp_path):
    target=tmp_path/'missing-sql.tar'
    repack(cold_bundle,target,skip='payload/surreal/database.db')
    with pytest.raises(BackupInvalid):
        verify(target)


def test_byte_corruption_detected_by_content_sha(cold_bundle,tmp_path):
    target=tmp_path/'corrupted.tar'
    repack(cold_bundle,target,corrupt='payload/native/synthetic-original.pdf')
    with pytest.raises(BackupInvalid):
        verify(target)


def test_target_collision_refused_before_restore(cold_bundle,tmp_path):
    destination=tmp_path/'existing'
    destination.mkdir()
    with pytest.raises(BackupInvalid):
        restore_isolated(cold_bundle,destination)


def test_safe_standalone_restore_bytes_match(cold_bundle,tmp_path):
    destination=tmp_path/'isolated-new'
    status=restore_isolated(cold_bundle,destination)
    assert status['result']=='ISOLATED_OFFLINE_COPY_NOT_DB_RESTORE_VERIFIED'
    assert (destination/'native'/'synthetic-original.pdf').read_bytes().startswith(b'%PDF-')
