# PUBLIC_REPO_INSTRUCTION_GAP_MATRIX — 2026-11-14

**Verified live main baseline:** `b8c3d984b31ed7ef073ceecfe398f1002d962d01`, tree `b27c3896433966c92c263ab4a7b373183a5aba27`. Repository PUBLIC; Protect main active Ruleset `26914637`. PR14 Draft HEAD `83474cf42ba899d5d0427b3b22ee16d6b74592eb`, PR24 Draft HEAD `3c709f635c3d4536cdea993824fc0089bdd6404f`, with PR24 base PR14 implementation branch. Recheck live values before further changes.

| Priority | Target files | Verified outdated assumption | Remediation |
|---|---|---|---|
| P0 | `AGENTS.md`, `INSTRUCTIONS.md` | Stale PR14/24 copies and historical D08 no-Actions risk inconsistent operational policy | Scope-aware approved Owner amendment → merged main governance → actual Stage Registry/AT/API → executed evidence → PR writer lease → historical prompts |
| P0 | `.github/PULL_REQUEST_TEMPLATE.md` | States no GitHub Actions | Capture Head/Tree/Tested/merge-result/post-squash SHA separately, CI Run/Job and native/restore/AT statuses |
| P0 | `SECURITY.md` | No public repository incident and responsible disclosure procedure | Private-report-if-enabled, fork/PR/log/artifact risk and credential rotation |
| P1 | `CONTRIBUTING.md`, `docs/delivery/GITHUB_CONNECTION_RUNBOOK.md` | Private repo, obsolete validate-docs, old one-container DNS restriction | Correct public read vs authorized API/git write, runtime-specific network and CI controls |
| P1 | `docs/delivery/RELEASE_POLICY.md`, `docs/stage1/evidence/README.md` | Private/no Actions, non-native vs formal evidence ambiguity | Preserve R01/UAT/AT, evidence tier separation |
| P2 | `docs/delivery/{NEW_REPO_STAGE0,REPO_SETUP,PROJECT_STATUS,HANDOVER}.md` | Historical correct at issuance; misleading as current instructions | Add superseded notices only, do not rewrite historical decisions |
| P2 | `README.md` | Stage1 historical planned status looks current | Add public/branch/runtime status warning |
| P0 QA discovery | `scripts/verify_kit.py` | Historical Draft-skip assertion conflicted with Owner 2026-11-14 Draft-inclusive CI amendment | Owner-authorized minimal static QA code repaired in PR26; 18 targeted tests PASS, full Repository QA still NOT_RUN |
| P0 CI discovery | Both approved Stage1 workflows | Light only `main` target; Native manual uses stale single DB fixed ports | `CI_WORKFLOW_REPAIR_REQUIRED`, no workflow code changes in this PR |

**Formal unchanged requirements:** D01–D08 original Stage0 decision; S0–S28 Registry and A/B/I/U tracks; A-only dual physical SurrealDB, secure Gateway/strict TLS, JWT/CSRF/school/source IDOR, S1-AT01–15, independent restore, Owner UAT and distinct R01. Public source is not publicly deployed runtime.
