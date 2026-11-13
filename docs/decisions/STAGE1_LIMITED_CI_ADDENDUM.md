# Stage 1 [A] — Limited GitHub Actions authorization addendum

**Owner approval: 2026-11-13.** This is a scope-limited *later exception* to the historical 2026-11-10 D08 decision forbidding GitHub Actions. Preserve the original Stage 0 decision file and D01–D08 text unchanged. This exception does not authorize R01, real data, production hosting, paid APIs, Copilot, B/I/U changes or changes to S1-AT01–15.

## Exactly two workflow files, only after independently reviewed PR merges

- `.github/workflows/stage1-light.yml`: auto-run on Stage 1 code-relevant `pull_request` events only (`opened`, `synchronize`, `reopened`, `ready_for_review`). Skip substantive work for Draft PRs. Restrict trigger paths to Stage 1 source/test/runtime-support code. Ubuntu 24.04, Python 3.12, 5-minute job timeout maximum, concurrency cancels superseded PR jobs. Run real available syntax, unit/component and security-negative tests; no `push`, `schedule`, or `pull_request_target`. Never configure a path-filtered or unstable check as Required Status Check.
- `.github/workflows/stage1-native-integration.yml`: `workflow_dispatch` **only**, initiated manually by an authorized Integration Reviewer after this workflow itself has merged to main. Ubuntu 24.04, max 30-minute timeout. Verify pinned Open Notebook v1.15.1 commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`, tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af`, patch provenance and final image digest. Lock actual SurrealDB v2 version/digest once compatible in real tests. Run real native API, worker, DB migrations, synthetic PDF extraction, scoped text-only search, safe retry, notebook ACK loss, graph link/unlink, restart and persistence wherever executable. Mark unexecuted checks NOT_RUN, never PASS.

## Security and billing

- `uses:` may reference only separately verified immutable full 40-hex commit SHAs of `actions/checkout` and `actions/setup-python`. No unreviewed reusable/repository-owned/third-party Actions, floating tags, auto-merge, bypass or force push. Token `permissions: contents: read`; checkout `persist-credentials: false`.
- No secrets beyond generated ephemeral synthetic credentials, no provider/API keys, no real school/student materials, no hosted deployment. Keep Open Notebook API, SurrealDB and Worker private; no native host port exposure. Review outbound dependency downloads and preserve evidence of external AI egress OFF.
- **No increase in allowed spending**: Owner's $0 Budget and Stop Usage stay unchanged. Owner-reported Billing UI displayed `Usage blocked` and previously `$0.08/$18.00` included compute; that is not proof that a new runner can start. After approval, at most one lowest-cost Runner Smoke before further usage. If Billing blocks it, save exact run/job error and stop; do not alter budget or spend cap without new Owner permission.
- CI PASS does not substitute independent Integration Reviewer QA/security/negative/regression checks, isolated A Backup/Restore, S1-AT01–15, Owner UAT or R01 approval. Evidence must cite tested SHA, image digests, UTC, exit codes and sanitized logs. Manual QA `scripts/run_qa_no_actions.py` remains valid despite its historical filename.
- Other Stages and workflow names remain under D08's Actions ban.

## Activation and precedence

1. This addendum and its minimal governance amendments must pass fresh full QA, independent review, manual squash merge and post-merge main/tree verification.
2. Only then create and review the two workflow PRs, separately. Workflow presence is not proof of authorization or of runner success.
3. Builder B's existing A-only implementation and PR #14 continue independently; workflow changes must not be mixed into that PR.
