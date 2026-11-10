# Stage 20 [B] — Deterministic Analytics & Weakness Keep-two

**Release:** `R20` | **Exactly one owner:** `B` | **Technical prerequisites:** S17 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 由有效 Grade Event 計算 Analytics，讓 Admin 預覽、選擇／丟棄最多兩份有效 Weakness Memory。

**完成後可親自試用：**Admin 看到各 Topic 的有依據弱點，點 Keep 後下次出卷可選 0–2 個版本；更正成績後舊弱點自動失效。

### 2. 驗收：甚麼情況才可以標記完成？

- 指標可用確定性方法獨立重算，分子／分母與有效成績來源可追溯。
- 同 Course/Target 最多兩個 VALID ACTIVE；並發 Keep 不會超限，Discard/Retire 不會刪原成績。
- S17 Correction 發生時相應 Snapshot 必須變 STALE，不能在下一次生成使用過時資料。
**本期原有驗收設計：**`S20-AT01–S20-AT11`（11 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 成績統計與 AI 評語要分開；不容相關變因果或以小樣本當普遍結論。
- 「Keep 兩版」限制的是可選 Weakness Snapshot，不是學生所有歷史事件。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 只能依賴 S17 確認 Grade，不用 S16 Draft 或 S19 尚未批准的 AI Suggest。
- 不向 A Notebook 寫學生弱點或分數；不改 I 的 Evidence 模型。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S21 UI 會顯示弱項兩版，S27 年終結算要保留 Score/Audit 歷史與快照狀態。
- 日後用弱項生成下一份卷時要檢查 Course/Scope 和舊版過期狀態。
**明確技術前置：**S17。**直接依賴本期的後續 Stage：**S21, S22, S27。

### 6. 暫定參考，暫時不作技術承諾

- 統計指標／門檻／可視化可持續調整；但算術、Source Grade Watermark 和 Keep2 原則要先固定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

Grade Events→Analytics Snapshot→候選弱點→Keep 最多兩份 Active Memory，舊 Grade 不刪。

## Complete user flow

Admin→分析→Metrics→Candidate→Keep/Discard→下一次出卷選取0/1/2份。

## Data / Source of Truth

B grade_events/analytics_snapshot/weakness_candidate/weakness_memory distinct。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/analytics` (`runDeterministicAnalytics`; auth=admin) — Complete Grade Events -> Metrics
- `GET /core/v1/analytics/{run_id}` (`getAnalyticsRun`; auth=admin) — Get deterministic analytics run and source revision
- `GET /core/v1/weakness` (`listActiveWeakness`; auth=admin) — List only valid active weakness snapshots by course scope
- `POST /core/v1/weakness` (`keepWeaknessMemory`; auth=admin) — Candidate Keep2 with stale watermark
- `GET /core/v1/weakness/candidates` (`listWeaknessCandidates`; auth=admin) — Full Candidate / Stale / Retired review state of course
- `GET /core/v1/weakness/{snapshot_id}` (`getWeaknessSnapshot`; auth=admin) — Single Snapshot review with actual state and grade revision
- `POST /core/v1/weakness/{snapshot_id}/discard` (`discardWeaknessSnapshot`; auth=admin) — Discard Candidate with expected revision; cannot resurrect stale


## Not in this Stage

不向 A 寫弱點或學生分析。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S20-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 確定性 | 平均分／題目弱點統計與 SQL/人工獨立重算一致 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 兩版上限 | 同 Course+Target Scope 不能有第 3 個 VALID ACTIVE | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 老師選擇 | 未經 Admin/教師 Keep 不可納入下一份卷 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 更正失效 | Grade Correction 後受影響 Snapshot 標記 STALE | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 來源 | Snapshot 只引用 B Grade Events，A 無弱項內容 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 一致重跑 | B Restore／重算不會將 Retired/Wrong Scope Profile 誤變 Active | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 記憶不等於數據 | Grade Event/Analytics Snapshot/Weakness Candidate/Weakness Memory 四者區分 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Keep2 原則 | 最多兩個 Valid Active Memory，但不得刪 Event 或原始 Analytics；更正後 STALE | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S20-AT10 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | Analytics／Weakness 讀取，包含偽造範圍／失敗路徑 | B 可讀已完成 Analytics 與每 Course 最多兩個有效 Weakness，STALE 或跨 Course 資料不會當作 Active | HTTP/schema/provider test + Commit SHA + Owner UAT |
| S20-AT11 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Weakness 完整狀態 | B 有 Candidate／Active／STALE／RETIRED 查詢以及 Discard，既有分數不受影響 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**B S17 ledger immutable event + S6 Topic metadata; no A data。
- **不應重造的部分：**讓 ON RAG Score 或模型猜測取代 deterministic SQL analytics。
- **Sunrise 仍須自己交付的能力：**B metrics Snapshot/Candidate/Keep2/Discard/STALE/RETIRED and watermark。
- **當期風險／不可與前期撞：**Weakness Keep2 只限 ACTIVE 記憶，不可刪真正的 Grades／統計。
- **後續 consumer／依賴影響：**S21 UI 要候選／Discard／Stale 讀寫，S27 Closing 要能 Retire。
- **真實試用入口：**B local Analytics/Weakness Console。正式 R20 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
