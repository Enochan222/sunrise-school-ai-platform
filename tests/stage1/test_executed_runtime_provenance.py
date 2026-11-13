"""Synthetic-only negative tests for executed-case provenance; NOT Runtime PASS."""
import hashlib
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from executed_runtime_provenance import inspect,guard


def identity(source_sha,source_tree):
    return {
        'type':'SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED',
        'source_commit':source_sha,
        'source_tree':source_tree,
        'gateway':{'tls_verified':True},
        'services':{name:{
            'status':'running','container_id':digit*64,'image_id':'sha256:'+digit*64}
            for name,digit in (('a_db','a'),('on_db','b'),('native','c'))}
    }


def test_runtime_binding_rejects_missing_or_wrong_source(monkeypatch,tmp_path):
    a,b='a'*40,'b'*40
    monkeypatch.setattr('executed_runtime_provenance._git',
                        lambda root,key: a if key=='HEAD' else b)
    path=tmp_path/'runtime.json'
    path.write_text(json.dumps(identity(a,b)))
    digest=inspect(ROOT,path,a,b)
    assert len(digest)==64
    guard(ROOT,path,a,b,digest)
    with pytest.raises(RuntimeError,match='revision'):
        inspect(ROOT,path,'d'*40,b)
    with pytest.raises(RuntimeError,match='revision'):
        inspect(ROOT,path,a,'d'*40)
    with pytest.raises(RuntimeError,match='revision'):
        inspect(ROOT,path,'a'*39,b)


@pytest.mark.parametrize('mutation',[
    lambda d:d.update({'type':'UNRELATED'}),
    lambda d:d.update({'gateway':{'tls_verified':False}}),
    lambda d:d['services'].pop('on_db'),
    lambda d:d['services']['a_db'].update({'status':'stopped'}),
    lambda d:d['services']['a_db'].update({'image_id':'sha256:wrong'}),
    lambda d:d['services']['native'].update({'container_id':'wrong'}),
])
def test_runtime_identity_mismatches_fail_closed(monkeypatch,tmp_path,mutation):
    a,b='a'*40,'b'*40
    monkeypatch.setattr('executed_runtime_provenance._git',
                        lambda root,key:a if key=='HEAD' else b)
    document=identity(a,b)
    mutation(document)
    path=tmp_path/'runtime.json'
    path.write_text(json.dumps(document))
    with pytest.raises(RuntimeError):
        inspect(ROOT,path,a,b)


def test_external_runtime_evidence_immutability(monkeypatch,tmp_path):
    a,b='a'*40,'b'*40
    monkeypatch.setattr('executed_runtime_provenance._git',
                        lambda root,key:a if key=='HEAD' else b)
    path=tmp_path/'runtime.json'
    path.write_text(json.dumps(identity(a,b)))
    digest=inspect(ROOT,path,a,b)
    path.write_text(json.dumps(identity(a,b),indent=2))
    with pytest.raises(RuntimeError,match='changed'):
        guard(ROOT,path,a,b,digest)


def test_runtime_path_must_be_external_to_checkout(monkeypatch):
    a,b='a'*40,'b'*40
    monkeypatch.setattr('executed_runtime_provenance._git',
                        lambda root,key:a if key=='HEAD' else b)
    with pytest.raises(RuntimeError,match='external|absent|unsafe'):
        inspect(ROOT,ROOT/'scripts/stage1/runtime_identity.py',a,b)
