# Stage 27 [B] — Academic Year Closing & Grade Retention

**Release:** `R27` | **Exactly one owner:** `B` | **Technical prerequisites:** S17, S18, S20, S25 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 建學年結算、成績事件保留／查核及封存報告，不影響 A 教材。

**完成後可親自試用：**System Admin 預覽未完成 Assessment，將學年按合法狀態關閉／封存，保留 Grade History 和稽核紀錄。

### 2. 驗收：甚麼情況才可以標記完成？

- 結算 Open→Closing→Closed→Archived 及失敗回退可測，不合法轉換拒絕。
- 正式 Grade Ledger/Correction/Audit 不會因 Closing 或 Weakness Keep2 被靜默刪除。
- B-only Restore、重新計分及結算報告可核；B 版本改動不觸及 A。
**本期原有驗收設計：**`S27-AT01–S27-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 真實學生記錄的保留期限、撤回及法律保留優先於省儲存成本。
- 已關閉學年仍可能有合法更正，應有受控補正流程而非無稽核 UPDATE。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不能改動 S26 A 教材封存狀態；B Academic Year Close 不會自動 Delete Notebook。
- S17 不可覆寫 Grade、S20 保留 Weakness 版本記憶原則仍有效。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S28 的跨服務檢查依賴 B 的學年狀態與對帳 API。
- 如未來支援跨年 Course Copy，需有獨立版本／資料治理設計而非直接共用原資料物件。
**明確技術前置：**S17, S18, S20, S25。**直接依賴本期的後續 Stage：**S28。

### 6. 暫定參考，暫時不作技術承諾

- 學校實際學年邊界、保留期與 Close/Reopen 權限需 Owner／校方決定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B 獨立學年結算、成績事件保存/留存政策及稽核報告。

## Complete user flow

Admin→Close Academic Year→Review Pending→Archive/Retention→Report。

## Data / Source of Truth

B academic_year_closure/grade_audit/retention_refs。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/academic-years/close` (`closeAcademicYear`; auth=admin) — B-only Grade Event preservation and closing
- `GET /core/v1/health` (`getCoreHealth`; auth=service; scope=core.health.read) — Read-only B health for I S28
- `GET /core/v1/backup-status` (`getCoreBackupStatus`; auth=service; scope=core.backup.status) — Read-only B backup status for I S28


## Not in this Stage

不清除 A 教材或更改 A Schema。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S27-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 結算狀態 | Open→Closing→Closed→Archived，非法轉換拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 保留成績 | Grade Events/Corrections 不因 Keep2／Year Close 消失 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 政策 | Legal Hold/Retention 未核准不可硬刪 PII | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B 恢復 | 學年結算與稽核可 B-only Restore/Rebuild | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 操作證據 | 每個 Close/Archive 有 Actor/Reason/Time | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 分線 | A/I/U 不修改，內容 Vault 不因此刪除 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 影響範圍 | B Year Close 不可直接 Delete A Notebook 或 Grade Ledger Source | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S27-AT09 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | B 健康及備份受控讀取 | B 提供最小 ServiceToken-only /health 和 /backup-status 含 migration/snapshot/restore 時點；不能透出學生/成績內容 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**B grade ledger/projections/assessment state, Postgres backup tools。
- **不應重造的部分：**從 B 發命令刪 A notebook / 藉 closing 清除 Grade Events。
- **Sunrise 仍須自己交付的能力：**B year-close transition, pending assessment checks, grade audit/retention, health/backup service status。
- **當期風險／不可與前期撞：**S18 pending marking/S20 weakness stale scope 需進入 Closing Gate；不同 A 年度封存互不觸發。
- **後續 consumer／依賴影響：**S28 I dashboard consumes owner-only read status。
- **真實試用入口：**B local year-close and retention admin console。正式 R27 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
