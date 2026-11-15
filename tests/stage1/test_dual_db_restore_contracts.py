"""Dual-engine cold bundle fail-closed regressions; no Docker or personal data."""
from pathlib import Path
import importlib.util
import pytest

ROOT=Path(__file__).resolve().parents[2]
BACKUP=ROOT/'scripts/stage1/a_cold_backup.py'


def source():
    spec=importlib.util.spec_from_file_location('backup',BACKUP)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def snapshot(tmp_path):
    data=tmp_path/'staged'
    for folder in ('a_db','on_db','native','gateway'):
        path=data/folder
        path.mkdir(parents=True)
        (path/('synthetic-'+folder+'.dat')).write_bytes(b'isolated synthetic '+folder.encode())
    return data


def test_requires_two_distinct_db_volume_roots(snapshot):
    backup=source()
    names={name.split('/')[0] for name,*_ in backup.safe_members(snapshot)}
    assert names=={'a_db','on_db','native','gateway'}
    (snapshot/'on_db'/'synthetic-on_db.dat').unlink()
    with pytest.raises(backup.BackupInvalid):
        backup.safe_members(snapshot)
    (snapshot/'on_db').rmdir()
    with pytest.raises(backup.BackupInvalid):
        backup.safe_members(snapshot)


@pytest.mark.parametrize('missing',('a_db','on_db','native','gateway'))
def test_missing_required_recovery_volume_fails_closed(snapshot,missing):
    backup=source()
    for file in (snapshot/missing).iterdir():
        file.unlink()
    with pytest.raises(backup.BackupInvalid):
        backup.safe_members(snapshot)


def test_foreign_symlink_volume_fails_closed(snapshot,tmp_path):
    backup=source()
    (snapshot/'on_db'/'synthetic-on_db.dat').unlink()
    (snapshot/'on_db').rmdir()
    (snapshot/'on_db').symlink_to(tmp_path)
    with pytest.raises(backup.BackupInvalid):
        backup.safe_members(snapshot)


def test_format_is_not_legacy_one_engine_bundle():
    backup=source()
    assert backup.FORMAT=='sunrise-a-dual-db-cold-bundle-v2'
    assert backup.REQUIRED_ROOTS==('a_db','on_db','native','gateway')


def test_restore_compose_two_engines_no_public_tcp():
    text=(ROOT/'scripts/stage1/restore/compose.isolated.yml').read_text()
    assert '  a_db:' in text and '  on_db:' in text
    assert '  native:' in text
    assert 'a_db_data:' in text and 'on_db_data:' in text
    assert 'ports:' not in text
