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
