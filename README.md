# Sunrise School AI Platform

**Active GitHub:** https://github.com/Enochan222/sunrise-school-ai-platform  
**Stage 0: BOOTSTRAP ONLY — complete v0.7.5 Master Kit is NOT YET uploaded to GitHub.**  
**AI:** ChatGPT / GPT; **GitHub Copilot:** not used; **GitHub Actions:** not used or required.

This private repository is independent from `IssacSitHk`. It currently contains only a bootstrap. The full, locally verified 164-file v0.7.5 No-Actions package has been prepared for import, but a ZIP archive does not automatically unpack into GitHub.

## Four planned subsystems

- **A:** Open Notebook / SurrealDB Content Vault with Sunrise school/source policy and scoped API.
- **B:** PostgreSQL/Supabase Learning Operations for Courses, Teaching Groups, generation, assessments, immutable grade histories and analytics.
- **I:** A/B integration via authenticated APIs only, without cross-database credentials.
- **U:** Sunrise front end consuming controlled APIs.

## Testing policy

A PR does **not** automatically invoke GPT. Since GitHub Actions is disabled and no independent CI service has been connected, the `Protect main` ruleset requires a PR but **does not enforce QA results**. AI must run applicable tests in a real environment and record the exact commit SHA, command, output, dependency versions and failures before a controlled squash merge. No unattended PR auto-merge.

For this small bootstrap, run `python -m unittest discover -s tests -p 'test_*.py' -v` and `python scripts/validate_stage0.py`. For the **complete kit** (once imported), run `python scripts/run_qa_no_actions.py`, ideally using the specified Docker environment in [QA environment](docs/delivery/QA_ENVIRONMENT.md). Passing these tests does not prove deployed A/B/I/U runtimes, school-data security or Stage 0 business sign-off.

See [Stage0 checklist](docs/delivery/STAGE0_CHECKLIST.md), [master import](docs/delivery/IMPORT_V075.md) and [AI rules](AGENTS.md).
