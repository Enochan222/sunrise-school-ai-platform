# Sunrise Stage 1 [A] — Private local synthetic Gateway

STATUS: `LOCAL_SYNTHETIC_DEVELOPMENT`, Native ON/SurrealDB/Worker `RUNTIME_NOT_RUN`, WP00 `IN_PROGRESS`, R01 `NOT_APPROVED`.

**This is not a production service.** The present A Gateway has a temporary SQLite synthetic journal only. It cannot meet formal SurrealDB / durable ACK-loss / isolated restore requirements. Only synthetic PDFs, no real school or student data.

## Reproduce verified Gateway checks

Install `apps/a-vault/requirements-dev.txt` in a private Python environment, then from the Sunrise repository root run:

```bash
PYTHONPATH=wp00_builder_b python -m pytest -q wp00_builder_b/tests tests/stage1
python scripts/stage1/http_smoke.py
bash scripts/stage1/start_local.sh
```

Launch URL: `http://127.0.0.1:8765/auth/login`. The Gateway is loopback-only and refuses uncertain notebook creation and unsafe text search. Historical WP00 preliminary tests live in a separate downloadable local ZIP; do not imply they are all committed in this PR.

## Candidate true pinned Native backend (requires a Docker-capable machine)

1. Create a clean checkout of `lfnovo/open-notebook` at commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`, tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af`. Verify exact `git rev-parse HEAD`, `git rev-parse HEAD^{tree}` and empty `git status --porcelain`.
2. Set `ON_SOURCE_DIR` to that absolute checkout and `ON_PATCHED_DIR` to a **nonexistent absolute destination**. Set unique, strong `SURREAL_USER`, `SURREAL_PASSWORD`, `OPEN_NOTEBOOK_PASSWORD`, `OPEN_NOTEBOOK_ENCRYPTION_KEY` in a private persistent secret store/session; do not disclose in GitHub/logs. Keep same secrets for restart. Never use `root:root`.
3. Run `bash scripts/stage1/native_runtime_prepare.sh` from the Sunrise repo root. It creates a separate pinned staging copy (does not mutate upstream), patches text-only fallback, failed-only embedding-off retry, graph edge predicates and a protected patch marker; then attempts private Docker Compose build/run. SurrealDB candidate image `surrealdb/surrealdb:v2.3.10`; image digest must be recorded **from real Docker**. Native REST binds only 127.0.0.1:5055. UI port 8502 and SurrealDB 8000 are not published; internal Docker network disables external model egress. Runtime compatibility NOT_TESTED in this Chat.
4. Run `python scripts/stage1/native_runtime_smoke.py --out native-runtime-redacted.json` with the **same** `OPEN_NOTEBOOK_PASSWORD` in the local environment. This is a true HTTP (not mocked) native Notebook/PDF/Worker/Chinese+ASCII/BM25/original-hash probe, but it was NOT_RUN here. Record all actual results and migrations, logs, image IDs, exit codes and UTC.
5. When a patched native runtime is independently verified, optionally set `VAULT_NATIVE_PASSWORD` equal to that native password and `VAULT_NATIVE_TEXT_ONLY_VERIFIED=true` for local Gateway testing. Merely setting the flag does not bypass live `/api/sunrise-patch-status` attestation. Confirm school/owner on every read. The local SQLite journal still prevents formal Stage completion.
6. Stop with `docker compose -f scripts/stage1/compose.native.synthetic.yml down` and **do not use `-v`** while retaining fault/restore evidence.

## Mandatory NOT_RUN gates

Native SurrealDB v2 Migration 25 and source graph edge counts; real Worker crash/restart/retry with zero external AI; Notebook create ACK-loss idempotency/atomic recovery (quarantine is not recovery); Source original persistence; two-school IDOR; full A SurrealDB journal; network isolation; isolated DB/files/keys/index restore; Owner UAT and all S1-AT01–15. Reviewer-only manual merge after applicable gates pass. No GitHub Actions/Copilot/auto-merge.
