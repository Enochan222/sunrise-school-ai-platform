# Project Status — v0.7.5 No-Actions Candidate (as of 2026-11-10)

> **2026-11-14 operational notice (historical document preserved):** This file records an earlier Stage 0 setup snapshot. The active repository is now **PUBLIC**; Stage0 D01–D08 were approved within bounded planning, and the [later Stage 1 Limited CI Addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md) authorizes exactly two Stage 1 workflows despite historical D08. For current operational instructions use [AGENTS.md](../../AGENTS.md), [INSTRUCTIONS.md](../../INSTRUCTIONS.md) and [GitHub connection runbook](GITHUB_CONNECTION_RUNBOOK.md). Historical private/no-Actions/old-repository/NOT_STARTED statements below are not live status assertions. This notice does not alter the historical decision record or authorize release.


**Current repo:** `Enochan222/sunrise-school-ai-platform` (private). The former IssacSitHk repository is abandoned as active project source and none of its history is carried forward.

| Item | Evidence-based state |
|---|---|
| Initial GitHub bootstrap PR #1 | Merged to `main` as `bfeb8d2a010c8b34f2ead71a9baa61801096ff94`; historical Actions success before Owner disabled Actions |
| Deliberate failing PR #2 | Failed as intended, closed unmerged; historical evidence only |
| `Protect main` | Active with PR/squash/no-bypass/deletion/force restrictions; no Required Status Checks after Owner chose no Actions |
| Original v0.7.5 source ZIP | SHA-256 verified, 149 entries, 148 file hashes |
| Adapted no-Actions Master Kit | **Merged via PR #8** on 2026-11-10, `main` `5506c5b9487563cf23cebcc1785061f09c12b50a`; 164/164 exact-source Git Blob/hash verification completed |
| S0 Owner architecture/signoff | **APPROVED: D01–D08 bounded planning**, 2026-11-10 (chat authorization recorded in Issue #10); Stage0 planning COMPLETE after final approval PR |
| S1–S28 A/B/I/U runtime | NOT IMPLEMENTED / NOT DEPLOYED / NOT RUN |
| Provider API tests, real auth, real Restore, school PII | NOT RUN / NOT AUTHORIZED |

**Next:** Stage0 bounded D01–D08 product signoff **DONE**; import and technical evidence are also DONE. S1 **NOT STARTED**. Independent A-only offline/synthetic implementation can be proposed under a new S1 branch after this signed gate. **Before any S1 deployment or ingestion, hosting region, budget, secrets, network policy, content rights/retention and privacy approvals remain blocking decisions.** Stage1 must run real A-only security/source/index/search/Restore tests; see [Stage1 entry gate](STAGE1_START_CRITERIA.md). Upstream Open Notebook reference remains pinned at v1.15.1.

The source v0.7.5 plan includes 29 Stages, 100 candidate APIs and 310 planned ATs; these are document designs and NOT LIVE tests. See [current Stage0 policy](NEW_REPO_STAGE0.md) and [Reuse-first audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md).

## Stage 1 documentation preparation addendum (2026-11-12; not a GitHub PR)

Stage0 final signoff PR #11 was squash-merged into `main` at `744fbbd0ac3b479c80782d6a990c7bfed093f4dd`; preserve independent PR #8 provenance. **Stage1 Planning: COMPLETE; Implementation: NOT_STARTED; S1 Runtime AT01–15: NOT_RUN; R01: NOT_APPROVED.** The Stage1 [v1.1 handoff](../stage1/IMPLEMENTATION_PLAN.md) and [WORKBOARD](../stage1/WORKBOARD.md) do **not** certify their own Docs-only PR merge; use live GitHub PR/main records for Documentation Integration status. Publication of docs does not authorize runtime writes, production deployment, paid API or real school/student content.
