# API Actor / Least-privilege Permission Matrix — v0.7.4 (CANDIDATE, NOT DEPLOYED)

**Staff role starts S22; the affected pre-existing B routes remain Admin-only in deployed releases up to S21.** This document is a future contract and does not claim existing staff access. All Staff requests require StaffSession + school/course/group grant and resource scope; Service uses separate bounded ServiceToken. No AdminToken impersonation.

| First Stage | Owner | Method | Operation | Actor | Service scope | Staff grant | Staff activation |
|---|---|---|---|---|---|---|---|
| S1 | A | GET | `listContentShells` | `admin` | `—` | `—` | — |
| S1 | A | POST | `createContentShell` | `admin` | `—` | `—` | — |
| S1 | A | GET | `getContentShell` | `admin_or_service` | `vault.shell.read` | `—` | — |
| S1 | A | POST | `archiveContentShell` | `admin` | `—` | `—` | — |
| S1 | A | GET | `listVaultMaterials` | `admin_or_service` | `vault.materials.read` | `—` | — |
| S1 | A | POST | `uploadVaultMaterial` | `admin_or_service` | `vault.materials.write` | `—` | — |
| S1 | A | GET | `downloadVaultMaterial` | `admin_or_service` | `vault.materials.read` | `—` | — |
| S1 | A | POST | `searchContentShell` | `admin_or_service` | `vault.search.read` | `—` | — |
| S2 | A | POST | `setVaultCutoverPolicy` | `admin_or_service` | `vault.cutover.manage` | `—` | — |
| S2 | A | POST | `provisionVaultShell` | `service` | `vault.shell.provision` | `—` | — |
| S2 | A | GET | `getVaultOperation` | `service` | `vault.operation.read` | `—` | — |
| S2 | A | GET | `getVaultSourceManifest` | `admin_or_service` | `vault.manifest.read` | `—` | — |
| S2 | A | POST | `attestVaultVersion` | `service` | `vault.source.attest` | `—` | — |
| S3 | B | GET | `getCourseBinding` | `admin_or_service` | `core.binding.read` | `—` | — |
| S3 | B | GET | `listPendingCourseOperations` | `service` | `core.operation.read` | `—` | — |
| S3 | B | POST | `reserveCourseOperation` | `admin_or_service` | `core.course.reserve` | `—` | — |
| S3 | B | GET | `getCourseOperation` | `service` | `core.operation.read` | `—` | — |
| S3 | B | POST | `finalizeCourseOperation` | `service` | `core.operation.finalize` | `—` | — |
| S3 | B | POST | `quarantineCourseOperation` | `service` | `core.operation.quarantine` | `—` | — |
| S3 | B | GET | `listAcademicCourses` | `admin_or_staff` | `—` | `course.read` | S22 |
| S3 | B | POST | `createAcademicCourse` | `admin` | `—` | `—` | — |
| S3 | B | GET | `getAcademicCourse` | `admin_staff_or_service` | `core.course.read` | `course.read` | S22 |
| S3 | B | POST | `createTeachingGroup` | `admin` | `—` | `—` | — |
| S3 | B | GET | `listTeachingGroups` | `admin_or_staff` | `—` | `course.groups.read` | S22 |
| S4 | I | POST | `commitAdoption` | `admin` | `—` | `—` | — |
| S4 | I | POST | `dryRunAdoption` | `admin` | `—` | `—` | — |
| S4 | I | POST | `createUnifiedCourse` | `admin` | `—` | `—` | — |
| S4 | I | GET | `listLinkedCourseContent` | `admin` | `—` | `—` | — |
| S4 | I | GET | `listCourseMaterials` | `admin` | `—` | `—` | — |
| S4 | I | POST | `uploadCourseMaterial` | `admin` | `—` | `—` | — |
| S4 | I | GET | `downloadCourseMaterial` | `admin` | `—` | `—` | — |
| S4 | I | POST | `searchCourseMaterials` | `admin` | `—` | `—` | — |
| S4 | I | GET | `getIntegrationOperation` | `admin` | `—` | `—` | — |
| S4 | I | POST | `retryIntegrationOperation` | `admin` | `—` | `—` | — |
| S4 | I | GET | `getCoreReconciliation` | `admin` | `—` | `—` | — |
| S6 | B | POST | `validateQuestionSchema` | `admin` | `—` | `—` | — |
| S6 | B | POST | `createQuestionTemplate` | `admin` | `—` | `—` | — |
| S6 | B | POST | `createBlueprint` | `admin` | `—` | `—` | — |
| S6 | B | GET | `getBlueprint` | `admin` | `—` | `—` | — |
| S6 | B | PUT | `updateBlueprintDraft` | `admin` | `—` | `—` | — |
| S6 | B | POST | `publishBlueprint` | `admin` | `—` | `—` | — |
| S6 | B | GET | `listBlueprintVersions` | `admin` | `—` | `—` | — |
| S6 | B | GET | `getQuestionTemplate` | `admin` | `—` | `—` | — |
| S6 | B | POST | `createRubricVersion` | `admin` | `—` | `—` | — |
| S6 | B | GET | `getRubricVersion` | `admin` | `—` | `—` | — |
| S7 | B | POST | `saveAiProvider` | `admin` | `—` | `—` | — |
| S7 | B | POST | `revokeAiProvider` | `admin` | `—` | `—` | — |
| S7 | B | POST | `testAiProvider` | `admin` | `—` | `—` | — |
| S8 | B | POST | `ingestEvidenceBundle` | `service` | `core.evidence.ingest` | `—` | — |
| S8 | B | GET | `getEvidenceBundleStatus` | `admin_or_service` | `core.evidence.read` | `—` | — |
| S8 | B | POST | `enqueueGenerationJob` | `admin_or_service` | `core.job.enqueue` | `—` | — |
| S8 | B | GET | `getGenerationJob` | `admin_or_service` | `core.job.read` | `—` | — |
| S8 | B | POST | `approveGenerationJob` | `admin` | `—` | `—` | — |
| S9 | I | POST | `createEvidenceBundle` | `admin` | `—` | `—` | — |
| S9 | I | POST | `validateEvidenceBundle` | `service` | `link.evidence.validate` | `—` | — |
| S11 | B | POST | `createMathPaper` | `admin` | `—` | `—` | — |
| S11 | B | GET | `getPaper` | `admin` | `—` | `—` | — |
| S11 | B | GET | `downloadPaperPdf` | `admin` | `—` | `—` | — |
| S12 | B | POST | `createChinesePaper` | `admin` | `—` | `—` | — |
| S13 | B | POST | `createEnglishPaper` | `admin` | `—` | `—` | — |
| S14 | B | POST | `createGeneralStudiesPaper` | `admin` | `—` | `—` | — |
| S15 | B | POST | `assignSyntheticStudent` | `admin` | `—` | `—` | — |
| S15 | B | GET | `listSyntheticStudents` | `admin_or_staff` | `—` | `course.synthetic_roster.read` | S22 |
| S15 | B | POST | `createSyntheticStudent` | `admin` | `—` | `—` | — |
| S16 | B | POST | `createAssessment` | `admin` | `—` | `—` | — |
| S16 | B | GET | `getAssessment` | `admin_or_staff` | `—` | `course.assessment.read` | S22 |
| S16 | B | POST | `createScoreDraft` | `admin` | `—` | `—` | — |
| S17 | B | POST | `correctGrade` | `admin` | `—` | `—` | — |
| S17 | B | POST | `submitGrade` | `admin_or_staff` | `—` | `course.grade.submit` | S22 |
| S17 | B | GET | `getCurrentGrade` | `admin_or_staff` | `—` | `course.grade.read` | S22 |
| S17 | B | GET | `getGradeHistory` | `admin_or_staff` | `—` | `course.grade.read` | S22 |
| S18 | B | POST | `approveManualMarking` | `admin_or_staff` | `—` | `course.manual_mark` | S22 |
| S18 | B | POST | `createSubmission` | `admin` | `—` | `—` | — |
| S18 | B | GET | `listSubmissions` | `admin_or_staff` | `—` | `course.submissions.read` | S22 |
| S18 | B | POST | `markItemSubmission` | `admin` | `—` | `—` | — |
| S18 | B | GET | `listSubmissionItemMarking` | `admin` | `—` | `—` | — |
| S19 | B | POST | `createAiMarkingJob` | `admin` | `—` | `—` | — |
| S19 | B | POST | `reviewAiMarkingJob` | `admin` | `—` | `—` | — |
| S20 | B | POST | `runDeterministicAnalytics` | `admin` | `—` | `—` | — |
| S20 | B | GET | `getAnalyticsRun` | `admin` | `—` | `—` | — |
| S20 | B | GET | `listActiveWeakness` | `admin` | `—` | `—` | — |
| S20 | B | POST | `keepWeaknessMemory` | `admin` | `—` | `—` | — |
| S20 | B | GET | `listWeaknessCandidates` | `admin` | `—` | `—` | — |
| S20 | B | GET | `getWeaknessSnapshot` | `admin` | `—` | `—` | — |
| S20 | B | POST | `discardWeaknessSnapshot` | `admin` | `—` | `—` | — |
| S22 | B | POST | `grantStaffCourse` | `admin` | `—` | `—` | — |
| S22 | B | POST | `revokeStaffGrant` | `admin` | `—` | `—` | — |
| S22 | B | GET | `getUserGrants` | `staff` | `—` | `staff.grants.self.read` | — |
| S22 | B | GET | `getStaffPermissionsService` | `service` | `core.grant.check` | `—` | — |
| S23 | I | GET | `getTeacherContent` | `staff` | `—` | `staff.course.read` | — |
| S23 | I | GET | `downloadTeacherContent` | `staff` | `—` | `staff.grants.self.read` | — |
| S23 | I | POST | `searchTeacherContent` | `staff` | `—` | `staff.grants.self.read` | — |
| S25 | B | POST | `importRealStudents` | `admin` | `—` | `—` | — |
| S26 | A | POST | `reviewVaultRetention` | `admin` | `—` | `—` | — |
| S26 | A | GET | `getVaultHealth` | `service` | `vault.health.read` | `—` | — |
| S26 | A | GET | `getVaultBackupStatus` | `service` | `vault.backup.status` | `—` | — |
| S27 | B | POST | `closeAcademicYear` | `admin` | `—` | `—` | — |
| S27 | B | GET | `getCoreHealth` | `service` | `core.health.read` | `—` | — |
| S27 | B | GET | `getCoreBackupStatus` | `service` | `core.backup.status` | `—` | — |
| S28 | I | GET | `getReconciliationDashboard` | `admin` | `—` | `—` | — |


