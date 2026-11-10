# Authorization and Privacy by Owner/Stage

S0 designs actor and scope: `school_id`, `subject_id`, `course_id`, `actor_id`, `created_by`, `owner_id`, `access_scope`, `audit_actor`, binding version and tenant security boundary; these fields are recorded from S1 A and S3 B, even with **one Admin only through S21**. Avoid redoing all data when S22 users added.

S1 A: Password/MFA protected external Admin gateway, server authorization and source scope check for Create/Search/Download/Preview/SSE. Open Notebook raw API private only; if `OPEN_NOTEBOOK_PASSWORD` absent, its upstream middleware may bypass auth — Sunrise fails startup and does not expose raw routes. Secrets from service-side Secret Store, encryption keys backed up separately from DB dumps. S2 A: Source/Version Ownership and AI usage restrictions and retention documented/checked, not mere UI hide.

S3 B: separate PostgreSQL project and immutable audit actor fields; no browser `service_role`, no A direct DB link. Basic RLS/DB role constraints before real students. S4 I: service JWT scopes and egress allowlist only, no A/B DB ports; B operation log auditable. S5 U: Session expiry/logout/CSRF protection and no DB SDK/admin passwords. S7 B Gemini key encrypted/reference on server, rotate/revoke/test; never place in localStorage/Queue logs.

S9 I signed Evidence: `kid`/issuer/audience/purpose/jti/time/binding revision/usage policy and source version validated at model-use time, not only ingestion. No user-supplied Notebook ID, prevent document Prompt Injection elevating data to API authority. S17 B immutable Grade Event Ledger DB privilege enforced; S22 staff IAM. S23 I queries B Grant epoch on every teacher course-content request, no prolonged unsafe cache; read-only A and no student data crossing. S25 B real PII with school/provider/privacy signoff. S26/27 advanced retention UI, but basic policy mandatory from S1/2.

Privileged physical DBA is outside normal append-only guarantee; sensitive event streams may additionally require tamper-evident external audit for production. Incidents/misbindings stop new writes and quarantine until owner approves repair.

## Contract-specific service principals (v0.7.2)

I is not a human user and must never borrow AdminSession. A S1/S2 and B S3 endpoints have explicit `ServiceToken` alternative **only** where required by downstream I, each with a single named service scope. Both API owners verify JWT issuer/audience/expiry/subject/jti, course/source owner, rate and size limits, audit and replay. S22 introduces B private per-staff grant lookup accessible only by I `core.grant.check`; self grant lookup is `StaffSession`. S23 I teacher content route accepts `StaffSession` only and obtains B permissions using its own service principal. Do not put Supabase `service_role` or Open Notebook native password in I/U.

Stage1 Gemini embeddings or source AI search, if selected, need **A-owned secret configuration, explicit provider scope/cost/retention approvals and tests** in S1; it does not implicitly use the B S7 Gemini BYOK. B S7 is a separately owned provider credential manager for Generation. If A-side semantic AI provider is not safely approved, S1 still needs usable deterministic text search and Source Indexing; the model-enabled search is an optional approved S1 branch, not a hidden dependency on future B.


## v0.7.4 Effective Staff Rights from S22

`StaffSession` is accepted only on explicit B business operations with `staff_activation_stage=S22`, and each Owner API checks effective current School/Course/TeachingGroup/student grant, revocation epoch and object ownership. Teacher B Course/Assessment/Grade/Submissions reads and authorized first Grade submission/manual marking do **not** borrow AdminSession; formal Grade corrections and IAM administrative changes stay Admin-only. S23 I may read B grants using its own `core.grant.check` ServiceToken and give teachers A read-only content; no other I/A operations are elevated. Do not infer authorization from OpenAPI alternative security alone; add provider/consumer checks and DB enforcement.
