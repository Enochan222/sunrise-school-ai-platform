# ChatGPT Work / Handover Prompts — Reviewed v0.7

> **CURRENT REPOSITORY OVERRIDE (2026-11-10):** Active repo is `Enochan222/sunrise-school-ai-platform`; no GitHub Copilot/Actions; local QA must be executed and evidenced; old repo, old CI, old ADR references below are historical only. Read [current Stage0 rules](NEW_REPO_STAGE0.md).

## 通用前置要求（所有 Work Stage）

先讀 `docs/product/STAGE_BOUNDARY_MATRIX.md`、`docs/delivery/STAGE_DECISION_POLICY.md`、當期 `STAGE_XX.md` 的七項控制卡。先核對目標、全部驗收、前版 Regression 和後續影響，再決定具體 API／Schema／Tool ；未經真實測試的技術細節只作參考。跨 A/B/I/U Owner 工作必須拆 Stage/PR。更新 PROJECT_STATUS 需要區分「實作 PASS／規格 PASS／NOT RUN」。

## Prompt A — Docs-only Baseline PR

> Inspect actual private GitHub `IssacSitHk/sunrise-education-ai-platform` main, branch/PR/Issues, historic ADR-001..010 and CODEOWNERS/CI. The uploaded Reviewed v0.7 is a proposed planning update; main is still v0.5. Open **docs-only** branch/PR mapping old Issues to new Stages, preserving old ADR-001..010, CODEOWNERS `@IssacSitHk`, existing `validate-docs` CI job and manual Squash Merge workflow; add ADR-011..021. Run `scripts/validate_docs.py`, contract/semantic mutation tests and get Owner approval. Do not deploy A/B, change production, auto-merge, or claim Stage0 runtime PoC. Record real PR evidence.

## Prompt B — S1 A-only Goal

> Only implement Stage1 owner A: pinned Open Notebook/SurrealDB/Files/Worker with one Admin HTTPS, mandatory Secrets fail-start, private native ON API, minimum Content Shell→unique Notebook, upload/classify/search/download source authorization before and after results including preview/SSE, A-only Restore. Use S1 Stage ATs, no B Postgres, no cross DB I, no teacher/student/generated papers. Full negative tests and restore, not one-hour completion promise. One A-only feature PR, all evidence/Owner signoff, no unapproved main merge or deploy.

## Prompt C — Owner-only Incremental Stage

> Read AGENTS/Stage Registry/Canonical API Inventory/current Stage spec/STATUS and actual released manifest. Verify earlier owner APIs and consumer tests. Implement exactly one current Owner runtime and real user workflow. If I calls A/B it must only use previously published signed HTTPS APIs; if contract missing, stop and propose earlier A-only/B-only release. Verify schema/API compatibility and expand/migrate/contract, owner-local restore and other-owner hashes unchanged. Update issue/docs/evidence; submit Draft PR, no unapproved merges.

## Prompt D — I S4 high-risk preflight

> BEFORE S4 code, require deployed S2 A/S3 B OpenAPI contract freeze with tests. Confirm B atomic Course+Op reserve CREATE_NEW, ADOPT_EXISTING uses existing Course, A Create op idempotent, same key/different body ->409, B Finalize idempotent. Design state transitions, failover and Core Reconciliation from contracts/state_machines/course_binding.json. Run fault injection at every commit/ACK; test read-after-write/A+B restore, old Shell/Source Hash unchanged, no direct DB egress in I, cutover write freeze. Do not claim ACTIVE on A success alone; do not postpone recovery to S28 Dashboard.

## v0.7.2 Contract Freeze warning for Work agents

> Do not begin S4 I until the actual A S2 and B S3 versions have provider/consumer contract tests passing for all called endpoints, including unique Binding, API resource ownership, ServiceToken (iss/aud/scope/exp/jti), idempotent retries, all required path/query/body parameters, binary streaming and typed success/failure schema checks. Current OpenAPI candidate files are not proof of those tests. Don't resolve a contract hole by adding raw SQL or borrowing an Admin Token. If a contract must change, create preceding owner-specific A/B Stage and update dependency/test mapping. Under R05, render only Course and Vault material functions; do not expose Assessment/Grade UI until their later owning Stages and the corresponding U Gate.


## S3/S6/S9/S17/S20/S22 focused repair prompt

> Treat v0.7.4 typed schema as *candidate*; before code compare it to actual service, implement only the current owner, test required operations plus forbidden scope, same-key different request, correct/incorrect grants, active/stale transitions and replay/revalidation. Record real provider evidence and freeze actual API in Owner Release Manifest. If missing another-owner API, do not change it in this Stage; file dependency and mark BLOCKED.
