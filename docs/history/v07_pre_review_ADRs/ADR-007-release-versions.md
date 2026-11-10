# ADR-007: Release Versions

**Status:** PROPOSED; requires Owner signoff. **Date:** 2026-11-08.

## Decision

A/B/I/U versions separately pinned by SHA/digest/API/migration; each platform Release Rxx changes exactly one owner, keeps all previous functionality and evidence; stage number != runtime SemVer.

## Alternatives and rejection

Single shared database, mixed A/B Stage, I direct SQL, letting teachers reuse Open Notebook admin, and combining all changes into one PR were rejected because they break ownership, audit, rollback and course access boundaries.

## Verification

Relevant Stage ATs must be executed on actual deployed services; SPEC document checks do not prove the runtime.
