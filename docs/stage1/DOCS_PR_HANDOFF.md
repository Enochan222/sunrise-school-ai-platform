# Stage 1 [A] — Docs-only PR, multi-Builder coordination and QA handoff

**State of this document:** Procedure/handoff reference, not a self-certified PR or merge record. Its historical drafting-time baseline is below; always use live GitHub for current PR/main status.  
**GitHub baseline checked read-only:** `Enochan222/sunrise-school-ai-platform` `main` at `744fbbd0ac3b479c80782d6a990c7bfed093f4dd`. **Recheck before applying**; historical SHA is not a permanent moving-main pointer.  
**Formal precedence:** Stage 0 [D01–D08](../decisions/STAGE0_APPROVAL_DECISIONS.md), [S1 Stage Card](../stages/STAGE_01.md), [Registry](../quality/STAGE_REGISTRY.json) and [API Inventory](../architecture/API_INVENTORY.json) outrank [v1.1](IMPLEMENTATION_PLAN.md). This document changes no Stage, Acceptance or API contract.

## 1. Authorized documentation-only PR: proposed file list

| Repo path | Change | Why |
|---|---|---|
| `docs/stage1/IMPLEMENTATION_PLAN.md` | **NEW; exact byte-for-byte copy of approved v1.1** | Single Builder handoff, no substantive plan amendments |
| `docs/stage1/WORKBOARD.md` | NEW | Canonical Stage1 WP00–09 index and gate states |
| `docs/stage1/evidence/README.md` | NEW | One independent evidence file per **actual** implementation PR |
| `docs/stage1/DOCS_PR_HANDOFF.md` | NEW | Multi-Builder/PR rules, SHA refresh, QA and Owner handoff |
| `AGENTS.md` | Small addition | Stage1 entry, read sequence, exclusive WORKBOARD editor, express permissions |
| `INSTRUCTIONS.md` | Small replacement | Remove misleading live v0.5/current Stage0 migration instructions |
| `docs/architecture/BOUNDARY_RULES.md` | One obsolete status sentence replacement | `main` is not v0.5; preserve Owner boundaries |
| `docs/delivery/STAGE_01_EXECUTION.md` | Two small corrections | Pinned upstream reference and `curriculum_stream` in Shell grain |
| `docs/delivery/PROJECT_STATUS.md` | Dated addendum only | Record S0 PR #11 and S1 planning docs handoff, preserve historical evidence |
| `FILE_MANIFEST.sha256` | Regenerate entries for all changed/new files | Enforce actual byte hashes under existing verifier |

**Not in docs-only PR:** `.github/workflows`, Runtime code, `docs/stages/STAGE_01.md`, Stage Registry, API Inventory, Stage 0 baseline/signoff, historical manifests, any prior AT results or QA logs claimed as already completed. Existing `.github/PULL_REQUEST_TEMPLATE.md` is sufficient; complete it when a real PR is authorized.

The v1.1 copy has no intentional content change; if an editor changes even whitespace, make a separate exact diff/reason and re-run checks. A companion `review_only/proposed-doc-edits.patch` is for future application, **not** an instruction to modify GitHub now.

## 2. Multi-Builder operating procedure (no bots or Actions)

**Before any claim:** (a) Builder read latest main SHA, `AGENTS.md`, `INSTRUCTIONS.md`, [plan](IMPLEMENTATION_PLAN.md), [WORKBOARD](WORKBOARD.md), [evidence spec](evidence/README.md), official S1 card and relevant merged evidence; (b) inspect all open S1 pull requests and changed-file lists; (c) present WP ID, exact likely files, dependency merged SHAs, tests and intended deliverable; (d) ask the **one Integration Reviewer** to assign/reassign responsibility and resolve conflicts; (e) obtain **separate** explicit local-dev and GitHub-write permissions before doing those actions.

**Claim ownership:** Workboard is the durable index; reviewer is sole editor and serially merges any proposed WORKBOARD change. Open PR description/reviewer messages are provisional live coordination until the next approved index update is merged. An unmerged PR is **PENDING_REVIEW**, not DONE. Two builders may work at once only if the Integration Reviewer has confirmed their file sets/data model migrations do not overlap and both dependencies are satisfied. If the reviewer is not appointed or file scope overlaps, STOP the conflicting work rather than duplicate it.

