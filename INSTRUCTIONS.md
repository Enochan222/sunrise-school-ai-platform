# Handover Execution Rules

> **CURRENT REPOSITORY OVERRIDE (2026-11-10):** Active repo is `Enochan222/sunrise-school-ai-platform`; no GitHub Copilot/Actions; local QA must be executed and evidenced; old repo, old CI, old ADR references below are historical only. Read [current Stage0 rules](docs/delivery/NEW_REPO_STAGE0.md).

Before starting implementation, reconcile live GitHub **v0.5** with proposed reviewed v0.7 in a **docs-only PR**. Reuse `validate-docs`, `.github/CODEOWNERS` and manual PR/squash workflow; do not modify old ADR-001..010. Stage0 itself needs **documents, configuration/ownership checks and signoff only, no running DB/restore/PoC**. S1 must use private A Vault API + security hard gate; B first deployed S3; I first deployed S4; U first deployed S5. Use `docs/product/ROADMAP.md`, `docs/quality/STAGE_REGISTRY.json` and `docs/architecture/API_INVENTORY.json` as canonical data. No direct I database connections. UI is separately staged: S5/S10/S21/S24. Real students forbidden until S25 school approval. Full tests and independent restore required for each runtime release; document checks are NOT runtime evidence.


## v0.7.4 Stage contract repairs

Start from `docs/quality/CONTRACT_GAP_REMEDIATION.md` and `docs/architecture/API_INVENTORY.json`. Reconfirm S0 Course/Group/School/Gemini decisions, follow one-owner contract Gate, use real tests at corresponding stages. `scripts/test_review_invariants.py` checks replay/Grade/School cases in memory only; does not establish deployed security.
