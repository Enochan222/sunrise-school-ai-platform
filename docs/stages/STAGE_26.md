# Stage 26 [A] — Content Retention & Annual Archive Tools

**Release:** `R26` | **Exactly one owner:** `A` | **Technical prerequisites:** S2 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

A 做自己的年度教材封存、原檔／版本校驗與保留政策管理工具。

**完成後可親自試用：**Admin 選學年進行 A 教材 Archive、查保留規則、執行原檔 Hash／A-only Restore 核對。

### 2. 驗收：甚麼情況才可以標記完成？

- Archive 後 Notebook／Source/Version/Hash 仍可依政策查閱，普通功能無直接 Delete。
- 保留期／例外須有管理審查；A-only Backup/Restore／索引重建可驗。
- A-only Release 不改 B Student/Grade、I Binding 或 U Runtime。
**本期原有驗收設計：**`S26-AT01–S26-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 「年度 Housekeeping」不是定時清空；教材版權／法規／校方保留要求需先批准。
- A 來源封存後可能影響 S9 Evidence，需有 API 可識別版本已撤回／不可用。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S1 起已有最低安全與基本保留資訊，S26 只加治理 UI/進階程序，不能推遲早期備份。
- 不刪 B Grade Events 或學生紀錄，也不修改 I 整合契約。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S28 I 對帳要知道 A 來源封存狀態而非把 Archive 當刪除。
- 資料依法清除若涉及 B 學生紀錄須各自另行批准及單 Owner 流程。
**明確技術前置：**S2。**直接依賴本期的後續 Stage：**S28。

### 6. 暫定參考，暫時不作技術承諾

- 具體保留年期、Legal Hold、刪除申請責任及存儲成本待正式校方政策確認。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

A 後期教材年度封存、舊版保留、原檔校驗，S1 已先有基本 retention policy。

## Complete user flow

Content Admin→Archive Year→Inspect Versions/Hash→Backup/Restore。

## Data / Source of Truth

A archive_events/retention policy with legal holds, source_version lineage。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /vault/v1/admin/retention-review` (`reviewVaultRetention`; auth=admin) — A-only content year archive and retention
- `GET /vault/v1/health` (`getVaultHealth`; auth=service; scope=vault.health.read) — Read-only A health for I S28
- `GET /vault/v1/backup-status` (`getVaultBackupStatus`; auth=service; scope=vault.backup.status) — Read-only A last verified backup/restore manifest for I S28


## Not in this Stage

不刪 B 分數／學生。

## Real deployment and operations（原規劃參考與實測要求）

This is a A-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S26-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 學年封存 | Archive 保留 Notebook、Source、歷史版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 不誤刪 | 普通 UI 不能硬刪 Notebook；Retention 須政策批准 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 原檔校驗 | Source/Asset/File SHA 對帳可重跑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | A 獨立恢復 | A-only Restore Drill 與內容索引可恢復 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Admin 操作 | 有清楚保留與 Review 紀錄 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 分線 | B/I/U 版本完全不變 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 基本保留政策回歸 | 確認 S1 已有 Retention/License 初版；S26 只增加操作 UI 與年度封存 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S26-AT09 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | A 健康及備份受控讀取 | A 提供最小 ServiceToken-only /health 和 /backup-status 含可核對 snapshot/restore 狀態；不可暴露檔案或 Root Key | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON notebook archived field / Source updated/topics + A source files。
- **不應重造的部分：**自行重建整個 ON notebook 檔案存儲/備份引擎，或藉 archive 直接 hard-delete。
- **Sunrise 仍須自己交付的能力：**A retention policies, source version retention, hash/backup-status read APIs and archive UI。
- **當期風險／不可與前期撞：**S1 已需最小 backup+restore；來源版權政策先定，不能等到 S26。
- **後續 consumer／依賴影響：**S28 I health/backup view only through API; no DB access。
- **真實試用入口：**A local source-year archive & recovery report。正式 R26 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
