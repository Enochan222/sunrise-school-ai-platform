# Compatibility / Rollback Design — API and Data Migrations

Each Platform Release `R01–R28` changes one runtime owner only; **not** every owner SemVer. Manifest fields required: stage, owner, Git SHA, container digest, DB Migration Hash/DDL version for changed owner, all A/B/I/U pinned versions, OpenAPI contract versions, `min_compatible_api_version`, feature flags, backup snapshot ID+restore report, schema/data downgrade safety, Actor/Scope impacts, Owner signoff. Unchanged owners' SHA/Image/Schema configs must match preceding manifest exactly.

For schema changes, migrate with **EXPAND → MIGRATE → CONTRACT** across successive owner-only releases; do not combine breaking SQL and I hotfix. Old code rollback is allowed only if new DB schema remains read-compatible, otherwise freeze writes and forward-fix with controlled recovery. On A Source Version retraction, B pinned references must display `UNAVAILABLE` or validation error, never point silently to new Version. On mismatch in separate A/B backups, I quarantines Binding and prevents content generation until restored epochs/operation logs reconcile.

[Schema](../../contracts/schemas/course_operation_v1.schema.json) · [Release Policy](../delivery/RELEASE_POLICY.md) · [Release Manifest Schema](../delivery/RELEASE_MANIFEST_SCHEMA.json)

## API Freeze Gates and contract type policy (v0.7.2)

- S2 A and S3 B must sign off their **versioned provider OpenAPI**, complete resource owner rules, ServiceToken claims/scope and consumer/provider tests before S4 I.
- S1 A Material operations are defined and testable independently, including media type, SHA, source owner and binary streaming.
- S8 B generation/evidence contract must be tested before S9 I; S22 B staff service scope must be tested before S23 teacher content.
- `contracts/openapi/*.json` is a **typed candidate baseline**, not a frozen API, while any real provider/consumer tests, IAM adversarial tests or data migration checks are NOT RUN. No CI script may set Release Gate PASS from static schema validation.
- Existing API paths, JSON required-fields and enum values are *proposed* decisions. Any break must use Owner-only Expand → Migrate → Contract changes with contract versioning and explicit compatibility gate; no joint A+B runtime PR.


## v0.7.4 contract change plan

These are planning changes to Owner API candidates, not proof that a deployed v1 provider can be broken: S3 Course/TeachingGroup contract, S6 Blueprint lifecycle, S8 Worker ServiceToken expectations, S9 Evidence validate, S17 Grade Hash, S20 Weakness lifecycle, S22 Staff business API, S26/S27 Health. At real stage freeze, use Expand→Migrate→Contract and consumer contract tests; I/U stages are blocked from altering preceding A/B. S8 Queue must work with Evidence OFF until S9 and S21 Weakness UI cannot invent data before S20. Contract/document CI is not production Freeze.
