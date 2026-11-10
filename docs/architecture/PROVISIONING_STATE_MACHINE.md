# S4 Integration State Machine: CREATE_NEW vs ADOPT_EXISTING

**State owner B**: durable `course_operations` and `course_bindings`; **A owner**: `creation_op` journal and immutable source/Notebook metadata. I reads and updates only through published A and B HTTPS APIs; it has no database of record and does not directly connect to either store. See machine file [course_binding.json](../../contracts/state_machines/course_binding.json).

## Why two flows

**CREATE_NEW**: I calls B `POST /core/v1/course-operations/reserve` with `mode=CREATE_NEW`, stable `link_key`, canonical body hash + scoped idempotency key. **Within one B SQL transaction**, B (i) creates/claims Course and (ii) writes reserved operation. If B fails, both roll back. I then A `POST /vault/v1/internal/provision` with same link_key and child operation ID → A returns existing Shell/Notebook or creates exactly one. Finally B `POST /core/v1/course-operations/{operation_id}/finalize` after verifying both read APIs and uniqueness.

**ADOPT_EXISTING**: B Course exists and is `CONTENT_UNLINKED`; Admin selects an A Shell by immutable `a_external_course_key`. I dry-runs collisions and source owner/version manifest; calls B Reserve with `mode=ADOPT_EXISTING`, validates A existing object via A manifest; **must NOT call A Create**; B Finalize binds existing shell/notebook (no hard delete/recreate). B `course_id` and A `external_course_key` are separate IDs linked by approved, versioned binding.

## Binding state transitions

| State | Allowed next | Condition / action |
|---|---|---|
| `UNLINKED` | `RESERVED`, `ARCHIVED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `RESERVED` | `PROVISIONING`, `VERIFYING`, `RETRYABLE`, `CONFLICT`, `QUARANTINED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `PROVISIONING` | `VERIFYING`, `RETRYABLE`, `CONFLICT`, `QUARANTINED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `VERIFYING` | `ACTIVE`, `RETRYABLE`, `CONFLICT`, `QUARANTINED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `RETRYABLE` | `PROVISIONING`, `VERIFYING`, `CONFLICT`, `QUARANTINED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `ACTIVE` | `VERIFYING`, `CONFLICT`, `QUARANTINED`, `ARCHIVED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `CONFLICT` | `QUARANTINED`, `VERIFYING` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `QUARANTINED` | `VERIFYING`, `ARCHIVED` | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |
| `ARCHIVED` | terminal | Must use B status/version/idempotency compare-and-swap and verify predecessor constraints |


Course business lifecycle (ACTIVE/ARCHIVED) is separate from binding operation state: a B Course can be ACTIVE but CONTENT_UNLINKED, and no A content should appear. Binding ACTIVE requires B Course exists, A Shell+Notebook exist, `link_key` matches both journals and binding record, unique course/shell/notebook mapping, Source ownership/Hash checks, A and B **read-after-write** API queries match.

## Crash / Retry matrix

| Failure injection | Correct response |
|---|---|
| B Course insert but operation reserve fails | B transaction rolls back entirely; no orphan Course from a half-reserve |
| B Reserve 200 but I loses ACK | Query B operation with same key/body hash; same response; no new Course |
| A creates notebook but I times out before response | Query A creation op and Shell; retry same key, get exact same Notebook ID; no blind Create |
| B Finalize succeeded but I lost ACK | GET B operation+binding and A manifest; no duplicate Finalize Binding |
| Same idempotency key, different request body or actor scope | HTTP 409, retain existing object unchanged |
| A Shell already bound to another Course | 409/CONFLICT→QUARANTINED, never overwrite or delete Source |
| A Source changed/revoked during B binding | VERIFYING then CONFLICT/STALE; human Resolve, no false ACTIVE |
| I down after cutover policy freeze | A/B read-only existing data and B operation list remain; worker resumes on restart; no two concurrent create authorities |
| Backup of A and B not same logical epoch | Restore separately in isolated environment; I API manifest reconciliation blocks READY until explicit forward fix/repair |

## Cutover sequence

A S2 pre-releases `POST /vault/v1/admin/cutover-policy`, which only controls new `ContentShell Create` modes: `STANDALONE` → `FREEZE` → `MANAGED` (no unplanned global toggle); Source read/search/download and Admin incident Restore stay accessible. In S4 I proves dry-run and owner signs a maintenance window; set FREEZE, reconcile all existing operations, enable MANAGED for I service principal, disable standalone public Create. If I goes down, freeze new creates and preserve A/B independent read/restore; don't automatically revert to simultaneously writable two authorities. Recorded operation logs support finite retry with backoff and manual quarantine; never compensate by deleting A Notebook.

## Release S4 hard blockers

Consumer contract tests against **deployed S2 A and S3 B**; I has no DB egress; crash injection at every ack boundary, duplicate key+different body, same-name collisions, material hashes, orphan recovery, A/B paired restore API reconciliation, write-freeze/rollback rehearsal, source-scope tests. S28 is a Dashboard convenience, not the first time core reconciliation exists.
