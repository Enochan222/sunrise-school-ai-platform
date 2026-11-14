# Sunrise PR — Evidence-gated / limited Stage 1 CI

**Stage / single Owner / change scope:**
**User-visible outcome and affected contracts / S1-AT IDs:**
**Base branch and exact base SHA:**
**Full Source HEAD SHA and Git tree:**
**Tested Revision (commit or independently hashed snapshot):**
**Final PR Head SHA (reviewer live read, not self-changing evidence):**
**Actions PR merge-result SHA (if any; never substitute for Head):**
**Changed paths and Git Blob SHAs:**
**CI workflow name / run URL / job / event / trigger / tested checkout SHA / status (or NOT_RUN):**
**Non-Native Regression (`pytest tests` vs `pytest tests/stage1` clearly distinguished):**
**Runtime / browser / strict TLS / Native / independent restore evidence (or NOT_RUN):**
**Security negatives: School/Source IDOR, JWT, CSRF, gateway isolation, secret exposure:**
**Tests not run, known failures, regression impact and remaining blockers:**
**Independent reviewer, method, source identity and result (or PENDING):**
**Owner approval scope, product/security/cost/PII approvals (or PENDING):**
**Formal S1-AT / Owner UAT / R01 status (default NOT_APPROVED):**
**Rollback / forward-fix and downstream compatibility:**

- [ ] Current merged Owner decisions and [Stage 1 Limited CI Addendum](../docs/decisions/STAGE1_LIMITED_CI_ADDENDUM.md) checked; original Stage 0 D01–D08 unchanged.
- [ ] CI_PASS, NON_NATIVE_REGRESSION_PASS, NATIVE_RUNTIME_PASS, FORMAL_AT_PASS, INDEPENDENT_REVIEW_PASS, OWNER_UAT_APPROVED and R01_APPROVED independently assessed, not inferred from one another.
- [ ] PR HEAD vs tested revision vs Actions merge-result SHA vs eventual squash merge commit identified separately.
- [ ] Applicable local QA, source/contract regression and negative tests executed; missing tests explicitly NOT_RUN.
- [ ] Exactly one runtime Owner where applicable; no unapproved A/B/I/U cross-database access.
- [ ] No secrets, real student data, copyrighted originals, raw backups or private logs in source, PR comments, CI logs or artifacts.
- [ ] Protect main: human PR/squash only, no auto-merge, no force-push/deletion/bypass; Owner release authority retained.

Only two Stage 1 workflows are authorized; Light CI targets PRs to `main` with specified code paths and runs `tests/stage1` only. PRs targeting an implementation branch (such as PR #24) are not covered by that trigger. Manual Native workflow may require separate dual-DB compatibility repair; do not treat its existence as a passing runtime test. No GitHub Copilot or additional paid Actions authorized.
