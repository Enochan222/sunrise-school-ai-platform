# Reuse-first Implementation Policy (v0.7.5)

This supplement does **not** approve any untested supplier/service. It clarifies which code to carry forward versus where Sunrise owns new behaviour. All ownership and release gates remain authoritative.

## Default implementation decision

1. Before building a new A component, inspect the exact pinned Open Notebook source/API for equivalent Notebook/Source/Notes/extraction/search/credential/worker/UI capability and provide `REUSE | WRAP | BUILD` decision with code path+test evidence.
2. Always wrap native A operations with school/shell/source ownership; never expose raw upstream create/delete/list/search or secret to ordinary Sunrise browser clients. Reuse native functionality as *internal engine*, not as a trusted authorization boundary.
3. B must not take a shortcut by storing exam papers, students, grades or analytics as Open Notebook Sources/Notes. B's own durable task queue is necessary despite A's existing source-processing worker.
4. Native A `Source.topics` can be used for coarse categorisation, but School Source Version/Publish/Right/Hash metadata is a separately governed A policy. Avoid duplicate fulltext extraction, indexing and file copies.
5. Reuse UI components/patterns when cheaper than rebuilding, but replace API clients, permissions and navigation; do not present inherited unrestricted Open Notebook Admin UI as school front-end.
6. B-only stage requires real usable protected local trial surface; U stage is separate unified presentation. Record the distinction explicitly in acceptance evidence and release manifest.
7. For the first release pin upstream commit/image digest and test default auth, source scope, credential encryption, migration & backup. Upstream upgrades are A-only releases with compatibility tests for I/U consumers.
8. Optional AI-provider/Chat/Transformations/Podcast features are not secretly part of S1 or S2. A Gemini / B Gemini secrets are distinct until a separately approved cross-system credential design is proven safe.

## Task sizing

Do not extend S1/S4 indefinitely because of existing upstream code. Use internal implementation slices and Scope Stop gates; only formal Rxx can be marked complete after all functional+security+data/restore/owner tests pass. If one consumer needs a new owner API, add a preceding owner-only Stage/PR and update the Registry/AT/ADR before integration. No undocumented mixed owner PR.

**B supply-side reuse:** Before coding auth/queue/provider SDK manually, evaluate Supabase Auth/RLS, Queues (pgmq logged tables), Storage, PostgreSQL constraints and Esperanto model provider library as independently maintained components. The business authorization and immutable grade/assessment semantics are still Sunrise's responsibility. A's SurrealDB and keys must remain isolated. pgmq retry uses visibility windows; require idempotent B effects in tests.
