# ADR-002: Stage Single Owner

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

A Stage has exactly one runtime owner (A/B/I/U). I may orchestrate A+B via pre-released APIs but has no DB DSN and may not patch either runtime. Cross-owner needs new Stage; releases strictly gated.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
