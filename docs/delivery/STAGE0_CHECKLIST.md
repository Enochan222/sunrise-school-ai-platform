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
- [ ] Owner explicitly approves required Course/TeachingGroup, school ownership, S1 Gemini option, S4 Cutover, hosting/privacy/cost decisions.
- [ ] Stage0 approval with actual GitHub docs PR and evidence. S1 stays NOT IMPLEMENTED until its own real A tests pass.

**Live S0 acceptance:** [Evidence and AT matrix](STAGE0_EVIDENCE_2026-11-10.md); [Owner signature decisions](../decisions/STAGE0_APPROVAL_DECISIONS.md); [S1 entry checklist](STAGE1_START_CRITERIA.md). **Product approval still PENDING**; no Stage 1 runtime work authorized by static checks.

**No independent merge gate:** GitHub cannot automatically block untested PRs without an external service. Avoid unattended PR auto-merge. GPT's local QA output is evidence, not independently-enforced status.