**Branch naming suggestions (not evidence of creation):** `stage1/a-wp00-source-pin`, `stage1/a-wp01-private-network`, etc. Actual names must avoid existing branches and be assigned. Branch off fresh main or explicitly declared dependency PR head; merge stacked PRs in dependency order. Builders never push directly to main and never edit `WORKBOARD.md` in their implementation PRs. A change to the same source, schema, generated OpenAPI, or migration file requires serial work or a documented owner handoff, not competing edits.

**Practical integration order:** docs-only handoff PR first, then WP00 → WP01 → WP02 → WP03 → WP04 → WP05 → WP06 → WP07/08 (where independently ready) → WP09. Multiple WPs may be combined into a well-reviewed PR; one WP may require multiple PRs. No fixed PR count. Merged implementation dependencies are tracked by real full commit SHAs, not by PR titles or Builder claims. S1 only ever changes A Runtime; I/B/U runtime remain unchanged.

**PR opened, not yet merged:** the live PR is a progress signal, not a completed result. Reviewer consults head commit, merge base, open-review status, matching test evidence and blockers; records `PENDING_REVIEW` in the next approved Workboard PR. If a new PR opens or main changes, re-read the **latest** main and any intervening merged PR before approval. Rebase/update feature branch only by an explicitly authorized maintainer without force-push or bypass; compare and resolve conflicts, then compare the Tested Revision against the reviewer-verified live PR Head and rerun tests only where material tested content or dependencies changed.

**Before each merge:** reviewer checks fresh main, actual changed files, single-A-owner boundary, previous merged evidence, dependency ordering, no duplicate shell/Source model/schema edits, security/negative/restart regressions, **Evidence Tested Revision**, current **Final PR Head SHA fetched live from GitHub**, material diff between them and independent evidence. Do not update Evidence solely to embed the current PR Head SHA (it would change again). Each merge needs explicit Owner authorization; the specific Stage1 Docs-only integration may use its separate, scope-limited Owner authorization, while all later Builder Runtime PR merges need their own approval. No unattended auto-merge, Force Push, bypass or Actions. If `main` differs from the baseline used by the PR, recompute impact and rerun affected checks. After squash, independently fetch and verify main Merge Commit SHA, Git Tree and changed file contents/hashes, then reviewer updates WORKBOARD through a serial docs-only change. Until that is merged, query open/merged PR metadata for freshest facts and treat the old WORKBOARD record as last confirmed snapshot.

**Interrupted Builder:** successor reads current main, WORKBOARD, exact PR head and merged evidence (not merely previous Chat), asks reviewer to formally transfer/reclaim WP, checks the file conflict and its own separate permissions, reproduces pending tests and reports new SHA/result. Never inherit an assumed approval to write, merge or deploy.

## 3. Authorization levels (non-interchangeable)

| Action | Required written authorization | Not implied by |
|---|---|---|
| Local synthetic A development/test | Per-Builder local scope approval; isolated/no paid/no real data | Planning COMPLETE or this docs package |
| GitHub feature branch, commit, push or PR | **Separate explicit GitHub write permission**, exact repository and scope | Local development approval or WP claim |
| Merge to main | **Separate explicit merge approval** with evidence gate | PR existence, green local output, or Docs-only strategy approval |
| Hosted staging, paid provider, school materials, R01 release | Specific Owner approval for each relevant network/privacy/region/budget/secrets/data/release gate | Any earlier approvals, including Stage0 D01–D08 |

All `S1-AT01–15` are **NOT_RUN** until tested in real relevant environments. Planning COMPLETE and docs-only merge do not advance Stage1 Runtime or R01.

## 4. Manifest update (execute **only** in a future authorized working tree)

Existing `scripts/verify_kit.py` checks `FILE_MANIFEST.sha256` lines (`<sha256><two spaces><path>`) against tracked entries; the manifest excludes itself. It permits additional unlisted files, so **explicitly add the four new Stage1 docs** instead of relying on the verifier to discover omission. Do **not** regenerate by blindly hashing `.git`, `.env`, backup folders or QA logs. Update the ten named paths in §1, excluding `FILE_MANIFEST.sha256` itself:

