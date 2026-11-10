# Fresh GitHub repository — v0.7.5 import and PR plan

> **COMPLETION UPDATE 2026-11-10:** The docs-only import prescribed below **was completed by PR #8** and confirmed on GitHub `main` (164/164 source files). Numbered steps below are a historical import procedure, not an outstanding import task. Stage0 architecture/signoff is still pending; see [S0 evidence](STAGE0_EVIDENCE_2026-11-10.md).

The owner decided to use `Enochan222/sunrise-school-ai-platform` as the only current repository. Older `IssacSitHk` v0.5, Issue/PR/ADR-001–010 and `@IssacSitHk` CODEOWNERS material are NOT imported. Preserve versioned v0.7.5 ADR-011..022 **as proposals**; no implied owner approval or old GitHub history.

1. Validate original v0.7.5 ZIP CRC, safe paths, 149 source file entries, SHA-256 and the 148-line original source manifest. Keep provenance; do not commit ZIP or real school/student data.
2. Construct **docs-only PR** in the new repo with 29 Stage specs S0–S28, 100 candidate APIs, 310 planned ATs, 13 QA scripts, and reuse-first architecture. Do not deploy or implement runtime in S0.
3. Enforce live Owner policy from `docs/delivery/NEW_REPO_STAGE0.md`: GitHub Copilot OFF, GitHub Actions OFF, no `.github/workflows/*.yml`, status checks OFF, CODEOWNERS `@Enochan222`. PR required, squash-only, protected main, no forced push.
4. Run `python scripts/run_qa_no_actions.py` against exact proposed HEAD; preserve command output and hashes. Local tests are **not GitHub enforced**. Do not auto-merge without a trusted enforcement source.
5. Open PR with changes and evidence; Owner approves product/security/cost decisions (no requirement for human source review). Report any missing true runtime test as NOT RUN.
6. After merged docs+product approval, allow S1 A-only secure Open Notebook deployment via another Stage PR. Do not claim full release merely from static documentation checks.

**Do not resurrect the prior `validate-docs` CI / GitHub Free private policy or historical ADR preservation instructions from old kit.** All former instructions are superseded by this new-repository project decision.
