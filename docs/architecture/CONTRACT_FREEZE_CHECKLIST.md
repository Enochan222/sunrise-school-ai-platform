# Actual Provider Contract Freeze Checklist — NOT YET PASS

The v0.7.2 `a-v1`, `b-v1`, `i-v1` JSON files are **typed candidates**, not runtime-accepted APIs. Static validations alone cannot close any of the following.

## v0.7.3 對 API Freeze 的判斷

目前 100 個 OpenAPI Operation 和 JSON DTO 仍是**候選參考**，不能因文件／Schema 檢查全部 PASS 就稱「已可實作且完全凍結」。真正由 A S2、B S3（及後續所屬 Stage）以 Provider/Consumer Runtime Contract Test、授權 Scope、錯誤分支、版本回退證據及 Owner 批准，才可標 Freeze。API 路徑／欄位如需更新，先更新單一真實 Owner 的合約，並檢查 I/U 下游依賴。

詳見 [Stage 決策政策](../delivery/STAGE_DECISION_POLICY.md)。

## Stage A S1 / S2

- [ ] Confirm pinned Open Notebook commit/Image/SurrealDB schema and private Gateway + sole Admin Auth; verify raw notebook create/delete/source link/SSE/preview cannot bypass policy.
- [ ] Provider implements every A route in the canonical API Inventory with real HTTP contract testing against typed JSON schemas and binary file downloads. Reject missing/surplus query/path, invalid body, unsupported media, Idempotency duplicate/different body, unscoped search/source owner mismatch.
- [ ] Separate `ServiceToken` issuer/audience/subject/scope TTL, jti replay, and A-vault resource ownership tests; A Portal Admin never delegates its AdminSession to I.
- [ ] Real A DB + file backup/restore, SHA of originals, version publication/retention/AI usage policy and failed-job compensation.
- [ ] S1 Gemini model/embedding or AI search, if enabled, uses separately approved A Key/AI policy; it never reuses future B S7 credentials.

## Stage B S3 / S8 / S22

- [ ] Actual independent PostgreSQL/Supabase B instance/host/keys/backup, full CourseOperation/Binding SQL uniqueness, Reserve+Course Transaction and read-after-write; verify B cannot direct-connect to A DB.
- [ ] B S3 `ServiceToken` narrow `core.course.reserve`, `core.operation.finalize` etc; fail wrong aud/scope/cross-Course; no broad Supabase service_role in I.
- [ ] B S8 provider contract for signed Evidence Bundles, cannot accept admin-made unsigned evidence; verifies issuer/audience, source hash, version and revoked/expired evidence before model use.
- [ ] B S22 offers `StaffSession` self-grants and separate I-to-B private `core.grant.check` lookup; correct grant epoch and revoke behavior proven.

## Stage I S4 / S9 / S23

- [ ] Verify A S2 and B S3 released API versions, exact digests, consumer fixtures, typed response codes and resource ownership before writing I.
- [ ] I has only API allowlist and no A SurrealDB/B PostgreSQL DSNs; cannot borrow any AdminSession. API calls can cause permitted state changes but I Stage touches only I code/config.
- [ ] S4 S1→B Adoption by stable identity, CREATE_NEW and ADOPT_EXISTING separate state machines, retry idempotently after crash, quarantine and explicit no-delete compensation.
- [ ] S4 I Materials List/Upload/Search/Download proxied to A with per-request B Binding & A Owner check; streams handle disconnect, size limit, TTL, Content-Disposition and checksum safely.
- [ ] S9 Evidence rechecks publication, license, AI-usage, binding revision and source content hash at model-use time; revoked/expired/stale rejections proven.
- [ ] S23 teacher StaffSession must be currently granted B Course; per-request B grant epoch, A read-only scoped service call and download-after-revoke fail closed.

## Stage U S5 / S10 / S21 / S24

- [ ] R05 Course/Content Portal only uses S4 I and S3 B APIs; **Assessment/Grades remain disabled/unavailable** until their backend and U release.
- [ ] R10 Generation, R21 Assessment/Analytics, R24 Teacher UI have independent U-only release gates with real data retrieval, responsive/accessibility/error tests and no DB/admin client keys.

## Cross-owner Release Gate

- [ ] Immutable API/schema/migration/image/git SHA manifest; exactly one runtime owner changed per Release; previous Stage regression and rollback plan; actual provider/consumer tests; Owner approval. If any API change needed, introduce preceding owner-specific Stage/ADR and DO NOT patch A+B inside I PR.
- [ ] No real student data before approved S25, all earlier student tests synthetic.

**Status:** ALL unchecked pending actual implementation and human signoff. The `scripts/validate_openapi_contracts.py` result is a static candidate-schema gate only, not evidence to check these boxes.


## v0.7.4 Delta — mandatory Owner Provider proofs (all still unchecked)

- [ ] S0 Owner signs off Course one-to-many TeachingGroups, A Shell school ownership, S1 Gemini optional, S4 Cutover.
- [ ] S3 B Contract exposes `grade` and `curriculum_stream` and separate TeachingGroup create/list; Course does not contain `class_id`.
- [ ] S6 B implements immutable Blueprint version lifecycle and Rubric/Question read APIs; S8 Queue pins published Blueprint ID/version.
- [ ] S8 B Worker gets scoped ServiceToken to call S9 I evidence validation; same Job repeat validation, another Job reuse blocked, all phases check source revocation.
- [ ] S15 B Enrollment requires TeachingGroup ID and enforces cross School/Course/Student scope.
- [ ] S17 B Grade submit canonical request hash computed by server; same key conflicting score yields 409 instead of ignored.
- [ ] S18 B manual marking stores one decision per QuestionItem, RubricVersion, revision; no AI direct grade publish.
- [ ] S20 B Candidate/Keep/Discard/Stale/Retired available before S21 U; Grade changes invalidate Weakness.
- [ ] S22 B actual business read/submit per StaffSession and current grant revocation; teacher may not borrow AdminSession.
- [ ] S26 A + S27 B expose private read-only health and backup status API for S28 I Dashboard.

**These contract descriptions are a design candidate, not a freeze or runtime PASS.**
