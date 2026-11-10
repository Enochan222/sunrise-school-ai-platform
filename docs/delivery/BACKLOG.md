# Backlog — Proposed v0.7 Reviewed (not created as GitHub Issues)

One Stage→one Owner Feature Branch/Release; issues may be broken down further within that owner. Scope Gate for S4/S9/S23 must confirm prior contract freeze. Do not auto-overwrite live v0.5 GitHub Issues: use [PR/Issue Plan](GITHUB_BASELINE_PR_PLAN.md).

| Issue template ID | Track | Prerequisites | Deliverable | AT Reference |
|---|---|---|---|---|
| S00-P-WORK | P | — | Planning Baseline & Security Decisions | S0-AT01..AT10 |
| S01-A-WORK | A | S0 | Secure Open Notebook Vault | S1-AT01..AT15 |
| S02-A-WORK | A | S1 | Versioned Content Catalog & A Contract Freeze | S2-AT01..AT15 |
| S03-B-WORK | B | S0 | Independent Academic Course & B Contract Freeze | S3-AT01..AT17 |
| S04-I-WORK | I | S2, S3 | Course–Content Linking & Core Recovery | S4-AT01..AT21 |
| S05-U-WORK | U | S4 | Sunrise Course & Content Admin Portal | S5-AT01..AT12 |
| S06-B-WORK | B | S3 | Question/Answer/Rubric Schema Studio | S6-AT01..AT09 |
| S07-B-WORK | B | S3 | AI Provider Key & Capability Settings | S7-AT01..AT07 |
| S08-B-WORK | B | S6, S7 | Durable Generation Queue & Draft Review | S8-AT01..AT13 |
| S09-I-WORK | I | S4, S8 | Version-pinned Notebook Evidence Bridge | S9-AT01..AT15 |
| S10-U-WORK | U | S5, S9 | Sunrise Generation & Evidence Workspace | S10-AT01..AT07 |
| S11-B-WORK | B | S6, S8 | Mathematics Paper Builder & PDF | S11-AT01..AT10 |
| S12-B-WORK | B | S11 | Chinese Language Paper Adapter | S12-AT01..AT08 |
| S13-B-WORK | B | S11 | English Language Paper Adapter | S13-AT01..AT08 |
| S14-B-WORK | B | S11 | General Studies Paper Adapter | S14-AT01..AT08 |
| S15-B-WORK | B | S3 | Synthetic Student Roster | S15-AT01..AT10 |
| S16-B-WORK | B | S6, S15 | Assessment & Score Drafts | S16-AT01..AT09 |
| S17-B-WORK | B | S16 | Append-only Grade Events & Corrections | S17-AT01..AT12 |
| S18-B-WORK | B | S11, S17 | Submissions & Manual Marking | S18-AT01..AT11 |
| S19-B-WORK | B | S18, S8 | AI-assisted Marking Benchmark & Review | S19-AT01..AT09 |
| S20-B-WORK | B | S17 | Deterministic Analytics & Weakness Keep-two | S20-AT01..AT11 |
| S21-U-WORK | U | S10, S17, S18, S19, S20 | Sunrise Assessment/Analytics Workspace | S21-AT01..AT07 |
| S22-B-WORK | B | S3, S17, S18, S20 | Staff IAM, Grants & B Authorization | S22-AT01..AT12 |
| S23-I-WORK | I | S4, S22 | Teacher Read-only Course Content | S23-AT01..AT13 |
| S24-U-WORK | U | S5, S21, S23 | Sunrise Teacher Portal UI | S24-AT01..AT06 |
| S25-B-WORK | B | S22, S23, S24 | Approved Real Student Data Gate | S25-AT01..AT08 |
| S26-A-WORK | A | S2 | Content Retention & Annual Archive Tools | S26-AT01..AT09 |
| S27-B-WORK | B | S17, S18, S20, S25 | Academic Year Closing & Grade Retention | S27-AT01..AT09 |
| S28-I-WORK | I | S4, S26, S27 | Cross-service Health/Restore Dashboard | S28-AT01..AT09 |


## Issue 裏必須新增的欄位（逐 Stage 控制卡）

每個 `Sxx-Owner-WORK` Issue 除原有 AT 外，需引用 [控制卡](../product/STAGE_BOUNDARY_MATRIX.md)，逐項確認：**本期最小試用流程、必過 Gate、前版不可被影響的流程、必須預留的後續 Contract、目前仍是 Reference 的技術方案、停止／拆 Stage 條件**。不能把「盡量試」當完成標準；也不能預先決定所有未實測細節。

**Implementation blockers:** S1 native API bypass/Secrets; S2/S3 frozen Contract; S4 Saga statuses/dual restore; S9 Evidence TOCTOU; S23 Grant revocation; S25 PII approval. Each release needs user journey+negative tests+owner restore+rollout compatibility, not elapsed-time target.


## v0.7.4 contract-first backlog and blocking issues

See [19-row CSV](CONTRACT_REPAIR_BACKLOG.csv) (NOT executed issues). Must first approve CG-03/08/09/10 at S0 then implement owner A S1–S2, owner B S3/S6/S8/S15–20/S22/S27, owner I S4/S9/S23/S28 separately. A passing document QA cannot mark a provider API, staff grant or DB CAS as done.
