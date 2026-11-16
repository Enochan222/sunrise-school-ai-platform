# Stage 1 operational RPC failure recovery — Issue 34

This is an operational repair and an A-only error-handling change, not a replacement for the historical R01 acceptance or a new Stage release. See [Issue 34](https://github.com/IssacSitHk/sunrise-school-ai-platform/issues/34).

## Observed failure and operational repair

Two controlled Mac attempts on accepted implementation `7ebe3d89e49ca5623030427c73804da12021552b` failed: first an eight-second A RPC query-receive timeout caused the Shell list to return HTTP 500; the second list succeeded, but scoped search returned HTTP 503 and cleanup logout timed out during a new WebSocket handshake. Neither attempt established operational usability. Their original failure records remain unchanged.

The Docker VM had approximately 243 MiB available RAM and almost no free space in its 1 GiB swap. Thirty-three historical restore-test containers across twelve `sunrise-s1-restore-*` projects were still running. After explicit Owner approval, only those existing historical restore containers were stopped. Original named/anonymous volumes, keys and backups were retained; the Owner UAT project, Open WebUI and every other previously running container were verified still running. Available VM memory increased to approximately 5.4 GiB, with approximately 829 MiB swap free.

Subsequent controlled tests used the **same accepted source, container identities, keys, volumes, SQL and eight-second timeout**. The full authenticated login, existing Shell/Notebook, scoped search, original PDF SHA256 and logout/relogin HTTP journey passed. Read-only probes after the journey also passed for `RETURN true`, filtered Shell selection and the exact previously failing ordered selection; the final ordered probe took approximately 100 ms including connect/signin/use/query/close.

This before/after evidence supports resource contention from accumulated restore runtimes as the operational explanation. It does not prove a specific kernel/database defect, exclude every intermittent transport failure, or establish a production SLA. Do not claim that an index change or a timeout increase fixed the fault: neither was performed.

## Code hardening in this candidate

An unavailable A DB now produces a sanitized HTTP 503 rather than an unhandled HTTP 500, including failures during authentication, session readback and material operations. The response states that the operation outcome is unconfirmed. It does not create an authentication cookie after an uncertain login write, suggest replay, expose backend exception messages or automatically retry a transaction.

A RPC transport failures record only the fixed phase (`connect`, `signin`, `use`, `query`), monotonic elapsed milliseconds and exception type. Native request failures record only the endpoint category, elapsed milliseconds and exception type. SQL, URLs, bound parameters, source IDs, credentials, cookies, tokens, request/response bodies and underlying exception messages are excluded from these logs. Existing timeouts, private boundaries, per-request authorization, ownership rechecks and transaction semantics are unchanged.

The code candidate is separate from the operational fix: its changes were **not deployed into the frozen accepted Gateway**. A successful smoke of `7ebe3d89…` must not be represented as a runtime test of this candidate's future Git SHA. Candidate fault/regression tests and runtime evidence have separate identities.

## Safe operating procedure

1. Verify the exact accepted source/tree, existing private configuration/keys, stopped container and volume identities, strict Gateway TLS identity and latest verified cold backup before any controlled startup.
2. Inspect VM capacity and the exact running synthetic project list. Restoring many isolated targets for acceptance does not authorize leaving all of them consuming resources indefinitely. Obtain scope-specific approval before stopping other projects. Stop only pinned approved IDs; never prune, delete volumes, reset DBs, replace credentials or stop unrelated services.
3. Keep Gateway maintenance enabled while starting the existing DB/relay containers. Check the current ON schema version against the pinned migration list before starting Native; pending/unverified migrations block a no-migration smoke. Verify A source ownership, Native graph and all original PDF hashes against the recovery point's authoritative metadata.
4. A normal pinned Native source read stamps `last_viewed_at`; the pinned `source.updated` field also evaluates `time::now()` on that update. Compare every other source field before/after and verify graph, original hashes and A business records. Do not interpret these documented read timestamps or normal authentication audit records as byte-for-byte DB rollback. Never silently ignore unexplained content changes.
5. Release the existing maintenance flag only after all checks pass. Execute the complete real login/list/search/download/hash/logout/relogin journey. Record source SHA, commands, UTC, statuses, exact identities and sanitized hashes. Use a fresh transport to clean up this attempt's own session via the authenticated logout API; never replay an ambiguous DB write or directly delete session records.
6. In `finally`, restore the original maintenance marker, drain requests, stop only the six original approved services, verify the same mounts/volumes/keys/backups/source remain and check the Gateway reports maintenance enabled. Report operational usability and frozen-state restoration independently.

## Validation and limitations

Ten new focused cases cover backend failures in login/list/session authentication, absent login cookies after uncertain writes, sanitized phase/Native logging, and no automatic write replay. The full local regression suite passed **510 tests**, including the existing browser and real loopback ACK-loss tests. Pinned local governance QA passed its sixteen commands. The first sandboxed full run could not launch Chromium or bind loopback sockets; it is retained as a restricted execution attempt, not counted as PASS.

Original private traces, backup/key references, resource snapshots, approved stopped IDs and controlled smoke records stay outside Git. The runtime evidence is an operational diagnostic subset, not all fifteen formal S1 acceptance cases, an independent review, a merge approval, deployment authorization or a new R01 signoff. Earlier failed verification-tool attempts are preserved; five successful HTTP steps alone do not override an unexplained preservation failure.
