#!/usr/bin/env sh
# Run locally when explicitly invoked by an operator/GPT with a Docker engine.
# This does NOT register a PR trigger or GitHub required check.
set -eu
cd "$(dirname "$0")/.."
docker build -f Dockerfile.qa -t sunrise-stage0-qa:py3.11.11 .
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m sunrise-stage0-qa:py3.11.11
