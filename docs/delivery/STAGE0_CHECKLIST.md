# Stage 0 — Acceptance and Evidence

This checklist is a bootstrap supplement, not a replacement for the 29 Stage Specs in v0.7.5.

- [x] New private repository at `Enochan222/sunrise-school-ai-platform`; no old repo imported.
- [x] New default branch `main` initialized with README and gitignore.
- [ ] **Exact v0.7.5 ZIP** available, archive CRC/path safety/SHA-256 verified and all files imported via docs-only PR.
- [ ] 29 Stage documents S0–S28, 100 candidate APIs, 310 designed ATs and Owner dependency matrix present (NOT actual runtime UAT).
- [ ] Owner explicitly approves Course/TeachingGroup, A school ownership, S1 optional Gemini/embedding, S4 Cutover and budget/security choices.
- [ ] GitHub Actions `validate-docs` has a verified successful PR run and real logs.
- [ ] Deliberately broken PR fails CI and is **not merged**.
- [ ] `Protect main` enforceable with required `validate-docs` status, no bypass/force-push and squash-only; test actual enforcement, not only Active appearance.
- [ ] Full Master Kit CI tests (Stage Registry, contract/schema fixtures, negative mutations) pass on imported-source PR.
- [ ] Stage 0 accepted with evidence in its Issue. Stage 1 remains NOT STARTED and requires A-only real implementation/Restore.

**Important:** A green bootstrap CI result is not a Stage 0 release approval. Owner does not need to manually review code but retains authority for product requirements, data privacy, billing and production changes.
