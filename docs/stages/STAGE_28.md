# Stage 28 [I] — Cross-service Health/Restore Dashboard

**Release:** `R28` | **Exactly one owner:** `I` | **Technical prerequisites:** S4, S26, S27 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

I 提供跨服務狀態與異常 Dashboard，但不取代兩套庫各自的還原工具。

**完成後可親自試用：**管理員查看 A/B Healthy、Course Binding、Source Version、Backup/Restore 報告及異常告警，能清楚定位哪邊需處理。

### 2. 驗收：甚麼情況才可以標記完成？

- 以既有 API 偵測缺 B Binding、孤兒 A Notebook、Source Hash/版本差異、Restore 時點不一致。
- 不一致就標示異常／阻止誤判 READY；I 不直接執行 SurrealQL／SQL/DB Restore。
- S4 原有核心 Reconcile/Retry 仍可用，I-only Dashboard 升級可回退。
**本期原有驗收設計：**`S28-AT01–S28-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Dashboard 是診斷工具，不能偷偷直接執行未獲批准的刪除／自動修復資料庫操作。
- 狀態顯示要標明資料新鮮度及監控缺口，不能把最後一次成功當即時健康。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不能把 S4 已必需的 Saga Recovery 推遲到 S28；不得修改 S26 A/S27 B 的治理資料模型。
- I 沒有 A/B DB Root Secret，不能藉方便監控加 DB DSN。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- 作為後續運維平台的 API-only 基線，異常跨 Owner 修復仍應拆 A-only/B-only 版本。
- Retention/PII 變更必須遵守 S25–S27 的批准與證據，不由 I 自行決定。
**明確技術前置：**S4, S26, S27。**直接依賴本期的後續 Stage：**—。

### 6. 暫定參考，暫時不作技術承諾

- 監控平台、報警閾值、Dashboard 技術和日誌保留細節在部署後根據真實故障模式決定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

I 顯示 A/B API 對帳和 Restore 狀態／告警；S4 已有最低必要 Core Recovery，本期只加管理工具。

## Complete user flow

Admin→Cross-service Health→Compare A Manifest/B Binding→Drill Result/Exceptions→Follow-up。

## Data / Source of Truth

I only logs/reports, durable operator evidence through B Audit API.

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `GET /link/v1/reconciliation-dashboard` (`getReconciliationDashboard`; auth=admin) — Additional health/history UI over S4 core recovery API


## Not in this Stage

不把底層 Restore、資料庫操作搬入 I。

## Real deployment and operations（原規劃參考與實測要求）

This is a I-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S28-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 一致性 | I 可列出每個 B Course 對應唯一 A Shell/Notebook/Source Hash | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 異常 | 找出孤兒 A Notebook、缺 B Binding、Duplicate Key 與未對齊版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 失敗封閉 | 不明所有者的教材拒絕進出卷 Context | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 獨立復原 | A-only、B-only Restore 各自有證據，I 只讀 Manifest 並交叉核對 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 界線 | I 不存任何 A/B DB Credentials，不修改 DB Schema 或直接 Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 後向相容 | A/B/U 版本不動，完整平台回歸通過 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | S4 核心已存在 | 此 Stage 只加 Dashboard/Alert History，不在此期首次補救遺失 Binding 恢復能力 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S28-AT09 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | I Dashboard 使用前置 API | I 只使用 S26 A 與 S27 B Health/Backup/Manifest Service API，不使用 SQL/SurrealDB 或 DB Restore 權限 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S4 I core reconcile + S26 A and S27 B health/backups APIs。
- **不應重造的部分：**新增 I 管理 DB 用於跨服務 SQL、代替 A/B 自己 Restore。
- **Sunrise 仍須自己交付的能力：**I read-only health/version/backup manifest dashboards and mismatch/quarantine alerts。
- **當期風險／不可與前期撞：**A/B 各自 restore+cross snapshot discrepancy impossible to hide, I no DB credentials。
- **後續 consumer／依賴影響：**運維後續以此基線做事件響應/告警，不改兩邊 backup。
- **真實試用入口：**I 唯讀管理員健康狀態、備份狀態及跨服務異常對帳 Dashboard。正式 R28 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
