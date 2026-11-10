# Stage 0 — Current repository and no-Actions operating contract

**Official new repo:** `Enochan222/sunrise-school-ai-platform` (private). The old `IssacSitHk/sunrise-education-ai-platform` repo is NOT the owner and is NOT to be migrated. Any inherited passages referring to the old repo, old Issues #4/#7, old ADR001–010, old GitHub Free/CI/CODEOWNERS, or old v0.5 baseline are **historical only and not executable operational guidance**. This document and root `AGENTS.md` take precedence.

**No GitHub Copilot or GitHub Actions.** The owner explicitly elected not to use either. Do not reintroduce `.github/workflows/docs-check.yml`, `.github/workflows/validate-docs.yml`, or a required status check on a disabled workflow. The local test runner does not automatically run when PRs are opened. Do not enable unconditional auto-merge or describe absence of status checks as equivalent security.

**Current decision:** 29 Stage planning specs, 100 candidate operations, 310 designed ATs; stages S1–S28 are NOT IMPLEMENTED. Stage 0 product approval is `PENDING`; no runtime testing, SQL/SurrealDB deployment, school-data import, backup/restore or AI provider spending took place.

**Repository control:** active `Protect main` Ruleset should demand pull requests with 0 code approvals, squash-only, no bypass, force-push and deletion prohibited, and required status checks OFF until an independent supported CI provider is adopted. Verify current settings before every merge.

**Local engineering Gate, with real executable evidence:** in a clean Python environment install `jsonschema==4.23.0` (or project-approved pinned compatible version), run `python scripts/run_qa_no_actions.py`, record stdout, Python version, source Commit SHA, hashes, results, and negative tests on PR. The Stage 0 planning checks are not UAT and do not substitute A/B/I/U runtime tests. If any test fails, do not merge. A separate reviewer is NOT automatically present.

**ADR numbering:** ADR-011..022 are in the v0.7.5 proposal. No ADR-001..010 from old GitHub was imported. Their absence is intentional. Do not renumber stage/ADR IDs without updating all references and QA.

**Owner decisions outstanding before S1:** Course vs TeachingGroup grain and academic stream; A Shell school ownership and Source policy; S1 Gemini optional vs B S7; S4 cutover path; hosting/security/cost, school privacy and Service boundaries. Owner makes these product/business decisions; GPT creates technical test evidence.

**Source ZIP:** sha256 `ee4d07d9e4d46fb9bf8c8b8f26c22413a4d2b0cca58acd0a45fc937da0b95bd5` from original v0.7.5; 149 original entries, copied source manifest in `docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256`. A migrated working tree is not byte-identical to source. See adapted `FILE_MANIFEST.sha256`.

**PR evidence card:** exact Stage & single owner, actual code/data or documents delivered, acceptance IDs, local QA commands plus stdout and SHA, negative test outcomes, regressions, remaining TBD, privacy/cost controls, manual release gates and rollback. Require no unverified automatic pass claim.

**Repeatable QA:** See [`docs/delivery/QA_ENVIRONMENT.md`](QA_ENVIRONMENT.md). Docker is a manual GPT/operator invocation, not a PR-triggered CI.
