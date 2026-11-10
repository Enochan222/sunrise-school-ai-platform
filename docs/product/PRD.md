# Sunrise Education AI Platform — Master PRD v0.7 Reviewed

**Status:** Architecture proposal revised using uploaded v0.7 ZIP and critical review; **NO product deployed / NO GitHub PR created**. 2026-11-08. This document is the proposed master plan, subject to Owner approval and subsequent actual PoC/contract gates.

## 本次修訂的產品決策層次

**產品/安全硬性不變條件**與**Stage 可試用成果／驗收條件**優先於任何實作候選，詳見 [29 Stage 目標驗收與衝突矩陣](STAGE_BOUNDARY_MATRIX.md) 及 [Stage 決策政策](../delivery/STAGE_DECISION_POLICY.md)。每期的「驗收條件」係實際 Release Gate，不是為了趕工可下放後期。未有證據的 API 字段、模型供應商、Queue／部署方案只標 `REFERENCE/TBD`，待所屬 Stage 真正實測、Owner 准許後決定。

Stage 0 只審批文件／Repo；S1 起每 Stage 必須有可試用、可持續、可回退的結果。新發現跨 Owner API 缺口時不能在 I/U Stage 偷改 A/B；需要獨立 Owner 版本與依賴重排。

## 1. Boundaries and product priority

A = Open Notebook/SurrealDB+private Original Files/Indexer/Search with school official Textbook, Note and Past Paper. B = separate PostgreSQL/Supabase with Course/Subject/AcademicYear/TeachingGroup, AI Questions/Queue, Synthetic and later real Student, Assessment, Grade Event Ledger, Marking and Analytics. I = HTTPS service API orchestration, no shared DB schema/credential or direct query. U = frontend-only. **One Stage modifies only one runtime Owner**; an I stage may call both existing service APIs with normal business-state effects but may not edit their implementations or DDL. Products remain deployable and restorable independently.

## 2. Users and early-to-late authorization

S1–S21: single Admin/Principal, protected HTTPS and no public root/open-notebook admin ports. S0 defines `principal_id`, `actor_id`, `school_id`, `owner_id`, `course_id`, `access_scope`, `audit_actor` from first schema as nullable/assigned with explicit default sole Admin, rather than adding fields in S22. S22 B actual Staff Login/Teacher/System Admin/Content Admin Course grants and revocation; S23 I Teacher A read-only; S24 U Teacher Portal; S25 REAL PII only after school privacy/provider/legal approval. No real student data in A ever, S15–S24 synthetic only. School Administrator cannot silently alter original Grade Event.

## 3. Course, Class and Content Shell identity

**Subject** = Mathematics etc. **B Course** = the teaching curriculum for a `(school, academic_year, grade, subject, curriculum_stream)` combination, e.g. 2026–27 P4 Maths; **Class/TeachingGroup** e.g. P4A and P4B is assigned to this Course N:1, so it does not duplicate the textbook. **A Content Shell** = one official material vault container for a B Course from S4 onwards, with one Notebook per Shell; before S4 the shell exists A-only. Same-name Courses must not auto-match; explicit A `external_course_key` mapped to B `course_id` in Versioned Binding. Different Course cannot share mutable Source IDs; optional future deduplicated physical blobs still require separate logical owners. Curriculum stream/year changes create new Course and require approved version-copy/retention policy, not hidden relinking. See [Course ADR](../decisions/ADR-012-course-granularity-and-notebook.md).

## 4. Durable user journeys, staged in priority order

**S1–S3:** Admin can A Create Shell→unique Notebook→Upload/Search/Download/Archive and A Restore. S2 classify and version material, hold old sources, publish stable source-manifest+attestation API. Separately B Admin can create real Course/Subject/AcademicYear/TeachingGroups with `CONTENT_UNLINKED` status and B-only Restore; reserve/finalize API is available but does not call A.

**S4–S5:** Admin performs one of two distinct I flows: `ADOPT_EXISTING` explicit A Shell→B Course (no A Create) or `CREATE_NEW` B Course+Reserve → A Provision → B Finalize. Core per-operation reconciliation, conflict isolation and cross-service restore API-level comparison required before S4 release. U S5 publishes the first integrated Sunrise Course/Content Portal, with real sessions and error states. S5 does not imply new future U screens are ready.

