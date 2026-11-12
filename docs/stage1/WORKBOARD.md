# Sunrise Stage 1 [A] — WORKBOARD (authoritative engineering progress index)

**Repository:** `Enochan222/sunrise-school-ai-platform`  
**Prepared against main:** `744fbbd0ac3b479c80782d6a990c7bfed093f4dd` (verify latest `main` before acting).  
**Source of requirements:** [Stage 1 official card](../stages/STAGE_01.md), [S0 decisions](../decisions/STAGE0_APPROVAL_DECISIONS.md), [candidate API inventory](../architecture/API_INVENTORY.json); [Implementation Plan v1.1](IMPLEMENTATION_PLAN.md) defines implementation sequence, not a replacement for formal requirements.  
**Evidence policy:** [Evidence README](evidence/README.md). **Collaboration / QA:** [Docs PR Handoff](DOCS_PR_HANDOFF.md).

## 1. Gate states (initial, not implementation evidence)

| Gate | Recorded status | Meaning / change authority |
|---|---|---|
| Stage 1 planning | **COMPLETE** | v1.1 planning gate only; not runtime acceptance |
| GitHub documentation handoff | **PENDING DOCS PR (draft-time only)** | Do not treat this row as evidence that its own PR has merged. After publication, check live GitHub PR/main records for actual handoff status; reviewer updates via a later authorized serial PR if needed |
| Stage 1 implementation | **NOT_STARTED** | No A runtime WP is claimed complete |
| S1-AT01–S1-AT15 runtime acceptance | **NOT_RUN** (15/15) | Every AT still needs actual tests and independently checkable evidence |
| R01 release | **NOT_APPROVED** | Separate runtime, security, privacy, hosting, budget and Owner gates |
| Local synthetic development | **NOT AUTHORIZED BY THIS FILE** | Local code work requires a separate explicit task-specific Owner instruction |
| GitHub feature branch / PR / merge / hosted deployment | **NOT AUTHORIZED BY THIS FILE** | Each level requires separate explicit authority; an assigned WP is not write approval |

**WP status vocabulary:** `NOT_STARTED / IN_PROGRESS / BLOCKED / PENDING_REVIEW / DONE`. Only an Integration Reviewer may propose a change to the merged WORKBOARD via the normal authorized docs PR process. `DONE` means implementation **merged** and pertinent tests/evidence verified; passing a self-described local test or opening a PR is not enough.

## 2. WP00–WP09 (all unassigned; no PRs or commits are presumed)

| WP | Deliverable | Depends on | Builder / Integration Reviewer | Status | Branch / PR | Verified implementation commit | Evidence | Blocker | Next executable task after authorization |
|---|---|---|---|---|---|---|---|---|---|
| **WP00** | Pin upstream/source/digest; scope, fixture and threat inventory; three spikes designed | S0 approved | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | None for planning; local/GitHub permissions pending | Read latest `main`, compare v1.1, verify pinned ON v1.15.1, propose ownership and first reproducible tests |
| **WP01** | Private ON API, storage, worker, DB and ingress isolation | WP00 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP00 | Demonstrate prohibited raw API/UI/DB routes cannot be reached outside private A boundary |
| **WP02** | Single Admin login, safe session, fail-start secrets, minimum Service JWT verifier | WP01 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP01 | Test missing secrets, cross-school session, token scope/issuer/audience/revocation limits |
| **WP03** | A Shell ↔ unique ON Notebook and durable ACK-loss idempotency | WP02 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP02 | Reproduce create-after-commit ACK loss and parallel retry; prove one Notebook |
| **WP04** | Source ownership, original version/hash, rights, native graph consistency | WP03 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP03 | Define minimal owner record and reject foreign/missing/multi-notebook edges |
| **WP05** | Native PDF upload/extraction/worker and Embedding-OFF recovery | WP04 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP04 | Process synthetic born-digital PDF; reproduce native retry `embed=True` and apply minimum safe fix if needed |
| **WP06** | Eight candidate A API operations; scoped list/search/original download; deny native streaming routes | WP04, WP05 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP04–05 | Test text-only search fallback, two-school IDOR, first-byte download denial, mixed results |
| **WP07** | Minimal A-only Admin page for the complete user journey | WP03, WP05, WP06 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP03/05/06 | Demonstrate Login→Shell→PDF→Search→Download→Archive with only A APIs |
| **WP08** | A-only consistent backup + independent isolated restore | WP00 design; WP03–06 runtime | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP03–06 | Freeze synthetic recovery point; restore DB, originals, encryption keys and indexes; compare hashes |
| **WP09** | Full S1-AT01–15 security, persistence, regression, UAT, R01 decision record | WP00–WP08 | **Unassigned / IR unassigned** | NOT_STARTED | — / — | — | — | WP00–08 | Collect fifteen actual results; independent recheck and Owner UAT; never call R01 approved prematurely |

`—` means **no verified branch, PR, SHA or evidence link**. No completed feature is implied. Before changing this table the reviewer must inspect live GitHub PRs and exact merged commits; `main` index reflects the **last independently verified merge**, while the open PR list is the live view of unmerged work.

## 3. Claim and coordination ledger (reviewer-controlled; empty at initialization)

