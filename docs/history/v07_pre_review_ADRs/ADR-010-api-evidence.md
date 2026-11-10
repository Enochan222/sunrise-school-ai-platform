# ADR-010: Api Evidence

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

I optional school course Notebook citations S10; B queue S9 can generate without them. References signed, bounded, provenance stored; no unscoped retrieval.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