```sh
# From an authorized clean checkout at the latest reviewed main, after applying the approved docs patch.
python3 - <<'PY'
from pathlib import Path
import hashlib
manifest = Path('FILE_MANIFEST.sha256')
changes = [
    'AGENTS.md', 'INSTRUCTIONS.md', 'docs/architecture/BOUNDARY_RULES.md',
    'docs/delivery/STAGE_01_EXECUTION.md', 'docs/delivery/PROJECT_STATUS.md',
    'docs/stage1/IMPLEMENTATION_PLAN.md', 'docs/stage1/WORKBOARD.md',
    'docs/stage1/evidence/README.md', 'docs/stage1/DOCS_PR_HANDOFF.md',
]
entries = {}
for raw in manifest.read_text(encoding='utf-8').splitlines():
    digest, path = raw.split('  ', 1)
    assert len(digest) == 64 and path not in entries, f'Bad manifest line: {raw}'
    entries[path] = digest
for rel in changes:
    file = Path(rel)
    assert file.is_file(), f'Missing changed/new file: {rel}'
    entries[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
manifest.write_text(''.join(f'{entries[p]}  {p}\n' for p in sorted(entries)), encoding='utf-8')
print(f'Manifest entries: {len(entries)}; refreshed: {len(changes)}')
PY
```

**Independent verification** (different hashing path and existing repo verifier; keep exact logs):

```sh
sha256sum --check FILE_MANIFEST.sha256
python3 scripts/verify_kit.py
python3 scripts/run_qa_no_actions.py
```

On systems without GNU `sha256sum`, independently rehash each listed file using `hashlib.file_digest(...,'sha256')` in a **separately implemented** verification pass. Check that the manifest includes all new Stage1 documents, contains no duplicate paths or missing file, and does **not** list itself. `scripts/verify_kit.py` does **not** fail for newly added but unlisted files, so inspect coverage explicitly.

**Do not edit** `stage0/STAGE0_BASELINE.json`, Stage0 signoff Issue/PR, `docs/decisions/STAGE0_APPROVAL_DECISIONS.md`, or historical source kit hashes to disguise the addition of new docs. Previous manifest entries must remain identical except those for **actually modified existing files**.

## 5. Docs-only QA checklist and evidence gate

Before PR submission: make sure the checkout uses the recorded head; apply only §1 files; run local checks and record exit code/stdout/stderr/UTC. This document does not assert that commands have been run on a complete checkout; require actual dated logs and exit codes for the submitted PR. Suggested reproducible log capture outside the repo:

```sh
# In an authorized checkout, with dependencies already installed.
mkdir -p /tmp/sunrise-stage1-docs-qa
python3 scripts/run_qa_no_actions.py > /tmp/sunrise-stage1-docs-qa/manual-qa.log 2>&1
qa_rc=$?
printf 'Manual QA exit code: %s\n' "$qa_rc"
python3 scripts/verify_kit.py > /tmp/sunrise-stage1-docs-qa/verify-kit.log 2>&1
manifest_rc=$?
printf 'Kit verifier exit code: %s\n' "$manifest_rc"
git diff --check
# Run sha256sum --check as in §4; inspect and sanitize logs before sharing.
```

**PR reviewer must check all of the following** (record `PASS / FAIL / NOT_RUN`):

- [ ] Exact v1.1 byte copy or documented and approved content diff; active official source precedence unchanged.
- [ ] `WP00`–`WP09` exactly ten records, all initially NOT_STARTED and no invented branch/PR/SHA/evidence.
- [ ] `S1-AT01`–`S1-AT15` all present and unchanged in Stage Card / plan mapping; all Runtime statuses NOT_RUN.
- [ ] Eight S1 candidate API `method+path+operation_id` retained; five S2 APIs not pulled into S1.
- [ ] D01–D08, S0–S28 Registry and A/B/I/U runtime owner boundaries unchanged; no new deployment or real data approval implied.
- [ ] Original Stage0 source/signoff/provenance documents untouched.
- [ ] AGENTS and INSTRUCTIONS reading order/permissions do not conflict or create a circular 'current version' claim.
- [ ] External and local Markdown relative links, Git diff paths and `.github/PULL_REQUEST_TEMPLATE.md` reviewed.
- [ ] Workboard initial status, reviewer-only updates, branch/PR and DONE rules are coherent with actual GitHub state.
- [ ] `FILE_MANIFEST.sha256` refreshed by actual bytes, four new docs included, independent rehash and `scripts/verify_kit.py` PASS.
- [ ] `python scripts/run_qa_no_actions.py` actually executed with exit 0 and redacted exact log; otherwise label NOT_RUN/FAIL and **do not merge**.
- [ ] No `.github/workflows`, generated code, runtime A/B/I/U, infrastructure, deployment or secrets in `git diff`; reviewer inspects full diff against latest main.
- [ ] Separate Owner docs-only PR approval obtained; no Builder branch/PR or main merge performed without another explicit authorization.

