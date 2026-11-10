# Sunrise Stage0 agent operating contract — no GitHub Actions

- The active private repo is `Enochan222/sunrise-school-ai-platform`. Do not migrate prior `IssacSitHk` commit/Issue history. The exact v0.7.5 Master Kit has been verified **locally**, but is **not yet uploaded to this GitHub repository**.
- **No GitHub Copilot and no GitHub Actions by Owner decision.** Never add files under `.github/workflows/`, require `validate-docs` from disabled Actions, or claim local tests run automatically for each PR.
- The `Protect main` ruleset uses PR-only, squash, required human code approvals 0, prevents deletion and force-push. A green manual GPT check is not a GitHub-enforced status. Keep unattended auto-merge disabled without an independent CI/Webhook service.
- Stage S0 is documentation/governance only. S1–S28 runtime work is NOT IMPLEMENTED. Stage 0 product signoff remains PENDING. No backup/restore, A/B databases, paid AI providers or student records have been tested or authorized.
- GPT works on a feature branch, runs applicable actual checks, records full evidence and commit SHA, audits failures/negative paths, and proposes PR. The Owner decides product/security/privacy/cost and irreversible releases; no technical code-review expertise is required.
- The complete v0.7.5 29-Stage docs, 100 API candidates and 310 planned ATs become source-of-truth only after exact archive import, manifest check, QA and controlled squash merge. Do not substitute an old v0.7 archive.
- Design boundaries: A reuses Open Notebook with school/source policy; B owns grades/questions/learning records; I calls A and B only through APIs; U consumes APIs only.
- For every runtime Stage, require real service/environment and tests; a static QA result alone is not Stage acceptance.
