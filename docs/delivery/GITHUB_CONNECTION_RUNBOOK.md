# GitHub connectivity and public repository operating procedure

**Active repository:** `Enochan222/sunrise-school-ai-platform` — **PUBLIC**, verified 2026-11-14. GitHub repository visibility is distinct from application/network visibility: Mac `127.0.0.1`, private Docker volumes, Native Open Notebook, SurrealDB, Gateway credentials and school data remain private.

## Transport and permission matrix

| Operation | What public access provides | Additional requirements |
|---|---|---|
| GitHub web/raw/API Git read | Public source, history and PRs without repository login | Network route to github.com; rate limits apply |
| GitHub Plugin / GitHub API write | Nothing by visibility alone | Connected identity, repository write permission, explicit Owner/Planning scope, protected-branch rules |
| Local Mac/Linux/Chat/Work `git clone/fetch` | Public source read if that **specific runtime** has DNS/network | TLS validation and available git; public does not fix a broken local network |
| Local `git push` | No anonymous write | Authenticated credential, network, branch lease and governance approval |
| GitHub Actions | Only the two Owner-approved Stage 1 workflows | Matching trigger/path/base, runner/budget availability, safe code and evidence; not a private Mac runtime |
| Mac private Docker / loopback | **No public access** | Explicit local execution and independent runtime evidence; GitHub runner cannot access Mac loopback |

**Historical incident (2026-11-10 only):** a particular container's `git ls-remote`, `getent` and `curl` failed DNS before authentication. That was an observed runtime-specific condition, **not** a current universal blocker or a proof that other Chat, Work, Mac or Linux runtimes fail. Re-test each actual execution environment. GitHub Plugin/API can read/write without local `git push` network, but connector commits are **not** proof of successful local push.

**Governance:** [Owner CI addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md) permits only `stage1-light.yml` and `stage1-native-integration.yml`, not Copilot, unapproved workflows, paid compute or automatic merge. Light workflow targets code-relevant same-repo PRs to `main`; `tests/stage1` is non-native only. Native workflow requires manual dispatch, and its current single-DB/fixed-port assumptions require separate technical review before any runtime PASS claim. $0 Budget/Stop Usage remains Owner-controlled. Check actual run/job event, head SHA, tested PR merge-result SHA, permissions, CI outcome and budget independently.

**Safe GitHub workflow:** fetch current main/branch ref and file blob SHAs; use a distinct scoped feature branch; apply docs-only changes; run actual QA and security-negative checks; open an evidence-gated PR; independently review final head/tree/diff and applicable ruleset; manually squash only with valid authorization and all applicable gates PASS. Re-read merged main/tree/blobs. Never post private credentials, raw logs, original licensed content or student data in GitHub issues, PRs, logs or artifacts. A PR/CI green check does not approve S1-AT, UAT, independent restore, R01, deployment or private data access.
