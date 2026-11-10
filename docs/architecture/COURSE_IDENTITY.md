# Course Identity, Class Granularity and A Source Ownership — ADR-012

## Terminology and cardinality

| Object | Owner | Natural business scope | Cardinality |
|---|---|---|---|
| `Subject` | B | Maths/Chinese/English/General Studies | One Subject many Courses |
| `AcademicYear` | B | e.g. 2026–2027 | One Year many Courses |
| `Course` | B | `(school_id, year_id, grade, subject_id, curriculum_stream)` | Course curriculum instance; unique by scope, mutable display label is NOT ID |
| `TeachingGroup / Class` | B | P4A, P4B or optional split set | Many Classes may enroll in the SAME Course; no Notebook per Class |
| `ContentShell` | A | A-local material partition with stable `external_course_key` | After S4 each B Course max 1 A Shell/Notebook; no second owner |
| `Notebook` | A upstream | 1 per ContentShell | Never create/delete independently via product UI |
| `SourceVersion` | A | Source in one Shell, immutable version/hash + policy | 1 logical owner; no mutable Source cross-Shell sharing |

S1 A has no knowledge of B Course primary key and can create a Shell scoped by school/year/grade/subject display metadata for pilot. S3 B Course has no A Notebook and remains `CONTENT_UNLINKED`. S4 operator selects explicit IDs; an A `external_course_key` is adopted into B `binding.a_external_course_key`, and B `course_id` remains independently generated. A and B external identifiers **need not be identical**, but the exact pair must be confirmed and immutable in the ACTIVE Binding. No course title-match automations.

P4A and P4B using the same Maths curriculum → one Course→one ContentShell→Notebook, many TeachingGroups with different enrollments. If curriculum stream or academic year differs, create distinct Course and Shell; if school wants cross-year textbook reuse, prefer controlled content version copy with separate Source logical owner, never link another Notebook's mutable Source ID. Physical Blob dedup by SHA is an optional **A-only future feature**, with per-logical-owner access checks; it does NOT authorize sharing source records.

## Integrity and policy

- `school_id`, `subject_id`, `academic_year_id`, `course_id`, `teaching_group_id`, `created_by`, `actor_id`, `access_scope`, `audit_actor`, `owner_id` typed and scoped from S1/S3 baseline. S1/3 may use a sole Admin principal; do not add actual teacher UI until S22.
- B Binding UNIQUE for each B Course, A shell ID, A notebook ID, external Course key; allow multiple historical Binding Versions via immutable audit, **only one ACTIVE per ID**. SQL constraints + serializable/select-for-update where needed.
- A `SourceVersion` content immutable, hash and original retained/archived according to usage/licensing/retention policy; rights revoked = do not supply new external Evidence. No normal notebook deletion.
- Enrollment belongs to TeachingGroup and Student in B; marks are attached to B Assessment/Course/Student, NOT A Notebook.

**Decision gate:** This Course grain is a proposed architecture default and must be explicitly signed by Owner in S0 before S1/S3 Schema design. If multiple schools/streams need one-to-many shared materials in future, file new ADR + owner-only migration stages.


## v0.7.4 Contract clarification (S0/S1/S3/S15)

`AcademicCourse` / `createAcademicCourseRequest`: **required** `grade` and `curriculum_stream`; `class_id` removed from Course (not nullable workaround). One School/Year/Grade/Subject/Stream Course has zero-to-many `TeachingGroup` records. `TeachingGroup` has `teaching_group_id`, `course_id`, `school_id`, `display_name` and lifecycle; S3 B API creates/lists them. S15 `Enrollment` and create-enrollment request **require teaching_group_id**, which must belong to the same B Course and School as student/cohort. Cross Course or cross school is a hard negative case. A `ContentShell` and S1 Create Shell Request must have `school_id`, and A verifies school+Source owner before search/download; no cross-School shared Notebook. These are candidate typed contracts, not deployed SQL constraints; prove UNIQUE/FK/negative tests in the owner stages.
