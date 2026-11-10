# Stage 03 [B] — Independent Academic Course & B Contract Freeze

**Release:** `R03` | **Exactly one owner:** `B` | **Technical prerequisites:** S0 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

交付可獨立運行的 B Course Registry，包含 School／Academic Year／Subject／Grade／Teaching Group 及可測的 Binding／Operation 合約。

**完成後可親自試用：**Admin 只用 B 就能建立、檢視、封存正式課程；未接 A 的課程清楚顯示 CONTENT_UNLINKED。

### 2. 驗收：甚麼情況才可以標記完成？

- B PostgreSQL／Supabase 與 A 使用不同帳密、網絡、備份；B 單獨完成課程 CRUD／Restore。
- Course／Teaching Group/Academic Year 的唯一性和基本關係可核查；未連結亦能正常使用。
- Reserve／Finalize／Operation 狀態 API 有真交易、冪等與唯一約束的 Provider Test；不實際調 A。
**本期原有驗收設計：**`S3-AT01–S3-AT17`（17 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Binding Reservation 不可在一半成功時宣稱 ACTIVE；要預留 Crash／Retry 狀態。
- S4 會呼叫 B API，但 B Service Token 不可等同 root 或前端 Admin 權限。
### 4. 不可以與之前已完成的功能撞／互相破壞

- B Course 是正式學校業務物件，不能把 S1 A 的 Content Shell 當成同一資料表。
- 不部署 I、不自動新增 A Notebook；保持 CONTENT_UNLINKED 直至 S4。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S4 直接依賴 B Reserve／Finalize／Read-back 與 Operation log，S22 未來 IAM 要有 Actor/Scope 預留。
- S15 Student 及 S16 Assessment 會引用 Course/Teaching Group，後期改主鍵成本很高。
**明確技術前置：**S0。**直接依賴本期的後續 Stage：**S4, S6, S7, S15, S22。

### 6. 暫定參考，暫時不作技術承諾

- Supabase 方案、B 的細分 Schema／交易流程與 Course 粒度先以候選合約表示，實測前不能宣稱正式凍結。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

獨立 B PostgreSQL/Supabase 有 School/Subject/AcademicYear/Grade/Course/Teaching Group，課程保持 CONTENT_UNLINKED；有原子 Reserve/Finalize 和 Operation Log API。

## Complete user flow

Admin→建立年度/科目/課程→綁定多個 Class/Teaching Group→看到 CONTENT_UNLINKED→Archive/Restore B。

## Data / Source of Truth

B school_id, subject_id, academic_year_id, grade, curriculum_stream, course_id, class_id, actor/scope/audit, binding intents and op log。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `GET /core/v1/course-bindings/{course_id}` (`getCourseBinding`; auth=admin_or_service; scope=core.binding.read) — B-owned binding version/state/readback
- `GET /core/v1/course-operations` (`listPendingCourseOperations`; auth=service; scope=core.operation.read) — Durable resumable operations for I worker
- `POST /core/v1/course-operations/reserve` (`reserveCourseOperation`; auth=admin_or_service; scope=core.course.reserve) — Atomic B Course create-or-adopt + operation reservation
- `GET /core/v1/course-operations/{operation_id}` (`getCourseOperation`; auth=service; scope=core.operation.read) — Idempotency/status read-back
- `POST /core/v1/course-operations/{operation_id}/finalize` (`finalizeCourseOperation`; auth=service; scope=core.operation.finalize) — Atomic UNIQUE binding finalize after dual API verification
- `POST /core/v1/course-operations/{operation_id}/quarantine` (`quarantineCourseOperation`; auth=service; scope=core.operation.quarantine) — Record conflict/failed verification, never delete A
- `GET /core/v1/courses` (`listAcademicCourses`; auth=admin_or_staff) — B-only course list
- `POST /core/v1/courses` (`createAcademicCourse`; auth=admin) — B-only independent formal Course, CONTENT_UNLINKED
- `GET /core/v1/courses/{course_id}` (`getAcademicCourse`; auth=admin_staff_or_service; scope=core.course.read) — B-only single academic course
- `POST /core/v1/courses/{course_id}/teaching-groups` (`createTeachingGroup`; auth=admin) — S3 TeachingGroup belongs exactly one B Course
- `GET /core/v1/courses/{course_id}/teaching-groups` (`listTeachingGroups`; auth=admin_or_staff) — S3 Teaching Groups; staff scope only activated at S22


