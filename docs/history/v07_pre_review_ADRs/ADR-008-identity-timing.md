# ADR-008: Identity Timing

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

S1–15 one Admin, B IAM S16, I teacher content read-only S17, real PII only B S18 with legal/provider approvals; minimal security always on.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
