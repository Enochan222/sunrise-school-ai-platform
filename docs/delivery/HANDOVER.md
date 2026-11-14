# Engineer Handover — Reviewed v0.7

> **2026-11-14 HISTORICAL / SUPERSEDED OPERATIONAL SNAPSHOT:** The 2026-11-10/12 status and D08 terms below are preserved as historical evidence. References to a *private* active repo, universal *no Actions*, obsolete `validate-docs` CI or Stage1 forever NOT_STARTED are **not current operating instructions**. Current repository is PUBLIC; only two approved Stage1 workflows may run under [current instructions](../../INSTRUCTIONS.md), [security](../../SECURITY.md), [CI addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md). Do not rewrite original D01–D08 decision text. Live `main` and applicable Stage acceptance contracts govern; prior statuses and commits are snapshots.

> **CURRENT REPOSITORY OVERRIDE (2026-11-10):** Active repo is `Enochan222/sunrise-school-ai-platform`; no GitHub Copilot/Actions; local QA must be executed and evidenced; old repo, old CI, old ADR references below are historical only. Read [current Stage0 rules](NEW_REPO_STAGE0.md).

**CURRENT HANDOVER GATE (2026-11-10):** The 164-file v0.7.5 planning kit is merged in new `Enochan222` repo PR #8. No `validate-docs` GitHub Actions job and no migrated old ADR 001–010. Before S1 coding: confirm [S0 Owner approvals](../decisions/STAGE0_APPROVAL_DECISIONS.md) and [Stage1 start criteria](STAGE1_START_CRITERIA.md); verify latest GitHub `main`, full QA evidence and security controls. Never treat proposed contracts as live deployment; Stage 1 can begin only after S0 signoff, in an A-only Stage PR.

## 接手者最先核對的 Stage Go／No-Go

以 [29 Stage 控制總表](../product/STAGE_BOUNDARY_MATRIX.md) 和當期 `STAGE_XX.md` 控制卡為交接主體；每一期都要講清楚「**可試用咩、點測、唔准整到邊舊舊功能、留咩接口畀下一期**」。原有 API／Schema／Token／模型詳細欄位仍屬 `TYPED_CANDIDATE/REFERENCE`，不因文件寫得仔細就視作凍結。Owner 在該 Stage 的真 Runtime Gate 中決定／確認細節。

**Blocker escalation：** 若某 Stage 必須修改另一 Owner，立即停止、開獨立 Stage/ADR，不得以「暫時參考」掩蓋當期核心功能已無法交付。

Next approved implementation once Owner signs S0 revised model: **S1 A only** Open Notebook/SurrealDB, private Vue/React or native safe Vault Content Shell screen, Admin HTTPS, Sources/Hash/Search, fail-start secrets and A Restore. S2 A catalog/API contract. S3 B Postgres Course/TeachingGroup/bindings reserve/ops API but no A call; independent B Restores. S4 I-only performs link/Create via those APIs, durable operation and core recovery. S5 U Sunrise Course Portal. B Question S6, Gemini Key S7, Queue S8, optional I evidence S9, U Generation S10. Four subject B S11–14 before Synthetic and IAM.

Every Stage follows its [Stage Spec](../product/ROADMAP.md) and [API Inventory](../architecture/API_INVENTORY.json), one owner runtime diff with contract freeze/prereqs, real negative tests and rollback/restore evidence. If I needs unexpected owner APIs, stop, create separate owner-only Release. Screenshots or CI success do not equal actual Deployment. Current Project Status is NOT IMPLEMENTED.


## v0.7.4 delta for engineer

Read [Contract Gap Register](../quality/CONTRACT_GAP_REMEDIATION.md) before any owner-stage code. Before I S4, A S2 and B S3 need real contract tests; before I S9, B S8 Worker identity, Blueprint and Evidence input; before U S21, B S20 Weakness full API; before I S23, B S22 **real StaffSession on business APIs**. All current OpenAPI paths/DTOs are **design candidates** until owner provider tests and approval. Never use AdminSession/Service Role to bypass restricted staff or worker operation. See [Grade Idempotency](../architecture/GRADE_IDEMPOTENCY.md) and [Evidence Revalidation](../architecture/EVIDENCE_REVALIDATION.md).


**v0.7.5 handover requirement:** Show a code-backed REUSE/WRAP/BUILD assessment before implementing S1/S2; do not start by cloning Open Notebook into a new RAG app. Check A native direct routes, source multi-notebook linking and search global fallback. S21/S22/S24/S27 dependency fixes in Stage Registry are now contract guards. See `docs/delivery/STAGE_FLOW_ENGINEERING_AUDIT.md`.
