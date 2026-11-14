# Stage 1 [A] — independent Implementation PR evidence

**Purpose:** one verifiable, redacted evidence record per actual Implementation PR. This README is a **template specification only**; it is **not** proof that any Stage 1 Runtime test has run. Formal tests: [S1 card](../../stages/STAGE_01.md); coordination: [WORKBOARD](../WORKBOARD.md); plan: [v1.1](../IMPLEMENTATION_PLAN.md).

## When and how to create evidence

- Before a PR exists, keep local redacted test logs attached to the proposed change; **do not invent PR numbers** or committed `PASS` assertions. When the PR exists, create `docs/stage1/evidence/WP03-pr-<actual-pr-number>.md` using that PR’s verified number. Other WPs follow the same pattern. Multiple WPs in a single PR require explicit cross-reference; avoid confusing evidence ownership.
- Record **Tested Revision** as the exact implementation/content commit SHA or an independently reproducible local snapshot SHA-256 (include the hashed file list), target base SHA, source digest, pinned ON version, environment, UTC, commands, exit codes and redacted logs. **Do not write the final PR Head SHA in this same PR Evidence file:** it changes when Evidence changes. Before merge, the Integration Reviewer independently fetches current PR Head SHA from GitHub, compares all changes since the Tested Revision, and verifies that the tested implementation/content is unchanged. Re-run affected tests if material tested code/config/contracts/fixtures have changed; Evidence-only or non-material editorial updates require documented impact verification, not an infinite SHA update loop.
- Every relevant case is `PASS`, `FAIL`, or `NOT_RUN`. Include positive and negative HTTP probes with asserted response and **zero foreign bytes**, unit/integration/worker/restore/regression as applicable. `NOT_RUN` is never treated as PASS. A test script result is not equal to independent review; record reviewer re-execution or verification separately.
- Include Stage 1 Acceptance IDs and whether each is *partial coverage* or *full tested coverage*. Only the WP09 stage-level matrix may claim all 15 have been executed. `DONE` requires merged code, verified evidence and coordinated WORKBOARD update; a PR that is merely open is `PENDING_REVIEW`.
- **Never commit** private keys, session tokens, passwords, sensitive IPs, personal information, real textbook pages, student records, raw DB/file backups, complete response bodies containing confidential text, or unsanitized logs. Use synthetic fixtures, hashes and redactions. When raw artifacts are needed for verification, retain them in an approved private location outside the repo; provide a reference without secrets.

## Copyable per-PR evidence template (create only after obtaining the real PR number)

