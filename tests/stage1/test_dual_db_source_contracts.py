"""Regression contracts for physically isolated synthetic A and Native SurrealDB.

Pure source-level checks, not a substitute for Docker v2.3.10 process tests.
"""
from pathlib import Path
import importlib.util
import pytest

ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'scripts/stage1'


def read(name):
    return (S/name).read_text(encoding='utf-8')


def import_source(name):
    spec=importlib.util.spec_from_file_location(name.replace('/','_'),S/name)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compose_two_engines_with_distinct_volume_and_secret_trust_domains():
    source=read('compose.native.synthetic.yml')
    assert '  a_db:' in source
    assert '  on_db:' in source
    assert '  native:' in source
    assert 'A_SURREAL_PASSWORD' in source
    assert 'ON_SURREAL_PASSWORD' in source
    assert source.count('surrealdb/surrealdb:v2.3.10')==2
    assert 'ws://on_db:8000/rpc' in source
    assert 'a_db_data:' in source and 'on_db_data:' in source
    assert 'a_db_private:' in source and 'on_db_private:' in source
    assert '127.0.0.1::8000' in source
    assert '127.0.0.1::5055' in source
    assert '127.0.0.1:8000:8000' not in source
    assert '127.0.0.1:5055:5055' not in source


def test_bootstrap_must_require_exclusive_new_project():
    source=read('native_runtime_prepare.sh')
    for token in ('VAULT_EXCLUSIVE_SYNTHETIC_PROJECT',
                  'A_SURREAL_PASSWORD','ON_SURREAL_PASSWORD',
                  'docker volume create','-p "$project"','on_db','a_db'):
        assert token in source
    assert 'chmod 777' not in source
    assert 'docker volume prune' not in source


def test_identity_requires_all_physically_distinct_services_and_networks():
    module=import_source('runtime_identity.py')
    assert module.EXPECTED_SERVICES=={'a_db','on_db','native'}
    assert module.EXPECTED_MOUNTS['a_db']=='/mydata'
    assert module.EXPECTED_MOUNTS['on_db']=='/mydata'
    assert module.EXPECTED_MOUNTS['native']=='/app/data'
    assert module.EXPECTED_PRIVATE_NETWORKS['a_db']!=module.EXPECTED_PRIVATE_NETWORKS['on_db']


@pytest.mark.parametrize('name',[
    'A_SURREAL_PASSWORD','ON_SURREAL_PASSWORD','OPEN_NOTEBOOK_PASSWORD'])
def test_no_missing_identity_secrets_silently_default(name,monkeypatch):
    module=import_source('runtime_identity.py')
    monkeypatch.delenv(name,raising=False)
    with pytest.raises((ValueError,RuntimeError)):
        module.require_explicit_env((name,))


def test_graph_viewer_must_not_share_a_journal_root_secret():
    source=read('wp04_native_graph_probe.py')
    assert 'ON_GRAPH_VIEWER_PASSWORD' in source
    assert 'ON_GRAPH_VIEWER_USER' in source
    assert 'A and Native DB addresses differ' not in source
    assert 'Native Graph read-only role must be independently authorized' in source


def test_restore_contract_has_two_independent_db_volumes():
    source=read('restore/compose.isolated.yml')
    assert 'a_db:' in source
    assert 'on_db:' in source
    assert 'native:' in source
    assert 'a_db_data:' in source and 'on_db_data:' in source
    assert 'ports:' not in source
