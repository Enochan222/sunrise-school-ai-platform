# Release Policy — Reviewed v0.7 / R01–R28

> **S0 SIGNOFF UPDATE (2026-11-10):** Owner has approved only the **bounded D01–D08 planning decisions** in [Stage0 approval packet](../decisions/STAGE0_APPROVAL_DECISIONS.md). Candidate ADR-011–022 implementation details remain proposals unless independently accepted. No deployment, spend, production school content, or student PII has been authorized.

> **CURRENT PUBLIC SOURCE NOTICE (2026-11-14):** Active repository is PUBLIC. Original 2026-11-10 Stage0 D08 no-Actions choice stays in the historical approval, with a later [Stage1 Limited CI Addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md) authorising exactly two workflows. GitHub Copilot, extra workflows, paid usage, unattended merge and public production data remain unapproved.

**Stage0** = planning/Repo/Owner approval only; NO compulsory runtime Staging, Gateway PoC, DB/Restore. **Runtime Releases R01–R28** = each one owner A/B/I/U changes; each must deliver a real usable journey, data persistence, negative/security tests, owner-local backup restore, prior Release regression, schema/API compatibility, actual Staging evidence + Owner approval. A one-hour Spike isn't release acceptance.

## Stage Release 新增 Go／No-Go 規則

本版 [Stage 控制總表](../product/STAGE_BOUNDARY_MATRIX.md) 將每個 Release 的**核心可試用成果、當期必要驗收、前版衝突、後續依賴**明確化。審批人應先查控制卡，再查逐項 AT；任何一項安全、權威資料、隔離或恢復 Gate FAIL，都不能以其他功能完成或留下一 Stage 補救替代。

**交付三態：** `PASS`（真實部署與測試證據齊全）；`BLOCKED`（核心 Gate FAIL／跨 Owner／危及歷史數據）；`PLANNED/NOT RUN`（規格已清楚，尚未執行）。技術參考沒有核實時一律 `TBD`，但如果會影響當期核心 Gate，不得標 PASS。

## Version manifest

Every Release records: `manifest_id Rnn`, `stage`, `owner_track`, Git SHA & image digest **for all four services**, changed owner's `db_migration_hash`, `schema_version` and minimal compatible API version, dependent OpenAPI contract versions and contract test SHAs, feature flags and their rollback state, deployment date/env, security/auth/data classification, Backup/Restore Snapshot IDs and RPO/RTO observed, Data Migration/Expand→Migrate→Contract compatibility, user UAT, failing tests/deferrals, human signoff. **Only one runtime owner SHA/Image/Config/Schema** may change compared with previous manifest, and any owner-specific migration requiring a second owner goes into another Stage, not a mixed PR. Data migrations may make old image rollback unsafe; use forward fix, write freeze or tested compatibility downgrade, never assume image revert suffices.

## Source of Truth and pull requests

The only current source of truth is public GitHub `Enochan222/sunrise-school-ai-platform`; reviewed 164-file v0.7.5 kit was merged through PR #8 on 2026-11-10. Historical `IssacSitHk`, v0.5, and old ADR-001..010 remain **outside** this repo. Current active ADR-011..022 are **proposals**, not all Owner-approved. Keep `.github/CODEOWNERS` targeting `@Enochan222`, protected PR/squash-only `main`, no Copilot and **only the two separately approved Stage1 CI workflows** under the later Owner addendum. Local GPT-run QA is not a GitHub-enforced PR check; do not unattended-auto-merge, auto-deploy, spend, or import real student data. See [S0 decisions](../decisions/STAGE0_APPROVAL_DECISIONS.md).

## Stage-critical gates

- S1: A private Open Notebook API, Secrets FAIL STARTUP, Source Ownership before+after Search/Stream/Download, A Restore.
- S2/S3: A/B respective APIs freeze and consumer test; S3 B Course `CONTENT_UNLINKED`, B Course+Operation Reserve atomic.
- S4: CREATE_NEW/ADOPT_EXISTING operations, core reconciliation, crash-injection & cross-service restore checks by API. S28 Dashboard is later UI only.
- S9: Evidence signed/version-pinned/TOCTOU/prompt-injection; A/B crypto/runtime verification must pass before use, not only Schema.
- S17: Grade DB INSERT-only, CAS Correction; S20 Weakness Keep2 separate from historical Analytics.
- S22/S23: staff scope and revocation; S25 real PII hard school consent/provider/privacy gate.

A separate U-only release is necessary for newly added Sunrise frontend capability: S5 Course/Content, S10 Generation, S21 Assessment/Analytics, S24 Teacher. New B feature is still useful via its own protected B local UI until a U release adds it.


## v0.7.4 independent contract gate

For each Stage owner, verify **published API consumers can perform the preceding Stage promise**, not just that endpoint exists. Any changed B Course grain / Staff permission / Grade Hash / Evidence status must first pass owner-specific provider tests + negative actor/scope tests; I/U code cannot patch that missing contract. A failed owner Stage means following consumers are blocked, not conditionally marked done. No Runtime acceptance or independent reviewer claimed by packaging QA.

## Public source and release boundary (2026-11-14)

Public Git access does **not** expose private Sunrise Gateway, Mac localhost, A/ON physical DBs, school/student information, real teaching material, backups or signing keys. The approved Stage1 Light workflow only tests its recorded non-native checkout (`tests/stage1`, not complete `pytest tests`). Record Head SHA, synthetic merge-result checkout SHA, Tested Revision, runtime identity and post-squash `main` separately. CI PASS cannot imply real Browser, strict TLS/IDOR, independent Restore, formal S1-AT01–15, independent review, Owner UAT or R01. Stage0 original D01–D08 wording remains unchanged; only the scope-limited later CI amendment overrides historical Actions prohibition for S1. No auto-merge, paid settings or new workflows.
