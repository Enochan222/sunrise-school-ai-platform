# v0.7.3 現行修訂：Stage 目標／驗收／衝突與未來影響

> **CURRENT v0.7.5 REVIEW:** [Reuse-first independent review](REUSE_FIRST_INDEPENDENT_REVIEW.md). This report below preserves earlier v0.7.2/v0.7.3 test history and historical counts; latest 29 Stages, 100 candidate APIs, 310 designed ATs and current QA are recorded in the v0.7.5 review and delivery JSON. No Runtime tests were run.

**本 ZIP 的最新增量 QA 以 [STAGE_GOVERNANCE_REVIEW.md](STAGE_GOVERNANCE_REVIEW.md) 為準。** 下面保留 v0.7.2 的工程合約審查歷史數據，並非 v0.7.3 全套文件的最新總檢查數。新版新增每個 Stage 控制卡、總表及 10 項 Stage Mutation Test，原有 AT=286、API=80、Stage=S0–S28 均未變。全部真 Runtime Test 仍為 NOT RUN。

---

# Document QA Report — Sunrise Reviewed v0.7 FINAL

**2026-11-08 | Result: PASS (documentation / contract drafts / pure models / archive integrity only).** The current private GitHub `main` still declares v0.5. This ZIP is **NOT MERGED**, S0 proposed Owner signoff is PENDING, and every real service test is NOT RUN.

## Input lineage and completed checks

- **Source ZIP:** user-uploaded `Sunrise_Master_Project_Kit_v0.7_Isolated_Stages.zip` (78 entries); original ZIP was unpacked and its Stage design and 149 tests mapped to the revised plan, not blindly replaced by generic prose.
- **Pasted critical review:** addressed early Integration + Sunrise UI, Open Notebook security, S2/S3 freeze, B atomic Create/Reserve, S4 distinct Create/Adopt and core reconciliation, Source Version/Evidence TOCTOU, anti-injection, early Actor/Scope, B Grade CAS and Keep2, Gemini Key, Maths/Chinese/English/General Studies independent early releases, frontend U gates, retention and rollback compatibility.
- **Connected GitHub inspection:** README baseline v0.5, `.github/CODEOWNERS` `* @IssacSitHk`, workflow job `validate-docs` and live `ADR-001` checked on 2026-11-08. Historic live ADR-001..010 preserved; old ZIP drafts moved to `docs/history/v07_pre_review_ADRs/`, new proposed ADR-011..021. No PR or Repo mutation performed.
- **Structural + semantic:** `python3 scripts/validate_docs.py` verifies 29 Stage owners/tech dependencies, 269 baseline Acceptance IDs, release range R01–R28, canonical API operations and generated owner OpenAPI, 4 U gates, PRD/Roadmap/Stage/Matrix trace, Markdown links, GitHub CI/CODEOWNERS and file SHA Manifest.
- **Pure in-memory model:** `python3 scripts/test_design_invariants.py` = **40/40 PASS**. These are illustrative state/authorization invariants, NOT real SQL transactions or deployed HTTP cryptography.
- **Contract fixture Schema check:** `python3 scripts/validate_contract_fixtures.py` = **6/6 PASS/rejected as specified** using jsonschema Draft2020-12. A sample Evidence placeholder signature/expired timestamp passes **structural Schema only**; actual crypto, expiry and revocation remain NOT TESTED.
- **Adversarial mutation verification:** `python3 scripts/test_semantic_mutations.py` = **9/9 intentional contradictions caught with Hash validation disabled**, including stale Release max, competing canonical path, wrong stage owner, future dependency, S0 staging, CODEOWNERS modification, missing teacher grant dependency and absent U Gate.
- **Archive:** after finalizing the manifest, ZIP CRC test, independent extraction, byte-for-byte SHA-256 comparison and re-running all scripts in extracted folder performed by packaging task; final delivery log records file count, hashes and pass counts.

