# Required v0.7.5 Master Kit Import

**Blocked:** exact source file `Sunrise_Master_Project_Kit_v0.7.5_Reuse_First_Stage_Logic_Reviewed.zip` is not accessible in the current workspace. Older `v0.7_Isolated_Stages.zip` has different Stage numbering and must never be presented as v0.7.5.

1. Obtain exact v0.7.5 ZIP from the user or a verified source; check CRC, duplicate/unsafe archive paths, SHA-256 of every file and `FILE_MANIFEST.sha256`.
2. Confirm 29 Stage Specs (S0–S28), Stage Registry 29 entries with exact technical dependencies, 100 candidate API Operations, 310 planned acceptance IDs and Reuse-first audit.
3. Reconcile README/AGENTS/workflow with this bootstrap without reintroducing old permissions or deleting CI. Commit the contents, **not** the ZIP or upstream Open Notebook source archive.
4. In a docs-only PR set `stage0/STAGE0_BASELINE.json` to `master_kit_phase: MASTER_CANDIDATE` and `full_master_kit_imported: true`. The CI will require the real files and run all 13 source QA scripts; it will fail if the kit is missing.
5. Preserve `stage0_product_approval: PENDING` until the owner accepts architecture decisions; `runtime_tests: NOT_RUN` until actual service tests are performed.
6. PR must pass real required checks before squash merge. No automatic merging or production work just because a planning ZIP is complete.
