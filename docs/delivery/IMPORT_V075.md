# Verified v0.7.5 Import (No GitHub Actions)

This local candidate **does include** the source ZIP contents adapted to the fresh Enochan222 repository, plus local-only QA. The external original ZIP has SHA-256 `ee4d07d9e4d46fb9bf8c8b8f26c22413a4d2b0cca58acd0a45fc937da0b95bd5` and 149 original file entries. Original file hashes are retained in `docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256`; adapted package hashes are in root `FILE_MANIFEST.sha256`.

## What to import into GitHub

Import the **contents of this package**, including hidden `.github/` but **excluding GitHub Actions workflows**. Import into a dedicated docs-only branch with `main` as its base, not through direct pushes to `main`. Do not import or delete the old IssacSitHk repository. GitHub's existing bootstrap README/AGENTS/S0 files should be replaced by the current full v0.7.5 package; delete the obsolete `.github/workflows/validate-docs.yml` from the new repo in the same PR.

## Validate and merge only on evidence

Run `python scripts/run_qa_no_actions.py` against the exact Git HEAD with a suitable Python 3.11+ and pinned jsonschema. Record logs/commit SHA and actual negative/regression outcomes in PR. Do not assert any GitHub Required Checks (they are deliberately OFF) or automatically merge untested code. No Runtime A/B/I/U, restore or student-data tests have run.

The connected GitHub app can modify individual text files and PRs but does NOT directly accept this workspace's entire local ZIP/folder; a Git client or connected Work-mode browser/desktop workflow is required for the one-off full bulk import. Do NOT claim the imported GitHub main is already complete until branch contents and hashes are independently checked.
