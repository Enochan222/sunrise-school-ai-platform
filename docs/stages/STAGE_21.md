# Stage 21 [U] — Sunrise Assessment/Analytics Workspace

**Release:** `R21` | **Exactly one owner:** `U` | **Technical prerequisites:** S10, S17, S18, S19, S20 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

U 增加可用的名冊、Assessment、Grade History、批改和 Weakness 操作入口，但不改 B 邏輯。

**完成後可親自試用：**Admin 由 Sunrise UI 查看模擬學生、提交／查成績歷史、查 AI／人工批改結果和 Keep／Discard 弱項。

### 2. 驗收：甚麼情況才可以標記完成？

- 頁面真正讀寫已發布 B API，顯示 Score Draft／正式分數／Correction History 的差異。
- Weakness 只能選擇 B 返回的 VALID ACTIVE，Stale/Retired 狀態清楚。
- U-only Responsive/Session/Empty/Error/E2E 回歸通過，沒有前端硬編成績或直連 DB。
**本期原有驗收設計：**`S21-AT01–S21-AT07`（7 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- S21 只會提供合成學生工作台，不能誤導操作者以為系統已獲真實個資批准。
- AI Marking 建議和最終 Grade 必須在畫面明確分開。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S5 原有 Course／Content 及 S10 Generation UI 不得被新頁面破壞。
- U 不修改 B 成績規則、S17 事件或 S20 Keep2 查詢。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S24 將加入教師可用版面與 B/I 授權；S25 才可能載入真實學生。
- 分權來臨時既有 UI route 要能隱藏未授權功能，Server 仍需實際拒絕。
**明確技術前置：**S10, S17, S18, S19, S20。**直接依賴本期的後續 Stage：**S24。

### 6. 暫定參考，暫時不作技術承諾

- 圖表風格、表單佈局及互動細節可以經試用修改；不得把 Mock 當最終有效數據。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

Sunrise U 加入合成學生、成績歷史、批改及 Weakness 操作入口；前端版本獨立試用。

## Complete user flow

Admin→Sunrise→Synthetic Student/Grades→Analytics Preview/Keep→Draft Paper。

## Data / Source of Truth

U-only frontend state；所有資料由 B/I API 提供。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- 本期無新增 Owner API；只使用已部署版本的受控 API。


## Not in this Stage

只修改 U；其他 Owner Runtime Digest 不變。

## Real deployment and operations（原規劃參考與實測要求）

This is a U-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Frontend Gate:** A U release makes only the named UI features visible. It does not imply that future B/I features automatically appear. Additional U-only Stages must be registered before promising a unified UI for them.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S21-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | U-only Regression | U 使用已發布 B 資料/API，B/I/A 不作同 Stage 修改 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 成績顯示 | 有真實 Synthetic Draft/Submitted/Correction History 的畫面 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Weakness UI | Keep/Discard，兩版本和 STALE 狀態可見 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S21-AT07 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | U UI 每種弱項狀態可用 | 從 B S20 API 真實取得 Candidate/Keep/Discard/STALE/RETIRED，無需在 U Stage 修改 B | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S10 U Generation + S15–20 B Existing APIs。
- **不應重造的部分：**U 直接 SQL；為了 UI 方便偷開新 B endpoints。
- **Sunrise 仍須自己交付的能力：**Sunrise U Roster/Assessment/Grade History/manual+AI Marking/Weakness Dashboard。
- **當期風險／不可與前期撞：**S18 S19 要成為明確 Technical prerequisites；不能用未發布的 B Marking read APIs。
- **後續 consumer／依賴影響：**S24 Teacher-specific extension 重用此 UI 頁與針對 Staff scope 逐項禁權。
- **真實試用入口：**Sunrise U 合成學生成績、改卷結果及弱項分析完整工作台。正式 R21 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
