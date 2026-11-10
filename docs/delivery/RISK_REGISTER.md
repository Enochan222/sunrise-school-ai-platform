# Risk Register — Reviewed v0.7

| Risk ID | Stage first affected | Failure mode | Release-blocking control |
|---|---|---|---|
| R1 | S1 A | Native Open Notebook API exposed, missing password disables auth | Mandatory secrets fail startup, private API ports, negative raw routes |
| R2 | S1 A | Empty Scope/global search, preview/SSE leakage | Before+after owner checking, no arbitrary Notebook IDs, file/stream negative tests |
| R3 | S1/S2 A | A data cited then source overwritten/deleted | Immutable Source Version/Hash/Locator, retention/AI usage/licence policy early |
| R4 | S0/S3 B | Course granularity confused with Class/Notebook | ADR-012, school/year/grade/subject/stream scope, Class N:1 Course |
| R5 | S3 B | Reserve/Finalize not atomic, duplicate B Course | Single DB transaction Course+Op, unique binding and replay different-body 409 |
| R6 | S4 I | A success/B response lost, orphan or two Notebooks | Durable B/A logs, Saga state machine, read-after-write, quarantine and API Restore |
| R7 | S4 I | One owner Stage secretly patches both Backend | Contract freeze, path/image/DDL owner diff, DB egress denial in I |
| R8 | S5 U | Portal claims future B functionality already present | Independent U-only feature gates S5/S10/S21/S24; B native UI until then |
| R9 | S7 B | Gemini Key exposed in Browser/log/queue | Secret Store, masked entry, rotate/revoke, 5-step capability test |
| R10 | S9 I | Signed Evidence stale, revoked or prompt injection | Source version/Hash/purpose/exp/jti/binding rev/TOCTOU pre-use, untrusted context |
| R11 | S17 B | Grade Event overwritten or correction races | DB append-only, CAS revision, audit actor, rebuildable projection |
| R12 | S19 B | AI marking passes despite shared OCR errors | Independent manually labeled Gold Set, partial-credit/align/extraction tests |
| R13 | S20 B | Weakness Keep2 wrongly removes historical Grades | Separate Memory/Candidate/Analytics Snapshot/Event and stale flag |
| R14 | S22/S23 | Teacher grant revoked but cached A Source link valid | B revocation epoch per-call check, I deny cached links and no teacher A raw API |
| R15 | S25 B | Real student data loaded without policy/legal signoff | import fail closed, real PII prohibited before approved Stage |
| R16 | Every release | Old app image incompatible after DB Migration | Expand/Migrate/Contract, compatibility manifest and forward-fix plan |
| R17 | S0/GitHub | main v0.5 and ZIP v0.7 conflict causes wrong PR | Owner-reviewed docs PR, new ADR ids, old Issue mapping, preserve CI/CODEOWNERS |
