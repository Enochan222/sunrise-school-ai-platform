# ADR-021 — Typed API Contracts and Separate Service Principals (PROPOSED)

**Status:** Pending Owner and A/B/I tech lead signoff, 2026-11-08.

## Decision

Keep original v0.7 S0–S28 single-owner releases. A and B each publish typed OpenAPI for their data endpoints and deny unscoped calls. I never receives A/B AdminSession or DB credentials. A/B pre-release ServiceToken verifies audience, issuer, subject, expiry, token ID, scope and bound course/source owner. S22 B supports private grant lookup for I; S23 I StaffSession is a human teacher identity, not privileged service authority.

S1 Content Vault material list plus S4 I proxy list/upload/search/download are explicitly added to support S5 Course/Content UI. Stage5 does not expose Assessment or Grades before owning Stages.

OpenAPI typed responses/requests are **proposed contract definitions**, not proof of runtime implementation or Owner Contract Freeze. Freeze of A S2 + B S3 needs real consumer/provider/negative auth tests before S4. I may not patch either data owner when integration reveals contract gaps.

## Alternatives rejected

Use I Admin Token, share B `service_role` with integration, raw Open Notebook UI for teacher, permit generic `{}` response payloads, or assume typo-free MD files prove API correctness.

## Required evidence

Actual provider/consumer test results, route-specific service scopes, negative source and staff access, response schema fixtures, cross-service retries and owner-locked release digests. No GitHub merged status inferred from this ZIP.
