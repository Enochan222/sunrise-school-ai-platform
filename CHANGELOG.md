# v0.7.3 — Stage goals, gates and collision control (document revision, NOT software release)

- 保留 S0–S28、A/B/I/U 單 Owner、80 項規劃 API、286 項設計驗收、既有 ADR-011..021 與 GitHub ADR 歷史不覆蓋。
- 29 份 Stage Spec 增加「目標／可試用成果／必過 Gate／風險／不可撞前期／未來影響／待決技術參考／Blocker」完整控制卡。
- 新增 `STAGE_CONTROL_MATRIX.json`、`STAGE_BOUNDARY_MATRIX.md` 及 Stage Go/No-Go policy，供人手／CI 獨立核對。
- OpenAPI/Queue/Key/Schema 等規劃細節標為 REFERENCE/TBD，**不削弱**必要的 Security、Data Ownership 和 Stage User Journey Gate。
- 原 v0.7.2 變更紀錄保留於下方；未做實際 API/DB/Restore/GitHub Merge。

# v0.7.2 — Engineering Contract Review, pending Owner approval

- Add canonical controlled A Materials GET and four I S4 proxy operations for Sunrise S5 UI; add B S22 private staff grant lookup.
- 80 total API operations now have per-operation typed request (where applicable), typed success and error responses, exact Path Parameter declarations and explicit JWT actor/service scope metadata. Downloads use binary response.
- Correct S5 AT01 early Grades/Assessment requirement. Protect I against borrowing Admin Session; S23 teacher access uses StaffSession and B private grant ServiceToken.
- Add contract freeze/negative tests for owner A S2/B S3 and I S4/I S23, service scope matrix and standalone engineering critical review.
- Preserve main historic ADR-001..010, GitHub `validate-docs` and CODEOWNERS. No GitHub mutation, DB/API/restore/UAT performed by this planning package.

# Changelog — Documentation Only

## Reviewed v0.7 — 2026-11-08 (not merged/deployed)

- Starts from uploaded `Sunrise_Master_Project_Kit_v0.7_Isolated_Stages.zip` with 24 planned Stages and Pasted architecture critique. Main Github README verified still v0.5; dedicated Docs PR required.
- Stage plan reorders to **S0–S28** for earlier I Course Linking (S4) / Sunrise UI (S5), then B question schema (S6), Gemini config (S7), B generation (S8), I evidence (S9), U generation (S10), B mathematics/chinese/english/general-studies (S11–S14), followed by Synthetic/Grades/Marking/Analytics and IAM/PII/governance.
- New canonical API Inventory and generated owner OpenAPI JSON, S4 distinct Create vs Adopt state machine, signed Evidence, Grade Event/Question Schemas and fixtures; revised risk/adversarial tests and QA semantic checks.
- Previous ZIP ADR-001..010 archived in docs/history, new ADR-011..021. Existing GitHub ADR-001..010 untouched; CODEOWNERS and `validate-docs` CI job retained in overlay.
- NOT RUN: actual A/B/I/U implementations, DB/HTTP security, E2E/Restore, independent Goldfish, Repo PR actions.


## v0.7.4 Targeted Contract Gap Remediation Candidate — 2026-11-08

Preserved S0–S28. Corrected Course vs TeachingGroup and school owner, B Blueprint/Rubric lifecycle, S8/S9 Worker Evidence ServiceToken and same-job revalidation, S17 Grade canonical hash rejection, S20 Weakness candidate/retire/discard API, S22 B StaffSession business rights, S26/S27 Health/Backup API for I S28, per-item S18 Marking and Stage tests. Historical v0.7.3a ZIP unverified, no live endpoint/DB work. 19 issue register added with explicit runtime blockers, plus focused tests and GitHub docs-only notes.


## v0.7.5 — Open Notebook Reuse-first & Stage Engineering Audit (2026-11-08)
- User-provided Open Notebook source statically inspected; evidence paths and reuse categories recorded; no runtime tests, no upstream commit equivalence claim.
- No stage renumbering; one-owner release R01–R28 unchanged; 100 candidate API operations and 310 AT cases unchanged.
- Fixed missing technical dependencies S21 S18/S19, S22 S18/S20, S24 S21, S27 S18/S20; updated Stage Registry/Control Matrix/Roadmap and stage specs.
- Added code-backed Reuse/Wrap/Build notes to 29 stages, no-rebuild constraints, owner-local trial UI vs U release distinction, and tests to prevent regressions.
- All Open Notebook authorisation/worker limitations are hard negative test requirements, not proven via actual runtime.
