# ADR-001: Independent Databases

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

A SurrealDB with original material files and B PostgreSQL/Supabase with student/score/generation are physically separate: hosts/projects, credentials, network, backups, migrations, ownership; cross-system only HTTPS APIs. Reject shared SurrealDB in v0.6.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
