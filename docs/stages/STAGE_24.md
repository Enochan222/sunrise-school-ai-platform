# Stage 24 [U] — Sunrise Teacher Portal UI

**Release:** `R24` | **Exactly one owner:** `U` | **Technical prerequisites:** S5, S21, S23 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

U 提供可登入的 Teacher Portal，與 Admin 介面分開，所有內容權限沿用 B/I。

**完成後可親自試用：**Teacher 登入只見自己課程及唯讀教材；Admin 仍可做原本管理，撤權後介面同步消失。

### 2. 驗收：甚麼情況才可以標記完成？

- 教師頁的 Course/Materials 搜尋、下載及唯讀顯示可真實使用。
- 直接猜 URL 或已撤權時 UI 不能偽裝授權；Server API 本身亦應拒絕。
- U-only 部署，A/B/I 的身份、來源和 Grant 邏輯完全未被改動。
**本期原有驗收設計：**`S24-AT01–S24-AT06`（6 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 前端隱藏按鈕不是授權；根據 API 授權結果處理導航與錯誤。
- 不要將教師可編輯教材誤認為學校已批准操作；唯讀是硬規則。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S5/S10/S21 的 Admin 入口及操作仍可用。
- S23 I 已處理授權，U 不另建一套 Role Table。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S25 可加入實名學生資料頁，但需校方批准及完整權限 Gate，不能提前開放。
- 教學班／課程編組改動需沿用 B Course TeachingGroup 而不是自建。
**明確技術前置：**S5, S21, S23。**直接依賴本期的後續 Stage：**S25。

### 6. 暫定參考，暫時不作技術承諾

- 界面導航／Mobile Layout 可先試用再調整，不能改變來源及授權責任。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

新增 Teacher 與 Admin 分開的 Sunrise UI 導覽、資料來源及只讀教材頁，維持後端不變。

## Complete user flow

Teacher Login→Assigned Course→Published Content Read→B Teaching/Marking Tools。

## Data / Source of Truth

U-only views/UX, cache invalidation on revoked grants。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- 本期無新增 Owner API；只使用已部署版本的受控 API。


## Not in this Stage

不在本期修改 IAM、I 授權或 A。

## Real deployment and operations（原規劃參考與實測要求）

This is a U-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Frontend Gate:** A U release makes only the named UI features visible. It does not imply that future B/I features automatically appear. Additional U-only Stages must be registered before promising a unified UI for them.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S24-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | U-only Teacher Gate | 已獲授權教師登入可看 A 教材唯讀；U 不接觸原生 Admin Password | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S24-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 跨課程 UI | 沒有授權的 Course 及 Source 被隱藏且 API 同時拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S24-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 撤銷 UI | Grant revoke 後舊 View/Download Cache 不能繼續使用 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S24-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S24-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S24-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S5 U Course, S21 U Assessment workspace + S23 I teacher read。
- **不應重造的部分：**重寫 A Notebook page，或在 U 幫 B 補角色授權。
- **Sunrise 仍須自己交付的能力：**U Teacher dashboard/read-only materials＋B permitted assignment/marking UI。
- **當期風險／不可與前期撞：**客戶端隱藏按鈕不構成安全控制，B/I server-side 仍須授權；無權時不能誤顯資料。
- **後續 consumer／依賴影響：**S25 real student readiness / staff onboarding workflow。
- **真實試用入口：**Sunrise U 教師課程／教材／被授權 B 學務功能操作入口。正式 R24 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