**S6–S10:** B S6 provides usable Question/Answer/Marking Rubric/Diagram/PDF Schema editor, including Numeric/Fraction/Multiple Choice/Text/Extended. B S7 Admin sets Gemini API key via Server Secret Store, tests authentication+model+quota+actual inference, rotates or revokes. B S8 generates and validates Draft with Durable Queue, Prompt/Model version, no A required, human approval. I S9 optional version-pinned Evidence Bundle retrieval from A, cross-scope filtering and revocation verification; U S10 provides the corresponding Sunrise Generation Page.

**S11–S14:** B independently adds Maths, Chinese, English, General Studies question/answer/subject-specific rubric/PDF; math answers deterministic when possible, prose answers human-reviewed, GS volatile facts date/source-checked. Each Stage is a live usable B workflow with separate subject test fixtures. **S15–S21:** B synthetic student roster, B Assessment score Draft, B append-only Grade Event Ledger, B submission and manual marking, B AI marking suggestions vs human Gold Benchmark, B deterministic analytics/Weakness Keep-two, then U adds Assessment/Analytics UI. All synthetic data until S25.

**S22–S28:** B staff roles and Course Grants S22; I teacher read-only access to A S23 with revocation, U Teacher Portal S24; B school-approved real PII and Evidence S25; A content archival tools S26, B year-close S27 and I **Dashboard** S28 (core S4 reconciliation already mandatory).

## 5. Permanent integrity rules

- A is the authoritative physical holder of original/retired versions and source hashes; B may retain IDs, citation locators and SHA/provenance, not full textbook originals. Citation pinned to `source_id`, `source_version_id`, `sha256`, `retrieved_at`, `locator`, `binding_revision`, `prompt/model/schema_version` and approved usage rights. Never silently display newer Source version as old paper evidence.
- Sunrise A Policy Layer verifies auth and `source→shell→notebook` BEFORE asking Open Notebook and AGAIN on every result/binary/preview/SSE/LLM context. Empty notebook scope must fail closed; native Open Notebook routes/DB not public. Need block when mandatory secrets missing, and Source retention/licensing conditions from S1/S2.
- I S4 state machine uses durable B operation log + A idempotent operation journal, never an imaginary cross-DB transaction; conflict quarantine, replay, read-after-write, API-level cross-store restore and rollback. All I and U Stage API needs pre-exist with executable contracts.
- B S8 generation includes Schema, Deterministic Domain, Citation Verification where applicable and Human Review. A uploaded documents remain untrusted input for model; never accept prompt injection instructions/tool calls. I S9 evidence signature and short expiry alone is insufficient: check binding revision, published Source Version, revocation and purpose at point of use and again before publication.
- B S17 grade ledger event INSERT-only, audit actor/corrected_event/reason and concurrency revision; projected latest score can be rebuilt from immutable event sequence. Root DBA tamper resistance is separate audit problem. S20 weakness memory limited to two active entries per target and is distinct from all historical Grade Events and Analytics Snapshots.
- B credentials never transmitted to A/U; I has only service-scoped API credentials and no DB connection. B Gemini Key not stored persistently in frontend; A model/embedding credentials if needed are provisioned separately. Async retry cannot be assumed exactly-once.

## 6. Contract Freeze and version/rollback

S2 A and S3 B each produce actual OpenAPI specification and consumer fixtures for S4. S6 Question/Rubric/PDF schema covers future Maths and marking early. S8 B generic optional evidence contract is ready before I S9. S22 B User Grants before I S23. Endpoint paths and release IDs are generated from [Canonical API Inventory](../architecture/API_INVENTORY.json) / [Stage Registry](../quality/STAGE_REGISTRY.json); no manually competing aliases. Breaking data changes use Expand→Migrate→Contract, with minimum compatible API version, schema hash, feature flags, retention/backups, forward-fix/rollback test in owner Stage. Other services pinned unchanged.

## 7. Stage list and requirement trace

