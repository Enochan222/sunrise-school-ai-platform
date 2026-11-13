#!/usr/bin/env bash
# Owner-only synthetic DB-backed local development; no public deployment.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
for key in VAULT_ADMIN_PASSWORD_HASH VAULT_SESSION_SECRET VAULT_ENCRYPTION_KEY \
 VAULT_SCHOOL_ID VAULT_ACTOR_ID VAULT_NATIVE_PASSWORD VAULT_SURREAL_USER VAULT_SURREAL_PASSWORD; do
 if [[ -z "${!key:-}" ]]; then echo "MISSING/UNSAFE: $key" >&2; exit 78; fi
done
: "${VAULT_NATIVE_URL:=http://127.0.0.1:5055}"
: "${VAULT_SURREAL_WS_URL:=ws://127.0.0.1:8000/rpc}"
: "${VAULT_SURREAL_NAMESPACE:=open_notebook}"
: "${VAULT_SURREAL_DATABASE:=open_notebook}"
export VAULT_NATIVE_URL VAULT_SURREAL_WS_URL VAULT_SURREAL_NAMESPACE VAULT_SURREAL_DATABASE
export VAULT_STORE_BACKEND=surreal
# Cannot rely on local in-memory defaults for a durable journal. No auto-migration downgrade.
cd "$ROOT/apps/a-vault"
exec python -m uvicorn server:app --host 127.0.0.1 --port 8765 --no-access-log
