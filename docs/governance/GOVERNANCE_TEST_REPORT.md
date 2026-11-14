# GOVERNANCE_TEST_REPORT — Executed and not-executed gates

**Original main/test baseline:** `b8c3d984b31ed7ef073ceecfe398f1002d962d01`, Git Tree `b27c3896433966c92c263ab4a7b373183a5aba27`. Final PR Head and post-merge SHA must be read remotely, not self-recorded by a mutating commit.

| Gate | Exact command / verification | Result and limitation |
|---|---|---|
| Repository visibility / branch/ref/ruleset | GitHub Plugin get_repo, get_pr_info, Git Ref, Ruleset reads | PASS; public, Protect main active, PR14/24 Draft |
| Source workflows | GitHub Plugin fetch_file for both approved workflow YAML | PASS review only; CI incompatibilities separately documented |
| Public tracked filename scan | GitHub Git Trees for main, PR14, PR24 | PASS for common sensitive filenames/extensions in enumerated trees only |
| Public PR conversation metadata | GitHub Plugin PR14/PR24 issue comments, redacted pattern scan | 8 potential metadata flags among 62 PR14 comments; 0 PR24 comments; NOT evidence of credential leak |
| Selected high-risk source signature scan | GitHub Plugin fetch_file of six Stage1 paths at exact PR14 source | NO_FINDINGS_IN_CHECKED_SCOPE for the searched literal patterns only |
| Secret scanning alert status, history-wide scan, fork permissions/Billing | Private/admin endpoints not available in connector | NOT_VERIFIED |
| Local terminal connectivity | `git ls-remote https://github.com/Enochan222/sunrise-school-ai-platform.git refs/heads/main` | FAIL: `Could not resolve host: github.com` in this environment; not a GitHub outage |
| Full repository static/contract/mutation QA | `python scripts/run_qa_no_actions.py` | NOT_RUN: no complete clean repository checkout through terminal DNS |
| Existing `scripts/verify_kit.py` CI semantic assertion | Read source lines asserting `!github.event.pull_request.draft` | STALE ASSERTION / EXPECTED FAILURE against current approved Draft CI; code repair outside docs-only scope |
| Runtime, Dual-DB, Strict TLS, Browser, Restore, formal AT, Owner UAT/R01 | Real Mac/owner gated source and runtime | NOT_RUN; outside governance PR |

**Required before merge:** independently check exact changed paths, Markdown paths/fences, generated manifest hashes and links, no secret-like contents and no unwarranted changes to Stage0 decisions/Stage1 AT, then run full repo QA in an authorised clean environment or obtain an evidence-backed exception for only a documented obsolete assertion. A PR is not equal to passing QA. If QA or privacy/security blocker remains, keep PR DRAFT/UNMERGED.

**Additional independently verified settings limitation (2026-11-14):** Repository metadata `allow_auto_merge=true` although policy forbids auto-merge. This is a settings-level **GOVERNANCE_CONTROL_GAP**, not an action taken in this PR. Owner must disable or document compensating control; PR merge remains blocked. GitHub Actions repository `/actions/permissions` query is unsupported by this connector, so repository fork/workflow permission and budget settings stay `NOT_VERIFIED`.
