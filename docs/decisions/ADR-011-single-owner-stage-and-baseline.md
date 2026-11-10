# ADR-011 — Single Owner Stage And Baseline

> **Current repository clarification (2026-11-10):** This original 2026-11-08 *proposal* uses historical v0.5/old-GitHub language. Reviewed 164-file v0.7.5 has now been merged into `Enochan222/sunrise-school-ai-platform` via PR #8. Product signoff is still pending; see [Owner decision packet](STAGE0_APPROVAL_DECISIONS.md).

**Status:** PROPOSED, PRODUCT OWNER SIGNOFF PENDING. **Spec date:** 2026-11-08. **New revision only; do not overwrite existing live ADR-001..010.**

## Decision

Existing GitHub main is v0.5; Reviewed v0.7 must be proposed via dedicated Docs PR before owner signoff. One runtime owner per Stage (A/B/I/U); API calls can have authorized side effects, but no cross-owner schema/deployment change.

## Reasoning and rejected alternative

This resolves a critical cross-stage dependency/security risk. Reject hiding unsafe native API controls in CSS, linking by Course names, direct I DB access, concurrent owner PRs, stale API aliases, app-image-only rollback and publishing new features without a corresponding U or protected owner-native UI. Retain A/B independent deployment and restore, and explicit owner approval prior to production.

## Required proof

A domain/contract or workflow specification here is NOT an executed test. The named owner Stage must run actual negative HTTP/database/evidence/restore and user acceptance tests in the pinned deployment; S0 remains document/owner approval only. A/B existing GitHub ADRs are not superseded until the dedicated change PR is merged by an authorized human.

[Roadmap](../product/ROADMAP.md) · [Canonical API Inventory](../architecture/API_INVENTORY.json) · [Stage0](../stages/STAGE_00.md)
