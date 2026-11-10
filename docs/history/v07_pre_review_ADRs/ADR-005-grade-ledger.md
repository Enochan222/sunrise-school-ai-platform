# ADR-005: Grade Ledger

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

B grade draft is editable, formal submit only once, corrections append events/reasons/actor, no UPDATE/DELETE; B-only source-of-truth. Original grades remain reconstructable.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
