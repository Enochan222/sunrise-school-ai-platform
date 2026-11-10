# Stage 0 — Acceptance Checklist (Current Repo)

This is the new Enochan222 Stage0 record; see also `docs/stages/STAGE_00.md` acceptance IDs S0-AT01..S0-AT10.

- [x] New private GitHub Repo initialized; old commits/PRs/Issue/ADR history NOT imported.
- [x] Current `Protect main` Ruleset uses PR-only, squash, no-bypass, force-push/delete blocked (actual enforcement requires testing against plan).
- [x] Owner decided no GitHub Copilot / no GitHub Actions. Required Checks disabled.
- [x] Original v0.7.5 ZIP safe-extracted, SHA verified, 149 entries, 148 original digest entries; migrated local package complete.
- [x] 29 Stage specs, 100 proposed APIs, 310 designed acceptance IDs included in local candidate.
- [x] Original source QA and new No-Actions local tests run; evidence is **local** only, no GitHub CI or real runtime.
- [ ] Import fully prepared local candidate into `Enochan222` via docs-only PR; compare remote branch/tree and inspect Merge state. Existing GitHub connector cannot upload a local folder/ZIP directly.
- [ ] Ensure all source/manifests, 13 QA scripts and zero Actions workflows are present in final merged GitHub `main`.
- [ ] Owner explicitly approves required Course/TeachingGroup, school ownership, S1 Gemini option, S4 Cutover, hosting/privacy/cost decisions.
- [ ] Stage0 approval with actual GitHub docs PR and evidence. S1 stays NOT IMPLEMENTED until its own real A tests pass.

**No independent merge gate:** GitHub cannot automatically block untested PRs without an external service. Avoid unattended PR auto-merge. GPT's local QA output is evidence, not independently-enforced status.
