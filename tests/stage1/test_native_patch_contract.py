"""Regression for narrow pinned-source patcher; actual checkout not available in Chat.

On a Docker/Owner host, set UPSTREAM_ON_SOURCE_ROOT to require the verified checkout.
The verified pre-patch source MUST take vector fallback; post-patch MUST raise typed DB error.
"""
import ast
import asyncio
import importlib.util
import os
import pathlib
import sys
import textwrap
import types
import pytest

ROOT=pathlib.Path(__file__).resolve().parents[2]
PATH=ROOT/'scripts/stage1/apply_native_text_only_patch.py'
spec=importlib.util.spec_from_file_location('pinned_text_patcher',PATH)
patch=importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

# Exact overflow control-flow shape of pinned v1.15.1, synthetic remainder for local regression.
TEXT='''\nasync def text_search(keyword, results, source=True, note=True, notebook_ids=None):
    if not keyword:
        raise InvalidInputError("Search keyword cannot be empty")
    try:
        search_results = await repo_query("SELECT", {"keyword": keyword,
            "notebook_ids": _scope_record_ids(notebook_ids)})
        return search_results
    except RuntimeError as e:
        # Pinned fallback on SurrealDB highlight position overflow.
        if "position overflow" in str(e):
            logger.warning(f"Highlight position overflow, falling back to vector search: {str(e)}")
            try:
                return await vector_search(
                    keyword, results, source, note, notebook_ids=notebook_ids
                )
            except Exception as ve:
                logger.error(f"Vector search fallback also failed: {str(ve)}")
                logger.exception(ve)
                raise DatabaseOperationError(ve)
        logger.error(f"Error performing text search: {str(e)}")
        logger.exception(e)
        raise DatabaseOperationError(e)
    except Exception as e:
        logger.error(f"Error performing text search: {str(e)}")
        logger.exception(e)
        raise DatabaseOperationError(e)
'''


def make_function(source):
    module=ast.parse(source)
    function=next(n for n in module.body if isinstance(n,ast.AsyncFunctionDef))
    count=[]
    async def repo_query(*args):
        raise RuntimeError('position overflow')
    async def vector_search(*args,**kwargs):
        count.append('VECTOR_CALL')
        return [{'parent_id':'source:unsafe'}]
    class DatabaseOperationError(Exception):pass
    class InvalidInputError(Exception):pass
    class Logger:
        def warning(self,*args):pass
        def error(self,*args):pass
        def exception(self,*args):pass
    env={'repo_query':repo_query,'vector_search':vector_search,'logger':Logger(),
         'DatabaseOperationError':DatabaseOperationError,'InvalidInputError':InvalidInputError,
         '_scope_record_ids':lambda x:x}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<pinned-native-snippet>','exec'),env)
    return env['text_search'],count,DatabaseOperationError


def test_pinned_fallback_red_then_safe_patch_green():
    original,vector,_=make_function(TEXT)
    results=asyncio.run(original('繁體中文',10,notebook_ids=['notebook:a']))
    assert vector==['VECTOR_CALL'], results
    changed=patch.modify_text(TEXT)
    assert changed!=TEXT
    safe,vector,DBError=make_function(changed)
    with pytest.raises(DBError,match='position overflow'):
        asyncio.run(safe('繁體中文',10,notebook_ids=['notebook:a']))
    assert vector==[]


def test_patch_rejects_unknown_source_shape_and_duplicate():
    with pytest.raises(RuntimeError):patch.modify_text(TEXT.replace('return await vector_search(', 'return await another_search('))
    with pytest.raises(RuntimeError):patch.modify_text(TEXT.replace('if "position overflow"', 'if "other error"'))
    with pytest.raises(RuntimeError):patch.modify_text(patch.modify_text(TEXT))


def test_checkout_runtime_source_only_when_available():
    checkout=os.environ.get('UPSTREAM_ON_SOURCE_ROOT')
    if not checkout:
        pytest.skip('Real pinned source checkout unavailable in this Chat container')
    root=pathlib.Path(checkout)
    patch.verified_checkout(root)
    source=(root/patch.REL).read_text()
    patched=patch.modify_text(source)
    assert patched!=source
    fn=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=='text_search')
    assert 'vector_search' in ast.get_source_segment(source,fn)
    new_fn=next(n for n in ast.walk(ast.parse(patched)) if isinstance(n,ast.AsyncFunctionDef) and n.name=='text_search')
    branch=ast.get_source_segment(patched,new_fn)
    assert 'return await vector_search' not in branch
