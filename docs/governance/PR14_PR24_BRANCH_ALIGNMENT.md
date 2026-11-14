# PR14_PR24_BRANCH_ALIGNMENT — Public Governance after an authorised merge

**Read-only snapshot:** `main=b8c3d984b31ed7ef073ceecfe398f1002d962d01`; PR14 Draft HEAD `83474cf42ba899d5d0427b3b22ee16d6b74592eb` (tree `3fdbdbcdd7cb466829d5c189c12beb46794af934`); PR24 Draft HEAD `3c709f635c3d4536cdea993824fc0089bdd6404f` (tree `75a40bc9244f823098a993c463b751e448de4f4c`). PR24 base is the PR14 Stage1 implementation branch. Re-read live GitHub immediately before any action.

1. Independently finish this docs-only governance PR against live `main`. Manual squash-only merge only with actual full QA/review and Owner permissions; otherwise remain Draft.
2. After authorized merge, re-read the new `main` SHA/tree and canonical instruction Git Blobs, and verify original Stage0 D01–D08 source is unchanged.
3. Compare `main` vs PR14 and PR24 Blob SHAs and diffs for `AGENTS.md`, `INSTRUCTIONS.md`, `SECURITY.md`, PR Template and other relevant governance docs. Produce a path-level Alignment Matrix; a stale branch copy is not itself the governing instruction, but a new document cannot silently override Stage AT/API security contracts.
4. Through the **current explicitly authorised PR14 engineering writer** only, schedule selective documentation-only alignment or a carefully checked normal merge/rebase if safe. Do NOT push to PR14/PR24 from this docs PR; do not blanket overwrite active code, scripts, tests, API schema or runtime identity, and never force push. Review PR24's stacked base and update order after PR14's state is fixed.
5. Re-run affected instruction/CI path consistency, non-native and any material source/runtime regressions at exact new Head/Tree. For PR24, `stage1-light.yml` only targets `main`; a standalone run on stacked PR24 cannot be assumed. Report a separately authorised CI repair if coverage is required.
6. Retain true native/browser/restore/AT, Owner UAT and R01 gates. If source heads move or conflict, stop and redo exact-head compare.

**Explicitly deferred:** changing PR14/PR24 branches, altering Workflow triggers, automatic merge, paid CI, product architecture, formal acceptance or release signatures.
