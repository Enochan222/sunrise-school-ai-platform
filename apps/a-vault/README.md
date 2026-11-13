# Sunrise Stage 1 [A] — Private local synthetic Gateway

STATUS: `LOCAL_SYNTHETIC_DEVELOPMENT`, Native ON/SurrealDB/Worker `RUNTIME_NOT_RUN`, WP00 `IN_PROGRESS`, R01 `NOT_APPROVED`.

**This is not a production service.** The Gateway now contains an A SurrealDB v2 journal and creation-marker recovery implementation; these are **CODED BUT NATIVE/DB RUNTIME_NOT_RUN**. SQLite remains an explicit synthetic-only test double. No formal SurrealDB/ACK-loss/isolated restore acceptance is proven. Only synthetic PDFs.

## Reproduce verified Gateway checks

Install `apps/a-vault/requirements-dev.txt` in a private Python environment, then from the Sunrise repository root run:

```bash
python -m pytest -q tests/stage1
python scripts/stage1/http_smoke.py
bash scripts/stage1/start_local.sh
```

Launch URL: `http://127.0.0.1:8765/auth/login`. The Gateway is loopback-only and refuses uncertain notebook creation and unsafe text search. Historical WP00 preliminary tests live in a separate downloadable local ZIP; do not imply they are all committed in this PR.

## Candidate true pinned Native backend (requires a Docker-capable machine)

1. Create a clean checkout of `lfnovo/open-notebook` at commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`, tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af`. Verify exact `git rev-parse HEAD`, `git rev-parse HEAD^{tree}` and empty `git status --porcelain`.
2. Set `ON_SOURCE_DIR` to that absolute checkout and `ON_PATCHED_DIR` to a **nonexistent absolute destination**. Set unique, strong `SURREAL_USER`, `SURREAL_PASSWORD`, `OPEN_NOTEBOOK_PASSWORD`, `OPEN_NOTEBOOK_ENCRYPTION_KEY` in a private persistent secret store/session; do not disclose in GitHub/logs. Keep same secrets for restart. Never use `root:root`.
3. Run `bash scripts/stage1/native_runtime_prepare.sh` from the Sunrise repo root. It creates a separate pinned staging copy (does not mutate upstream), patches text-only fallback, failed-only embedding-off retry, graph edge predicates and a protected patch marker; then attempts private Docker Compose build/run. SurrealDB candidate image `surrealdb/surrealdb:v2.3.10`; image digest must be recorded **from real Docker**. Native REST binds only 127.0.0.1:5055. UI port 8502 is not published. SurrealDB 8000 is bound to 127.0.0.1 only for the controlled host Gateway; internal Docker network disables external model egress. Runtime compatibility NOT_TESTED in this Chat.
4. Run `python scripts/stage1/native_runtime_smoke.py --out native-runtime-redacted.json` with the **same** `OPEN_NOTEBOOK_PASSWORD` in the local environment. This is a true HTTP (not mocked) native Notebook/PDF/Worker/Chinese+ASCII/BM25/original-hash probe, but it was NOT_RUN here. Record all actual results and migrations, logs, image IDs, exit codes and UTC.
5. When a patched native runtime is independently verified, optionally set `VAULT_NATIVE_PASSWORD` equal to that native password and `VAULT_NATIVE_TEXT_ONLY_VERIFIED=true` for local Gateway testing. Merely setting the flag does not bypass live `/api/sunrise-patch-status` attestation. Confirm school/owner on every read. Default runtime requires A SurrealDB; only the explicit synthetic SQLite test double is non-durable.
6. Stop with `docker compose -f scripts/stage1/compose.native.synthetic.yml down` and **do not use `-v`** while retaining fault/restore evidence.

## Mandatory NOT_RUN gates

Native SurrealDB v2 Migration 25 and source graph edge counts; real Worker crash/restart/retry with zero external AI; Notebook create ACK-loss idempotency/atomic recovery (quarantine is not recovery); Source original persistence; two-school IDOR; full A SurrealDB journal; network isolation; isolated DB/files/keys/index restore; Owner UAT and all S1-AT01–15. Reviewer-only manual merge after applicable gates pass. No GitHub Actions/Copilot/auto-merge.

## New WP03 A SurrealDB Journal — UNVERIFIED runtime

`apps/a-vault/surreal_store.py` is the A-owned WebSocket RPC persistence backend: `content_shell`, `vault_operation`, `vault_scope_claim`, `source_owner`, `vault_session`, scoped unique indexes, atomic operation reservation/Notebook mapping, persistent actor/School/Source identity. Data and SQL bindings are parameterized. Its current code was locally compiled and component-tested but **actual SurrealDB v2.3.10 SQL and concurrency are NOT_RUN** in this Chat.

The Gateway defaults to `VAULT_STORE_BACKEND=surreal` and fails startup if `VAULT_SURREAL_USER`/`VAULT_SURREAL_PASSWORD` or the private DB is unavailable. `VAULT_STORE_BACKEND=synthetic_sqlite` is for local tests only. `start_local.sh` explicitly selects the latter. To run real A journal on a trusted synthetic Docker host, supply stable `VAULT_ADMIN_PASSWORD_HASH` (Argon2id), `VAULT_SESSION_SECRET`, `VAULT_ENCRYPTION_KEY`, `VAULT_SCHOOL_ID`, `VAULT_ACTOR_ID`, `VAULT_NATIVE_PASSWORD`, `VAULT_SURREAL_USER`, `VAULT_SURREAL_PASSWORD`; optionally set `VAULT_SURREAL_WS_URL=ws://127.0.0.1:8000/rpc`, `VAULT_SURREAL_NAMESPACE=open_notebook` and `VAULT_SURREAL_DATABASE=open_notebook`. Never print/commit secrets. Start:

```bash
bash scripts/stage1/start_surreal_local.sh
```

The new, genuinely native-dependent reservation/crash-window harness is `scripts/stage1/surreal_journal_smoke.py`. With the pinned private ON/DB/Worker stack actually up, configure the same A DB variables above, plus `OPEN_NOTEBOOK_PASSWORD` and `VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES`, then run it from repo root. It forces child exit after real native Notebook Create but before A journal completion, opens a fresh A Store and attempts exact-marker recovery. **No network ACK-drop injection, DB process restart, Worker restart, complete graph link/unlink or isolated full restore is claimed.** This harness returned exit 69 (`RUNTIME_NOT_RUN`) in the Chat container. It must be executed/independently reviewed on a Docker-capable host.

Formal S1-AT01–15 remain NOT_RUN; preserve the current Draft PR and do not merge.
