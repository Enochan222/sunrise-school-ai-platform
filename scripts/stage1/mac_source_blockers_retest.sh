#!/usr/bin/env bash
# Read-only on existing Docker projects and volumes. Chromium is explicit opt-in.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || {
  echo "Fail closed: use clean source checkout" >&2; exit 78;
}
: "$VAULT_MAC_RETEST_OUT"
[[ "$VAULT_MAC_RETEST_OUT" = /* && ! -e "$VAULT_MAC_RETEST_OUT" ]] || {
  echo "Fail closed: fresh absolute evidence directory required" >&2; exit 78;
}
mkdir -m 700 "$VAULT_MAC_RETEST_OUT"
OUT="$VAULT_MAC_RETEST_OUT"
SHA="$(git rev-parse HEAD)"
TREE="$(git rev-parse 'HEAD^{tree}')"
printf 'HEAD=%s\nTREE=%s\n' "$SHA" "$TREE" >"$OUT/source.txt"
python -m pytest -q tests/stage1/test_native_patcher.py::test_pinned_native_entrypoint_missing_and_example_secrets_really_exit_fail_start \
  >"$OUT/native_fixture.log" 2>&1 || {
    code=$?; echo "Native fixture FAIL exit=$code" >&2; exit "$code";
  }
python -m pytest -q tests/stage1/test_gateway.py tests/stage1/test_executed_runtime_provenance.py \
  >"$OUT/gateway_affected.log" 2>&1 || {
    code=$?; echo "Gateway affected FAIL exit=$code" >&2; exit "$code";
  }
python -m pytest -q tests >"$OUT/full_non_native.log" 2>&1 || {
    code=$?; echo "Full Non-Native FAIL exit=$code" >&2; exit "$code";
  }
echo "FULL_NON_NATIVE_PASS_NO_RUNTIME_CLAIM"

: "$VAULT_GATEWAY_ORIGIN" "$VAULT_GATEWAY_CA_FILE" "$VAULT_MAINTENANCE_FILE"
: "$VAULT_DOCKER_CONTEXT" "$VAULT_SYNTHETIC_PROJECT" "$VAULT_ON_PATCH_SHA256"
: "$A_SURREAL_NAMESPACE" "$A_SURREAL_DATABASE" "$ON_GRAPH_NAMESPACE" "$ON_GRAPH_DATABASE"
for key in VAULT_GATEWAY_ORIGIN VAULT_GATEWAY_CA_FILE VAULT_MAINTENANCE_FILE \
    VAULT_DOCKER_CONTEXT VAULT_SYNTHETIC_PROJECT VAULT_ON_PATCH_SHA256 \
    A_SURREAL_NAMESPACE A_SURREAL_DATABASE ON_GRAPH_NAMESPACE ON_GRAPH_DATABASE; do
  [[ -n "$(printenv "$key" 2>/dev/null || true)" ]] || {
    echo "Required runtime parameter is blank: $key" >&2; exit 78;
  }
done
[[ "$VAULT_MAINTENANCE_FILE" = /* && -d "$(dirname "$VAULT_MAINTENANCE_FILE")" ]] || exit 78
python - "$ROOT" "$OUT" <<'PY_TLS'
import hashlib,json,os,pathlib,sys
import httpx
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
sys.path.insert(0,str(root/'scripts/stage1'))
from runtime_identity import tls_gateway_identity
origin=os.environ['VAULT_GATEWAY_ORIGIN'].rstrip('/')
ca=os.environ['VAULT_GATEWAY_CA_FILE']
observed=tls_gateway_identity(origin,ca)
wanted=hashlib.sha256(os.environ['VAULT_MAINTENANCE_FILE'].encode()).hexdigest()
if observed['maintenance_path_sha256']!=wanted or observed['maintenance'] is not False:
    raise RuntimeError('Gateway maintenance path mismatched or write-freeze active')
with httpx.Client(base_url=origin,verify=ca,trust_env=False,timeout=8) as c:
    health=c.get('/health')
    login=c.get('/auth/login')
    if health.status_code!=200 or login.status_code!=200 or 'text/html' not in login.headers.get('content-type',''):
        raise RuntimeError('CA-verified HTTPS /health or login form failed')
safe={'classification':'TLS_PEER_HEALTH_HTTP_OBSERVED',
      'http_health':health.status_code,'http_login':login.status_code,
      'gateway_instance':observed['instance_id'],
      'tls_peer_sha256':observed['tls_peer_sha256'],
      'maintenance_path_sha256':observed['maintenance_path_sha256']}
(out/'tls_health_http.json').write_text(json.dumps(safe,indent=2,sort_keys=True)+'\n')
print('REAL_CA_VERIFIED_TLS_HEALTH_HTTP_PASS')
PY_TLS
python scripts/stage1/runtime_identity.py \
  --context "$VAULT_DOCKER_CONTEXT" --project "$VAULT_SYNTHETIC_PROJECT" \
  --source-root "$ROOT" --gateway-url "$VAULT_GATEWAY_ORIGIN" \
  --gateway-ca-file "$VAULT_GATEWAY_CA_FILE" \
  --compose-file "$ROOT/scripts/stage1/compose.native.synthetic.yml" \
  --on-patch-sha256 "$VAULT_ON_PATCH_SHA256" \
  --surreal-namespace "$A_SURREAL_NAMESPACE" --surreal-database "$A_SURREAL_DATABASE" \
  --on-namespace "$ON_GRAPH_NAMESPACE" --on-database "$ON_GRAPH_DATABASE" \
  --out "$OUT/runtime_identity.json"
echo "RUNTIME_IDENTITY_RECORDED_NOT_FORMAL_ACCEPTANCE"
if [[ "$(printenv VAULT_RUN_CHROMIUM_DIAGNOSTIC 2>/dev/null || true)" == YES ]]; then
  python scripts/stage1/browser_admin_journey.py \
    --gateway "$VAULT_GATEWAY_ORIGIN" --gateway-ca-file "$VAULT_GATEWAY_CA_FILE" \
    --runtime-identity "$OUT/runtime_identity.json" \
    --context "$VAULT_DOCKER_CONTEXT" --project "$VAULT_SYNTHETIC_PROJECT" \
    --source-sha "$SHA" --source-tree "$TREE" \
    --out "$OUT/chromium_diagnostic.json"
else
  echo "CHROMIUM_NOT_RUN_EXPLICIT_OWNER_OPT_IN_REQUIRED"
fi
echo "RETEST_COMPLETE_NO_S1_AT_OR_R01_ASSERTION"
