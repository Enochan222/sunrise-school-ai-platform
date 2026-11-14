# GitHub Public Repository — Connectivity and Write-boundary Runbook

**Active repository**: `Enochan222/sunrise-school-ai-platform`, now PUBLIC. The 2026-11-10 `Could not resolve host: github.com` was an observed error in **one container**, not a permanent GitHub outage or permission verdict. See [AGENTS](../../AGENTS.md), [Security](../../SECURITY.md) and [Limited CI Addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md).

| Path | Public Git read | Authorized write | Access Owner Mac `127.0.0.1` |
|---|---|---|---|
| Browser/github.com and normal `git clone/fetch` | Yes if DNS/network works | Only with GitHub authentication, protected ref and Owner lease | No |
| Connected GitHub Plugin / REST API | Yes within connector scope | Yes only via permitted API action plus explicit Owner lease | No |
| Owner Mac Terminal `git clone/fetch/push` | Yes if connected | Yes with credentials, branch and sole-writer consent | Only locally and with real services |
| Chat/Linux/container Terminal | Environment-specific DNS and egress | Not inferred by Public status | No |
| GitHub Actions runner | Workflow/event-controlled checkout | Only its pinned read-only token, no privileged fork secrets | No |

**Separate failure modes:** DNS (`Could not resolve host`), GitHub credentials (401/403), connector scope, branch ruleset, and personal Owner write lease. A connector commit does not prove a literal terminal `git push` worked. Check working directory and exact Head/Tree; use a clean git checkout or safe exact-parent Git Data API write, never force push. Public clone does not connect to private Mac Docker, SurrealDB volumes or a local Gateway.

**Authorized Actions:** only `stage1-light.yml` (same-repo, path-filtered `main`-target PRs, Draft allowed, `tests/stage1`) and `stage1-native-integration.yml` (separately permitted manual dispatch). PR #24 targets PR #14's Stage1 implementation branch and is not covered by the Light `branches: [main]` trigger. Pull-request `GITHUB_SHA`/checkout may be a synthetic merge-result SHA, not PR Head: record both. The current Manual Native workflow still contains old single-DB/fixed-port assumptions: do not claim modern dual-DB acceptance from its presence.

**Cost / security:** GitHub 2026 documentation says standard public GitHub-hosted runners are free, but this does not establish the Owner account's Billing settings, availability or permission to increase budgets. Preserve the Owner's $0 Budget/Stop Usage, no new workflows, paid services, auto-merge or extra privileges. No real school/student content, raw logs, credentials, local private paths or backup keys in public PRs, Actions logs/artifacts or Git history. A missing/skipped run is NOT_RUN, and CI PASS never equals formal S1 AT, Owner UAT or R01.

**Release:** read current `main`, ruleset, PR Head/Base, changed blobs, exact test reports and independent reviewer before any authorized manual squash merge; then re-read the final `main` commit/tree/blobs.
