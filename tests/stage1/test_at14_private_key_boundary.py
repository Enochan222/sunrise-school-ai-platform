"""AT14 RSA fixture path boundaries: no key under source tree or unsafe mode.

These are isolated *negative* source tests, NOT real HTTPS/AT14 runtime proofs.
"""
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import http_boundaries


def test_at14_source_root_points_at_actual_repository():
    assert http_boundaries.ROOT == ROOT


@pytest.mark.parametrize('kind',('inside_source','symlink','world_readable','missing','oversized'))
def test_at14_rejects_unsafe_private_key_before_any_service_request(
        monkeypatch,tmp_path,kind):
    synthetic_source=tmp_path/'source'
    synthetic_source.mkdir()
    monkeypatch.setattr(http_boundaries,'ROOT',synthetic_source)
    monkeypatch.setattr(http_boundaries,'authorized_materials',
                        lambda client,shell:[{'source_id':'source:owned'}])
    private=tmp_path/'fixture.pem'
    if kind=='inside_source':
        private=synthetic_source/'fixture.pem'
        private.write_bytes(b'not-a-real-key')
    elif kind=='symlink':
        actual=tmp_path/'target.pem'
        actual.write_bytes(b'not-a-real-key')
        actual.chmod(0o600)
        private.symlink_to(actual)
    elif kind=='missing':
        pass
    elif kind=='oversized':
        private.write_bytes(b'X'*8193)
    else:
        private.write_bytes(b'not-a-real-key')
    if private.exists() and not private.is_symlink():
        private.chmod(0o644 if kind=='world_readable' else 0o600)
    monkeypatch.setenv('VAULT_AT14_SIGNING_KEY_FILE',str(private))
    monkeypatch.setenv('VAULT_AT14_ISSUER','synthetic-issuer')
    monkeypatch.setenv('VAULT_AT14_AUDIENCE','synthetic-audience')
    args=SimpleNamespace(school_a='synthetic-a',school_b='synthetic-b',
                         source_a='source:owned',source_b='source:foreign',
                         shell_a='synthetic-shell')
    session={'school_id':'synthetic-a',
             'available_schools':['synthetic-a','synthetic-b']}
    with pytest.raises(RuntimeError,match='private fixture key missing/unsafe'):
        http_boundaries.case_14(None,args,session)
