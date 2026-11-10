# Reuse-first Deep Engineering Review — v0.7.5

**Review status:** Document/source code/static model review PASS under implemented tests, **runtime gates NOT RUN**, Owner approval PENDING. No GitHub modifications, no live A/B/I/U deployed or independently restored. Scope: uploaded `v0.7.4_Contract_Gaps_Reviewed.zip` + supplied `open-notebook-main(1).zip` (exact SHA in source audit). Source ZIP does not establish a trusted upstream Git tag or image digest.

## New discoveries beyond previous review

1. Open Notebook has native **Notebook/Source/Note/Source topics, PDF import/processing, full-text/vector search, credential management, chat, transformations, worker and substantial UI**. A must reuse these, building only policy/ownership/version and scoped owner APIs. Build-duplicate test now embedded in all 29 Stage cards.
2. **Native Search may go global** if scope missing; Source may belong to multiple Notebooks; raw listing and deletion are legitimate upstream features but insecure for Sunrise Course-based authorization. S1 must fail closed and hide original UI/API from public ingress; do not treat existing upstream password as Staff IAM.
3. **A Worker is not B Generation Queue.** In supplied ZIP, `CommandService.list_command_jobs` returns `[]` and `cancel_command_job` logs/returns True; B still needs its job states & idempotent approvals. Evaluate Supabase Queues/pgmq for transport; not an A queue copy.
4. **A existing credentials prevent duplicated A Gemini UI**, with private reuse; B uses independent credential lifecycle. Evaluate Esperanto as a shared SDK library *without A/B secret sharing*. Both remain S1 optional vs S7 B.
5. **Owner Stage API consumers were omitted in Stage Registry:** S21 U needs S18/S19 B marking; S22 B Staff access tests must cover S18/S20; S24 Teacher U reuses S21 U; S27 Year Close needs S18/S20. Corrected tech dependencies, Roadmap, Backlog, Stage Specs, Stage Controls and machine map. No Stage renumbering.
6. **Prior Markdown AT table break:** new checker confirms all 310 AT rows are contiguous and exact in all Stage Specs, not just present somewhere in the source.
7. **Stage user usability is not automatic:** U-only Release is required to add user-visible features to unified Sunrise UI. B-only release must have an actual usable protected B-local trial tool/console or approved API access; a developer-only mock cannot be marked usable for principal UAT.

## Source type and strength

- **Directly inspected source ZIP:** Open Notebook routes, models, worker, Next.js frontend, Docker Compose, 16 code fact descriptions; optional `validate_reuse_stage_logic.py --upstream-root <extracted_source>` verifies high-risk source facts without internet.
- **Official docs corroboration (current as reviewed):** Open Notebook GitHub release notes; Supabase Queues/pgmq, Supabase Auth and Esperanto project documentation.
- **Architecture inference:** Thin A Adapter and library reuse should reduce duplicate code, but the exact saved engineering time, security and upgrade compatibility are not known until the target pinned version is deployed.
- **NOT RUN:** Container installation, model/provider connection, scanned PDF/OCR, sample textbook search quality, A/B Contract E2E, actual source/grade invariants in DB, teacher authorization, recovery drills, School/Provider PII approvals.

## Stage dependency repairs

| Stage | v0.7.4 technical dependencies | v0.7.5 technical dependencies | Expected negative test |
|---|---|---|---|
| S21 U | S10,S17,S20 | **S10,S17,S18,S19,S20** | UI cannot display nonexistent Manual/AI marking results by inventing B API |
| S22 B | S3,S17 | **S3,S17,S18,S20** | Staff cannot gain marking/analytics rights merely from existing grants; B must test per resource |
| S24 U | S5,S23 | **S5,S21,S23** | Teacher UI must reuse B/U workspaces while enforcing B/I authorization |
| S27 B | S17,S25 | **S17,S18,S20,S25** | Year close blocks incomplete manual marking and retains valid weakness/grade source state |

## Test categories (exact execution counts are recorded in delivery QA JSON)

- Stage reuse logic source check and manual consumer dependency check; all Stage files retain same 310 acceptance IDs and original ownership.
- Original Stage/GitHub/OpenAPI/Contract checks; original state models and typed fixtures unchanged.
- Independent mutation cases falsifying S21/S22/S24/S27 prerequisites, ownership and expected reuse boundaries. This is a *counterexample check of planning rules*, not backend correctness.
- Archive CRC, SHA-256 of every source-to-extracted file, independently rerun tests on extracted kit.

**Recommendation:** submit v0.7.5 as a **docs-only review candidate**. Stage 0 may approve architecture direction and upgrade/change-control policy, NOT all implementation detail. S1 owner must first pin source commit/image and run native API bypass / search scope / restore tests. Do not overengineer A; do not collapse B into Open Notebook.