## Not in this Stage

不調 A、不同時部署 I、不要求已有 Notebook。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Contract Freeze:** 需在本期提交可驗證 OpenAPI JSON、Context/Idempotency Fixture、Consumer Contract Test。不得一邊做 I 一邊修改 A/B。

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S3-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B-only 實例 | B Postgres 不共享 A Storage、Credentials、Docker Volume 或 Backup | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 課程管理 | Admin 可在獨立 B 畫面建立、列示、封存 Course | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 未連結清晰 | 未接 A 時狀態 CONTENT_UNLINKED；不假裝 Notebook 已建立 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 引用預留 | B Binding Reserve/Finalize/Unique 約束用 Mock A reference 測試；不呼叫實際 A | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B Restore | 隔離環境備份還原 B Course + audit | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 最小權限 | B 不存 A Root Credential；B Web 禁用 Service Role | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回歸 | S1、S2 A 發佈版本完全不變；B-only 部署可測可回退 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 原子 Reserve | CREATE_NEW 以單一 B Transaction 建 Course+Operation，任一失敗雙雙回滾 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 既有 Reserve | ADOPT_EXISTING 只鎖已存在 Course，不再 Create 第二個 Course | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Binder 唯一 | 對 course_id、A shell ID、notebook ID 的 UNIQUE constraint 與 null/status 策略可測 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Course 粒度 | P4A/P4B 可共享同學年/年級/科目/教材流 Course，但不因此共享 Source 跨不同 Course | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT12 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Contract Freeze | B reserve/finalize/status/list API 有 machine-readable OpenAPI、Consumer Fixtures、Idempotency 錯 body 回 409 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT13 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | IAM 預留 | B school_id, course_id, subject, actor_id, created_by, access_scope, audit_actor 欄位及未來 Grant relation 有規格 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT14 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S3-AT15 | 已部署該 Stage 相應服務與專用測試資料 | 預留交易與服務權限正向與越權／異常負面測試 | B reserve 必須在一個 DB transaction 記錄 Course/Operation，I 只可用 narrow ServiceToken 調用，並在重試時維持唯一綁定 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S3-AT16 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | B Course／Group 粒度 | Course 保持 grade+curriculum_stream，不設 class_id；同 Course 多 TeachingGroup 皆由 B API 可建立及查詢 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |
| S3-AT17 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 新 Staff 角色前置鍵 | School/Course/TeachingGroup/Actor 欄位及 B 權限界面預留，S22 不需改 Course 身份 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**PostgreSQL/Supabase 原生 database/Auth capabilities（非 Open Notebook）。
- **不應重造的部分：**透過 SurrealDB 模擬校務 SQL／以 ON notebook 當 School Course。
- **Sunrise 仍須自己交付的能力：**B School/Subject/Year/Course/TeachingGroup、UNLINKED 狀態、原子 Reserve/Finalize/operation log、B-only Restore、服務端 Admin Session Issuer。
- **當期風險／不可與前期撞：**Course 不等於 Class；一個 Course 多 TeachingGroups；即使尚未安裝 A 也可用 B Admin CRUD。
- **後續 consumer／依賴影響：**S4 不得依賴新 B API；S6/15/22 永遠保留 Course grain。
- **真實試用入口：**B 本地受保護的 Course / TeachingGroup CRUD 管理頁與恢復報告。正式 R03 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

**候選現成依賴（須本期驗證）：**Supabase Auth／PostgreSQL FK+RLS 可沿用作基礎；但 Course/TeachingGroup 與服務授權為 Sunrise B 專有，需獨立權限和 transaction test。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
