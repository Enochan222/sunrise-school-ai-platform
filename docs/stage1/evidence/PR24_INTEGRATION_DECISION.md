# PR24_INTEGRATION_DECISION

**DECISION: `BLOCKED_TEST_EXECUTION`**

**`INTEGRATION_REVIEW_READY=NO`**, `READY_FOR_CONTROLLED_INTEGRATION=NO`, both PR #24 and PR #14 must remain **DRAFT / OPEN / UNMERGED**. This is not a decision to discard the reviewed fixes. Integration is withheld because the user-mandated full-source command `python -m pytest -q tests` was **NOT_RUN** on a clean complete PR24 checkout, and no current PR24 head CI run exists.

## Verified conditions

- GitHub PR14 was open/Draft at exact HEAD `83474cf42ba899d5d0427b3b22ee16d6b74592eb`; PR24 base pointed to that exact SHA throughout repair. Compare showed ahead and behind=0, with no new conflicting PR14 commits.
- All original 14 changed files were independently reviewed. Five further engineering Source/Test files were changed by TDD corrections; the additional named reports are evidence-only under the existing allowed `docs/stage1/evidence/` prefix.
- `release_manifest.py` strict scope policy now allows exactly three named previously blocked handoff docs. Comparisons main→PR14 (99 paths) and PR14→engineering-candidate (19 paths) yielded no forbidden paths. Stage0/governance files and GitHub workflows remain blocked.
- Real isolated targeted checks passed as precisely recorded in `PR24_FULL_NON_NATIVE_TEST_REPORT.md`; UI stale-search false lock was reproduced against prior exact JS and cleared in revised exact JS.
- No committed private RSA PEM, token value, GitHub PAT or personal home path was found by explicit source-pattern scan of the 19 engineering files. This is not an exhaustive secrets scanner.

## Hard blockers

1. Complete, trustworthy **fixed-SHA private checkout** absent. Local `git ls-remote` failed DNS; connected GitHub Git Blob fetches do not provide a checkout with all `tests` and imports. No known full test count on current source, so FULL_NON_NATIVE_REGRESSION=NOT_RUN.
2. Local Python is 3.13.5 while project requirements document 3.11.11. Run full acceptance regression on a pinned supported Python 3.11.11 environment. Local Node availability alone is insufficient without full JS file checkout.
3. Actual Stage1 Mac Docker runtime identity, Native exactly-once journal/lost-ACK, Gateway strict HTTPS JWT, Firefox NSS, independent signed observer, non-destructive restart and cold restore NOT_RUN on PR24.
4. Formal S1-AT01–15, Owner UAT, R01 and reviewer approval remain NOT APPROVED. GitHub PR24 has not been merged.

**Not chosen:** `BLOCKED_SOURCE_DEFECT` (the identified source breakages were repaired in exact new blobs, but unseen defects may remain until full regression); `BLOCKED_INTEGRATION_CONFLICT` (no observed parent drift); `READY_FOR_CONTROLLED_INTEGRATION` (cannot pass Gate1 without complete tests).

## Mandatory next state transition

On an approved clean complete candidate checkout, run `git rev-parse HEAD`, `git rev-parse 'HEAD^{tree}'`, `git status --porcelain`, full `compileall`, `node --check`, and `python -m pytest -q tests`; require exit 0 and actual counts and a second clean-source check. Reconcile any new PR14 writer changes. Then a genuinely independent reviewer may reassess **controlled PR24→PR14 integration only**. Even an integrated PR14 must still pass 15 actual runtime cases, separate Owner UAT and R01; no automated merge or formal acceptance from this decision.
