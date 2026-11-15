# Sunrise Stage 1 [A] — Owner UAT Guide (SYNTHETIC ONLY)

**Status: IMPLEMENTED_UNTESTED.** This is an Owner UAT *procedure*, not a result, release approval or invitation to process real school/student data. Reviewer must first authorise a specific merged/tested code SHA, verify the Docker image digests, native worker, isolated restore and security gates, and supply a private environment.

## 1. Authority and scope

- Single Admin account, **two synthetic schools** (`synthetic-school-a`, `synthetic-school-b`) within a trusted *server-held* allowlist. Do not create second teacher account or use client headers to select a school.
- The only approved browser entry is the private A Gateway. Never open the raw Open Notebook API, native UI or SurrealDB from a public/untrusted network.
- Open Notebook pinned v1.15.1, commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`, SurrealDB v2.3.10, verified A-only text patch, **no Gemini/Embedding/AI/chat**.
- Use only newly generated born-digital synthetic PDFs from `scripts/stage1/acceptance/synthetic_fixtures.py`; the operator must provide an appropriately licensed Extended-Han-capable font. Never include actual pupils, school records or confidential teaching material.
- UAT cannot begin merely because this file or the Python source exists. Owner must record start/end UTC, exact code Git SHA/tree, image IDs/digests, container/project/DB identities, fixture hashes and assigned reviewer.

## 2. Safe local prerequisites (operator/reviewer, not run in coding-only phase)

1. Open the exact reviewed Git revision in a **separate synthetic checkout**; confirm `git rev-parse HEAD` and `git rev-parse HEAD^{tree}`. No tests or Docker actions are authorised during the current coding-only gate.
2. Use the existing private Stage 1 Compose and pinned patch. Supply secrets privately (environment / untracked secure secret source); do not paste passwords, JWTs, cookies or encryption keys into an issue, PR, UAT worksheet or shared screenshot.
3. Supply `VAULT_SCHOOL_ALLOWLIST=synthetic-school-a,synthetic-school-b`, `VAULT_SCHOOL_ID=synthetic-school-a`, `VAULT_STORE_BACKEND=surreal` and the exact verified A/ON DB namespace/database identities. The School Selector is always sourced from the server session.
4. Start the verified **private** local Gateway only after reviewer approves runtime configuration. Browser uses the Gateway URL supplied by the operator. HTTPS is a formal AT07 prerequisite; loopback HTTP alone is not evidence for remote HTTPS.
5. Generate two independent synthetic fixture groups, and **record** the expected English, Traditional Chinese and Extended-Han text markers, PDF SHA-256, file sizes and school assignment. Do not share the original passwords or tokens in logs.

## 3. Owner-controlled functional walkthrough

| Step | Owner action | Required observable result | Evidence to record |
|---|---|---|---|
| 1 | Open Gateway Login; log in as the **only** Admin | Protected Dashboard appears; `/admin` is inaccessible anonymously; no Native credentials exposed | Screen reference + HTTP status, redacted |
| 2 | Inspect school selector | Only Server-allowlisted synthetic A/B visible; default is A | School ID, no credential |
| 3 | Create Year/Grade/Subject/Stream Shell for School A | One Shell ID and one pinned Native Notebook mapping; same Idempotency-Key cannot create duplicate | Shell/Notebook hashed IDs and operation reference |
| 4 | Upload synthetic English & Traditional Chinese PDF to A | Original SHA correct; first receipt shows processing, **not** falsely READY; Worker independently completes extraction | PDF SHA, Source hashed ID, worker outcome |
| 5 | Search source marker within A Shell | Exact notebook-scoped text-only results; meaningful Chinese text; no Vector fallback on overflow | Search query classification and authorized source IDs |
| 6 | Download original A Source | PDF bytes/SHA match uploaded synthetic original; authorization happens before first byte | SHA comparison + HTTP status |
| 7 | Archive the A Shell | Archive state changes; original bytes retained; new Upload rejected; existing references remain available under permitted policy | Before/after state |
| 8 | Switch to B through selector, not header | Active School B displayed after session/CSRF rotation; B cannot read A Shell, A Source or search its material | School IDs, denial status |
| 9 | In B, create independent Shell/Notebook/PDF | B operation succeeds, with unique mapping; B materials are distinct from A | Record IDs and SHA |
| 10 | Try A Shell/Source IDs while active School B | 403/404, **no foreign content**, no preview/SSE/global search bypass | Redacted status/trace only |
| 11 | Switch back to A | Session holds A again; B IDs are now denied. Old CSRF must fail; arbitrary School header has no effect | Updated session/scope + negative status |
| 12 | Log out, attempt `/admin` again | Session revoked and Dashboard denied until re-login | HTTP denial |

Any inconsistent result, wrong School selection, duplicate Notebook, foreign Source or unverified Worker status is a **STOP and REVIEW** condition. Do not continue destructive steps while uncertain.

## 4. Recovery, restart and isolated restore (technical operator only)

- Reviewer first runs real WP03 journal/ACK-loss with fixed SHA. A full ACK-loss without an exact native receipt/marker must remain quarantined; **quarantine is not a recovery PASS**.
- Confirm gateway maintenance write-freeze, in-flight operation count, Worker drain and strict A/Native DB identity before cold capture.
- A successful archive/DB snapshot creation alone does **not** prove recovery. Perform `scripts/stage1/restore/isolated_restore.py` against a NEW Docker Compose Project and NEW volumes only. Keep original project and all its volumes untouched.
- Compare exact before/after A operations, owner mapping, graph direction, rights/license/retention/version, original PDFs, migration/index and search identity. No shared writable source/target volumes.
- Missing/wrong key, corrupt backup, dirty snapshot, missing Source, mismatched Image/DB, or target collision must fail without exposing the restored Gateway.
- Evidence classes for the owner: `NOT_RUN`, `FAILED`, `PASSED_LOCAL_CANDIDATE`, `REVIEW_PENDING`. Do not mark S1-AT05 / S1-AT12 as approved without formal Reviewer gate.

## 5. Record decisions

Maintain `OWNER_UAT_WORKSHEET.md` as a private worksheet with no identifying personal data, credentials or student records. Owner reports UI usability and expected actions; Integration Reviewer alone updates the formal WORKBOARD / S1-AT verdicts and decides any PR Merge. `R01` remains `NOT_APPROVED` until explicit later Owner release decision.

**Current coding-only phase:** all real UAT actions above are **NOT_RUN**.
