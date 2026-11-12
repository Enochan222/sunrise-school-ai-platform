"""WP08 preparation only; SQLite journal is not the A SurrealDB system of record."""
import hashlib
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'stage1'))
sys.path.insert(0,str(ROOT/'apps'/'a-vault'))
from synthetic_journal_backup import journal_backup,restore_isolated
from store import Store


def test_synthetic_sqlite_backup_restore_isolated(tmp_path):
    journal=tmp_path/'live.sqlite'
    store=Store(journal)
    data={'academic_year':'2026','grade':'P4','subject':'Math','curriculum_stream':'HK'}
    pending,fresh=store.start_shell('school-a','key1',data)
    assert fresh
    store.complete_shell('school-a','key1',pending,'notebook:123')
    backup=tmp_path/'isolated'/'journal.sqlite'
    digest=journal_backup(journal,backup)
    assert digest==hashlib.sha256(backup.read_bytes()).hexdigest()
    restored=tmp_path/'separate-place'/'restored.sqlite'
    counts=restore_isolated(backup,restored,digest)
    assert counts['shells']==counts['operations']==1
    assert Store(restored).shell('school-a',pending['shell_id'])['notebook_id']=='notebook:123'
    with pytest.raises(ValueError):restore_isolated(backup,tmp_path/'tampered.sqlite','f'*64)
    with pytest.raises(FileExistsError):journal_backup(journal,backup)
