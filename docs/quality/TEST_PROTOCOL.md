# QA Protocol: Structural, Semantic, Contract, Adversarial, Runtime

> **CURRENT REPOSITORY OVERRIDE (2026-11-10):** Active repo is `Enochan222/sunrise-school-ai-platform`; no GitHub Copilot/Actions; local QA must be executed and evidenced; old repo, old CI, old ADR references below are historical only. Read [current Stage0 rules](../delivery/NEW_REPO_STAGE0.md).

**Static structural:** Stage count/owner/dependency DAG, Stage AT IDs from Registry vs actual Stage files and Acceptance Matrix, PRD/Roadmap/Status references, Markdown local links, README/AGENTS, CODEOWNERS, CI job `validate-docs`, no live ADR-001..010 conflict in delivery package. ZIP CRC, manifest hashes, clean extraction, complete repo inventory.

**Semantic consistency:** Unique release range R01–R28 in RELEASE_POLICY (reject R01..R21); canonical API Inventory Method+Path+OperationID compares exactly to generated `API_CONTRACT.md`, Stage route sections, all A/B/I OpenAPI 3.1 JSON; I API first Stage cannot precede A/B prereqs. Route alias or wrong owner fails. Distinguish `depends_on` technical preconditions vs numeric release order; S4 I after S2/S3, S9 I after S8 B evidence intake, S23 I after S22 B permissions. S0 ATs do not mention Staging/Runtime evidence. UIDocument new features have U Stage S5/S10/S21/S24.

**Contract/Schemas:** JSON Schema is draft: use jsonschema Draft202012Validator fixture validation, including negative question denominator zero, correction event missing reason, Evidence expired/unknown signature requiring runtime crypto rejection even if schema passes. OpenAPI generated skeleton has draft response bodies; until S2/S3/S8 full binding schemas and consumer tests, I Stage cannot start. This static validation is NOT an executed A/B API contract.

**Adversarial models:** In-memory independent representation tests for B Reserve+Course atomicity, A Create retry/same key-different body, A/B ID ownership/collision, I state transitions and crash recovery, signed Evidence pre-use logic, Grade CAS correction and Keep2. These models are not proof that SQL transactions, public HTTP routes or production backups behave correctly.

**Mutation test:** In temporary modified copies deliberately inject old `R01–R21`, alternate `/core/v1/bindings` path, wrong API Owner, invalid dependency, forbidden Stage0 Staging expectation. Verifier must reject each *without relying only on sha256 manifest mismatch*. Re-run original validation after any QA fix.

**Runtime & Rollback:** Gate only upon real service deploy: network/unauthorized raw API, empty-scope, streaming/preview, DB role privileges, Queue retries and Worker crashes, source rights/version/TOCTOU, Test Gold Set, responsive U, separate A/B restore + cross-store I reconcile, full regression and Owner signoff. No Goldfish independent review unless an actual separate fresh-context reviewer ran it.

## v0.7.2 executable OpenAPI preflight

Run in this order: `python3 scripts/validate_openapi_contracts.py`, `python3 scripts/test_typed_contract_fixtures.py`, `python3 scripts/validate_contract_fixtures.py`, `python3 scripts/test_design_invariants.py`, `python3 scripts/test_openapi_mutations.py`, `python3 scripts/test_semantic_mutations.py`, `python3 scripts/validate_docs.py`. The new OpenAPI validator checks 70 method/path/operationId mappings, all templated path parameter declarations, all typed success/error responses (including binary downloads), closed request objects and Admin/Staff/Service JWT actor and scope metadata. It deliberately checks type correctness *independently of the SHA manifest*, so an incorrect contract can be discovered even when a mutated ZIP's hashes have been regenerated.

This is **contract schema QA**, not an actual JWT authentication, legal/privacy approval, streaming server, DB RLS, SurrealDB, Queue, backup or restore test. Stage owner Contract Freeze still requires live provider/consumer tests before I is allowed to call it. Type definitions are proposed and may be revised by preceding one-owner Stage with new version.

## v0.7.3 Stage-governance validation

`python3 scripts/validate_stage_controls.py` checks **29 stage control cards**: each has observable goal and at least three Release Gates, two explicit prior-collision conditions, two future implications and at least one unresolved technical choice; it cross-checks Stage Registry, AT IDs, downstream dependency links and the actual per-Stage Markdown. `python3 scripts/test_stage_control_mutations.py` makes ten independent deliberate mistakes and checks the semantic validator catches all ten. Both are document/model tests only, not Runtime Acceptance.


## v0.7.4 independent gap gate

Before considering each Owner Stage done, review [19-row contract gap register](CONTRACT_GAP_REMEDIATION.md) and confirm its API/identity/data-state prerequisites; the candidate interfaces are non-binding until real Provider/Consumer UAT.
