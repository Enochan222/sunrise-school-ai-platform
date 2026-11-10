# Stage 05 [U] — Sunrise Course & Content Admin Portal

**Release:** `R05` | **Exactly one owner:** `U` | **Technical prerequisites:** S4 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

交付初版 Sunrise Portal，只呈現已實作的 Course 與教材操作，所有資料仍在 A／B。

**完成後可親自試用：**Admin 從單一 Sunrise 入口進入 Course、教材列表、上載、搜尋、下載及 Link Status，錯誤有可理解的提示。

### 2. 驗收：甚麼情況才可以標記完成？

- Course/Content UI 真正呼叫 S4/B/A 受控 API，資料刷新後仍可見，無前端直接 DB 連線。
- 未推出的學生、Assessment、Grades、生成等功能不偽裝可用；空值／未連結／失敗可分辨。
- 實際登入／登出、響應式主要路徑、上載失敗、過期 Session 與 U-only 回退測試通過。
**本期原有驗收設計：**`S5-AT01–S5-AT12`（12 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 不可只改 Open Notebook CSS 當權限控制；後端政策仍由 A/B/I 負責。
- 不要在 U 內保存 ServiceToken、Gemini Key、任何 DB Root 憑證。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S4 已完成 API Link/代理，U 不可為了畫面方便直接讀 SurrealDB／Postgres。
- B 未有 Assessment/Grade，不能提前宣稱相關 Dashboard 可用。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S10 才加入 Generation Evidence UI；S21 才加入成績／分析；S24 才加入教師版面。
- UI 顯示的 Course ID、A Shell ID 和 Link Status 必須與 API 一致，避免使用者誤認資料已連結。
**明確技術前置：**S4。**直接依賴本期的後續 Stage：**S10, S24。

### 6. 暫定參考，暫時不作技術承諾

- 框架、顏色、版面細節可先做 Prototype；但可用流程、資料來源與權限不可留作 Mock。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

統一 Sunrise 初版 UI：Course List/Content Catalog、Upload/Search/Link Status，真正登入及安全 Session。

## Complete user flow

Admin Login→Sunrise Course→Link Status→I 的 Materials List/Upload/Search/Download；Archive 仍透過獨立 A 管理介面操作；Assessment/Grades 為 disabled「未推出」，錯誤顯示來源與 Retry。

## Data / Source of Truth

U transient UI only，無服務密鑰、無 DB SDK。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- 本期無新增 Owner API；只使用已部署版本的受控 API。


## Not in this Stage

不得在本期同時改 A/B/I；後續功能不會自動出現在 U。

## Real deployment and operations（原規劃參考與實測要求）

This is a U-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Frontend Gate:** A U release makes only the named UI features visible. It does not imply that future B/I features automatically appear. Additional U-only Stages must be registered before promising a unified UI for them.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S5-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 統一導覽 | R05 只可在同一介面操作 B Course、A 教材列表／上載／搜尋／下載及 Link 狀態；Assessment／Grades 尚未實作，須展示「未推出」，不假裝已有操作 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 獨立程式 | A/B/I Code/Image/Digest 完全不變；只部署 U | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 無直連 | 瀏覽器不接 SurrealDB/Postgres/service_role/raw Notebook | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 響應式 | 手機／平板／桌面主要工作流與提示無遮擋 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 失敗 UX | A 或 B 故障時顯示來源清楚、可重試，無假成功 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | UI 回歸 | Admin 原 A/B 功能仍可運作，E2E 檢查並保留版本 rollback | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Session Gate | Admin Browser Session 由後端驗證，過期、登出、CSRF 或未授權不得存取 A/B | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | U-only | U PR/Image 更新時 A/B/I Git SHA、schema hash、image digest 不變 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Responsive | 手機平板桌面交互、過期 Session、錯誤提示均可測 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 失敗 UX | B Course 未綁教材顯示清晰狀態，不會誤顯示 A Notebook 已建立 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Frontend coverage | R5 只表示 Course/Content Portal 已有；後續生成/成績/Teacher 對應新 U Stage | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S5-AT12 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON Next.js UI 的檔案表格/搜尋/Notebook context UI pattern；S4 API facades。
- **不應重造的部分：**另寫整套 A Source 搜尋或暴露 ON 全功能原生 UI。
- **Sunrise 仍須自己交付的能力：**Sunrise U Course / Materials / Upload / Search / Download／link-state／Session UX。
- **當期風險／不可與前期撞：**重用元件不能重用直接呼叫原生 ON API 的 Client；不預先顯示 Assessment / Grades。
- **後續 consumer／依賴影響：**S10 U 生成、S21 U 成績、S24 U 教師分別另出前端版本。
- **真實試用入口：**Sunrise U 真正可登入 Course / Content 入口。正式 R05 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