| WP | Approved claimant | Scope / exact expected files | Depends-on merged SHAs | Approved permissions | Active feature branch / PR | Claim status / last checked |
|---|---|---|---|---|---|---|
| — | No active WP claim | — | — | — | — | Not claimed |

**Claim protocol:** Builder first reads `main` + open Stage1 PRs, asks the **designated Integration Reviewer** to reserve a WP and concrete file boundary, and provides the proposed branch name, changed-file list and dependencies. Reviewer checks the table and live GitHub PRs, confirms one owner per overlapping file, and records the claim through the next **authorized, single-writer WORKBOARD documentation PR**. Until that PR has been merged, the reviewer’s explicit written assignment/PR discussion is **provisional**, not an independently enforced lock. Do not start overlapping implementation while a competing claim is unresolved. Without a designated reviewer, no concurrent builders may begin conflicting work.

**Allowed parallelism:** isolated tests/docs/spikes can be reviewed in parallel after WP00; WP03 must not race a second Builder changing the same notebook schema; WP04/05/06 share source/route files and must be serial or have nonoverlapping named ownership. Never have two Builder PRs change this WORKBOARD; reviewer alone owns its updates.

## 4. Progress, PR and `DONE` semantics

1. `NOT_STARTED`: no authorized work. `IN_PROGRESS`: explicitly assigned Builder has authorized active branch or local tests, evidence `NOT_RUN` as applicable. `BLOCKED`: reproduce and link blocker. `PENDING_REVIEW`: PR opened but **not merged**, exact ref recorded. `DONE`: reviewer confirms merged commit is on `main`, requirements/negative/regression tests verified, evidence linked, and no gate regression.
2. While a PR is open, query **GitHub PR description/comments, changed files and exact head SHA** for freshest status; WORKBOARD on main may lag. Reviewer reconciles to main by a *separate authorized serial workboard PR* when needed. Never claim a draft PR as merged.
3. Before each PR review, fresh-read `main`, new merged PRs, upstream image/contract dependencies, and overlapping files. Compare the Evidence **Tested Revision** (commit SHA or reproducible local snapshot hash) to the **Final PR Head** read live from GitHub. Do not embed current PR Head SHA in that PR's Evidence file. Rerun tests if tested code/config/contracts/fixtures changed; a change only to the Evidence document requires reviewer provenance and impact verification, not a new SHA loop. Rerun affected regressions if intervening main changes are material.
4. Every Implementation PR links **one file** `docs/stage1/evidence/<WPxx>-pr-<actual-number>.md` (create/update after PR number exists), with actual Tested Revision (commit SHA or local snapshot hash) and test results; reviewer reads live PR Head SHA separately. If a branch has no PR number yet, keep draft logs outside committed evidence or use a temporary local file; do not fabricate `pr-XX` evidence.
5. If Builder Chat is interrupted: new Builder re-read latest main, WORKBOARD, actual merged evidence and all active PRs; ask reviewer to transfer the claim, identify the original head SHA and blocker, run independent verification, then require explicit permissions again. Prior Chat statements alone are not proof of state or authority.
6. `DONE` is not the same as `S1-AT PASS` nor `R01 APPROVED`: all fifteen AT and the stage release have distinct gates. Any FAIL/NOT_RUN means R01 remains blocked.

## 5. Short Builder bootstrap (read-only until fresh authorization)

> You are a Sunrise Stage 1 [A] Builder. **Read-only first:** verify latest `Enochan222/sunrise-school-ai-platform` `main`, `AGENTS.md`, `INSTRUCTIONS.md`, `docs/stages/STAGE_01.md`, `docs/stage1/IMPLEMENTATION_PLAN.md`, `docs/stage1/WORKBOARD.md`, merged evidence and open PRs. Identify the next dependency-ready unclaimed WP, check file conflicts, and report your exact scope, expected files, tests and required permissions to the Integration Reviewer and Owner. **Stop before code edits or any GitHub writes.** Local synthetic development, branch/PR writes, main merge and hosted deployment/R01 each need **separate explicit authorization**. No Actions/Copilot, paid APIs, real materials or B/I/U runtime changes.

## 6. Release restraint

A complete WORKBOARD, a merged Docs-only PR, or several WP marked `DONE` **never** authorizes deployment. S1-AT01–15 remain `NOT_RUN` until real proof. R01 approval additionally requires an authorized protected Runtime, independent A-only Restore, Owner UAT, privacy/content/hosting/region/budget/secrets signoff and no unresolved Critical/High security issue. See [plan](IMPLEMENTATION_PLAN.md), [official AT](../stages/STAGE_01.md), and [evidence rules](evidence/README.md).

## 7. Evidence identities and reviewer-only merge verification

Implementation Evidence contains **Tested Revision** (commit SHA or complete snapshot SHA256). It must **not** contain a claim that its own current/final PR Head SHA is authoritative. Reviewer separately reads the **Final PR Head** from GitHub, checks the material diff since Tested Revision, and stores that verification in the PR review record. After squash, Reviewer reads `main` **Merge Commit + Git Tree + relevant actual file contents/hash**. Only then may a separate authorized, serial WORKBOARD update mark `DONE`. No generated/document-only self-reference is evidence of merge.
