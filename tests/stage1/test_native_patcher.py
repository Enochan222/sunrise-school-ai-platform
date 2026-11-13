"""Checks patcher transformation against synthetic pinned-shape source fixtures.
Not a SurrealDB / upstream import / native runtime test.
"""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('patcher',ROOT/'scripts/stage1/patch_pinned_native.py')
patcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


def test_text_search_removes_vector_fallback_preserving_handler():
    text='''async def text_search(keyword, results, source=True, note=True, notebook_ids=None):
    try:
        return await repo_query('select')
    except RuntimeError as e:
        if "position overflow" in str(e):
            return await vector_search(keyword, results, source, note, notebook_ids=notebook_ids)
        raise DatabaseOperationError(e)
    except Exception as e:
        raise DatabaseOperationError(e)

async def vector_search(keyword, results, source=True, note=True, notebook_ids=None):
    pass
'''
    fixed=patcher.patch_text_search(text)
    assert 'return await vector_search(' not in fixed.split('async def vector_search')[0]
    assert 'raise DatabaseOperationError(e) from e' in fixed
    assert "return await repo_query('select')" in fixed


def test_retry_never_embeds_and_unknown_state_denied():
    fixture='''async def retry_source_processing(source_id):
        # Check if source already has a running command
        if source.command:
            try:
                status = await source.get_status()
                if status in ["running", "queued"]:
                    raise HTTPException(status_code=400)
            except Exception as e:
                continue_with_retry = True
        # Get notebooks that this source belongs to.
        # synthetic fixture
                embed=True,  # Always embed on retry

@router.delete('/sources')
'''
    fixed=patcher.patch_retry(fixture)
    assert 'embed=False' in fixed
    assert 'if status != "failed":' in fixed
    assert 'Cannot verify source command state' in fixed


def test_graph_orientation_and_fail_fast():
    fixture='''"SELECT * FROM reference WHERE out = $source_id AND in = $notebook_id"
"DELETE FROM reference WHERE out = $notebook_id AND in = $source_id"'''
    fixed=patcher.patch_graph(fixture)
    assert 'WHERE in = $source_id AND out = $notebook_id' in fixed
    assert 'WHERE out = $source_id AND in = $notebook_id' not in fixed
    with pytest.raises(ValueError): patcher.patch_graph('missing expected predicates')


def test_patch_main_adds_only_protected_marker():
    fixed=patcher.patch_main('app = FastAPI()\n\nif CORS_IS_DEFAULT_WILDCARD:\n    pass\n')
    assert '/api/sunrise-patch-status' in fixed
    assert patcher.MARKER in fixed


def test_chinese_search_merges_scoped_literal_and_bm25_results():
    """Retain substring matches when BM25 also returned a different source."""
    import asyncio

    fixture = '''async def text_search(keyword, results, source=True, note=True, notebook_ids=None):
    if True:
        search_results = await repo_query("bm25", {})
        return search_results

async def vector_search():
    pass
'''
    transformed = patcher.patch_scoped_cjk_search(fixture)
    calls = []

    async def query(sql, params):
        calls.append((sql, params))
        if sql == "bm25":
            return [
                {"parent_id": "source:exact"},
                {"parent_id": "source:shared"},
            ]
        return [
            {"parent_id": "source:substring"},
            {"parent_id": "source:shared"},
        ]

    namespace = {"repo_query": query, "ensure_record_id": lambda value: value}
    exec(transformed, namespace)
    result = asyncio.run(namespace["text_search"](
        "繁體中文", 3, source=True, note=False, notebook_ids=["notebook:owner"]
    ))
    assert [hit["parent_id"] for hit in result] == [
        "source:substring", "source:shared", "source:exact"
    ]
    assert calls[1][1]["notebook"] == "notebook:owner"
    assert calls[1][1]["term"] == "繁體中文"

    calls.clear()
    result = asyncio.run(namespace["text_search"](
        "𠀀", 3, source=True, note=False, notebook_ids=["notebook:owner"]
    ))
    assert calls[1][1]["term"] == "𠀀"
    assert result[0]["parent_id"] == "source:substring"

    calls.clear()
    result = asyncio.run(namespace["text_search"](
        "繁體中文", 3, source=True, note=False, notebook_ids=[]
    ))
    assert len(calls) == 1
    assert len(result) == 2


def test_pinned_native_entrypoint_missing_and_example_secrets_really_exit_fail_start():
    """Future source fixture: exercise POSIX guard without Docker/API/worker."""
    import os
    import subprocess

    pinned_shape='#!/bin/sh\nVENV_PY="/app/.venv/bin/python"\nexec /bin/sh -c 'exit 0'\n'
    guarded=patcher.patch_entrypoint(pinned_shape)
    assert 'SUNRISE_NATIVE_SECRET_FAIL_START' in guarded
    assert 'exec /bin/sh -c 'exit 0'' in guarded
    with pytest.raises(ValueError,match='already patched'):
        patcher.patch_entrypoint(guarded)

    values={'OPEN_NOTEBOOK_PASSWORD':'synthetic-native-password-strong',
            'OPEN_NOTEBOOK_ENCRYPTION_KEY':'synthetic-encryption-key-at-least-32-characters',
            'SURREAL_USER':'synthetic',
            'SURREAL_PASSWORD':'synthetic-db-password-strong'}
    baseline={**os.environ,**values,'OPEN_NOTEBOOK_PASSWORD_FILE':'',
              'OPEN_NOTEBOOK_ENCRYPTION_KEY_FILE':''}
    good=subprocess.run(['/bin/sh','-c',guarded],env=baseline,
                        capture_output=True,text=True,timeout=10)
    assert good.returncode==0
    for missing in values:
        env=baseline.copy()
        env.pop(missing)
        result=subprocess.run(['/bin/sh','-c',guarded],env=env,
                              capture_output=True,text=True,timeout=10)
        assert result.returncode==78
        assert 'SUNRISE_NATIVE_SECRET_FAIL_START: '+missing in result.stderr
    for key,weak in [('OPEN_NOTEBOOK_PASSWORD','password'),
                     ('OPEN_NOTEBOOK_ENCRYPTION_KEY','changeme'),
                     ('SURREAL_PASSWORD','root:root')]:
        result=subprocess.run(['/bin/sh','-c',guarded],env={**baseline,key:weak},
                              capture_output=True,text=True,timeout=10)
        assert result.returncode==78
        assert 'SUNRISE_NATIVE_SECRET_FAIL_START: '+key in result.stderr
