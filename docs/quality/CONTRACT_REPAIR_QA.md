# Contract Repair QA — v0.7.4 Targeted Review

**This is a SPECIFICATION/LOGIC QA report; not a production or staged-runtime pass.**

## Reproduction

From kit root run `python3 scripts/validate_docs.py`, `python3 scripts/validate_stage_controls.py`, `python3 scripts/validate_openapi_contracts.py`, `python3 scripts/validate_review_contracts.py`, `python3 scripts/validate_contract_fixtures.py`, `python3 scripts/test_typed_contract_fixtures.py`, `python3 scripts/test_design_invariants.py`, `python3 scripts/test_review_invariants.py`, `python3 scripts/test_semantic_mutations.py`, `python3 scripts/test_openapi_mutations.py`, `python3 scripts/test_stage_control_mutations.py`, `python3 scripts/test_review_mutations.py`.

The independently created verification script `scripts/validate_review_contracts.py` checks critical protocol obligations (Course/Class, blueprint, grade hash, evidence worker, staff rights, weakness and Health). `scripts/test_review_mutations.py` intentionally alters these contracts while **not relying on a file hash mismatch** to catch defects. `test_review_invariants.py` includes actual in-memory model tests for same-job repeated Evidence validation and changed Grade Payload 409. This is not an HTTP, database, OAuth or crypto implementation.

## Acceptance status

- Planned Stages: **S0–S28 unchanged**; Owner per Stage A/B/I/U unchanged.
- Candidate API operations: **100** (not live/frozen).
- Designed Stage acceptance cases: **310**, **none executed against a deployed service**.
- 19 gap rows: design closure status and runtime blockers listed in [Contract Gap Register](CONTRACT_GAP_REMEDIATION.md). These are reconstructed from the user-pasted audit, not a verbatim v0.7.3a ZIP diff.
- GitHub main, ADR history and existing Issues: not modified. Owner signoff pending.
- Runtime A/B/I/U deployment, security boundaries, backups, Restore, real users/PII: NOT RUN.
- Independent EGM Goldfish fresh-context review: NOT RUN.

The final external delivery JSON reports actual source/extracted-archive checks and CRC. Any static PASS does **not** approve Owner API Freeze or S1 Runtime release.
