# ADR-004: Notebook Permissions

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

Notebook creation is a Course workflow only; normal delete forbidden; Source has single owner; global/empty search forbidden; teachers read-only after S17 via I; raw Open Notebook admin endpoints remain private.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
