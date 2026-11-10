# Stage 23 [I] — Teacher Read-only Course Content

**Release:** `R23` | **Exactly one owner:** `I` | **Technical prerequisites:** S4, S22 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

I 提供 Teacher 唯讀的課程教材搜尋／下載，查 B Staff Grant 後才向 A 取數。

**完成後可親自試用：**授權教師只讀其班級課程的教材；取消 Grant 後即使保存舊連結亦無法搜尋／下載。

### 2. 驗收：甚麼情況才可以標記完成？

- StaffSession 必須先經 B Grant API 驗證，且查 A 每個 Source/Download 仍受 Scope 限制。
- 教師所有 A Upload/Edit/Create/Delete/Link 請求均拒絕，跨課程、猜 ID、撤銷後即時失效。
- I-only 新增讀取 API／授權邏輯，A/B Runtime SHA、Schema、憑證及部署不變。
**本期原有驗收設計：**`S23-AT01–S23-AT13`（13 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 快取 URL／瀏覽器檔案／既有 Stream 亦需考慮撤銷與過期的影響。
- S9 的 Admin Evidence Scope 不可直接變成教師權限。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 依賴 S22 B Grant 查核與 S4 Course Binding；不能用 AdminToken 代表 Teacher。
- 保留 S1 原生 A raw API 私有化，教師不能繞過 I 直接登入 A 管理端。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S24 將呈現教師 UI，權限決策必須由 I/B 服務端作出。
- S25 實名學生資料不應因教材唯讀 Token 而被授權瀏覽。
**明確技術前置：**S4, S22。**直接依賴本期的後續 Stage：**S24, S25。

### 6. 暫定參考，暫時不作技術承諾

- Token 壽命、快取失效策略和授權聲明格式待真正 IAM Provider 測試確認。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

I 查 B Course Grant，以 A 只讀 API 搜尋/下載已授權教材；Revocation 即時拒絕。

## Complete user flow

Teacher StaffSession→I Verify Grant via B private ServiceToken→A Scoped Search/Download→Revoke→立即拒絕。

## Data / Source of Truth

I 不另建身份資料庫、token cache 必須限時/版本驗證。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `GET /link/v1/teacher/content` (`getTeacherContent`; auth=staff) — Read-only A after live B Grant check
- `GET /link/v1/teacher/courses/{course_id}/materials/{material_id}/download` (`downloadTeacherContent`; auth=staff) — Teacher read-only binary download with B grant epoch recheck
- `POST /link/v1/teacher/courses/{course_id}/search` (`searchTeacherContent`; auth=staff) — Teacher scoped Search requires B grant check and A owner-filtered service API


## Not in this Stage

不允許教師 Create/Delete/Link/Upload/Edit A。

## Real deployment and operations（原規劃參考與實測要求）

This is a I-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S23-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 教師只讀 | Teacher 只能查看所屬 B Course 的 A Source | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 跨課程負面 | 偽造 Course/Notebook/Source/Download ID 返回拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 寫入禁止 | Teacher 不能用 I/A raw API upload/edit/create/delete/link | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 權限撤銷 | 撤銷 B Grant 後 I 新請求即時拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | I-only 修改 | 不改 B RBAC Schema／A Content Schema/Code | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 審計與回歸 | 授權 Trace/拒絕紀錄清晰、原 Admin 功能不退步 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 即時撤銷 | Teacher Permission 撤銷後舊 Session/Cache/下載連結不能繼續授權 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 讀取邊界 | 跨 Course／偽造 Notebook/Source ID 或上游直接存取全部禁止 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S23-AT10 | 已部署該 Stage 相應服務與專用測試資料 | Teacher 與 Service 分離正向與越權／異常負面測試 | 教師只用 StaffSession 呼叫 I，I 使用獨立窄權 B Grant ServiceToken 與 A 唯讀 ServiceToken；拒絕 AdminSession 冒充 Teacher | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S23-AT11 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | 教師搜尋 API，包含偽造範圍／失敗路徑 | StaffSession 按 Course Grant 向 I 搜尋 A 教材；過期或撤銷、偽造 Course/Source 必須拒絕 | HTTP/schema/provider test + Commit SHA + Owner UAT |
| S23-AT12 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | 教師下載 API，包含偽造範圍／失敗路徑 | 教師透過 I 下載二進位教材檔案；I 逐次驗證 B grant epoch + A Source Owner，不能用 AdminToken 代替 | HTTP/schema/provider test + Commit SHA + Owner UAT |
| S23-AT13 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 教師授權端到端一致 | S23 I只讀 A，S22 B 的 Staff Grant 每次查核；舊 Stream/下載/快取 URL 過期及撤權測試 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S4 I Binding, S22 B grants, S2 A search/download API。
- **不應重造的部分：**在 A 原生 API 開 teacher password 或在 I 直接查 B 資料庫。
- **Sunrise 仍須自己交付的能力：**I StaffSession→B service Grant lookup→A scoped read only（含 search/download）。
- **當期風險／不可與前期撞：**舊 token/cache 撤銷失效；Cross School/Course/Group 需要負面測試。
- **後續 consumer／依賴影響：**S24 U teacher content UI/S25 real PII preconditions。
- **真實試用入口：**I read-only teacher API console。正式 R23 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
