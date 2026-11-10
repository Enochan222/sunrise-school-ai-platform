# Stage 0 — Owner product / security / budget decision packet

**Decision state: PROPOSED; OWNER NOT YET SIGNED.** Prepared 2026-11-10 from reviewed v0.7.5 and [S0 acceptance evidence](../delivery/STAGE0_EVIDENCE_2026-11-10.md). Technical documentation PASS does **not** authorize paid services, school data or runtime deployment. Explicit Owner confirmation of this entire package is required before status changes from PENDING.

## Exact recommendations for Owner approval

| ID | Proposed binding S0 decision | Deliberately postponed boundary |
|---|---|---|
| D01 System ownership | Four independent Owners: **A** Open Notebook/SurrealDB Content Vault; **B** PostgreSQL/Supabase academic/grades/marking; **I** API-only orchestrator; **U** API-only frontend. Never share A/B DB credentials, files, backup stores or schemas. One Stage changes one runtime Owner. | Runtime/hosting implementations belong to S1 onward |
| D02 Course identity | B `Course = (school_id, academic_year, grade, subject, curriculum_stream)`; TeachingGroup/Class is **many-to-one** per Course. A creates one Shell per Course and one Notebook per Shell; no auto-match by name or cross-course mutable source IDs. | Exact database schema and index choice are B S3 concerns |
| D03 Source rights / school owner | `school_id` mandatory for A Shell and every owned Source; school owner/retention/license/approved-sharing flags and immutable source version/hash tracked before use. Search, list, preview, download and native Open Notebook direct routes must enforce school/shell scope; fail closed. | School-specific retention days/licensing approvals before importing actual textbooks |
| D04 Users and student privacy | S1–S21 may initially use **one controlled Admin account** (as previously chosen), with stable principal/school/actor IDs, audited actions and secure authentication; S22–S24 add Staff/Teacher IAM without bypass. **Synthetic data only** before S25. Real identifiable student data requires separate school/legal/provider/region approval. | Named teacher roles, class-level grants, retention and real personal-data processing belong to their Stage gates |
| D05 S1 AI and provenance | S1 delivers **A-only** restricted private Source upload/index/search, original download, fail-start secrets, A backup/Restore; reuse **exact Open Notebook v1.15.1** source reference. Gemini/cloud embedding is **optional and OFF by default** until separately approved with scoped key, measured cost and privacy assessment; B S7 Gemini keys must never substitute for A credentials. | Actual model/version/vector backend/hosting cost require separate S1 decision and real tests |
| D06 S4 Cutover | **I owns S4** linking and durable reconciliation. Separate `ADOPT_EXISTING` and `CREATE_NEW` flows; B reserves atomically and A provisions idempotently via published APIs. No shared transaction/DB connection, enable ACTIVE only after API read-after-write/reconciliation, quarantine conflicts. | Migration cutover timing/rollback needs S2/S3 provider contract and S4 fault tests |
| D07 Spending, region, safety | Stage 0 is **docs-only**; authorize **no paid deployment, external AI provider activation, production data migration or real student data**. Before S1 deployment the Owner must choose hosting location/region, initial budget cap, retention and privacy policy, secret storage, TLS/private network, A backup/Restore acceptance. No default to publicly exposed Open Notebook. | Vendor, deployment region, spend amount and school privacy paperwork can remain OPEN only if **S1 cannot deploy/ingest data before resolution** |
| D08 GitHub process | Private `Enochan222/sunrise-school-ai-platform`, PR/squash-only protected main, CODEOWNERS points to Owner but **0 required code approvals**; **no GitHub Copilot or GitHub Actions**. GPT runs local tests and attaches immutable commit/log evidence; manual result is **not independently enforced**. No unattended auto-merge without other CI. | If fully automated PR-triggered tests are needed later, explicitly adopt a separate runner/provider and fund it with Owner approval |

## Explicit acceptance / refusal

The Owner should confirm **all D01–D08 as one bounded Stage 0 architecture package**, or request edits to named IDs. Approval affirms this **planning design only**; it does not authorize deploying S1, spending money, using licensed content or processing actual student data. In particular, D07's specific region and budget remain **S1 predeployment blockers**, not falsely 'approved' numeric values.

**Signoff record (currently blank, do not fabricate):**
- Owner approval: **PENDING**
- Confirmed decision IDs: **NONE**
- Confirmation date / Issue or chat evidence: **NOT RECORDED**
- Production / student-data permission: **NOT GRANTED**

Once explicit approval is given, document the exact approval reference, update Stage0 baseline and its static gate together, rerun all 16 QA groups and negative tests, and merge via a **separate Stage0 approval PR**. Only then mark S0 COMPLETE and open S1 implementation work.
