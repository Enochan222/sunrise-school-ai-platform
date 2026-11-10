# Engineering Critical Review — v0.7.2 Candidate

**Date:** 2026-11-08. **Input artifact:** the exact `Sunrise_Master_Project_Kit_v0.7_Critical_Review_Updated.zip` uploaded in this task, plus the two Critical Review analyses pasted by the user. The separately named v0.7.1 ZIP mentioned in the paste was **not an available artifact**. We do not claim a byte-level v0.7.1-to-v0.7.2 diff.

**Recommendation:** This is materially stronger as a **typed API/Stage planning candidate**, but **DO NOT** mark S2/S3/S4 API Contract Freeze or production readiness until the actual A/B servers implement and pass provider/consumer/auth/restore tests. No GitHub push, merge, deployment or real DB work occurred in this package.

## 1. Critical findings from independent re-review

| Issue | Original v0.7 condition | Engineering revision | First runtime Gate |
|---|---|---|---|
| OpenAPI Path Parameters | Templated route names but missing Parameter Objects (20 operations, 21 occurrences identified by prior independent reviewer) | Every templated operation now declares exactly each matching path parameter, `in=path`, `required=true`, type string; checked by separate validator | Owner contract stage S1/S2/S3 etc |
| Success response shape | Original 64 operations had only descriptions, no typed JSON success schema | 80 operations have typed `data` success schema (binary downloads typed as octet stream / PDF according to content); error responses typed; consumer examples have positive/negative validation | S1, S2, S3, S8, S22; then dependent I |
| Request shape | Most POST operations used free-form `additionalProperties: true` | Per-operation JSON request with closed typed properties and required fields, multipart upload typed as binary; conditional B ADOPT_EXISTING requires course_id | Owner contract freeze |
| I impersonates Admin | A/B operations used AdminSession, including paths I must call | Separate ServiceToken with `aud/iss/sub/exp/jti/scope`; independently scoped per owner action; B Evidence ingestion is service-only | S2/S3, S8/S9 |
| Teacher impersonation | S22 `getUserGrants` and S23 teacher content were AdminSession | `getUserGrants` StaffSession self-only; new S22 `getStaffPermissionsService` via `core.grant.check`; S23 `getTeacherContent` requires StaffSession and course_id query; I calls B/A with its own limited service token | S22 → S23 |
| S5 premature modules | S5-AT01 claimed synthetic Assessment/Grades UI years before corresponding B stages | S5 only Course, Content Catalog, Upload/Search/Download/Link Status; Assessment/Grades disabled `未推出` | S5 U |
| S5 Content API gap | I only had linked content summary, no materials list/upload/search/download routes | A S1 GET scoped materials list; four I S4 authorized routes providing list/upload/search/download through existing A/B APIs | S1 A, S4 I, S5 U |
| GitHub v0.5 history | Active ADR-001..010 could be overwritten and CI job changed | Preserve current GitHub historic ADRs, old validate-docs job and CODEOWNERS; new ADR-021 proposed, docs-only PR with preflight SHA/owner approval | S0 docs PR |
| A S1 Gemini vs B S7 Key | BYOK unclear | A S1 AI search needs separate A-owned configured/approved Key if enabled; B S7 BYOK is for B generation, not retroactive A | S0 decision, S1 runtime and S7 runtime |
| v0.6 Stage0 PoC conflict | Older expectation required both DBs early | S0 docs/Repo/Approval only; S1 A Vault; S2 A contract; S3 B DB/contract; S4 I API-only integration | S0 Owner approval, S1–S4 runtime |
| Later UI lacks read APIs | R11 paper PDF, R15 synthetic roster, R16 assessment, R17 grade history, R20 analytics/weakness and R23 teacher search/download not fully consumable | Added ten B/I owner-specific read contracts; typed binary PDF/teacher downloads; synthetic roster DTO rejects real students | Owner stages S11/S15–S17/S20/S23 |

## 2. Changed artifacts and counts

- 29 Stage Specs S0–S28 and owner mapping **unchanged**; planned product releases R01–R28.
- API Inventory: **64 → 80** operations (1 new A material list, 4 new I content proxies, 1 new B private Staff Grant lookup, 10 additional B/I owner-specific retrieval operations for students, assessments, grades, analytics, PDFs and teacher materials). Exact Method/Path/Operation ID/first Stage/Actor and Service Scope are canonical in `docs/architecture/API_INVENTORY.json`.
- Acceptance Matrix: **269 → 286** designed test cases (17 new cases for A/B Service Authorization, I proxy, Evidence, Staff delegation and owner-specific retrieval APIs). All remain **NOT RUN**. Stage5-AT01 corrected in place, not double-counted.
- OpenAPI A/B/I 3.1 JSON: concrete Path/Query/Header Parameters, typed request bodies, typed 2xx success and error contracts, strict scopes and response definitions. The A/B/I components include shared domain schema definitions for source provenance, GradeEvent, EvidenceBundle, CourseOperation, staff grants and AI provider handles.
- New: `docs/architecture/API_PERMISSION_MATRIX.md`, `ADR-021`, `scripts/validate_openapi_contracts.py`, `scripts/test_typed_contract_fixtures.py`, `scripts/test_openapi_mutations.py` and this report; CI keeps `validate-docs` while running all new checks.

