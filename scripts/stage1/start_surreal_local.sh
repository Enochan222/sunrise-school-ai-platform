#!/usr/bin/env bash
# A-only synthetic Gateway startup; fixed-version runtime work by local Owner.
# Dual physical SurrealDB; only Gateway serves HTTPS; never publish API/Worker.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERE="$ROOT/scripts/stage1"
[[ "${VAULT_RUNTIME_SYNTHETIC_CONFIRM:-}" == YES ]] || exit 69
: "${VAULT_DOCKER_CONTEXT:?exact Docker context}"
: "${VAULT_SYNTHETIC_PROJECT:?new synthetic Compose project}"
: "${VAULT_GATEWAY_PORT:?explicit free HTTPS loopback port}"
: "${VAULT_GATEWAY_TLS_CERT_FILE:?signed TLS leaf}"
: "${VAULT_GATEWAY_TLS_KEY_FILE:?TLS private key}"
: "${VAULT_GATEWAY_CA_FILE:?independent trust anchor}"
[[ "$VAULT_GATEWAY_PORT" =~ ^[0-9]{2,5}$ ]] &&
    (( 1024 <= 10#$VAULT_GATEWAY_PORT && 10#$VAULT_GATEWAY_PORT <= 65535 )) || exit 78
for f in "$VAULT_GATEWAY_TLS_CERT_FILE" "$VAULT_GATEWAY_TLS_KEY_FILE" "$VAULT_GATEWAY_CA_FILE"; do
    [[ -f "$f" && ! -L "$f" ]] || { echo "TLS material invalid path" >&2; exit 78; }
done
origin="https://127.0.0.1:$VAULT_GATEWAY_PORT"
[[ "${VAULT_GATEWAY_ORIGIN:-}" == "$origin" ]] ||
    { echo "TLS Gateway origin does not match operator-fixed port" >&2; exit 78; }
for key in VAULT_ADMIN_PASSWORD_HASH VAULT_SESSION_SECRET VAULT_ENCRYPTION_KEY \
    VAULT_SCHOOL_ID VAULT_ACTOR_ID OPEN_NOTEBOOK_PASSWORD A_SURREAL_USER \
    A_SURREAL_PASSWORD A_SURREAL_NAMESPACE A_SURREAL_DATABASE; do
    [[ -n "${!key:-}" ]] || { echo "Missing Gateway private variable: $key" >&2; exit 78; }
done
[[ "$VAULT_SCHOOL_ID" == synthetic-* ]] || { echo "Synthetic school identity mandatory" >&2; exit 78; }
compose="$HERE/compose.native.synthetic.yml"
project="$VAULT_SYNTHETIC_PROJECT"
ctx="$VAULT_DOCKER_CONTEXT"
[[ "$project" =~ ^sunrise-s1-[a-z0-9-]{8,40}$ ]] || exit 78
lookup() {
    local output
    output="$(docker --context "$ctx" compose -p "$project" -f "$compose" port "$1" "$2")"
    [[ "$output" =~ ^127\.0\.0\.1:[0-9]{1,5}$ ]] || exit 78
    printf '%s' "$output"
}
a_rpc="ws://$(lookup a_db 8000)/rpc"
native_http="http://$(lookup native 5055)"
[[ -z "${VAULT_SURREAL_WS_URL:-}" || "$VAULT_SURREAL_WS_URL" == "$a_rpc" ]] || exit 78
[[ -z "${VAULT_NATIVE_URL:-}" || "$VAULT_NATIVE_URL" == "$native_http" ]] || exit 78
export VAULT_SURREAL_WS_URL="$a_rpc"
export VAULT_NATIVE_URL="$native_http"
export VAULT_SURREAL_USER="$A_SURREAL_USER" VAULT_SURREAL_PASSWORD="$A_SURREAL_PASSWORD"
export VAULT_SURREAL_NAMESPACE="$A_SURREAL_NAMESPACE" VAULT_SURREAL_DATABASE="$A_SURREAL_DATABASE"
export VAULT_STORE_BACKEND=surreal VAULT_COOKIE_SECURE=true
export VAULT_NATIVE_PASSWORD="$OPEN_NOTEBOOK_PASSWORD"
# Gateway must not receive ON database root/VIEWER credentials.
unset ON_SURREAL_USER ON_SURREAL_PASSWORD ON_GRAPH_VIEWER_USER ON_GRAPH_VIEWER_PASSWORD
python - "$VAULT_GATEWAY_PORT" <<'PY_PORT'
import socket,sys
with socket.socket() as s:
    s.bind(('127.0.0.1',int(sys.argv[1])))
PY_PORT
cd "$ROOT/apps/a-vault"
exec python -m uvicorn server:app --host 127.0.0.1 \
    --port "$VAULT_GATEWAY_PORT" --ssl-certfile "$VAULT_GATEWAY_TLS_CERT_FILE" \
    --ssl-keyfile "$VAULT_GATEWAY_TLS_KEY_FILE" --no-access-log
