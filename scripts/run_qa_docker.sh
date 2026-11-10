#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
docker build -f Dockerfile.qa -t sunrise-stage0-qa:py3.11.11 .
# Bootstrap: only local bootstrap tests and Stage0 gate.
# Once Master Kit is imported, run complete runner (as defined by imported files).
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m sunrise-stage0-qa:py3.11.11
