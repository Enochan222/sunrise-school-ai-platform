# Sunrise School AI Platform

**Owner:** `Enochan222` · **Repository:** `sunrise-school-ai-platform` · **Private**

**STAGE 0 BOOTSTRAP ONLY — MASTER KIT v0.7.5 NOT YET IMPORTED.**

This new repository is independent of the former IssacSitHk repository. Do not copy its commit history, ADRs, issues or stale v0.5–v0.7 specifications. The target planning candidate is **Sunrise Master Project Kit v0.7.5 Reuse-first Stage Logic Reviewed**, but its exact ZIP is not currently available for a verified import.

## System boundaries (planning only)

| Track | Responsible for |
|---|---|
| A | Open Notebook + SurrealDB teaching-source vault, secured school/source policy |
| B | Independent PostgreSQL/Supabase Course, Teaching Groups, papers, grades, marking, IAM |
| I | A/B integration using ONLY authenticated public service APIs; no DB connections |
| U | Sunrise UI via controlled APIs; no direct database access |

Stage 0 covers documentation, repo governance, CI and product decisions only. Runtime Stage S1–S28 must have one owner each. No deployment, data restore or school-data approval is claimed.

Read [Stage 0 Checklist](docs/delivery/STAGE0_CHECKLIST.md), [v0.7.5 import instructions](docs/delivery/IMPORT_V075.md) and [AI working rules](AGENTS.md). The CI check `validate-docs` reports **bootstrap tests only** while the master archive is missing; it cannot be used as proof that v0.7.5 was imported or that Stage 0 was approved.
