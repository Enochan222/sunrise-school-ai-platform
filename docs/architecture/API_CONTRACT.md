# Canonical API Contract Inventory (v0.7 Reviewed)

**Only** [API_INVENTORY.json](API_INVENTORY.json) defines the canonical Path+Method+Operation ID+First Owner Stage. Human-readable table below is **generated** from it. Different names (`/source-manifest`, `/core/v1/bindings/*`) found in prior v0.7 drafts are obsolete and MUST NOT reappear as active routes. Owner typed proposed OpenAPI contracts: [A](../../contracts/openapi/a-v1.openapi.json), [B](../../contracts/openapi/b-v1.openapi.json), [I](../../contracts/openapi/i-v1.openapi.json). These are PROPOSED **typed candidate** contracts: concrete Path Parameters, per-operation typed request/success/error responses, auth actor class and narrowly scoped service actions are included. They still require provider implementation, negative HTTP tests, transaction/restore verification and explicit Owner API Freeze in S2/S3/S8/S22 before dependent I stages. **DO NOT call this a frozen production contract merely because JSON/OpenAPI validates.**

| First Stage | Owner | Method | Canonical Path | Operation ID | Auth / Service scope |
|---:|:---:|---|---|---|---|
| S1 | A | `GET` | `/vault/v1/shells` | `listContentShells` | admin |
| S1 | A | `POST` | `/vault/v1/shells` | `createContentShell` | admin |
| S1 | A | `GET` | `/vault/v1/shells/{shell_id}` | `getContentShell` | admin_or_service · vault.shell.read |
| S1 | A | `POST` | `/vault/v1/shells/{shell_id}/archive` | `archiveContentShell` | admin |
| S1 | A | `GET` | `/vault/v1/shells/{shell_id}/materials` | `listVaultMaterials` | admin_or_service · vault.materials.read |
| S1 | A | `POST` | `/vault/v1/shells/{shell_id}/materials` | `uploadVaultMaterial` | admin_or_service · vault.materials.write |
| S1 | A | `GET` | `/vault/v1/shells/{shell_id}/materials/{material_id}/download` | `downloadVaultMaterial` | admin_or_service · vault.materials.read |
| S1 | A | `POST` | `/vault/v1/shells/{shell_id}/search` | `searchContentShell` | admin_or_service · vault.search.read |
| S2 | A | `POST` | `/vault/v1/admin/cutover-policy` | `setVaultCutoverPolicy` | admin_or_service · vault.cutover.manage |
| S2 | A | `POST` | `/vault/v1/internal/provision` | `provisionVaultShell` | service · vault.shell.provision |
| S2 | A | `GET` | `/vault/v1/operations/{operation_id}` | `getVaultOperation` | service · vault.operation.read |
| S2 | A | `GET` | `/vault/v1/shells/{shell_id}/manifest` | `getVaultSourceManifest` | admin_or_service · vault.manifest.read |
| S2 | A | `POST` | `/vault/v1/source-versions/{version_id}/attest` | `attestVaultVersion` | service · vault.source.attest |
| S3 | B | `GET` | `/core/v1/course-bindings/{course_id}` | `getCourseBinding` | admin_or_service · core.binding.read |
| S3 | B | `GET` | `/core/v1/course-operations` | `listPendingCourseOperations` | service · core.operation.read |
| S3 | B | `POST` | `/core/v1/course-operations/reserve` | `reserveCourseOperation` | admin_or_service · core.course.reserve |
| S3 | B | `GET` | `/core/v1/course-operations/{operation_id}` | `getCourseOperation` | service · core.operation.read |
| S3 | B | `POST` | `/core/v1/course-operations/{operation_id}/finalize` | `finalizeCourseOperation` | service · core.operation.finalize |
| S3 | B | `POST` | `/core/v1/course-operations/{operation_id}/quarantine` | `quarantineCourseOperation` | service · core.operation.quarantine |
| S3 | B | `GET` | `/core/v1/courses` | `listAcademicCourses` | admin_or_staff · course.read (Staff S22+) |
| S3 | B | `POST` | `/core/v1/courses` | `createAcademicCourse` | admin |
| S3 | B | `GET` | `/core/v1/courses/{course_id}` | `getAcademicCourse` | admin_staff_or_service · core.course.read · course.read (Staff S22+) |
| S3 | B | `POST` | `/core/v1/courses/{course_id}/teaching-groups` | `createTeachingGroup` | admin |
| S3 | B | `GET` | `/core/v1/courses/{course_id}/teaching-groups` | `listTeachingGroups` | admin_or_staff · course.groups.read (Staff S22+) |
| S4 | I | `POST` | `/link/v1/adoptions/commit` | `commitAdoption` | admin |
| S4 | I | `POST` | `/link/v1/adoptions/dry-run` | `dryRunAdoption` | admin |
| S4 | I | `POST` | `/link/v1/course-provision` | `createUnifiedCourse` | admin |
| S4 | I | `GET` | `/link/v1/courses/{course_id}/content` | `listLinkedCourseContent` | admin |
| S4 | I | `GET` | `/link/v1/courses/{course_id}/materials` | `listCourseMaterials` | admin |
| S4 | I | `POST` | `/link/v1/courses/{course_id}/materials` | `uploadCourseMaterial` | admin |
| S4 | I | `GET` | `/link/v1/courses/{course_id}/materials/{material_id}/download` | `downloadCourseMaterial` | admin |
| S4 | I | `POST` | `/link/v1/courses/{course_id}/search` | `searchCourseMaterials` | admin |
| S4 | I | `GET` | `/link/v1/operations/{operation_id}` | `getIntegrationOperation` | admin |
| S4 | I | `POST` | `/link/v1/operations/{operation_id}/retry` | `retryIntegrationOperation` | admin |
| S4 | I | `GET` | `/link/v1/reconciliation` | `getCoreReconciliation` | admin |
| S6 | B | `POST` | `/core/v1/question-schemas/validate` | `validateQuestionSchema` | admin |
| S6 | B | `POST` | `/core/v1/question-templates` | `createQuestionTemplate` | admin |
| S6 | B | `POST` | `/core/v1/blueprints` | `createBlueprint` | admin |
| S6 | B | `GET` | `/core/v1/blueprints/{blueprint_id}` | `getBlueprint` | admin |
| S6 | B | `PUT` | `/core/v1/blueprints/{blueprint_id}/draft` | `updateBlueprintDraft` | admin |
| S6 | B | `POST` | `/core/v1/blueprints/{blueprint_id}/publish` | `publishBlueprint` | admin |
| S6 | B | `GET` | `/core/v1/blueprints/{blueprint_id}/versions` | `listBlueprintVersions` | admin |
| S6 | B | `GET` | `/core/v1/question-templates/{template_id}` | `getQuestionTemplate` | admin |
| S6 | B | `POST` | `/core/v1/rubric-versions` | `createRubricVersion` | admin |
| S6 | B | `GET` | `/core/v1/rubric-versions/{rubric_id}/{version_id}` | `getRubricVersion` | admin |
| S7 | B | `POST` | `/core/v1/admin/ai-providers` | `saveAiProvider` | admin |
| S7 | B | `POST` | `/core/v1/admin/ai-providers/revoke` | `revokeAiProvider` | admin |
| S7 | B | `POST` | `/core/v1/admin/ai-providers/test` | `testAiProvider` | admin |
| S8 | B | `POST` | `/core/v1/evidence-bundles` | `ingestEvidenceBundle` | service · core.evidence.ingest |
| S8 | B | `GET` | `/core/v1/evidence-bundles/{bundle_id}/status` | `getEvidenceBundleStatus` | admin_or_service · core.evidence.read |
| S8 | B | `POST` | `/core/v1/generation-jobs` | `enqueueGenerationJob` | admin_or_service · core.job.enqueue |
| S8 | B | `GET` | `/core/v1/generation-jobs/{job_id}` | `getGenerationJob` | admin_or_service · core.job.read |
| S8 | B | `POST` | `/core/v1/generation-jobs/{job_id}/approve` | `approveGenerationJob` | admin |
| S9 | I | `POST` | `/link/v1/evidence-bundles` | `createEvidenceBundle` | admin |
| S9 | I | `POST` | `/link/v1/evidence-bundles/{bundle_id}/validate` | `validateEvidenceBundle` | service · link.evidence.validate |
| S11 | B | `POST` | `/core/v1/papers/math` | `createMathPaper` | admin |
| S11 | B | `GET` | `/core/v1/papers/{paper_id}` | `getPaper` | admin |
| S11 | B | `GET` | `/core/v1/papers/{paper_id}/pdf` | `downloadPaperPdf` | admin |
| S12 | B | `POST` | `/core/v1/subject-adapters/chinese` | `createChinesePaper` | admin |
| S13 | B | `POST` | `/core/v1/subject-adapters/english` | `createEnglishPaper` | admin |
| S14 | B | `POST` | `/core/v1/subject-adapters/general-studies` | `createGeneralStudiesPaper` | admin |
| S15 | B | `POST` | `/core/v1/enrollments` | `assignSyntheticStudent` | admin |
| S15 | B | `GET` | `/core/v1/students` | `listSyntheticStudents` | admin_or_staff · course.synthetic_roster.read (Staff S22+) |
| S15 | B | `POST` | `/core/v1/students` | `createSyntheticStudent` | admin |
| S16 | B | `POST` | `/core/v1/assessments` | `createAssessment` | admin |
| S16 | B | `GET` | `/core/v1/assessments/{assessment_id}` | `getAssessment` | admin_or_staff · course.assessment.read (Staff S22+) |
| S16 | B | `POST` | `/core/v1/score-drafts` | `createScoreDraft` | admin |
| S17 | B | `POST` | `/core/v1/admin/grade-corrections` | `correctGrade` | admin |
| S17 | B | `POST` | `/core/v1/grades/submit` | `submitGrade` | admin_or_staff · course.grade.submit (Staff S22+) |
| S17 | B | `GET` | `/core/v1/grades/{grade_key}/current` | `getCurrentGrade` | admin_or_staff · course.grade.read (Staff S22+) |
| S17 | B | `GET` | `/core/v1/grades/{grade_key}/history` | `getGradeHistory` | admin_or_staff · course.grade.read (Staff S22+) |
| S18 | B | `POST` | `/core/v1/manual-marking` | `approveManualMarking` | admin_or_staff · course.manual_mark (Staff S22+) |
| S18 | B | `POST` | `/core/v1/submissions` | `createSubmission` | admin |
| S18 | B | `GET` | `/core/v1/courses/{course_id}/submissions` | `listSubmissions` | admin_or_staff · course.submissions.read (Staff S22+) |
| S18 | B | `POST` | `/core/v1/submissions/{submission_id}/item-marking` | `markItemSubmission` | admin |
| S18 | B | `GET` | `/core/v1/submissions/{submission_id}/item-marking` | `listSubmissionItemMarking` | admin |
| S19 | B | `POST` | `/core/v1/marking-jobs` | `createAiMarkingJob` | admin |
| S19 | B | `POST` | `/core/v1/marking-reviews` | `reviewAiMarkingJob` | admin |
| S20 | B | `POST` | `/core/v1/analytics` | `runDeterministicAnalytics` | admin |
| S20 | B | `GET` | `/core/v1/analytics/{run_id}` | `getAnalyticsRun` | admin |
| S20 | B | `GET` | `/core/v1/weakness` | `listActiveWeakness` | admin |
| S20 | B | `POST` | `/core/v1/weakness` | `keepWeaknessMemory` | admin |
| S20 | B | `GET` | `/core/v1/weakness/candidates` | `listWeaknessCandidates` | admin |
| S20 | B | `GET` | `/core/v1/weakness/{snapshot_id}` | `getWeaknessSnapshot` | admin |
| S20 | B | `POST` | `/core/v1/weakness/{snapshot_id}/discard` | `discardWeaknessSnapshot` | admin |
| S22 | B | `POST` | `/core/v1/admin/grants` | `grantStaffCourse` | admin |
| S22 | B | `POST` | `/core/v1/admin/grants/revoke` | `revokeStaffGrant` | admin |
| S22 | B | `GET` | `/core/v1/me/permissions` | `getUserGrants` | staff · staff.grants.self.read (Staff S22+) |
| S22 | B | `GET` | `/core/v1/staff/{staff_id}/permissions` | `getStaffPermissionsService` | service · core.grant.check |
| S23 | I | `GET` | `/link/v1/teacher/content` | `getTeacherContent` | staff · staff.course.read (Staff S22+) |
| S23 | I | `GET` | `/link/v1/teacher/courses/{course_id}/materials/{material_id}/download` | `downloadTeacherContent` | staff · staff.grants.self.read (Staff S22+) |
| S23 | I | `POST` | `/link/v1/teacher/courses/{course_id}/search` | `searchTeacherContent` | staff · staff.grants.self.read (Staff S22+) |
| S25 | B | `POST` | `/core/v1/real-students/import` | `importRealStudents` | admin |
| S26 | A | `POST` | `/vault/v1/admin/retention-review` | `reviewVaultRetention` | admin |
| S26 | A | `GET` | `/vault/v1/health` | `getVaultHealth` | service · vault.health.read |
| S26 | A | `GET` | `/vault/v1/backup-status` | `getVaultBackupStatus` | service · vault.backup.status |
| S27 | B | `POST` | `/core/v1/academic-years/close` | `closeAcademicYear` | admin |
| S27 | B | `GET` | `/core/v1/health` | `getCoreHealth` | service · core.health.read |
| S27 | B | `GET` | `/core/v1/backup-status` | `getCoreBackupStatus` | service · core.backup.status |
| S28 | I | `GET` | `/link/v1/reconciliation-dashboard` | `getReconciliationDashboard` | admin |


