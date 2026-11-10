# Stage 0 — Acceptance Checklist (Current Repo)

This is the new Enochan222 Stage0 record; see also `docs/stages/STAGE_00.md` acceptance IDs S0-AT01..S0-AT10.

- [x] New private GitHub Repo initialized; old commits/PRs/Issue/ADR history NOT imported.
- [x] Current `Protect main` Ruleset uses PR-only, squash, no-bypass, force-push/delete blocked (actual enforcement requires testing against plan).
- [x] Owner decided no GitHub Copilot / no GitHub Actions. Required Checks disabled.
- [x] Original v0.7.5 ZIP safe-extracted, SHA verified, 149 entries, 148 original digest entries; migrated local package complete.
- [x] 29 Stage specs, 100 proposed APIs, 310 designed acceptance IDs included in local candidate.
- [x] Original source QA and new No-Actions local tests run; evidence is **local** only, no GitHub CI or real runtime.
- [x] Exact 164-file adapted kit imported to `main` via [PR #8](https://github.com/Enochan222/sunrise-school-ai-platform/pull/8), Squash Merge `5506c5b9487563cf23cebcc1785061f09c12b50a`; all 164 source paths and Git Blob hashes independently matched remote; original runbook preserved.
- [x] `FILE_MANIFEST.sha256`, source documents and QA scripts exist on merged `main`; zero tracked GitHub Actions workflows; 16/16 QA groups PASS locally (Python 3.12.14 in PR #8; independently Python 3.13.5); Docker 3.11.11 NOT RUN.
- [x] Owner explicitly approved bounded D01–D08 planning/architecture/security decisions on 2026-11-10; [Issue #10](https://github.com/Enochan222/sunrise-school-ai-platform/issues/10) records the chat authorization. Specific hosting region, numeric budget, school license/retention and privacy choices remain mandatory **S1 predeployment blockers**, not Stage0 spending approval.
- [x] Stage0 bounded Owner approval received and signed in [decision packet](../decisions/STAGE0_APPROVAL_DECISIONS.md), `stage0/STAGE0_BASELINE.json` and [S0 AT evidence](STAGE0_EVIDENCE_2026-11-10.md); final approval PR documents/validates this. S1 remains NOT STARTED and all runtime tests NOT RUN.

**Live S0 acceptance:** [Evidence and AT matrix](STAGE0_EVIDENCE_2026-11-10.md); [Owner signature decisions](../decisions/STAGE0_APPROVAL_DECISIONS.md); [S1 entry checklist](STAGE1_START_CRITERIA.md). **Product approval APPROVED for D01–D08 only; Stage0 COMPLETE as planning**, with no spending, live deployment or school/student data permission. S1 runtime still NOT RUN.

**No independent merge gate:** GitHub cannot automatically block untested PRs without an external service. Avoid unattended PR auto-merge. GPT's local QA output is evidence, not independently-enforced status.
