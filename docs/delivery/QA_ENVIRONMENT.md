# Repeatable QA environment (manual QA; limited Stage 1 CI exception)

**Scope:** Stage 0 document, OpenAPI-candidate, semantic, mutation and Stage0 status tests only. Not runtime, security penetration testing, production deployment or a hosted PR CI.

## Local user/GPT invocation

With Docker installed and a running Docker daemon, from the repository root run:

```sh
sh scripts/run_qa_docker.sh
```

The Dockerfile uses Python `3.11.11` on Debian Bookworm and pins the six Python requirements in `requirements-qa.txt`. The first build needs to download base image and dependencies; the test container runs with no network access and a read-only filesystem. We have *not* verified the Docker build in the ChatGPT execution environment because Docker is unavailable. A base-image digest, image supply-chain integrity, and lockfile with hashes are not provided yet; patch+dependency pinning is useful reproducibility, not cryptographic environment identity.

If Docker is unavailable but Python >=3.11 and dependencies are available, run `python scripts/run_qa_no_actions.py`; **label this fallback non-identical** unless its `python --version`, dependency versions and OS match the pinned environment. The current Stage0 QA has previously been executed under Python 3.13, not the Docker Python 3.11 container; do not claim the Docker path has passed until it actually runs.

## Each PR evidence card

1. Exact feature-branch commit SHA, Stage and single runtime Owner.
2. Docker image/container identification and `python --version`; `pip freeze`, command and exit code.
3. Save full stdout and stderr to a log and identify the corresponding commit. Check negative cases, predecessor regression and Stage Acceptance IDs.
4. Attach logs/summary to GitHub PR; if runner is offline/unavailable label `NOT_RUN` and do not merge.
5. For runtime stages, use staging A/B/I/U services with isolated credentials and DBs. Docker Stage0 QA is never proof of A/B security, restore or actual serving behavior.

**Automatic PR trigger:** historically absent for Stage 0. The [Stage 1 limited CI addendum](../decisions/STAGE1_LIMITED_CI_ADDENDUM.md) permits only one automatic PR lightweight workflow and one manual Native Runtime workflow, after their own reviewed PR merges. Skipped/blocked checks are NOT_RUN; their status does not replace independent QA, native security, restore or Owner UAT. The $0 spending cap and no-auto-merge rule remain.
