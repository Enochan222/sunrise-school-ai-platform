# Stage 22 [B] — Staff IAM, Grants & B Authorization

**Release:** `R22` | **Exactly one owner:** `B` | **Technical prerequisites:** S3, S17, S18, S20 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 由單 Admin 擴展至 Staff/Teacher/System Admin 身份與課程授權，只開放 B 資料。

**完成後可親自試用：**System Admin 發出邀請、分配 Course／Teaching Group Grant；Teacher 登入後只能使用所屬 B 功能。

### 2. 驗收：甚麼情況才可以標記完成？

- 登入／停用／Grant／撤銷實際生效；跨 Course B API read/export/write 一律被拒絕。
- Teacher 不能直接改正式分數；歷史唯一 Admin 操作在新 Actor/Role 模型下可核。
- B 向 I 提供最小化 Staff Grant 查核 API；本期不開 A 教材存取。
**本期原有驗收設計：**`S22-AT01–S22-AT12`（12 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- StaffSession、ServiceToken 不可混用；前端不能得到 B service_role。
- 遷移早期單 Admin Actor 資料時需保留舊 Audit，不得改寫事件作者。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S1–S21 單 Admin 模式既有業務操作不能因增加身份而無故失效。
- S23 I Teacher A Content 功能未做完之前，不向教師顯示 A 教材可讀。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S23 必須驗證實際 B Grants／Revocation，S24 UI 再公開教師教材介面。
- S25 真實學生准入還依賴更嚴格的 Course／Class 授權與校方資料政策。
**明確技術前置：**S3, S17, S18, S20。**直接依賴本期的後續 Stage：**S23, S25。

### 6. 暫定參考，暫時不作技術承諾

- OIDC 供應商、教師身份資料、Class 權限粒度仍需 Owner 批准；不能直接將 B RLS 搬入 A SurrealDB。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B 建教師/Content Admin/System Admin 身份、B Course/班級 Grants、撤銷與 Audit；不開放 A 教材。

## Complete user flow

System Admin→Invite Teacher→Assign B Course/Class→Teacher B read/write permitted workflows; staff self read-grants via StaffSession and I via separate service scope→Revoke。

## Data / Source of Truth

B identity/users/roles/grants + actor_id/access_scope from S3；migrate 既有 Admin actor。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/admin/grants` (`grantStaffCourse`; auth=admin) — System admin Course/Class grant
- `POST /core/v1/admin/grants/revoke` (`revokeStaffGrant`; auth=admin) — Revoke and bump grant epoch
- `GET /core/v1/me/permissions` (`getUserGrants`; auth=staff) — Signed staff/courses grant and revocation epoch
- `GET /core/v1/staff/{staff_id}/permissions` (`getStaffPermissionsService`; auth=service; scope=core.grant.check) — Private I-to-B staff course grant / revocation lookup


## Not in this Stage

教師不能修改學校教材，A 功能留 I Stage 23。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S22-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 多人身份 | 教師及不同管理角色可登入且退出／停用生效 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B 權限 | 跨 Course B API read/write/export 被阻止 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 成績 | Teacher 不可更新已提交 Grade，System Admin 可追加更正 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | A 尚未開放 | Teacher UI 不顯示可用 Content Vault，無任何 A token | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 服務角色 | B Service Secret 未暴露前端；RLS/Views/Functions 經檢查 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回歸 | Single Admin 歷史數據與工作流保留 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 舊 Actor migration | S1/S3 預留 admin actor/scope，S22 首次多用戶 migration 前後所有事件歸屬不丟失 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 權限撤銷 | B Course grant revoke 產生 version/epoch 並讓 I 可用 API 重新驗證 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S22-AT10 | 已部署該 Stage 相應服務與專用測試資料 | 個別教師授權服務 API正向與越權／異常負面測試 | B 以 ServiceToken + `core.grant.check` 對指定 staff_id+Course 實際核驗 Grant/epoch，教師不能取得該服務憑證 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S22-AT11 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Teacher 真實業務操作 | 教師可用 StaffSession 讀獲授權 Course、TeachingGroup、Synthetic Roster、Assessment、Grades、Submissions；只可授權 Submit/Manual Mark，不可更正正式分數 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |
| S22-AT12 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Teacher 撤權與分組負面 | 停用/撤權時，舊 Token/舊列表/跨 Course/Group/Student 被 B 每一個業務 API 拒絕；無 AdminToken | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**B existing Supabase Auth/RLS patterns + early school/course/group model。
- **不應重造的部分：**重造 A multi-user ACL 或讓教師共用 ON admin key。
- **Sunrise 仍須自己交付的能力：**B StaffSession/MFA(按政策)/invitation/grants + backend resource checks, revoke epoch。
- **當期風險／不可與前期撞：**教師需有真實可用 B operations，不只查自身 Grant；不能自動授權 A。
- **後續 consumer／依賴影響：**S23 I Staff course-level read；S24 U staff portal；S25 real PII gate。
- **真實試用入口：**B teacher sign-in + authorized course/grade/marking actions。正式 R22 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

**候選現成依賴（須本期驗證）：**Supabase Auth／RLS 可以提供登入與基礎隔離，不代表已自動具備 Sunrise 的 Course／TeachingGroup／Student 權限；須在 B endpoint 實測。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
