# Stage 12 [B] — Chinese Language Paper Adapter

**Release:** `R12` | **Exactly one owner:** `B` | **Technical prerequisites:** S11 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 單獨交付中文卷題型及繁體中文 PDF，作文／理解題保留人工覆核。

**完成後可親自試用：**Admin 可獨立設定中文科 Blueprint、生成試卷、預覽並批准 PDF。

### 2. 驗收：甚麼情況才可以標記完成？

- 中文閱讀／語文／作文題型可生成、分值及 Rubric 版本可查。
- 繁體中文、標點、字體、分頁等 PDF 實際可讀；人工覆核主觀題。
- 中文科固定測試集獨立通過，不能以數學測試當作中文驗收。
**本期原有驗收設計：**`S12-AT01–S12-AT08`（8 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 作文不存在唯一標準答案；評分規則不能被固定答案 Schema 限死。
- 版權教材只可由 S9 Evidence 按授權引用，不能自行全庫掃描。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不可修改 S11 數學既有驗證結果或 S6 Rubric 原始版本。
- 單 Owner B，不順便改英文、常識、I 或 U。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S18／S19 人工及 AI 建議改卷需要中文主觀題評分模型；本期先留下題目與 Rubric 引用。
- 中文作文 Benchmark 不能日後直接沿用選擇題 Accuracy 指標。
**明確技術前置：**S11。**直接依賴本期的後續 Stage：**—。

### 6. 暫定參考，暫時不作技術承諾

- 各年級題型細節、校本 Rubric、文字排版方案待教師試用後確定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

中文科題型、閱讀理解/作文 Rubric、繁體中文 PDF 及人工覆核，獨立可試用。

## Complete user flow

Admin→中文科 Blueprint→生成→中文驗證→PDF/Review。

## Data / Source of Truth

B chinese_adapter、rubric/test_set。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/subject-adapters/chinese` (`createChinesePaper`; auth=admin) — Chinese question/answer/rubric/PDF


## Not in this Stage

不順便改英文／常識/A/I。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S12-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 中文題型 | 選擇題、閱讀理解及作文草稿符合中文 Schema | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 字元與排版 | 中文標點、繁體字、字型及試卷換行可驗證 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 答案與評分 | 客觀題規則可核；作文人工覆核，不以 LLM 直接發分 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 課綱對應 | 題目 Topic/Learning Objective 有可追查版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 獨立測試 | 中文測試集不沿用數學通過結果 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回歸 | A/I/U 版本不變且 B 原流程仍可用 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 中文獨立 | 繁體／標點／閱讀理解／作文 Rubric 資料集單獨驗收 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S12-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S6 Question Contract + B Maths PDF pipeline。
- **不應重造的部分：**複製一份中文專屬 Queue、重寫數學共用 PDF 引擎。
- **Sunrise 仍須自己交付的能力：**B 中文 Question Type、繁體字版面、閱讀理解、寫作 Rubric、人審 Gold Cases。
- **當期風險／不可與前期撞：**不能只修改 Prompt 就聲稱中文科可用；閱讀理解及主觀作文答案需要專科人工覆核，不能默認唯一答案。
- **後續 consumer／依賴影響：**S18/S19 Marking 支援中文作文／人工驗收。
- **真實試用入口：**B local Chinese paper preview/PDF。正式 R12 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
