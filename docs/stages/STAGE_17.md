# Stage 17 [B] — Append-only Grade Events & Corrections

**Release:** `R17` | **Exactly one owner:** `B` | **Technical prerequisites:** S16 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 將 Draft 正式提交為不可覆寫 Grade Event，唯一 Admin 只能追加可稽核更正。

**完成後可親自試用：**Admin 提交一次模擬分數後，舊紀錄鎖定；用更正原因建立第二筆事件，歷史與最新成績都可查。

### 2. 驗收：甚麼情況才可以標記完成？

- 同請求重試不能重覆提交；正常 DB/API UPDATE/DELETE 既有 Grade Event 必須拒絕。
- 更正包含 Actor、Reason、Expected Revision；並發修改時拒絕衝突。
- Current Projection 由 Event Replay 可獨立重算，還原後歷史事件完整。
**本期原有驗收設計：**`S17-AT01–S17-AT12`（12 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 「不可修改」是有權限的產品／DB 操作限制，不可宣稱物理上無人能更改 DB Root。
- 避免把分析 Snapshot 當成正式分數或錯把 CAS 同 Idempotency 混用。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S16 Draft 仍可編輯，但提交後不能以 Draft UI 覆蓋 Ledger。
- 沒有真實學生資料；不能修改 A、I、U。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S18 Manual Marking、S19 AI Suggest 只能經 Ledger API 發分；S20 Weakness 必須隨更正失效。
- S22 多帳戶來到時，舊 Admin 事件要有足夠 Actor/Role 來源以便遷移。
**明確技術前置：**S16。**直接依賴本期的後續 Stage：**S18, S20, S21, S22, S27。

### 6. 暫定參考，暫時不作技術承諾

- DB 觸發器／稽核簽章／保留政策實作細節待正式 B DB 權限測試確認。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

分數提交後舊事件不可修改；System Admin/唯一 Admin 只能追加帶原因／Actor／Revision 的更正。

## Complete user flow

Admin→Validate Draft→Submit→Grade Event→Correction Request→Append Correction→Projection Rebuild。

## Data / Source of Truth

B immutable grade_events、audit、revision、current_projection derived。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/admin/grade-corrections` (`correctGrade`; auth=admin) — Revision CAS, reason, actor, timestamp, immutable history
- `POST /core/v1/grades/submit` (`submitGrade`; auth=admin_or_staff) — APPEND once, DB role forbids UPDATE/DELETE
- `GET /core/v1/grades/{grade_key}/current` (`getCurrentGrade`; auth=admin_or_staff) — Read current projection of immutable Grade Ledger
- `GET /core/v1/grades/{grade_key}/history` (`getGradeHistory`; auth=admin_or_staff) — Read append-only GradeEvent history and correction audit


## Not in this Stage

不直接 UPDATE/DELETE 事件；只用 Synthetic Students。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S17-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 一次提交 | 同 idempotency key 只建立一條提交事件 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 不可覆寫 | 普通 UPDATE/DELETE Grade Events 在 API+DB role 層失敗 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 正式更正 | Admin 補上原因／actor／revision，原始事件完整保留 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 現值正確 | Current Projection 可由 Event Ledger 重放重算 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 並發 | 兩個更正衝突時有版本檢查與序號 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B 恢復 | B-only Restore 及 Event Replay 產生相同 Current Grades | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | DB Privileges | 非 Admin API 或普通 DB role DELETE/UPDATE old grade_events 拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 同時更正 | 同一 Grade 相同 Revision 兩個不同 Correction 只有一個 CAS 成功，另一個 409 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 投影重算 | Grade Events 完整重播可重建 Current Projection；Supabase service_role 權限與審計分開說明 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S17-AT11 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | Grade 現值及歷史，包含偽造範圍／失敗路徑 | 可按 Grade Key 讀有效現值及完整事件歷史，Correction 不能改寫第一次提交；跨 Course 拒絕 | HTTP/schema/provider test + Commit SHA + Owner UAT |
| S17-AT12 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Grade Idempotency Payload 衝突 | 同 idempotency_key+相同 canonical_request_hash 返回同一 Event；同 key 不同 Payload 明確 409，不可默默忽略 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**Postgres constraints/transactions/RLS + S16 Draft。
- **不應重造的部分：**用 ON Source、一般可覆寫 row、前端限制代替 immutable score。
- **Sunrise 仍須自己交付的能力：**B append-only Grade Event + correction with canonical_request_hash + CAS revision + replay projection。
- **當期風險／不可與前期撞：**同 key 不同 payload 應 409；DB 超級用戶無法被一般 append-only 保證約束。
- **後續 consumer／依賴影響：**S18 manual grading / S20 analytics／S27 retention 視 Grade ledger 為真值。
- **真實試用入口：**B local ledger submit/history/correction UI。正式 R17 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
