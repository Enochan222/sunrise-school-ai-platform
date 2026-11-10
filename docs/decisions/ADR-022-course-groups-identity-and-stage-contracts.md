# ADR-022 — Course/TeachingGroup, staff business grants and replay-safe contracts (candidate)

**Status:** PROPOSED, Owner Approval PENDING. **Scope:** S0 grain signoff, S3 B group contract, S6 B Blueprint, S9 I Evidence, S17 B Grade, S20 B Weakness, S22 B Staff grants. Retain historical ADR-001…010 in existing GitHub without overwrite; ADR-011–021 are still pending new architecture history. This ADR does not authorize a runtime code change.

## Decision

Keep one B Course per school/year/grade/subject/stream, many TeachingGroups; A Shell includes mandatory School owner and one Notebook. B staff authorization must apply to **real B business APIs** with scoped StaffSession, not only `/me/permissions`. B Worker uses ServiceToken to I Evidence validate, with same Job repeatable fresh validation and cross-job jti reuse forbidden. Grade formal event operation must reject same idempotency key with different canonical request. Blueprint and Weakness have complete read/write/state APIs before consuming I/U Stages. S26 A and S27 B each supply health/backup APIs before S28 I.

## Alternatives rejected

Share a Notebook for arbitrary schools, keep Course.class_id as one class, let I use Admin Token, mark Evidence jti used after first verify, silently ignore changed Grade Payload, or let U implement Missing B API in S21. Those patterns violate user goal, block later Stage or impair audit. Technology/vendor and exact wire shapes remain reference until Owner Stage Freeze.

## Gate

Approval requires proposed contract consistency and explicit Stage negative tests; runtime acceptance remains NOT RUN. No v0.7.3a hash-diff is claimed without original input file.