```markdown
# Stage 1 Evidence — WP<actual-id> / PR #<actual-number>

**Evidence status:** NOT_RUN / IN_PROGRESS / VERIFIED (choose accurately)
**Stage / owner:** S1 [A]
**Builder:** <actual actor>  **Independent reviewer:** <actual actor or PENDING>
**Feature PR URL:** <actual URL>  **Branch:** <actual branch>
**Tested Revision:** <code/content commit SHA OR local snapshot SHA256 + full file manifest>  **Target main/base SHA at test:** <full SHA>
**Pinned ON source commit/tree:** <SHA/SHA>  **Runtime image digest:** <digest or NOT_RUN>
**Test environment:** <OS, Docker/Python versions, dependency pins, network mode>
**UTC test timestamp:** <ISO 8601>

## Exact changes and owner boundary
- Changed files / APIs / migrations: <real paths>
- One-owner diff: A only / EXCEPTION BLOCKED
- Reused ON components: <real versions>
- S1 Acceptance IDs affected: <S1-ATxx ...>
- Downstream compatibility: <S2/S4/S5/S22/S23/S26 impact or none>

## Actual commands and outcomes
| Case ID / type | Exact reproducible command or test | Expected | Observed | Exit code | PASS / FAIL / NOT_RUN | Redacted log ref |
|---|---|---|---|---|---|---|
| <case> | <command> | <assertion> | <observed output> | <code> | NOT_RUN | <relative safe log link or NO LOG> |

## Security / fault negative cases
- Authn/Authz, School/Shell/Source IDOR and empty search scope: <actual tests/status>
- Raw ON route/API/DB/private UI network probe: <actual tests/status>
- Preview/SSE/download first-byte: <actual tests/status>
- Notebook ACK-loss/duplicate retry, worker/embedding-off/search fallback: <as applicable>

## Persistence, backup/restore and regression
- DB/worker restart and Source/Notebook/Hash checks: <actual results or NOT_RUN>
- Isolated DB + original files + keys/index Restore: <actual results or NOT_RUN / not relevant to this PR>
- Tests for preceding merged WPs and affected consumers: <actual results>
- New/remaining failures and known limitations: <explicit list>

## Independent reviewer checks
- Tested Revision/hash and tested-file identity independently verified: PASS / FAIL / NOT_RUN
- Evidence re-executed / log provenance verified: PASS / FAIL / NOT_RUN
- Current main/PR conflict check and live final PR Head SHA fetched directly from GitHub (not written into this Evidence file): PASS / FAIL / NOT_RUN
- Acceptance coverage and security gate: PASS / FAIL / NOT_RUN
- Reviewer name, UTC date and exact verification method: <real facts>

## Decision / release impact
**PR merge recommendation:** PENDING / APPROVE / BLOCK
**WORKBOARD WP status:** PENDING_REVIEW until merged and verified
**R01:** NOT_APPROVED unless separate authorized release process completes
```

## Required review of evidence before merge

The Integration Reviewer checks: matching PR/branch/Tested Revision and file list; final PR Head SHA fetched live and changes since Tested Revision independently checked; exact executable commands with reproducible outputs and exit codes; positive and security-negative tests; no leaked secrets/real files; tests valid for the final material implementation/content revision; downstream regressions; affected AT evidence (not just count); restore evidence where pertinent; independent reviewer finding; no cross-owner runtime change. The owner does **not** need to approve code semantics personally, but must explicitly authorize irreversible operations, paid/data use and release gates.

The repository does not use GitHub Copilot. Only the two workflows authorized by [the Stage 1 Limited CI Addendum](../../decisions/STAGE1_LIMITED_CI_ADDENDUM.md) may run. Light CI is same-repository, code-path-filtered and targets PRs to `main`; it runs `tests/stage1` (non-native), not full `pytest tests`. A PR targeting PR #14's implementation branch is outside that Light trigger. Manual test evidence is **not** an automatically enforced required branch-protection check. A CI PASS is not Native, full regression, formal acceptance, independent review, Owner UAT or R01.

**Separate evidence levels:** `CI_PASS`, `NON_NATIVE_REGRESSION_PASS`, `NATIVE_RUNTIME_PASS`, `FORMAL_AT_PASS`, `INDEPENDENT_REVIEW_PASS`, `OWNER_UAT_APPROVED`, `R01_APPROVED`. Each needs its own tested source revision, command/run, actual outcome and reviewer/Owner provenance. Record workflow name, run/job URL, event, PR Head SHA and distinct Actions synthetic merge-result SHA; do not substitute the latter for the former. Record unexecuted tests as `NOT_RUN`. Never infer one status from another.

## Final Head and Squash Merge without a SHA loop

**Three distinct identities:** (A) `Tested Revision` belongs in the committed Evidence file; (B) `Final PR Head` is verified by the reviewer using live GitHub PR metadata immediately before merge, **outside** this self-changing Evidence file; (C) `Merge Verification` is performed *after* squash, by independently reading `main` merge commit, final Git tree and relevant file bytes/hash. Record (B)/(C) in the PR review/merge report or a later separately authorized WORKBOARD update, never by changing this same PR solely to refresh its SHA. Test validity depends on the tested content, not on equality between the Evidence-file commit SHA and PR head.
