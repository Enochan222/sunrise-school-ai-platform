# ADR-009: Integration Saga

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

I S7 uses B operation reservation + A idempotent Shell creation + B finalize; no cross-DB ACID. Orphans quarantined, not deleted. I only calls pre-published APIs.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
