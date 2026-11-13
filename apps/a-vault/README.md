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

The new, genuinely native-dependent reservation/crash-window harness is `scripts/stage1/surreal_journal_smoke.py`. With the pinned private ON/DB/Worker stack actually up, configure the same A DB variables above, plus `OPEN_NOTEBOOK_PASSWORD` and `VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES`, then run it from repo root. It forces child exit after real native Notebook Create but before A journal completion, opens a fresh A Store and attempts exact-marker recovery. **A separate real TCP downstream ACK-drop injector and fresh-first-reservation race harness are now implemented, but neither has been executed against pinned Native/SurrealDB; DB restart, Worker restart, complete graph link/unlink and isolated full restore remain NOT_RUN.** This harness returned exit 69 (`RUNTIME_NOT_RUN`) in the Chat container. It must be executed/independently reviewed on a Docker-capable host.

Formal S1-AT01–15 remain NOT_RUN; preserve the current Draft PR and do not merge.

## WP03 Builder B critical corrections (2026-11-13)

The A SurrealDB journal now verifies exact UNIQUE index **table, index name, field list and field order**, using v2 INFO SQL strings or {sql: ...}; missing, extra, wrong-order and wrong-target definitions fail startup. Run the real v2 drift negative on an **exclusive synthetic Docker host** after setting private Surreal credentials and both `VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES` and `VAULT_EXCLUSIVE_SCHEMA_PROBE=YES`:

```bash
python scripts/stage1/wp03_schema_drift_probe.py
```

`surreal_journal_smoke.py` additionally calls `wp03_races.py`: three **fresh** eight-client barrier races, then (when Native is available) exactly one winning Notebook Create with verified marker/replay. It separately tests native **post-ACK process death** and **real client-facing lost-ACK**, the latter using `native_ack_loss_probe.py` to complete upstream POST but drop the downstream HTTP response before any bytes are delivered. Both must read back the durable marker; they must not send a second POST. All native/SurrealDB cases remain NOT_RUN in the Docker-less Builder Chat.

For an actual *private loopback, synthetic-only* Admin→Shell→Notebook→PDF→Worker→Text Search→Download→Archive→Logout probe after starting the real SurrealDB-backed Gateway and pinned Native worker, set `VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES`, `VAULT_STORE_BACKEND=surreal`, and private `VAULT_ADMIN_PASSWORD` plus `OPEN_NOTEBOOK_PASSWORD`, then run:

```bash
python scripts/stage1/real_admin_journey.py --gateway http://127.0.0.1:8765
```

The probe explicitly leaves Gateway Restart, secondary School B gateway negative and isolated full Restore as NOT_RUN. It does not authorize public hosting, budget changes, Work checkout edits or R01.

## WP07 verified scratch UI candidate port — IMPLEMENTED_UNTESTED (2026-11-13)

**Do NOT treat earlier test counts or runtime reports in this README as results for this new UI/API revision.** The Owner expressly required a coding-only sprint; no UI Browser/HTTP, pytest, compile, lint, native runtime, or CI checks were executed for the latest commits.

Source: `Sunrise_WP07_Codex_UI_Candidate_Handoff copy.zip`, SHA-256
`8d974fbf614171b0ae4e742f66ccdd02d0daf970ea5300d08e4ef7aca68490da`. All eight ZIP paths were inspected; seven manifest-listed file hashes match. This was `SCRATCH_IMPLEMENTATION_UNTESTED`, not a previously accepted product.

The integrated Gateway loads `templates/login.html` and `templates/admin.html` as **private local templates**, served exclusively by existing `GET /auth/login` and authenticated `GET /admin`; it does not publish a separate template route. The login handler creates a fresh signed ten-minute HttpOnly cookie and substitutes exactly one `__SUNRISE_LOGIN_CSRF__` with `escape(csrf,quote=True)`. The existing POST handler continues to support JSON Login for JS and HTTP 303 Redirect for HTML forms. Session expiry/revocation, Origin guard, Argon2id password and CSP remain on the Gateway.

Candidate JavaScript was adapted as the sole `apps/a-vault/ui.js` asset, using `/assets/app.js`, with `style.css` for responsive Chinese UI. No external CDN, Inline Script, Native API credentials or untrusted `innerHTML` rendering is intended. Browser state tracks only the current session's CSRF and unresolved mutation snapshots; **no durable cross-refresh/browser-restart recovery is claimed**. Source/School authorisation stays entirely server-side.

The unchanged formal eight A routes are used for Shell List/Create/Read/Archive, Materials List/Upload/Download and Scoped Search. Upload acknowledgment means `SUBMITTED_NATIVE_PROCESSING`, not Worker extraction complete. The Gateway now projects conservative Native statuses (`PROCESSING`, `READY`, `FAILED`, `UNKNOWN`) onto the existing Materials List `state` field, after per-Source Ownership readback. Unknown/completed-without-text is not considered READY.

Other code-only updates in this revision:
- WP02/WP04: stable authenticated Service JWT actor identity scopes formal A SurrealDB Material Operation, source-rights metadata/initial version/original locator and AI-use disabled.
- WP03: same actor's reused Material Idempotency-Key with a different Shell or payload is rejected; duplicate source scope claims are read back without blindly creating another Source.
- WP05: private disabled-by-default failed-only Native Retry validates patched source marker, Native owner/status, and original SHA before/after. Operator harness: `scripts/stage1/wp05_private_retry_probe.py`.
- WP01: `scripts/stage1/wp01_network_boundary_probe.py` is an isolated-network source-only probe. WP04 Native graph source-only probe: `scripts/stage1/wp04_native_graph_probe.py`.
- WP06: Shell/Search normalization and PDF form metadata/MIME/path validation happen before Native operations.

**Restricted coding lease:** WP08/WP09 `a_cold_backup.py`, `test_a_cold_backup.py`, `restore/**`, `acceptance/**`, `docs/stage1/uat/**` remain frozen until Reviewer records Codex's local stop/handoff and issues `WP08_WP09_LEASE_RELEASED_TO_BUILDER_B`. Existing committed WP08 code is preserved without modification. There is no new WP09 accepted harness or Owner UAT result.

**Rollback boundary:** restore the matched Gateway template handling, both private templates, `ui.js` and `style.css` together to the previous tested commit; do not mix new DOM IDs with old JavaScript. Re-running formal QA is mandatory after rollback or subsequent integration. Current Stage 1 Acceptance, Native Worker readiness, full restore and R01 remain NOT_APPROVED/NOT_RUN.
