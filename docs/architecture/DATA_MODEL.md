# Data Model and Immutable Identity / Source of Truth

## A — SurrealDB + private school materials

`content_shell(content_shell_id,external_course_key,school_id,academic_year_label,grade_label,subject_label,actor_id,status,notebook_id,creation_key)`; `source_owner(source_id,content_shell_id,notebook_id,created_by,access_scope)`; `source_version(source_version_id,source_id,sha256,locator,published,revoked_at,retention_policy_ref,ai_usage_policy_ref,created_at)`; `a_creation_op(operation_id,link_key,idempotency_key,request_body_hash,notebook_id,status)`; original files and indexes/worker state. One logical Source belongs to one Shell; immutable versions preserved for authorized replays, no cross Shell `reference`/source link. Blob dedup (if adopted later) doesn't share ACL.

## B — independent PostgreSQL / Supabase

- S3 `school(school_id)`, `subjects(subject_id)`, `academic_years(id)`, `courses(course_id,school_id,academic_year_id,grade,subject_id,curriculum_stream,created_by,actor_id,access_scope,status)`, `teaching_groups(teaching_group_id,course_id,school_id,group_key,display_name,status)`; unique Course by scope, not name. `CONTENT_UNLINKED` permitted until S4.
- S3 `course_operations(operation_id,mode,link_key,idempotency_key,request_hash,course_id,binding_status,version,actor_id,attempt,last_error)`; `course_bindings(binding_id,course_id,a_shell_id,a_notebook_id,a_external_course_key,link_key,binding_version,verified_at,state)` with UNIQUE active Course/Shell/Notebook and historic audit; B transaction keeps new Course+Op atomic. I never owns this table directly.
- S6 draft/published Blueprint+QuestionTemplate+RubricVersion lifecycle with immutable version refs, Question/Rubric/Answer Specs + PDF Render Contract versions; S7 AI provider secret references and tests; S8 generation jobs/prompt/model/immutable drafts/artifacts/evidence acceptance refs; S9 evidence metadata from I is NOT textbook original.
- S15 synthetic_students/enrollments(student_id,course_id,teaching_group_id) with same School/Course FK validation, S16 Assessments/Score Drafts, S17 `grade_events(event_id,grade_key,event_type,expected_prior_revision,revision,corrects_event_id,reason,actor_id,created_at,score,operation_id,canonical_request_hash)` INSERT-only, latest projection rebuildable. S18–S20 Submissions, AI marking and deterministic analytics/Weakness Memory.
- S22 identity/users/roles/grants/revocation_epoch; S25 real student PII only on School Approval; S27 Year Archive. `school_id`, `created_by`, `actor_id`, `access_scope` reserved from first B stage, not first invented at S22.

## Scope and retention

B Course defined by school+year+grade+subject+curriculum_stream, teaching groups/class many-to-one; A Content Shell one per Course after integration. Cross-course use requires controlled Source Version Copy, not sharing mutable Source ID. S1/S2 A retention/AI usage/rights policy exists before Evidence or Paper Generation; S26 adds advanced archive UI only. Generated paper stores citation IDs/version/content SHA/retrieved_at/locator and Prompt/Model/Rubric version in B; Original files remain A.

## Write permissions

A API only creates/updates A data. B API only B. I calls A/B APIs, never SQL or SurrealDB. UI no admin credentials. Grade Events UPDATE/DELETE blocked for normal DB roles; CAS revision ensures exactly one competing correction succeeds; `current_projection` is recomputable from original Event Log. Max 2 `VALID ACTIVE` Weakness memories per Course+Target+Subject; don't delete Grade Events/Analytics historic Samples.
