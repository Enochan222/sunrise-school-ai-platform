# ADR-015 — Contract Freeze And Provenance

**Status:** PROPOSED, PRODUCT OWNER SIGNOFF PENDING. **Spec date:** 2026-11-08. **New revision only; do not overwrite existing live ADR-001..010.**

## Decision

Canonical API Inventory and generated owner OpenAPI contracts must be frozen and executable consumer-tested before I stages S4/S9/S23. Evidence Bundle signed+jti/iss/aud/kid/purpose/expiry and authorization version, pin source_version/hash/locator; B checks revocation just before actual use and publication.

## Reasoning and rejected alternative

This resolves a critical cross-stage dependency/security risk. Reject hiding unsafe native API controls in CSS, linking by Course names, direct I DB access, concurrent owner PRs, stale API aliases, app-image-only rollback and publishing new features without a corresponding U or protected owner-native UI. Retain A/B independent deployment and restore, and explicit owner approval prior to production.

## Required proof

A domain/contract or workflow specification here is NOT an executed test. The named owner Stage must run actual negative HTTP/database/evidence/restore and user acceptance tests in the pinned deployment; S0 remains document/owner approval only. A/B existing GitHub ADRs are not superseded until the dedicated change PR is merged by an authorized human.

[Roadmap](../product/ROADMAP.md) · [Canonical API Inventory](../architecture/API_INVENTORY.json) · [Stage0](../stages/STAGE_00.md)
