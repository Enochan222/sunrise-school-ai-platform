# v0.7.4 — 19 Contract Gap Review Map (PLANNING CANDIDATE)

**Source limitation:** available input ZIP is `v0.7.3_Stage_Goals_Acceptance_Reviewed`; the separately described `v0.7.3a` audit ZIP / its exact 19-row machine report is not present. These 19 rows are a **reconstructed work register from the user-pasted review**, not a falsely claimed exact original 19 findings.

**Decision:** preserve S0–S28, A/B/I/U owner boundaries and 1-stage 1-owner. No live API/DB backup/Restore/IAM check performed. `DESIGN_UPDATED` means draft type/Stage contract written and statically checkable, not implemented or owner-approved.

| Gap | Owner Stage | Area | What must be true before owner Release | State |
|---|---|---|---|---|
| CG-01 | S22 B | Teacher business API authorization | staff Session on real B Course/Group/Assessment/Grade/Submission operations; no Admin impersonation | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-02 | S9 I | Evidence validate B Worker identity | service-only link.evidence.validate with exact B Worker/Job audience, S8 B worker reference | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-03 | S3 B | Course grain | grade+curriculum_stream, no single class_id; Course one-to-many Teaching Groups | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-04 | S6 B | Blueprint lifecycle | create/read/draft update/publish/versions; stable Blueprint ID pinned in S8 | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-05 | S20 B | Weakness full state | candidate/active/stale/retired read, discard/keep, source Grade watermark | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-06 | S9 I | Evidence second validation | same jti+job can revalidate at different phases; different job denied; fresh revocation each time | MODEL_FIXED / RUNTIME_NOT_RUN |
| CG-07 | S17 B | Grade idempotency hash | same op+same canonical_request_hash replay; changed payload 409, actor bound | MODEL_FIXED / RUNTIME_NOT_RUN |
| CG-08 | S1 A | School ownership for Content Shell | A shell has mandatory school_id and all searches/downloads verify school before source | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-09 | S4 I | Course/Content Cutover | S3 B reserve then S2 A idempotent create then B finalize; FAIL CLOSED on school mismatch | STAGE_GATE_UPDATED / RUNTIME_NOT_RUN |
| CG-10 | S0 P | Stage1 Gemini decision | A search indexing required; A Gemini optional separate key/consent/budget; B S7 key separate | REFERENCE_DECISION / OWNER_APPROVAL_PENDING |
| CG-11 | S15 B | TeachingGroup enrollment | student_id/course_id/teaching_group_id must reconcile same School/Course | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-12 | S18 B | Item-level manual marking | item ID + rubric version + score/max + revision, preserve Grade Ledger | DESIGN_UPDATED / PROVIDER_NOT_RUN |
| CG-13 | S21 U | Assessment/weakness UI readiness | S20 B supplies candidate/active/stale/retired/read/keep/discard before S21 U | STAGE_GATE_UPDATED / UAT_NOT_RUN |
| CG-14 | S22 B | Teacher grant revocation | B validates staff session epoch/School-Course-Group scope at each resource API | STAGE_GATE_UPDATED / SECURITY_NOT_RUN |
| CG-15 | S25 B | Real student privacy gate | no real PII before school and vendor permissions, class grants, retention consent | RETAINED / SCHOOL_APPROVAL_PENDING |
| CG-16 | S26 A | Vault health and backup read | A read-only ServiceToken health/backup-status for S28, no root access | DESIGN_UPDATED / RUNTIME_NOT_RUN |
| CG-17 | S27 B | Core health and backup read | B read-only ServiceToken health/backup-status for S28, no student/grade leakage | DESIGN_UPDATED / RUNTIME_NOT_RUN |
| CG-18 | S2 A | Contract freeze and compatibility | S2 A, S3 B, S8 B, S22 B provider tests and consumer negative tests before dependent I stage | STAGE_GATE_UPDATED / CONTRACT_NOT_FROZEN |
| CG-19 | S4 I | Independent migration rollback | no cross-db ACID; read-after-write, bounded retries, orphan quarantine, forward-fix, never notebook delete | RETAINED / RUNTIME_NOT_RUN |

## Priority and rollback order

1. **Owner Stage0**: Course vs TeachingGroup grain, A School ownership, S1 Gemini optional, S4 Cutover, and no overwrites of GitHub v0.5 ADRs.
2. **A S1/S2**: private raw Open Notebook API, school-scoped shell/source lookup, immutable IDs, ServiceToken contracts with consumer tests before I S4.
3. **B S3**: Course/Group identity, Binding reserve/finalize/idempotency + B-only Restore before I S4. A and B changes never in same runtime PR.
4. **B S6/S8 → I S9**: Blueprint/Rubric lifecycle and immutable references, separate B Worker identity, Evidence same-job phase checks, revocation/expiry at every validation.
5. **B S15–S20**: group enrollment, per-question marking, grade canonical hash, all Weakness state APIs before U S21.
6. **B S22 → I S23**: Teacher StaffSession on actual B business operations, staff grants per School/Course/Group, revocation epoch, I content read-only.
7. **A S26/B S27 → I S28**: owner-local readonly Health/Backup status APIs then I reconciliation UI. Do not give I DB credential or backup engine access.

## Stop/go and what stays TBD

Hard Gate: actor/resource identity, school/course/group ownership, stage dependencies, release compatibility, data immutability, API semantics needed for next owner. Details not yet frozen: hosting region/cost, Gemini models, JWT issuer implementation, concrete DB/Queue libraries, PDF renderer, exact Cache TTL, schema migration approach. These are references for the matching owner stage; owner must document tradeoffs and prove actual tests before freeze. Any change requiring another owner becomes another Stage/ADR, never an informal combined PR.
