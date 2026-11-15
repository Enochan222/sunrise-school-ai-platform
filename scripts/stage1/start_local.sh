#!/usr/bin/env bash
# Local SYNTHETIC only. Not a production deployment. Must be run from repository root.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/apps/a-vault"
python - <<'PY'
import importlib.metadata as m
for package in ('fastapi','uvicorn','argon2-cffi','itsdangerous','python-multipart','PyJWT','httpx'):
    print(package,m.version(package))
PY
if [[ -z "${VAULT_NATIVE_PASSWORD:-}" ]]; then
  read -r -s -p 'Temporary local Open Notebook private password (no real secrets): ' VAULT_NATIVE_PASSWORD
  echo
fi
if [[ -z "${VAULT_ADMIN_PASSWORD:-}" ]]; then
  read -r -s -p 'Temporary local Sunrise Admin password: ' VAULT_ADMIN_PASSWORD
  echo
fi
export VAULT_NATIVE_PASSWORD
export VAULT_ADMIN_PASSWORD
export VAULT_ADMIN_PASSWORD_HASH="$(python - <<'PY'
import os
from argon2 import PasswordHasher
print(PasswordHasher().hash(os.environ['VAULT_ADMIN_PASSWORD']))
PY
)"
unset VAULT_ADMIN_PASSWORD
export VAULT_SESSION_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export VAULT_ENCRYPTION_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export VAULT_SCHOOL_ID="${VAULT_SCHOOL_ID:-synthetic-school-a}"
export VAULT_ACTOR_ID="${VAULT_ACTOR_ID:-synthetic-admin}"
export VAULT_NATIVE_URL="${VAULT_NATIVE_URL:-http://127.0.0.1:5055}"
export VAULT_SQLITE_FILE="${VAULT_SQLITE_FILE:-$ROOT/.local-synthetic-vault/journal.sqlite3}"
export VAULT_COOKIE_SECURE=false
# Local synthetic mode is explicit; never the formal runtime default.
export VAULT_STORE_BACKEND="${VAULT_STORE_BACKEND:-synthetic_sqlite}"
# Never ship the admin/native secret or expose an HTTP listener publicly.
exec python -m uvicorn server:app --host 127.0.0.1 --port 8765 --no-access-log