## 3. Mandatory security semantics not enforced by OpenAPI alone

- Every ServiceToken request requires separate short-lived issuance, audience exact to A/B, issuer/subject trust, `exp`/`nbf`/`jti`, named scope, route/actor binding, resource ownership checks, rate limits, audit and replay protection. **ServiceToken is not equivalent to AdminSession or Supabase `service_role`.**
- StaffSession identifies a real staff subject; S23 I must query current B grant epoch via private B service API per request, and may issue only A read-only scoped content calls. No persistent download URLs that survive revoke.
- All evidence sent to model use must recheck binding version, Source content SHA and publication/AI-usage policy; structural Schema does not prove signature cryptography or authorization.
- All backup/restore, HTTP status/retry, worker race, school data privacy and source isolation test cases need actual deployed providers, not generated sample payloads.

## 4. Tests executed in this artifact cycle

| Check | Classification | Evidence |
|---|---|---|
| Original baseline static QA | PASS before modifications | 1,699 checks |
| Standalone v0.7.2 typed OpenAPI structural check | PASS; re-run in extracted ZIP | 80 typed success shapes, required Path Params, scoped actors; standalone report |
| Typed positive/negative JSON Fixtures | PASS; re-run in extracted ZIP | 22 fixture cases incl plaintext secret leak, correction reason, Staff read-only |
| Original 6 domain Schema fixtures | PASS; re-run in extracted ZIP | Existing `validate_contract_fixtures.py` |
| Original 40 pure design model tests | PASS; re-run in extracted ZIP | Existing `test_design_invariants.py` |
| New OpenAPI semantic mutations | PASS; re-run in extracted ZIP | 9/9 modifications caught without SHA dependency |
| Original cross-file semantic mutations | PASS; re-run in extracted ZIP | 9/9 modifications caught without SHA dependency |
| Files/hash and ZIP CRC | PASS only after final package rebuild | Check output of `scripts/verify_kit.py` and final packaging log |
| Real A/B API, Open Notebook/SurrealDB/Postgres, Service JWT, Queue, Restore, Teacher UAT | **NOT RUN** | Stage-specific runtime owners must supply signed evidence |
| Independent EGM Goldfish review | **NOT RUN** | Not simulated by a self-review |

## 5. Remaining engineering decisions / blockers

1. **Owner signoff on DTO fields and wire formats.** These new typed contracts are **not frozen**. Verify actual providers implement media types, 201/202 status code behavior, error envelopes and idempotency semantics; only then pin version and create client SDKs. Some late-Stage DTOs are candidate models and need UI/teacher/product review.
2. **A Open Notebook adapter implementation** must safely enforce one Shell→Notebook, deny raw notebook CRUD/link and global scope, and implement MIME/file streaming and client ServiceToken; require actual negative tests and Restore at S1/S2.
3. **B CourseOperation transaction and adoption state machine** must be proven with SQL uniqueness, partial crash replay and authoritative Binding projection at S3; I S4 depends on this and A v1.
4. **Service identity trust and staff revocation** are platform security decisions requiring auth issuer, KMS, revocation semantics, time skew and tenant binding implementation. S22 → S23 must deny unauthorized Course/Source even after session refresh.
5. **S1 Gemini decision:** default for Stage1 is useful indexed text search with no B dependency; A Gemini/embedding search is optional only after explicit A key, budget, permitted documents/privacy and Source AI usage policy approval. B S7 Gemini BYOK is separate.
6. **S0 / GitHub scope:** preserve existing live main and ADR history. Create docs-only PR; do not claim Stage0 GitHub issue signoff or deploy Stage1 from a generated ZIP alone.

## 6. Explicit release recommendation

**PASS WITH DISCLOSED LIMITATION — PLANNING / CONTRACT CANDIDATE ONLY**: document and typed Schema structure can be delivered for Owner review. **FAIL / NOT RUN — LIVE PROVIDER CONTRACT FREEZE**, before S4 may implement against A/B. If exact live provider tests fail, repair the earliest A-only or B-only Stage and re-run its tests, then rebase I separately. This is not an approval to merge GitHub main.
