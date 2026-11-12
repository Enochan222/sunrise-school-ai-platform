#!/usr/bin/env bash
# Prepares a reviewed, isolated patched copy; no modifications to upstream checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${ON_SOURCE_DIR:?absolute path to a pristine Open Notebook checkout required}"
: "${ON_PATCHED_DIR:?absolute destination path for fresh patched staging copy required}"
[[ "$ON_SOURCE_DIR" = /* && "$ON_PATCHED_DIR" = /* ]] || { echo "Absolute paths required" >&2; exit 2; }
[[ ! -e "$ON_PATCHED_DIR" ]] || { echo "Destination must not already exist" >&2; exit 2; }
python - "$ON_SOURCE_DIR" "$ON_PATCHED_DIR" <<'PY_CHECK'
import os,sys
source=os.path.realpath(sys.argv[1]); dest=os.path.realpath(sys.argv[2])
if os.path.commonpath([source,dest]) in (source,dest):
    raise SystemExit('Source/destination must be nonoverlapping directories')
PY_CHECK
[[ "$(git -C "$ON_SOURCE_DIR" rev-parse HEAD)" == '5e285b7a2e435895c4ee99ad7e4b8d2af64c3239' ]] || { echo 'Pinned source commit mismatch' >&2; exit 3; }
[[ "$(git -C "$ON_SOURCE_DIR" rev-parse 'HEAD^{tree}')" == '2d101001de594c7d6a0e4aaeb8e85ac4c52980af' ]] || { echo 'Pinned source tree mismatch' >&2; exit 3; }
[[ -z "$(git -C "$ON_SOURCE_DIR" status --porcelain --untracked-files=normal)" ]] || { echo 'Pristine checkout must be clean' >&2; exit 3; }
mkdir -p "$ON_PATCHED_DIR"
# Export committed pinned files only, so no untracked secrets/dependencies leak into build context.
git -C "$ON_SOURCE_DIR" archive HEAD | tar -xf - -C "$ON_PATCHED_DIR"
python "$ROOT/scripts/stage1/patch_pinned_native.py" "$ON_PATCHED_DIR"
python -m compileall -q "$ON_PATCHED_DIR/api/main.py" "$ON_PATCHED_DIR/api/routers/sources.py" "$ON_PATCHED_DIR/api/routers/notebooks.py" "$ON_PATCHED_DIR/open_notebook/domain/notebook.py"
printf 'Source: %s\nPatched context: %s\n' '5e285b7a2e435895c4ee99ad7e4b8d2af64c3239' "$ON_PATCHED_DIR"
python - "$ON_PATCHED_DIR" "$ROOT/scripts/stage1/patch_pinned_native.py" <<'PY_PROVENANCE'
import hashlib,json,sys
from pathlib import Path
stage=Path(sys.argv[1]);script=Path(sys.argv[2])
files=['api/main.py','api/routers/sources.py','api/routers/notebooks.py','open_notebook/domain/notebook.py']
state={'pinned_source_commit':'5e285b7a2e435895c4ee99ad7e4b8d2af64c3239',
       'patcher_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
       'patched_files':{p:hashlib.sha256((stage/p).read_bytes()).hexdigest() for p in files}}
(stage/'.sunrise-patch-provenance.json').write_text(json.dumps(state,indent=2)+'\n')
PY_PROVENANCE
