# Stage 0 — engineering evidence and acceptance matrix (2026-11-10)

**Status: S0 DOCUMENT PLANNING COMPLETE — OWNER APPROVED D01–D08 (2026-11-10).** This is S0 [P] planning/Repo/security review only. No A/B/I/U runtime is implemented, deployed or accepted. See [formal S0 spec](../stages/STAGE_00.md), [decision packet](../decisions/STAGE0_APPROVAL_DECISIONS.md), and [S1 start gate](STAGE1_START_CRITERIA.md).

## Sources, independent verification and provenance

1. Current authorized repo `Enochan222/sunrise-school-ai-platform`, private `main`, import [PR #8](https://github.com/Enochan222/sunrise-school-ai-platform/pull/8) squash-merged 2026-11-10 at commit `5506c5b9487563cf23cebcc1785061f09c12b50a`. Prior unrelated `docs/delivery/GITHUB_CONNECTION_RUNBOOK.md` preserved. No old `IssacSitHk` Git history.
2. Adapted ZIP SHA-256 `40c0b17a54b5d199a7ec58b91dcdcb4738a8d94c44755cbdacc4ba22a89ab1cf`: **164/164 source files** compared against `main` paths and Git Blob hashes; `FILE_MANIFEST.sha256` **163/163** before this S0 closeout delta. Git Tree contains one additional pre-existing runbook. Changes in *this closeout PR* intentionally extend the adapted source and require refreshed manifest hashes; historical PR #8 provenance is retained by Git history.
3. [Stage Registry](../quality/STAGE_REGISTRY.json): S0–S28 = 29; [Stage Control Matrix](../quality/STAGE_CONTROL_MATRIX.json): 29; [API Inventory](../architecture/API_INVENTORY.json): 100 *candidate* operations; [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md): 310 *planned*, not executed, acceptance IDs.
4. GitHub Ruleset `Protect main` ID `26914637` checked Active: default branch target, PR required, approvals=0, squash only, no bypass actors, deletion and force-push denied; no required GitHub Actions status check. No tracked `.github/workflows` YAML. **Caveat:** Without another CI provider, GitHub does not independently block a PR whose GPT-run tests fail. Never unattended-auto-merge.
5. Actual source static QA: `python scripts/run_qa_no_actions.py` 16/16 PASS on Python 3.12.14 (Work PR #8) and independently Python 3.13.5; `python scripts/verify_kit.py` 1,722/1,722 on the imported 164-file baseline; negative source corruption and missing Stage samples correctly failed. Docker-pinned Python 3.11.11 **NOT RUN**; runtime, auth/restore, E2E, student-data tests **NOT RUN**. These are document/contract tests, not system implementation.
6. **Exact upstream provenance independently established:** user-provided `open-notebook-main(1).zip` SHA-256 `db552e1f492af158918c503be873eeb531c8673394a1bab0df31f0412e6bd04d` contains 648 files; reconstructing its Git file modes, blobs and nested trees yields Git tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af`. This **exactly equals** GitHub official [lfnovo/open-notebook v1.15.1](https://github.com/lfnovo/open-notebook/releases/tag/v1.15.1) commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239` (released 2026-11-04). Repository license metadata: **MIT**. Future S1 uses this pinned source as **starting reference**, rechecks license/third-party assets and hashes, and must perform actual Auth, Source-scope, Search and Restore tests; latest `main` is NOT a substitute.

## S0 AT assessment (design evidence versus Owner acceptance)

| ID | Stage 0 evidence | Engineering | Owner gate |
|---|---|---|---|
| S0-AT01 | Uploaded Open Notebook ZIP **exact** official v1.15.1 tree, MIT repo metadata, explicit unsafe native-route limitations | PASS | S1 source-security trials still NOT RUN |
| S0-AT02 | A SurrealDB and B PostgreSQL/credentials/backups isolated; I may use only published scoped APIs | DOCUMENT PASS | D01/D03 **APPROVED** (planning only) |
| S0-AT03 | 29 Stage Registry/Owner/technical dependency structure checked; one runtime owner per Stage | PASS | D01 **APPROVED** |
| S0-AT04 | S1 A only; S2 A, S3 B, S4 I only after provider contracts; S5 U | PASS | D01/D05/D06 **APPROVED** |
| S0-AT05 | Protected GitHub main, secret policy, CODEOWNERS, PR templates verified; no Actions/status check as requested | PASS with stated lack of independent merge QA | D08 **APPROVED**; no server-enforced GPT QA |
| S0-AT06 | Planning documents imported; Owner D01–D08 signed; S1–S28 runtime still NOT RUN | PASS | **S0 approved; runtime NOT AUTHORIZED** |
| S0-AT07 | 12 current ADR-011..022 retained as candidate documents; bounded D01–D08 approved, implementation-specific ADR details still proposed | PASS for completeness | **D01–D08 approved; candidate ADR freeze deferred** |
| S0-AT08 | New Enochan222 repo and PR #8 verified, no old history imported | PASS | Owner D08 **APPROVED** |
| S0-AT09 | All S0 tests explicitly design/document only, no staging or DB/Restore requirement | PASS | Owner D07 **APPROVED**; no deployment permission |
| S0-AT10 | Course/Group grain, mandatory A school owner, optional S1 Gemini, I-only S4 cutover described | PASS for design | D02/D03/D05/D06 **APPROVED** |

**Release decision: S0 DOCUMENT PLANNING GO — bounded Owner D01–D08 signoff received.** [Formal decision packet](../decisions/STAGE0_APPROVAL_DECISIONS.md), [Issue #10](https://github.com/Enochan222/sunrise-school-ai-platform/issues/10) and [Stage0 baseline](../../stage0/STAGE0_BASELINE.json) record **APPROVED / COMPLETE**. This closes S0-AT01..AT10 **as design/document-review gates**, not 10 runtime feature tests. S1 is **NOT STARTED**; only separate A-only offline synthetic work is eligible to begin. External hosting, spend, real student data, paid AI, licensing and deployment all remain separately unauthorized. No GitHub Actions/Copilot or unattended PR auto-merge. Before S1 deployment, resolve the explicit [S1 prerequisites](STAGE1_START_CRITERIA.md).
