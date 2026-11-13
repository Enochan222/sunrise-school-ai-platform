#!/usr/bin/env bash
# Stage 1 dual physical A/ON synthetic bootstrap · IMPLEMENTED_UNTESTED.
# NEVER repair/reuse Docker volumes; no automatic teardown, prune or student data.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
compose="$HERE/compose.native.synthetic.yml"
: "${VAULT_RUNTIME_SYNTHETIC_CONFIRM:?must explicitly equal YES}"
: "${VAULT_EXCLUSIVE_SYNTHETIC_PROJECT:?must explicitly equal YES}"
[[ "$VAULT_RUNTIME_SYNTHETIC_CONFIRM" == YES && "$VAULT_EXCLUSIVE_SYNTHETIC_PROJECT" == YES ]] || exit 78
: "${VAULT_SYNTHETIC_PROJECT:?new exclusive project name required}"
project="$VAULT_SYNTHETIC_PROJECT"
[[ "$project" =~ ^sunrise-s1-[a-z0-9-]{8,40}$ ]] || { echo "Unsafe project name" >&2; exit 78; }
: "${VAULT_DOCKER_CONTEXT:?explicit Docker context}"
context="$VAULT_DOCKER_CONTEXT"
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || exit 78
: "${ON_SOURCE_DIR:?pristine pinned upstream checkout}"
: "${ON_PATCHED_DIR:?new absolute staging copy}"
: "${VAULT_GATEWAY_ORIGIN:?explicit loopback HTTPS origin}"
: "${VAULT_GATEWAY_CA_FILE:?trusted Gateway CA file}"
[[ "$VAULT_GATEWAY_ORIGIN" =~ ^https://(127\.0\.0\.1|localhost):[0-9]{1,5}$ ]] ||
    { echo "Only loopback HTTPS Gateway origin accepted" >&2; exit 78; }
[[ -f "$VAULT_GATEWAY_CA_FILE" && ! -L "$VAULT_GATEWAY_CA_FILE" ]] ||
    { echo "Private TLS CA trust file absent or unsafe" >&2; exit 78; }
for key in A_SURREAL_USER A_SURREAL_PASSWORD A_SURREAL_NAMESPACE A_SURREAL_DATABASE \
    ON_SURREAL_USER ON_SURREAL_PASSWORD ON_GRAPH_NAMESPACE ON_GRAPH_DATABASE \
    ON_GRAPH_VIEWER_USER ON_GRAPH_VIEWER_PASSWORD OPEN_NOTEBOOK_PASSWORD \
    OPEN_NOTEBOOK_ENCRYPTION_KEY VAULT_SURREAL_IMAGE_DIGEST; do
    [[ -n "${!key:-}" ]] || { echo "Missing private config variable: $key" >&2; exit 78; }
done
for name in A_SURREAL_USER A_SURREAL_NAMESPACE A_SURREAL_DATABASE ON_SURREAL_USER \
    ON_GRAPH_NAMESPACE ON_GRAPH_DATABASE ON_GRAPH_VIEWER_USER; do
    [[ "${!name}" =~ ^[A-Za-z_][A-Za-z0-9_]{1,63}$ ]] ||
        { echo "Unsafe database identifier: $name" >&2; exit 78; }
done
[[ "${#A_SURREAL_PASSWORD}" -ge 24 && "${#ON_SURREAL_PASSWORD}" -ge 24 &&
   "${#ON_GRAPH_VIEWER_PASSWORD}" -ge 24 && "${#OPEN_NOTEBOOK_PASSWORD}" -ge 24 &&
   "${#OPEN_NOTEBOOK_ENCRYPTION_KEY}" -ge 32 ]] || exit 78
[[ "$A_SURREAL_PASSWORD" != "$ON_SURREAL_PASSWORD" &&
   "$A_SURREAL_PASSWORD" != "$ON_GRAPH_VIEWER_PASSWORD" &&
   "$ON_SURREAL_PASSWORD" != "$ON_GRAPH_VIEWER_PASSWORD" &&
   "$OPEN_NOTEBOOK_PASSWORD" != "$ON_SURREAL_PASSWORD" ]] || exit 78
[[ "$VAULT_SURREAL_IMAGE_DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]] ||
    { echo "Immutable SurrealDB digest required" >&2; exit 78; }
command -v docker >/dev/null || exit 69
docker --context "$context" info >/dev/null
docker --context "$context" compose version >/dev/null
# Project and volumes must be NEW. Do not adopt any pre-existing container.
existing="$(docker --context "$context" ps -aq --filter "label=com.docker.compose.project=$project")"
[[ -z "$existing" ]] || { echo "Project already has containers; refusing startup" >&2; exit 78; }
for short in a_db_data on_db_data native_data; do
    if docker --context "$context" volume inspect "${project}_${short}" >/dev/null 2>&1; then
        echo "Project volume already exists; no ownership changes allowed" >&2
        exit 78
    fi
done
# Prepare pinned ON source without editing pristine checkout.
bash "$HERE/prepare_native_checkout.sh"
[[ -s "$ON_PATCHED_DIR/.sunrise-patch-provenance.json" ]] || exit 78
# Pinned exact tag plus externally verified immutable registry digest.
image=surrealdb/surrealdb:v2.3.10
image_id="$(docker --context "$context" image inspect "$image" --format '{{.Id}}')"
[[ "$image_id" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 78
repo_digests="$(docker --context "$context" image inspect "$image" --format '{{json .RepoDigests}}')"
[[ "$repo_digests" == *"@$VAULT_SURREAL_IMAGE_DIGEST"* ]] ||
    { echo "Wrong/unverified SurrealDB image registry digest" >&2; exit 78; }
# Only use verified Pinned Image's actual non-root numerical UID and GID.
image_user="$(docker --context "$context" image inspect "$image" --format '{{.Config.User}}')"
[[ "$image_user" =~ ^[1-9][0-9]*:[1-9][0-9]*$ ]] ||
    { echo "Pinned DB image does not expose verified numeric nonroot UID:GID; manual review" >&2; exit 78; }
uid="${image_user%%:*}"; gid="${image_user##*:}"
export A_SURREAL_IMAGE_UID="$uid" A_SURREAL_IMAGE_GID="$gid"
export ON_SURREAL_IMAGE_UID="$uid" ON_SURREAL_IMAGE_GID="$gid"
docker --context "$context" compose -p "$project" -f "$compose" config --quiet
docker --context "$context" compose -p "$project" -f "$compose" build native
native_image="$(docker --context "$context" image inspect sunrise-on-s1-v1.15.1-text-only:local --format '{{.Id}}')"
[[ "$native_image" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 78
# Initialize ONLY the three brand new project-labelled volumes. Ownership
# adjustment is restricted to the empty DB volume root; no recursive chown.
for short in a_db_data on_db_data native_data; do
    docker --context "$context" volume create \
        --label "com.docker.compose.project=$project" \
        --label "com.docker.compose.volume=$short" \
        --label sunrise.stage1.synthetic=true "${project}_${short}" >/dev/null
done
for short in a_db_data on_db_data; do
    volume="${project}_${short}"
    docker --context "$context" run --rm --network none --read-only --user 0:0 \
        --security-opt no-new-privileges \
        -v "$volume:/target:rw" -v "$HERE/volume_owner_check.py:/helper.py:ro" \
        --entrypoint python "$native_image" /helper.py --mode init --uid "$uid" --gid "$gid"
    docker --context "$context" run --rm --network none --read-only --user "$uid:$gid" \
        --security-opt no-new-privileges \
        -v "$volume:/target:rw" -v "$HERE/volume_owner_check.py:/helper.py:ro" \
        --entrypoint python "$native_image" /helper.py --mode write-probe --uid "$uid" --gid "$gid"
done
# Start both authentic, independent DB engines BEFORE ON API/Worker.
docker --context "$context" compose -p "$project" -f "$compose" up -d --no-build a_db on_db
port_of() {
    local output host port
    output="$(docker --context "$context" compose -p "$project" -f "$compose" port "$1" 8000)"
    [[ "$output" =~ ^127\.0\.0\.1:[0-9]{1,5}$ ]] || exit 78
    printf 'ws://%s/rpc' "$output"
}
a_url="$(port_of a_db)"; on_url="$(port_of on_db)"
[[ "$a_url" != "$on_url" ]] || exit 78
export VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES
# Repeated attempts permitted ONLY for readiness, never automatic data reset.
ready=NO
for _ in {1..30}; do
    if python "$HERE/dual_db_readiness.py" --a-url "$a_url" --on-url "$on_url" \
         --provision-new-viewer >/dev/null 2>&1; then ready=YES; break; fi
    # Provisioning is one-shot and fails if VIEWER exists; run an existing-viewer
    # read-only check after a failed attempt before classifying as still unready.
    if python "$HERE/dual_db_readiness.py" --a-url "$a_url" --on-url "$on_url" \
         >/dev/null 2>&1; then ready=YES; break; fi
    sleep 2
done
[[ "$ready" == YES ]] || { echo "Dual DB RPC/Viewer readiness failed; leave project stopped for review" >&2; exit 78; }
docker --context "$context" compose -p "$project" -f "$compose" up -d --no-build native
# Dynamic measured endpoints are not secrets; operator must attest identities.
native_port="$(docker --context "$context" compose -p "$project" -f "$compose" port native 5055)"
[[ "$native_port" =~ ^127\.0\.0\.1:[0-9]{1,5}$ ]] || exit 78
printf 'DUAL_DB_SOURCE_READY_NOT_ACCEPTED a_db=%s on_db=%s native=http://%s\n' \
    "$a_url" "$on_url" "$native_port"
