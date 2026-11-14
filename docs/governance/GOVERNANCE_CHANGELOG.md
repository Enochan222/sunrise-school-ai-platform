# GOVERNANCE_CHANGELOG — Public Repository Instructions Repair

**Scope and source:** docs/governance-only changes based on live `main` `b8c3d984b31ed7ef073ceecfe398f1002d962d01`. This change is not an acceptance/release or workflow-code authorization.

**Changed existing files:** root `AGENTS.md`, `INSTRUCTIONS.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`; `.github/PULL_REQUEST_TEMPLATE.md`; `docs/delivery/GITHUB_CONNECTION_RUNBOOK.md`, `RELEASE_POLICY.md`, `NEW_REPO_STAGE0.md`, `REPO_SETUP.md`, `PROJECT_STATUS.md`, `HANDOVER.md`; `docs/stage1/evidence/README.md`; and generated `FILE_MANIFEST.sha256` for the changed docs. **New documentation:** six `docs/governance/*.md` audit/QA/alignment files.

**Purpose:** state PUBLIC read vs authorised write/local runtime; preserve historical Stage0 D08 text while recognising later Stage1-only CI, without permitting additional workflows or paid usage; distinguish PR Head / checkout merge-result / Tested Revision / post-squash SHA; repair public security disclosure and credential-revocation guidance; keep native/Restore/AT/UAT/R01 gates distinct; mark historical operations as superseded without rewriting substantive decisions.

**Immutable boundaries:** `docs/decisions/STAGE0_APPROVAL_DECISIONS.md` unchanged; Stage Registry S0–S28 and A/B/I/U owner boundaries unchanged; Open Notebook reuse-first and Stage1 A-only dual physical SurrealDB, strict Gateway/TLS/School IDOR/JWT/CSRF, independent Restore and S1-AT01–15 unchanged. No `.github/workflows/*`, `scripts/*`, `apps/*`, tests, PR14/24 engineering branch, billing, Merge or R01 were modified.

**Known blocked QA:** The existing Python `scripts/verify_kit.py` still asserts the old Draft-skip CI guard, conflicting with the already merged later addendum; full repository QA is not run without an actual clean checkout. Leave documentation PR Draft until current QA/manifest and independent review pass. See [test report](GOVERNANCE_TEST_REPORT.md) and [CI workflow repair](CI_WORKFLOW_REPAIR_REQUIRED.md).