**Contract preflight for I S4/S9/S23/S28:** compare deployed SHA/OpenAPI version and `operationId` against inventory, run independent consumer tests using valid and negative fixtures (including retry same key/different body, 409 conflicts, 401/403 source boundaries, provider 503), verify API network allowlist. If owner contract not implemented, schedule owner-only Stage; never patch A/B inside I PR. I can call both APIs normally, but cannot connect to either database.

HTTP semantic examples: missing Session `401`, scope denied `403`, unknown ID `404`, same idempotency key with altered canonical JSON+actor hash or binding collision `409`, invalid schema/semantics `422`, upstream/contract missing `503`. Correlation/operation/version IDs required; no partial success returned as ACTIVE. All candidate operation IDs and success shapes have typed envelopes; domain constraints and actual status/error semantics remain OWNER-APPROVAL GATED until real consumer/provider tests. File downloads use `application/octet-stream` with binary schema, not a JSON success envelope. Service scopes are checked per route and per resource; I is never given an Admin Session or DB Root key.

## Forward provider/consumer contract freeze (changed in v0.7.4)

S3 MUST pin B `AcademicCourse.grade/curriculum_stream`, 1 Course:many TeachingGroups, and Group-scoped grants. S6 MUST publish blueprint/rubric draft-edit, immutable publish version, read/list history endpoints before S8 can refer to `blueprint_id/version`. S8 B Worker MUST use S9 I ServiceToken-only evidence-validation API **after S9 is deployed**; until S9, evidence is OFF and standalone B Generation remains usable. S20 Weakness Candidate/Discard/Retired/STALE endpoints MUST precede S21 UI. S26 A and S27 B MUST expose read-only health/backup status APIs before S28 I dashboard. These are proposed contracts requiring actual implementation before owner Freeze.
