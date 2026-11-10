# ADR-003: Content Shell

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

S1 A-only creates a Course Content Shell/Notebook via A-admin page. B course is separate and CONTENT_UNLINKED until S7; I adopts explicit stable IDs, never title-matches or overwrites originals.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
