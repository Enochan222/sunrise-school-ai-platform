# Question, AI, Grade and Weakness Domain Contracts

## B S6 Question/Rubric Schema / reusable by four subjects

Per Question: `question_id`, schema version, subject, question_type (Numeric, Fraction, Multiple Choice, Text Accepted Values, Extended Response), stem, answer_spec, rubric_version, max_score, optional diagram/geometry data and learning objectives. Separate `question_definition`, `answer_spec`, `marking_spec` and `pdf_render_contract`; do not store Markdown-only unsplittable questions. Formal JSON Schema: [Question v1](../../contracts/schemas/question_v1.schema.json). Math-paper is a design reference for validators and PDF, not permission to copy its app as-is; don't assume the external app already passed security review.

## B S7/S8 AI Provider + Queue

B Admin enters Gemini API key once and server stores via a Secret reference. Test levels: format, authentication, model permission, quota, actual small inference; READY reflects recent successful capability test, with expiry/errors. B Generation: durable Queue/Job state, Blueprint+Prompt/Model versions, schema/domain validators, optional signed external Evidence disabled by default, Human Approval, B Artifact; Queue redelivery idempotency but do not claim exactly-once LLM invocations. A Vault might need its own independent provider for extraction/embedding, no B Secret shared directly.

## I S9 Evidence / B Generated Artifact provenance

B records `source_id`, `source_version_id`, immutable `content_sha256`, `retrieved_at`, `locator`, `binding_revision`, `prompt_version`, `model_id`, `question_schema_version`, `rubric_version`, `usage_policy`. I signs short-lived Evidence and B must validate A rights/version revocation immediately before use and prior approval. Citation integrity is source-supported, not simply RAG retrieval successful. PDF Source text and OCR are untrusted data; no instruction privileges. A retains original material; B stores necessary provenance only.

## B S17 Grade Events

`SUBMIT` creates immutable event (ID, Grade Key, score, actor, op id, timestamp, revision). `CORRECT` is a new event referencing prior event and expected_revision, with mandatory reason. Normal app/DB roles have INSERT/SELECT but no UPDATE/DELETE for historical events, and DB concurrency/unique revision check prevents race. `current_projection` rebuilt from ledger. Model `grade_event_v1.schema.json` is only a structural contract, not SQL privilege proof. A DBA can still alter rows with high privilege; audit/encrypted backup and external tamper evidence considered separately.

## B S20 Analytics/Weakness

Keep separate: entire Grade Events (source), reproducible Analytics Snapshots, Weakness Candidates (not yet user-chosen), Weakness Memory (user Keep max 2 Valid Active scoped Course/target). Third Keep retires oldest active in transaction, never deletes Grade history. Event correction invalidates dependent snapshots/memory by watermark/STALE flag. Teacher may choose keep later; sole Admin until S22.

## B S19 AI Marking quality gate

PTH_Homework can inspire multi-pass suggestion and disagreement detection, not a security-compliant server. Test extraction, alignment, score range, partial credit, confidence, human judgement vs independently hand-labelled Gold Dataset, and audit of reviewer edits. Multiple AI passes may share OCR errors; agreement is not proof. Final formal event only after human Review and independent validation. No student marks in A.


## v0.7.4 contract-bound additions

S6: A Blueprint is a **B-owned versioned object** with create/read/draft update/publish/version history, stable QuestionTemplate and RubricVersion references. S8 `blueprint_id` PLUS `blueprint_version` must be resolved server-side and pinned at Job creation; cannot enqueue a missing/unpublished Blueprint. S9 Evidence uses B Worker ServiceToken-only I validation (see [Evidence Revalidation](EVIDENCE_REVALIDATION.md)). S17 grade Event Idempotency requires payload hash (see [Grade Idempotency](GRADE_IDEMPOTENCY.md)); S20 Weakness supports Candidate, Active, Retired, Stale, Keep and Discard before S21 U renders them. S18 per-item marking requires rubric-versioned score decisions, not unreviewed AI output as a Grade.