| Stage | Runtime owner | Deliverable | Detailed Stage Acceptance |
|---:|:---:|---|---|
| 0 | P | Planning Baseline & Security Decisions | [S0](../stages/STAGE_00.md) |
| 1 | A | Secure Open Notebook Vault | [S1](../stages/STAGE_01.md) |
| 2 | A | Versioned Content Catalog & A Contract Freeze | [S2](../stages/STAGE_02.md) |
| 3 | B | Independent Academic Course & B Contract Freeze | [S3](../stages/STAGE_03.md) |
| 4 | I | Course–Content Linking & Core Recovery | [S4](../stages/STAGE_04.md) |
| 5 | U | Sunrise Course & Content Admin Portal | [S5](../stages/STAGE_05.md) |
| 6 | B | Question/Answer/Rubric Schema Studio | [S6](../stages/STAGE_06.md) |
| 7 | B | AI Provider Key & Capability Settings | [S7](../stages/STAGE_07.md) |
| 8 | B | Durable Generation Queue & Draft Review | [S8](../stages/STAGE_08.md) |
| 9 | I | Version-pinned Notebook Evidence Bridge | [S9](../stages/STAGE_09.md) |
| 10 | U | Sunrise Generation & Evidence Workspace | [S10](../stages/STAGE_10.md) |
| 11 | B | Mathematics Paper Builder & PDF | [S11](../stages/STAGE_11.md) |
| 12 | B | Chinese Language Paper Adapter | [S12](../stages/STAGE_12.md) |
| 13 | B | English Language Paper Adapter | [S13](../stages/STAGE_13.md) |
| 14 | B | General Studies Paper Adapter | [S14](../stages/STAGE_14.md) |
| 15 | B | Synthetic Student Roster | [S15](../stages/STAGE_15.md) |
| 16 | B | Assessment & Score Drafts | [S16](../stages/STAGE_16.md) |
| 17 | B | Append-only Grade Events & Corrections | [S17](../stages/STAGE_17.md) |
| 18 | B | Submissions & Manual Marking | [S18](../stages/STAGE_18.md) |
| 19 | B | AI-assisted Marking Benchmark & Review | [S19](../stages/STAGE_19.md) |
| 20 | B | Deterministic Analytics & Weakness Keep-two | [S20](../stages/STAGE_20.md) |
| 21 | U | Sunrise Assessment/Analytics Workspace | [S21](../stages/STAGE_21.md) |
| 22 | B | Staff IAM, Grants & B Authorization | [S22](../stages/STAGE_22.md) |
| 23 | I | Teacher Read-only Course Content | [S23](../stages/STAGE_23.md) |
| 24 | U | Sunrise Teacher Portal UI | [S24](../stages/STAGE_24.md) |
| 25 | B | Approved Real Student Data Gate | [S25](../stages/STAGE_25.md) |
| 26 | A | Content Retention & Annual Archive Tools | [S26](../stages/STAGE_26.md) |
| 27 | B | Academic Year Closing & Grade Retention | [S27](../stages/STAGE_27.md) |
| 28 | I | Cross-service Health/Restore Dashboard | [S28](../stages/STAGE_28.md) |

## 8. Formal acceptance / decision authority

S0 only docs, old GitHub PR/ADR review and human signoff (no real DB deployment); real S1 onward requires protected staging URLs, actual data persistence, security negative tests, service-owning Restore, API contract freeze, prior release regression, migration compatibility, exact owner SHA/digest and Owner approval. A one-hour Spike tests feasibility only and cannot certify S1. There are no production deployments evidenced in this kit. Review/acceptance ID and future PR details in [QA Matrix](../quality/ACCEPTANCE_MATRIX.md) and [GitHub PR Plan](../delivery/GITHUB_BASELINE_PR_PLAN.md).


## v0.7.4 independent gap gate

Before considering each Owner Stage done, review [19-row contract gap register](../quality/CONTRACT_GAP_REMEDIATION.md) and confirm its API/identity/data-state prerequisites; the candidate interfaces are non-binding until real Provider/Consumer UAT.


## v0.7.5 avoid duplicate implementation

A uses verified upstream Open Notebook ingestion, search, note/insight and credential capabilities via its **private policy adapter**, not a new source/embedding engine. Upstream native auth, multi-notebook source linking, global scope and job-list/cancel placeholders are not trusted Sunrise permissions. B creates an independent authoritative school domain/AI Queue/Papers/Grades because Open Notebook transformations and job worker are not school-grade equivalents. Full source code evidence is in [Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md), and Stage-level dependency corrections in [Stage Flow Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md). All owner security and acceptance gates remain mandatory despite code reuse.