## Stage-specific high-risk engineering acceptance — intentionally NOT RUN

| Risk | First Stage runtime proof required |
|---|---|
| Open Notebook raw API/auth/password/SurrealDB defaults and SSE/download/source leakage | S1 A: actual network, Secret fail-start, scoped HTTP and A Restore |
| A Source Version, rights, API Consumer Contract | S2 A with pinned upstream and schema version |
| B Postgres atomic Create+Reserve, Binding unique, contract, B Restore | S3 B |
| Create/Adopt Crash boundaries, I no DB DSNs, A/B API read-back and separate restore reconciliation | S4 I |
| Actual Gemini Key/Model/Quota capability, B Queue idempotency | S7–S8 B |
| Evidence cryptography, Key rotation, replay, TOCTOU, prompt injection | S9 I/B runtime |
| Math/other subject validator/Gold Dataset/PDF/browser U | S11–S14, S19, relevant U release |
| Grade Event DB role/CAS; weak memory/history concurrency | S17/S20 B |
| Teacher Grant revocation / real student PII privacy | S22–S25 B/I/U |
| Independent fresh-context EGM Goldfish Review | NOT RUN; no attempt to claim independent reviewer |

**Interpretation:** QA PASS means the **planning artifact is internally consistent under implemented tests**. It is NOT architecture deployment approval, proof of secure Open Notebook integration, guarantee of all API contracts, or completed Stage0 human signoff. Machine OpenAPI request/response body schemas remain DRAFT placeholders until the owning Stage freezes and validates them against actual services. A direct implementation needs Owner decision and the separate docs-only PR first.

## Engineering Contract QA addendum (v0.7.2)

The base ZIP contained 64 API operations; now 80 typed candidate operations have required Path Parameters, explicit 2xx response and error structures, per-operation closed request bodies and actor-specific JWT Scope metadata. `docs/quality/ENGINEERING_CRITICAL_REVIEW.md` documents the critical findings, engineering changes and unresolved runtime Gates. Stages S0–S28 unchanged; Acceptance Matrix now 286 designed ATs (NOT RUN). Run `scripts/validate_openapi_contracts.py`, `scripts/test_typed_contract_fixtures.py` and `scripts/test_openapi_mutations.py` along with the original QA tests. **A green documentation CI cannot be used as evidence of provider API Contract Freeze.**

## Measured v0.7.2 engineering QA (2026-11-08)

- Cross-file canonical/Stage/GitHub compatibility checks: **1,484 PASS, 0 FAIL** in `scripts/validate_docs.py` (checked against the regenerated file manifest).
- Independent OpenAPI parameter/type/actor/service-scope checks: **1,966 PASS, 0 FAIL** in `scripts/validate_openapi_contracts.py`; **80/80 planned Operations have typed 2xx success responses** (including binary file media) and error objects.
- Positive/negative request/response fixtures: **22/22 PASS** in `scripts/test_typed_contract_fixtures.py`; original Schema fixtures **6/6 PASS**; design models **40/40 PASS**.
- Mutations with manifest disabled: original cross-document **9/9 PASS** and new OpenAPI/auth **9/9 PASS**; tools deliberately introduce invalid contracts and verify semantic rejection.
- **286 planned Stage ATs**; none is a runtime result. Formal provider consumer Contract Freeze is **NOT RUN**. Independent EGM Goldfish Review is **NOT RUN**.
- Final ZIP hash/CRC and independent extraction are additionally verified by the packaging procedure; see the accompanying standalone QA JSON log. No GitHub, API provider, database or deployment was modified.

**Limitations:** Custom OpenAPI 3.1 structural/JSON-Schema checks are not a substitute for independent full OAS validator, running provider/consumer contract tests, JWT cryptographic verification, actual B SQL policies, Open Notebook gateway security, real restore, or School Privacy approval. All new DTO field choices remain proposed until owner signoff.
