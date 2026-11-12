# Single-owner Runtime and Two Physical Data Planes — Reviewed v0.7

| Track | Source of Truth / allowed changes | Never allowed |
|---|---|---|
| A | Open Notebook wrapper, SurrealDB, original school materials and source version/owner policy/API | B PostgreSQL, Student, Grade, Generate artifact, I implementation |
| B | PostgreSQL/Supabase, academic Course, Teacher Group, Question/Rubric, AI Provider, Queue, Student, Grades, Analytics | A SurrealDB, A Source files, I code |
| I | Standalone Gateway/Orchestrator consuming only versioned, authorized A/B APIs, retriable operations via B operation API | **A/B DB DSN/drivers, SQL/SurrealQL, migrations, schemas, raw ON Admin API** |
| U | Frontend only (Sunrise), consumes I/B APIs with safe Session | A/B/I backend or DB, Service Role or provider key |
| P | Master Docs, Stage registry, ADRs | Runtime changes |

The API-only bridge **will** legitimately call both A and B, which may write their own owner-held data as part of authorized Create/Adopt/Marking/Query workflows. The rule forbids **modifying both implementations in one Stage**, not invoking approved API calls. Cross-service tests are required in I Stages but are not cross-service deployments. All I API preconditions must exist and be consumer-tested in preceding A/B Releases. When missing, **insert an owner-only Stage before I**. No speculative fallback to direct DB.

**Status (updated after Stage0 final signoff):** The v0.7.5 planning kit was merged into the active Enochan222 repository; Stage0 D01–D08 were formally signed off via PR #11 (`744fbbd0ac3b479c80782d6a990c7bfed093f4dd`). Fetch latest `main` before acting; older v0.5 migration wording is historical. Every Platform Release Manifest R01–R28 permits exactly one Runtime Owner code/schema/config/image change. Other service versions remain unchanged; docs control repo may change with every Release. Development in independent service branches can run in parallel once authorized and dependencies allow, but **platform Release sequence** remains by Stage number.

**Before S4** A Content Shell is an independent A material container, B Course is independent B entity with `CONTENT_UNLINKED`. At S4 I establishes one-to-one bound Content Shell per B Course, with N Classes/TeachingGroups per B Course. Names are not authoritative IDs. All reference/ownership tests are server-side, not hiding UI controls.

[Canonical APIs](API_INVENTORY.json) · [B/A Saga](PROVISIONING_STATE_MACHINE.md) · [Course Grain](COURSE_IDENTITY.md) · [Release Compatibility](RELEASE_COMPATIBILITY.md)
