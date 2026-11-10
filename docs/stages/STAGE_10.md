# Stage 10 [U] — Sunrise Generation & Evidence Workspace

**Release:** `R10` | **Exactly one owner:** `U` | **Technical prerequisites:** S5, S9 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

U 顯示完整出卷任務與 Evidence 操作流程，不改生成或檢索後端。

**完成後可親自試用：**Admin 在 Sunrise 選 Blueprint、生成、勾選或取消教材 Evidence、查看 Queue 狀態、引用和人工批准。

### 2. 驗收：甚麼情況才可以標記完成？

- U 按 S8/S9 API 顯示 Job／Draft／Evidence 狀態，不使用假進度。
- ON／OFF 切換正確影響送出請求，Evidence 失效與 Provider 錯誤清楚可讀。
- U-only 更新，既有 S5 Course/Materials 仍可用；無 Key／Token／DB 直接曝光。
**本期原有驗收設計：**`S10-AT01–S10-AT07`（7 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 不能為了 UI 方便將敏感教材片段永久寫入 LocalStorage／客戶端 log。
- 不能將 AI Draft 顯示成正式已批准 Paper。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S5 Portal、S8 Queue、S9 Evidence 已可用，U 不可重寫其邏輯。
- B-only 不用 A 的出卷能力仍要保留。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S11–S14 紙本 PDF 及四科細節會增加 UI，但要按獨立 U Stage/Owner 安排，不能在 B Stage 偷改 U。
- S21 將擴充成績分析 UI，不應提前塞入本版。
**明確技術前置：**S5, S9。**直接依賴本期的後續 Stage：**S21。

### 6. 暫定參考，暫時不作技術承諾

- 頁面佈局、進度視覺化、模型選擇控件形式可後定；資料與狀態真實性是硬要求。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

Sunrise UI 可以提交 B Generation Job，開關 I Evidence，見來源、AI 失敗及人工批准；不要求 B/I 調整程式。

## Complete user flow

Admin→Sunrise Generation→Prompt Blueprint→Use Content Checkbox→Progress→Citation→Approve/Reject。

## Data / Source of Truth

U transient view of B jobs/I results only；不得永久儲存第三方 AI Key。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- 本期無新增 Owner API；只使用已部署版本的受控 API。


## Not in this Stage

只改 U；B local generation interface 在 R8 已可試用。

## Real deployment and operations（原規劃參考與實測要求）

This is a U-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Frontend Gate:** A U release makes only the named UI features visible. It does not imply that future B/I features automatically appear. Additional U-only Stages must be registered before promising a unified UI for them.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S10-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Evidence Toggle | Use OFF 不觸發 A；Use ON 明確顯示 A 原教材出處與引用版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | U-only | A/B/I Image/Schema 完全不變，Browser 不持 Gemini Key | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | UI 狀態 | Queue Pending/Retry/Failure 真實顯示和錯誤回復 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Session | 使用者登出及舊 Session 輸入失效 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S10-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON Chat/context/Ask UI 可作交互模式參考；S8/B S9/I APIs。
- **不應重造的部分：**把 A Chat workflow 當 B 出卷儲存或在 U 寫生成業務規則。
- **Sunrise 仍須自己交付的能力：**Sunrise U Task/Blueprint/Evidence/Approval 純展示/操作入口。
- **當期風險／不可與前期撞：**U 不持 provider secret；S9 A 斷線要明確提示，而非假成功或全庫 fallback。
- **後續 consumer／依賴影響：**後續四科試卷 UI 只可在各自 B-local Console 或另開 U-only stage 呈現。
- **真實試用入口：**Sunrise U 可提交任務、檢視 Draft 及引用。正式 R10 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