**High-value diff audit:** `git status --short`, `git diff --check`, `git diff --name-status <base>`, `git diff <base> -- AGENTS.md INSTRUCTIONS.md docs/architecture/BOUNDARY_RULES.md docs/delivery/STAGE_01_EXECUTION.md docs/delivery/PROJECT_STATUS.md`, plus list any staged/untracked files and real PR diff. Document test outputs and approvals in that future PR; the supplied patch is a recommendation only.

## 6. One-page non-technical Owner handoff

| Decision / status | Plain-language meaning | Action |
|---|---|---|
| **Planning: COMPLETE** | The minimum A-only implementation has already been scoped; 10 WPs, 8 candidate APIs, all 15 official acceptance items remain | No new planning cycle needed |
| **Docs-only PR: CHECK GITHUB** | This document does not certify its own merge; the current status must be read directly from GitHub | Follow the actual PR/main record; no self-referential merged claim |
| **Integration Reviewer: VERIFY ASSIGNMENT** | One coordinator assigns WPs, checks evidence and serially updates the workboard | Confirm a designated reviewer before overlapping Builders start |
| **Implementation: NOT_STARTED** | No implementation is verified or merged | Grant each Builder explicit local scope, and GitHub write scope separately if desired |
| **Runtime AT01–15: NOT_RUN** | Documents do not prove that upload, security and restore work | Review real evidence before considering any release |
| **R01: NOT_APPROVED** | No public deployment, real school materials, paid model or student data is authorized | Later sign hosting/region, privacy/content rights, budget, key/backup plan, Owner UAT and release separately |

**Recommended default:** authorize **only the specifically scoped docs-only PR** after verifying the approved 10-file scope, actual QA and Manifest; nominate a single Integration Reviewer; start WP00 local synthetic work only through a separate explicit Builder prompt. Keep Gemini/Cloud Embedding/AI Chat OFF, no Actions/Copilot, no automatic merge or production release.

### Owner signoff checklist (record each decision separately)

- [ ] **Document scope acknowledged:** exactly the four new docs, five small existing-doc patches and refreshed `FILE_MANIFEST.sha256`; official Stage0 decisions, Registry and ATs untouched.
- [ ] **Reviewer appointed:** name one Integration Reviewer responsible for WP claims, conflicts, evidence checks and serial WORKBOARD updates.
- [ ] **Docs-only branch/PR creation:** give separate express permission to a named agent **only after** reviewing live main and this proposed scope.
- [ ] **Docs-only merge:** use only the expressly approved Docs-only integration scope, after actual PR diff, real manifest verification, manual QA exit 0 and reviewer signoff; Squash only, never unattended auto-merge.
- [ ] **Builder local implementation:** a fresh, independent authorization specifying WP and synthetic-only limits, not inherited from Docs-only approval.
- [ ] **GitHub implementation writes:** authorize separately per Builder/branch/PR; no permission to merge by implication.
- [ ] **Hosted/R01:** remains **NOT APPROVED**; no paid model, real material/student data, public deployment or release without later independent approval.


## 7. Five-line read-only Builder bootstrap

> For Sunrise Stage1 [A], read latest GitHub `main`, `AGENTS.md`, `INSTRUCTIONS.md`, `docs/stages/STAGE_01.md`, `docs/stage1/IMPLEMENTATION_PLAN.md`, `WORKBOARD.md`, merged Evidence and open PRs. Find the next dependency-ready unclaimed WP and check file conflicts with the Integration Reviewer. Report intended files, tests and blocked dependencies **before changing anything**. **Wait for separate explicit authorizations** for local synthetic development, GitHub branch/PR writes, main merge and hosted deployment/R01. Never enable Actions/Copilot, paid AI, real material/student data or other Owner runtime.

**Authority reminder:** these instructions are not themselves GitHub write permission; verify each actual Owner authorization, PR state and applicable QA before acting.

## 8. Evidence SHA non-circularity — mandatory reviewer procedure

1. Builder records **Tested Revision** = exact implementation/content commit SHA or reproducible local snapshot hash, tested file list, command, environment, time, exit code and log in `evidence/WPxx-pr-<real number>.md`.
2. Reviewer queries GitHub for **Final PR Head SHA** immediately before merge, outside that PR Evidence document; compares the diff against Tested Revision. Material changes to tested code/config/contracts/fixtures require rerun of affected tests. Evidence-only changes require independent provenance/impact checks, not an automatic full retest solely because SHA changed.
3. After an authorized manual squash, reviewer independently queries the actual `main` merge commit, final Git tree and relevant file blobs/hash; records this in the PR review/merge report or a later serial WORKBOARD PR. Never pre-write this PR's own merged status or final SHA into itself.
