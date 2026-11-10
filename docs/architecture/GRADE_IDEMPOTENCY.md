# Grade Idempotency — Event Submission / Correction (B S17)

**Contract candidate, NOT live DB proof.** For every formal Score submit operation, B stores durable `(school_id,actor_id,operation_type,idempotency_key,canonical_request_hash,event_id)` with unique operation identity and a Grade key/revision. The server MUST recompute canonical hash over semantic payload (including Draft Revision, score, course/assessment/student scope and Actor), not trust a caller-supplied hash alone.

- Same key + identical canonical payload (+ same actor/scope) → return SAME prior Grade Event with same event_id and revision, no new ledger entry.
- Same key + changed payload / score 8→9 / student / Actor / rubric version → **HTTP 409 IDEMPOTENCY_PAYLOAD_CONFLICT**. Do NOT silently ignore and claim success.
- Different key but already submitted Grade key → reject duplicate first SUBMIT; any correction uses append-only Grade Correction with `expected_revision`, actor/reason and audit.
- Worker crash after B committed Event but before ACK → request with same key/body recovers original Event; no UPDATE/DELETE of original.
- Row-level locking/CAS or equivalent transaction plus DB role denies UPDATE/DELETE required at runtime Stage17; contract alone does not prove concurrency safety.

`submitGradeRequest` includes `canonical_request_hash` as candidate wire field, but B MUST compute its own hash and reject inconsistent client-provided hash. `GradeEvent` persists the resulting hash for audit and operation comparison.
