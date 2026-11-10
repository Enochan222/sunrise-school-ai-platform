# ADR-020 — Fresh Enochan222 Repository and GPT-led Handoff

**Status:** OWNER DECISIONS RECORDED (repository owner, no Copilot, no GitHub Actions); Full S0 architecture sign-off PENDING. **Updated:** 2026-11-10. This revises the original v0.7.5 PROPOSED ADR-020's legacy GitHub preservation approach; original source text remains verifiable via original ZIP SHA and source manifest.

## Decision

Use only the new private repository `Enochan222/sunrise-school-ai-platform`. Do not copy old `IssacSitHk` repo commits/issues/ADR-001..010/CODEOWNERS. The v0.7.5 design proposals retain ADR identifiers 011..022, without asserting that omitted ADR001..010 exist or were approved.

The Owner chooses **no GitHub Copilot and no GitHub Actions**. GitHub Pro is independently subscribed but does not require either. Keep PR-only, squash-only, 0 technical approvals, no bypass, force pushes or deletion. Required status checks OFF while no independent check runner exists. Never imply local GPT execution is an enforced CI gate. Disabled Actions workflow files must be removed on import.

## Evidence and rejection boundary

Each PR should carry exact local code/test version, commands, stdout/stderr, negative cases and regressions, real runtime checks where applicable, and explicit NOT RUN where absent. AI self-review is not an independent security gate. Owner retains product, privacy, billing and irreversible deployment decisions but is not asked to approve code they cannot read. A/B/I/U boundaries and Stage dependency gates remain unchanged.

Do NOT claim S0 acceptance or S1 execution without real proof and required Owner architecture signoff. Stage0 remains documentation only.

[Current repo policy](../delivery/NEW_REPO_STAGE0.md) · [Stage0](../stages/STAGE_00.md)
