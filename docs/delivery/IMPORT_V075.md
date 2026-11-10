# Import exact v0.7.5 into new private GitHub (no Actions)

**Source already verified locally:** `Sunrise_Master_Project_Kit_v0.7.5_Reuse_First_Stage_Logic_Reviewed.zip`, SHA-256 `ee4d07d9e4d46fb9bf8c8b8f26c22413a4d2b0cca58acd0a45fc937da0b95bd5`.

**Adapted package already prepared locally:** `Sunrise_v0.7.5_No_Actions_Fixed_QA_Environment.zip` (164 files including source manifest and Docker QA configuration). This GitHub repository has NOT imported its contents yet. The original v0.7.5 had 149 entries; no old GitHub history/ADRs 001–010 are to be migrated.

## Exact import gate

1. Upload **expanded individual files**, preserving folder paths, to a feature branch (never directly to protected `main`). Do not upload just the ZIP and claim its contents are imported.
2. Reconcile the adapted kit's README, AGENTS, QA scripts, `stage0/STAGE0_BASELINE.json`, docs, contracts and `.github` config; remove the old `.github/workflows/validate-docs.yml`. The adapted ZIP has **no workflow files**.
3. Verify adapted `FILE_MANIFEST.sha256` against all files and source provenance: 29 Stage specs S0–S28, 100 candidate API operations, 310 planned acceptance cases.
4. Run all 16 local test groups using `python scripts/run_qa_no_actions.py` (or a verified Docker QA environment), record commit SHA and actual logs. Local tests were run in Python 3.13; the Docker 3.11 recipe requires a separate real Docker execution check.
5. Open PR with evidence, check privacy/secrets and no old repo instructions, then squash merge only if the tests actually ran and passed. No required GitHub status check, no automatic GPT wake-up and no unattended auto-merge.
6. Keep `stage0_product_approval: PENDING` and `runtime_tests: NOT_RUN`. Product architecture decisions remain Owner-controlled.

**Web uploader limit:** GitHub's browser allows at most 100 files per upload. Use two uploads to the **same feature branch**, or use GitHub Desktop to copy the expanded folder locally and push once. The Owner does not need to read code.