## Mandatory staff authorization semantics

- B Stage22 SHALL issue actual StaffSession and enforce `staff_scope` at the **underlying owner service**, not just in U UI or I. Rights are per school → course → teaching_group/student/assessment/resource; scope is derived server-side, never by trusting a query-string ID.
- Teacher with `COURSE_READ` may list/read granted B Courses; `ASSESSMENT_READ` may read assigned Assessments; `GRADE_READ` may read only assigned Student's grades, `GRADE_SUBMIT` may first submit an authorized score (never correct); `SUBMISSION_READ`/`MANUAL_MARK` permit assigned submission workflows. Revocation and grant_epoch checked at request time. A content remains unavailable until S23.
- `getAcademicCourse` additionally allows narrowly scoped I ServiceToken `core.course.read`. The `admin_staff_or_service` class is a **one-of-three alternatives**; authorization result must additionally satisfy resource scope and activation gate.
- S9 I `/link/v1/evidence-bundles/{bundle_id}/validate` is ServiceToken-only with `link.evidence.validate` for a B Worker; I validates `aud`,`iss`,`sub`,`exp`,`jti`, allowed Job ID/purpose/binding, source version, freshness, and revocation **at every phase**. The evidence bundle `jti` may be revalidated for the **same** job; it cannot be used for a different job.
- All scopes, route/permission mapping and default deny require negative provider tests, not only OpenAPI policy text.
