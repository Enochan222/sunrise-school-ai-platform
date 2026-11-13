# Builder C Stage 1 [A] — Fixed Revision Codex Runtime Handoff

Source status: IMPLEMENTED_UNTESTED. No Builder C runtime, Docker, pytest,
compile, lint, HTTP, browser, backup or restore execution took place.
No formal acceptance or Owner UAT has been granted.

## Fixed-revision prerequisites

Integration Reviewer must first freeze the current PR #14 commit SHA and exact
tree SHA. Codex Local checks out that revision and uses ONLY synthetic data.
Every subsequent source modification invalidates affected prior runtime proof.
The upstream is Open Notebook v1.15.1 pinned to commit
5e285b7a2e435895c4ee99ad7e4b8d2af64c3239, tree
2d101001de594c7d6a0e4aaeb8e85ac4c52980af; SurrealDB is v2.3.10.
Do not start GitHub Actions, external AI, public services or real student data.

## Code and runtime coverage

The private patcher edits five pinned staging-copy files: text search, retry,
reference graph, API marker and scripts/docker-entrypoint.sh. The latter rejects
missing or weak Native/password/Surreal secrets BEFORE supervisor API/worker.
The preparer records all five modified paths in the source patch provenance.
AT08 additionally exercises the exact attested Native image entrypoint in a
networkless Docker run, requiring baseline exit 0, and missing/weak-secret
negative exit 78 plus a secret fail-start marker.

SurrealStore journal must undergo real v2.3.10 transaction/CAS, index,
concurrency, TCP ACK-loss and restart verification. New code includes atomic
Admin Login/Logout/School Switch audit records and receipt-bound SourceOwner
commit. The A Journal DB and Native Graph DB require separate identity proof
even if physically served by one Docker SurrealDB instance.

## AT01 and browser

Install the dev requirements (including Playwright) and a local Chromium browser
on the private testing host before using
scripts/stage1/browser_admin_journey.py. The browser script is loopback-only
and exercises real Admin login, school context, create Shell/Notebook, PDF
upload and Worker READY, scoped text search, original PDF byte/hash download,
archive and logout. It records actual Playwright and Chromium versions.

scripts/stage1/real_admin_journey.py remains PARTIAL by design. The updated
acceptance/run_stage1.py uses that real native HTTP journey as a preflight
BEFORE cold capture, and produces a distinct S1-AT01 Candidate only when
AT04 restart, AT05 isolated restore, AT15 two-school negative and genuine
Chromium checks have passed with the same source identity. A partial report
is never upgraded to PASS without those independent case files.

The orchestrator CLI is:

    python scripts/stage1/acceptance/run_stage1.py --config SCENARIO.json --source-sha COMMIT --source-tree TREE --output-dir NEW_EMPTY_DIRECTORY

SCENARIO.json provides separate case_flags for the fixed S1-AT commands,
browser_flags for the AT01 Chromium script, and restore_flags with capture,
restore and native dictionaries. No arbitrary shell commands may be supplied.

## AT07 independently reviewed synthetic-only data

AT07 requires real HTTPS Gateway, private boundary evidence, real Admin session
login/school-switch/logout with verified A SurrealDB audit records and a
Secure/HttpOnly/SameSite=Strict cookie. It also requires a separate human
Owner/Reviewer review of ALL A + Native databases, persistent volumes and
original PDF files. Synthetic school names alone do not prove absence of
real personal data.

Provide the signed JSON with fields payload and signature_ed25519, where
payload includes:

    type = S1_SYNTHETIC_DATA_INDEPENDENT_REVIEW_V1
    source_commit = exact tested commit SHA
    source_tree = exact tested tree SHA
    runtime_identity_sha256 = SHA-256 of exact runtime identity file bytes
    context = tested Docker context
    project = tested Compose project
    scope = FULL_ISOLATED_A_AND_NATIVE_DATABASES_AND_ORIGINAL_FILES
    reviewed_synthetic_only = true
    real_student_data_present = false
    reviewer_role = OWNER_OR_INDEPENDENT_REVIEWER
    reviewed_utc = reviewed UTC timestamp in Z notation

The independent signer canonicalizes payload as JSON UTF-8 with sorted keys
and compact separators (comma and colon), then signs using a separate Ed25519
private key. signature_ed25519 contains the base64 signature. The verifier
reads ONLY the independent pinned public key from private environment variable
VAULT_OWNER_AUDIT_PUBKEY_BASE64 (base64 of 32 raw Ed25519 public-key bytes).
The signed attestation is passed with --owner-attestation to the AT07 case.
Do not place private keys or real data in GitHub or evidence. A signature proves
the reviewer's claim was signed, not that the human review was correct.
Reviewer separately retains supporting data-inspection workpapers.
Missing/stale signature and unreviewed data mean NOT ACCEPTED.

## Restore and final authorization

AT05 must cold-stop, capture, restore into an isolated target and perform
independent Native graph, original bytes/SHA, owner and text-only patch
readback, all on the exact tested source SHA and tree. AT12 now compares
deterministic initial version IDs and canonical rights/retention hashes
BEFORE and AFTER restore. AT14 uses cookie-free Service JWT clients.
AT06 retains fresh racing claims and real TCP lost-ACK requirements.
AT13 requires all other 14 cases to pass; subsets do not satisfy Stage 1.

An executable test path is not a test result. Until Codex presents real evidence
and Integration Reviewer signs off, all new code remains IMPLEMENTED_UNTESTED;
S1-AT01–15 remain NOT_RUN and R01 remains NOT_APPROVED.
