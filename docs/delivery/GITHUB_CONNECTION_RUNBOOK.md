# GitHub connectivity and ChatGPT connector operating procedure

**Active repository:** `Enochan222/sunrise-school-ai-platform` (private)
**Scope:** GitHub transport troubleshooting, not Stage 0 product acceptance.

## Verified on 2026-11-10

- The container provides Git 2.47.3, but `git ls-remote https://github.com/Enochan222/sunrise-school-ai-platform.git HEAD` fails with `Could not resolve host: github.com`.
- `getent hosts github.com` and `curl -I https://github.com` also fail at DNS resolution. This happens **before** credential or Git push authorization checks.
- The connected GitHub app authenticates as `Enochan222`, reports repository write permission and can read the protected `main`.
- GitHub Ruleset `Protect main` requires pull requests, prohibits deletion and force-push, and requires linear history. There is **no required GitHub Actions status check**.
- Per Owner decision, do **not** enable GitHub Copilot or GitHub Actions.

## Supported operational fallback

Use the connected GitHub app to create a feature branch, commit files, open a pull request and squash-merge after reviewing actual test evidence. The connector uses GitHub API operations and **does not require Git DNS access from the local container**.

This is an alternative transport to `git push`, not a repair to the container network or proof that literal `git push` succeeds. Do not silently call connector-based commits a successful local Git push.

For new files, prefer a single Git tree+commit for a coordinated set of changes; verify the branch SHA and file contents after the remote write. For repository changes, create a PR to `main`, record the exact test commands/environment/commit SHA, and re-fetch the merged commit and files. Do not write directly to protected `main`.

## Actual runtime and safeguards

- With GitHub Actions disabled, GitHub cannot automatically verify ChatGPT's test statements. A PR is not a passing test. Require evidence from executed tests, real API/DB checks for runtime stages, and a recorded approval decision for private student data or production actions.
- Stage 0 Master Kit v0.7.5 is **not imported** merely because an archive exists in a chat. Maintain `stage0/STAGE0_BASELINE.json` as the authoritative import/approval status.
- Do not upload API tokens, school/student records or production backups to the repository.
- When using a different runtime with working outbound DNS, ordinary `git clone`, `git fetch` and `git push` can be used with authorized credentials. Avoid disabling TLS verification, editing `/etc/hosts` to guessed IP addresses or posting a Personal Access Token into a chat.

## Diagnostic distinction

`Could not resolve host` = DNS/network boundary problem. Authentication errors (`401`, `403`, `Permission denied`) can only be evaluated **after** connectivity exists. In this environment, the connected GitHub app is the supported remote transport.
