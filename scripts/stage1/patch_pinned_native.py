"""Fail-fast, narrowly scoped Sunrise A-only patch for exact Open Notebook v1.15.1.

Run against a staging COPY of a verified pinned checkout, NEVER the pristine source.
If upstream changes or an expected construct disappears, abort instead of silently
producing an unpatched/no-op image. Actual native test results remain NOT_RUN until
this staging copy is built with SurrealDB v2 + worker and exercised.
"""
from __future__ import annotations
import argparse
from pathlib import Path

PINNED = "5e285b7a2e435895c4ee99ad7e4b8d2af64c3239"
MARKER = "sunrise-a-text-only-no-vector-v1"


def replace_once(source: str, original: str, replacement: str, label: str) -> str:
    count = source.count(original)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one pinned-source occurrence, got {count}")
    return source.replace(original, replacement, 1)


def patch_text_search(source: str) -> str:
    begin = source.index("async def text_search(")
    end = source.index("\nasync def vector_search(", begin)
    fragment = source[begin:end]
    prefix = "    except RuntimeError as e:\n"
    start = fragment.index(prefix)
    stop = fragment.index("    except Exception as e:\n", start + len(prefix))
    old = fragment[start:stop]
    if '"position overflow"' not in old or "return await vector_search(" not in old:
        raise ValueError("Pinned source mismatch: unsafe native fallback construct not found")
    new = ("    except RuntimeError as e:\n"
           "        # Sunrise A: NEVER invoke vector/embedding fallback for any text error.\n"
           "        logger.error(f\"Text-only search failed: {str(e)}\")\n"
           "        raise DatabaseOperationError(e) from e\n")
    return source[:begin] + fragment[:start] + new + fragment[stop:] + source[end:]


def patch_scoped_cjk_search(source: str) -> str:
    """Match contiguous Han text when the English BM25 analyzer finds no source."""
    begin = source.index("async def text_search(")
    end = source.index("\nasync def vector_search(", begin)
    fragment = source[begin:end]
    old = "        return search_results\n"
    new = """        # English BM25 does not reliably match substrings of Han text.
        # Limit the literal match to sources linked to one explicit notebook.
        if (not search_results and source and not note and notebook_ids
                and len(notebook_ids) == 1
                and any("\u3400" <= char <= "\u9fff" for char in keyword)):
            search_results = await repo_query(
                "SELECT id, id AS parent_id, title, 0 AS relevance FROM source "
                "WHERE id IN (SELECT VALUE in FROM reference WHERE out = $notebook) "
                "AND (string::contains(title ?? '', $term) "
                "OR string::contains(full_text ?? '', $term)) "
                "ORDER BY id LIMIT $limit",
                {"notebook": ensure_record_id(notebook_ids[0]),
                 "term": keyword, "limit": results},
            )
        return search_results
"""
    return source[:begin] + replace_once(fragment, old, new, "scoped CJK literal search") + source[end:]



def patch_retry(source: str) -> str:
    start = source.index("async def retry_source_processing(")
    end = source.index("\n@router.", start)
    fragment = source[start:end]
    guard_start = fragment.index("        # Check if source already has a running command\n")
    guard_end = fragment.index("        # Get notebooks that this source belongs to.", guard_start)
    old = fragment[guard_start:guard_end]
    if 'status in ["running", "queued"]' not in old or "except Exception as e:" not in old:
        raise ValueError("Pinned source mismatch: retry guard is not as expected")
    fixed = '''        # Sunrise A: status uncertainty is NOT permission to requeue.
        if not source.command:
            raise HTTPException(status_code=409, detail="No durable processing command; retry quarantined")
        try:
            status = await source.get_status()
        except Exception as e:
            logger.warning(f"Source retry status unverified for {source_id}: {e}")
            raise HTTPException(status_code=503, detail="Cannot verify source command state") from e
        if status != "failed":
            raise HTTPException(status_code=409, detail="Only proven failed source commands may be retried")

'''
    fragment = fragment[:guard_start] + fixed + fragment[guard_end:]
    fragment = replace_once(fragment, "                embed=True,  # Always embed on retry", "                embed=False,  # Sunrise A: no embedding provider", "retry embed")
    return source[:start] + fragment + source[end:]


def patch_graph(source: str) -> str:
    source = replace_once(source,
        '"SELECT * FROM reference WHERE out = $source_id AND in = $notebook_id"',
        '"SELECT * FROM reference WHERE in = $source_id AND out = $notebook_id"', "native link duplicate predicate")
    source = replace_once(source,
        '"DELETE FROM reference WHERE out = $notebook_id AND in = $source_id"',
        '"DELETE FROM reference WHERE in = $source_id AND out = $notebook_id"', "native unlink predicate")
    return source


def patch_main(source: str) -> str:
    anchor = 'if CORS_IS_DEFAULT_WILDCARD:\n'
    marker = f'''# Sunrise A-only private patch attestation: protected by native password middleware.
@app.get("/api/sunrise-patch-status", include_in_schema=False)
async def sunrise_patch_status():
    return {{"marker": "{MARKER}", "text_only": True}}

'''
    return replace_once(source, anchor, marker + anchor, "native patch attestation")


def patch_checkout(root: Path) -> list[str]:
    edits = [
        ("open_notebook/domain/notebook.py",
         lambda source: patch_scoped_cjk_search(patch_text_search(source))),
        ("api/routers/sources.py", patch_retry),
        ("api/routers/notebooks.py", patch_graph),
        ("api/main.py", patch_main),
    ]
    originals = [(root / path, (root / path).read_text(encoding="utf-8"), fn)
                 for path, fn in edits]
    # No partial mutation if any pinned-source anchor fails.
    prepared = [(p, fn(content)) for p, content, fn in originals]
    for path, content in prepared:
        path.write_text(content, encoding="utf-8")
    return [str(p.relative_to(root)) for p, _ in prepared]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()
    for path in patch_checkout(args.source_directory):
        print("A-only local synthetic patched:", path)
