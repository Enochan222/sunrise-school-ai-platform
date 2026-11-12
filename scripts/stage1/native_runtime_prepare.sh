#!/usr/bin/env bash
set -euo pipefail
# Local Operator/Reviewer controlled synthetic only. Caller must supply clean pinned source checkout.
: "${ON_SOURCE_DIR:?Set ON_SOURCE_DIR to clean pinned Open Notebook checkout}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
if ! command -v docker >/dev/null; then
  echo "RUNTIME_NOT_RUN: Docker executable unavailable" >&2
  exit 69
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "RUNTIME_NOT_RUN: Docker Compose v2 unavailable" >&2
  exit 69
fi
# Do not write a rendered docker compose config: it includes secret ENV values.
for key in SURREAL_USER SURREAL_PASSWORD OPEN_NOTEBOOK_PASSWORD OPEN_NOTEBOOK_ENCRYPTION_KEY; do
  if [[ -z "${!key:-}" ]]; then
    echo "Missing required secret (variable name only): $key" >&2
    exit 78
  fi
done
if [[ "$SURREAL_USER" == "root" && "$SURREAL_PASSWORD" == "root" ]]; then
  echo 'Unsafe default Surreal root:root not permitted' >&2; exit 78
fi
if [[ "${#SURREAL_PASSWORD}" -lt 24 || "${#OPEN_NOTEBOOK_PASSWORD}" -lt 24 || "${#OPEN_NOTEBOOK_ENCRYPTION_KEY}" -lt 32 ]]; then
  echo 'Required synthetic passwords/keys must be sufficiently long' >&2; exit 78
fi
if [[ "$SURREAL_PASSWORD" == "$OPEN_NOTEBOOK_PASSWORD" ]]; then
  echo 'Surreal and Native passwords must not be equal' >&2; exit 78
fi
# Hard fail on untrusted external service publication (the compose file is source-controlled).
if grep -Eq '^\s+-\s*"?(0\.0\.0\.0|8502|8000):' "$HERE/compose.native.synthetic.yml"; then
  echo 'Unsafe published native/UI/DB port detected' >&2; exit 78
fi
python "$HERE/apply_native_text_only_patch.py" --source-root "$ON_SOURCE_DIR" --verify-only
python "$HERE/apply_native_text_only_patch.py" --source-root "$ON_SOURCE_DIR"
docker compose -f "$HERE/compose.native.synthetic.yml" up --build -d
printf '%s\n' "Native stack started. Runtime proof requires independent probes:"
docker compose -f "$HERE/compose.native.synthetic.yml" ps
# Print IDs only. Image digests, versions, and logs require recording on host.
docker image inspect sunrise-on-s1-v1.15.1-text-only:local --format 'Native Image ID={{.Id}}'
docker image inspect surrealdb/surrealdb:v2.3.10 --format 'Surreal Image ID={{.Id}} Repository Digests={{.RepoDigests}}'
