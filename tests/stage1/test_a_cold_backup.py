"""WP08 real offline file I/O tests; no live SurrealDB/Native/worker acceptance."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from a_cold_backup import BackupInvalid,build,restore_isolated,verify


@pytest.fixture
def snapshot(tmp_path,monkeypatch):
    monkeypatch.setenv('VAULT_BACKUP_EXCLUSIVE_COLD','YES')
    monkeypatch.setenv('OPEN_NOTEBOOK_ENCRYPTION_KEY','native-'+'A'*48)
    monkeypatch.setenv('VAULT_ENCRYPTION_KEY','vault-'+'B'*48)
    folder=tmp_path/'source'
    for name in ('a_db','on_db','native','gateway'):(folder/name).mkdir(parents=True)
    (folder/'a_db'/'db.rocks').write_bytes(b'SYNTHETIC_A_DB\x00INDEX_RECORD')
    (folder/'on_db'/'graph.rocks').write_bytes(b'SYNTHETIC_ON_DB_GRAPH_INDEX')
    (folder/'native'/'original.pdf').write_bytes(b'%PDF-1.4\nsynthetic\n%%EOF')
    (folder/'gateway'/'metadata.json').write_text('{"school":"synthetic"}')
    attestation=tmp_path/'operator.json'
    attestation.write_text(json.dumps({'exclusive_synthetic_host':True,
        'a_and_on_and_native_stopped':True,'offline_volume_copy':True,
        'docker_project':'only-synthetic-wp08','host_identity':'synthetic-test-host',
        'snapshot_utc':'2026-11-13T11:45:00Z'}))
    return folder,attestation,tmp_path


def bundle(snapshot):
    folder,att,root=snapshot
    output=root/'result.tar'
    summary=build(folder,output,att,'a'*40,'b'*40,'sha256:'+'c'*64)
    assert summary['files']==4 and output.is_file()
    return output


def test_bundle_verify_isolated_restore_round_trip_with_keys(snapshot):
    path=bundle(snapshot)
    manifest=verify(path)
    assert len(manifest['files'])==4
    assert 'OPEN_NOTEBOOK_ENCRYPTION_KEY' in manifest['required_external_key_sha256']
    assert 'A'*30 not in str(manifest) and 'B'*30 not in str(manifest)
    restored=snapshot[2]/'separate_namespace'
    output=restore_isolated(path,restored)
    assert output['files']==4
    for name,record in manifest['files'].items():
        assert hashlib.sha256((restored/name).read_bytes()).hexdigest()==record['sha256']
    assert not (restored/'manifest.json').exists()
    with pytest.raises(BackupInvalid):restore_isolated(path,restored)


def test_wrong_or_missing_key_never_creates_restore(snapshot,monkeypatch):
    path=bundle(snapshot)
    monkeypatch.setenv('VAULT_ENCRYPTION_KEY','wrong-'+'X'*48)
    with pytest.raises(BackupInvalid,match='key identity'):
        restore_isolated(path,snapshot[2]/'wrong-key')
    assert not (snapshot[2]/'wrong-key').exists()
    monkeypatch.delenv('OPEN_NOTEBOOK_ENCRYPTION_KEY')
    with pytest.raises(BackupInvalid):verify(path)


def test_changed_archive_detected_before_restore(snapshot):
    path=bundle(snapshot)
    data=path.read_bytes().replace(b'SYNTHETIC_A_DB',b'UNTRUSTED_A_DB')
    path.write_bytes(data)
    with pytest.raises(BackupInvalid,match='corrupted'):
        verify(path)
    dest=snapshot[2]/'not-restored'
    with pytest.raises(BackupInvalid):restore_isolated(path,dest)
    assert not dest.exists()


def test_cold_gate_symlink_and_missing_volume_rejected(snapshot,monkeypatch):
    folder,att,root=snapshot
    monkeypatch.delenv('VAULT_BACKUP_EXCLUSIVE_COLD')
    with pytest.raises(BackupInvalid,match='cold-volume'):
        build(folder,root/'no.tar',att,'a'*40,'b'*40,'sha256:'+'c'*64)
    monkeypatch.setenv('VAULT_BACKUP_EXCLUSIVE_COLD','YES')
    (folder/'native'/'fake-link').symlink_to(folder/'native'/'original.pdf')
    with pytest.raises(BackupInvalid,match='symlink'):
        build(folder,root/'no.tar',att,'a'*40,'b'*40,'sha256:'+'c'*64)
    assert not (root/'no.tar').exists()


def test_attestation_missing_or_false_refused(snapshot):
    folder,att,root=snapshot
    att.write_text(json.dumps({'exclusive_synthetic_host':False,'a_and_on_and_native_stopped':True,
        'offline_volume_copy':True,'docker_project':'p','host_identity':'h','snapshot_utc':'now'}))
    with pytest.raises(BackupInvalid,match='offline export'):
        build(folder,root/'no.tar',att,'a'*40,'b'*40,'sha256:'+'c'*64)


def test_restore_rejects_member_path_traversal(snapshot):
    import io
    path=bundle(snapshot)
    altered=snapshot[2]/'evil.tar'
    with tarfile.open(altered,'w') as tar:
        with tarfile.open(path) as original:
            manifest=original.extractfile('manifest.json').read()
            meta=tarfile.TarInfo('manifest.json');meta.size=len(manifest)
            tar.addfile(meta,io.BytesIO(manifest))
            bad=tarfile.TarInfo('payload/../outside');bad.size=1
            tar.addfile(bad,io.BytesIO(b'X'))
    with pytest.raises(BackupInvalid):restore_isolated(altered,snapshot[2]/'forbidden')
    assert not (snapshot[2]/'forbidden').exists()
