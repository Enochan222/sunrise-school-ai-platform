# Final Stage 1 technical acceptance — implementation main 7ebe3d89

Tested implementation: `7ebe3d89e49ca5623030427c73804da12021552b`, Git tree `658d687edd7f63139db5750d0b8aea06b091acdd`. This separate reviewer-owned reconciliation changes documentation only. It does not retest or relabel its own future docs commit as runtime source.

All fifteen formal local synthetic cases actually PASS. Owner explicitly accepted this latest-version UAT. Independent fresh-context agent review verified the case artifacts, dependencies, eighteen immediate child traces, Windows signatures and a second complete restore; it also ran its own 500-test regression. This is agent review, not a human GitHub approval. R01 remains **NO-GO / NOT_APPROVED** pending separate release authority, signed Release Manifest and applicable operational decisions. No deployment is authorized. Hosted Native workflow is NOT_RUN; no new dispatch was requested.

## Gate matrix and commands

| Gate | Result | Executable evidence |
|---|---|---|
| S1-AT01–15 | 15 PASS | New full campaign `campaign/private/full-15-01/stage1-at-run.json`; per-case hashes in [matrix](artifacts/final-main-7ebe3d89/formal-case-matrix.json) |
| Full pytest | 500 PASS, exit 0 | Product Python 3.11.11 `-m pytest -q tests`; full-pytest.json/log |
| Dedicated Stage 1 | 486 PASS, exit 0 | Product Python `-m pytest -q tests/stage1`; dedicated command metadata |
| Workflow contract | 54 PASS, exit 0 | Existing workflow contract suite, exact argv in command metadata |
| Governance / verify_kit | PASS, exit 0 | Separate pinned Governance Python `scripts/run_qa_no_actions.py` and `scripts/verify_kit.py` |
| Compilation / Node | PASS, exit 0 | Exact Python compile argv and `node --check apps/a-vault/ui.js` |
| Separate dependency environments | PASS, exit 0 | Product and Governance Python 3.11.11, each pip check/freeze retained |
| Native auth, TLS and school/shell isolation | PASS within executed cases | AT02/03/07/08/09/10/11/14/15 and Windows signed real port refusals |
| ACK-loss / concurrency | PASS | Current AT06 actual journal crash/lost ACK and eight-worker contention modes |
| Persistence / full cold restore | PASS | Formal restore plus second fresh independent full A DB/ON DB/originals/Native restore |
| Recovery negatives | PASS expected rejection | Actual wrong key, missing PDF, mixed snapshot, corrupt DB bytes, stale Native image; no target created |
| Semantic index fault | PASS expected failure | Third fresh target: drop three actual search indexes, scoped search HTTP500 and Native readback reject; no rebuild claim |
| Owner UAT | ACCEPTED | [Source-bound chat receipt](artifacts/final-main-7ebe3d89/owner-uat-acceptance.json) |
| Release Manifest | UNSIGNED candidate | [Candidate](artifacts/final-main-7ebe3d89/R01-release-manifest-candidate.json) |
| R01 / deployment | NOT_APPROVED / NOT_AUTHORIZED | Distinct Owner decision and applicable operational signoffs pending |

[Executed QA command metadata](artifacts/final-main-7ebe3d89/executed-qa-commands.json) records argv with symbolic local roots/endpoint redaction, cwd, source/tree, actual UTC and exit codes; private-original metadata hashes bind the unredacted commands. Docker console output is omitted with its hash retained. The private raw campaign traces retain the eighteen actual child command arrays and stdout/stderr with exit codes. Product and Governance environments are separate because the pinned dependencies are incompatible. The approved synthetic runtime uses pinned ON commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`, distinct A/ON DB credentials/volumes/private networks, strict TLS Gateway and pinned separate physical Windows observer. Observer private keys stayed on Windows.

## Reproduced failure and repair

The first campaign on merged `d7499142…` had fourteen PASS and AT13 FAIL. The manifest validator rejected the packaging filename although its three changed A-only entries matched Git blobs. PR #30 added bounded validation with regression and negative cases; it preserves rejection of non-A/workflow changes. Its squash produced this tested main. The original failure is retained and is not retrospectively PASS. Earlier source campaigns and UAT remain historical evidence only.

## Evidence identity and practical limits

Runtime identity SHA256: `e37a6d9cf8e2c2a1c7e1f7e11b08b6d36b915ed72ff5484148d67f690a42f07a`. Cold bundle SHA256: `ffd3d226c5006bcf5f755f60eb183a111b1e3150b9c918ccac150b512b145bc4`. Full run SHA256: `4cdcf3912d04491028be37fcf56c8265aa920ea39dcfa3599fbbf693cb490075`. Formal restore readback SHA256: `a96eac76b9301d44f747160ac1711c859d01a70de97197136c7aa9d151c892c5`. Independent semantic result SHA256: `cbadc8de8fc3304d6961455b3c41c4c8265bd98fd6eeaf1a3c18b39c5a1e1ffc`.

All eighteen immediate child traces are captured and hash-verified. Nested pytest stdout inside regression.py is only hashed by that child; separate same-source 500-pass console and independent 500-pass console are retained. AT10 live assertion checks denied HTTP/non-PDF prefix; universal absence of every foreign fragment is not independently established by that assertion. The reviewer inspected double ownership checks and negative component coverage. Independent review's live Docker inspect timed out; coordinator live read-only check succeeded, and the limitation remains recorded. No P1/P2 was found in that review.

Restore observation 13.700125 seconds is DB restore through Native readback only, not full Gateway availability RTO. Zero differences refers to verified inventory at the frozen recovery point, not a continuing backup SLA. Local immutable Native image ID is not represented as a registry digest. Backup frequency, off-host escrow, release host/region/operator policy and other applicable operational approvals are not invented. B/I/U remain absent and unchanged. See [independent update](artifacts/final-main-7ebe3d89/independent-review-update.md).

## Raw local evidence and retained state

Durable private evidence: `$PRIVATE_EVIDENCE_ROOT/final-technical-acceptance/` with SHA256SUMS. Actual original artifacts, cold bundle and configuration remain in `$CAMPAIGN_ROOT/`; independent restore evidence in `$REVIEWER_ROOT/`. Raw backups, private logs, credentials and original data are excluded from GitHub. Source is frozen, volumes retained, no destructive rollback or deployment performed.

The next reviewable action is this docs-only reconciliation, followed by separate Owner release/operational decisions and final manifest signing. Merging documentation cannot authorize R01, hosting, paid services, real data or Stage 2.
