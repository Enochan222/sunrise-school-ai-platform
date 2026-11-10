# ADR-006: Weakness Two

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

B analytics derived deterministically, user Keep/Discard; max 2 VALID ACTIVE weakness snapshots per course/target; corrections stale snapshots; no data in A.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
