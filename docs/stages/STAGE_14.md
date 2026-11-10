# Stage 14 [B] — General Studies Paper Adapter

**Release:** `R14` | **Exactly one owner:** `B` | **Technical prerequisites:** S11 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 單獨交付常識科卷，要求可核對題目事實與日期，解釋題人工確認。

**完成後可親自試用：**Admin 建常識科 Topic 試卷，看到待核的事實與來源標記，審核後生成 PDF。

### 2. 驗收：甚麼情況才可以標記完成？

- 常識科題型、Rubric、版本及分值可用並生成 PDF。
- 時效性知識有出題日期／來源審核提示，無可靠資料不可自動宣稱事實正確。
- 常識科獨立 Sample/Negative Test，並保留其他三科流程。
**本期原有驗收設計：**`S14-AT01–S14-AT08`（8 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 時事、地理、政策等內容會過期；教材引用不保證最新世界事實。
- Explanation／開放題不能用單一 LLM 判斷直接發布分數。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不能從 A Notebook 原文直接推斷已過事實查核；S9 Evidence 只證明來源，不等於真偽。
- 不在本期修改其他三科或 I 的檢索。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S19 AI 改卷要有常識科特定 Benchmark，S20 Analytics 保留 Topic／Learning Objective。
- 日後教材更新需能標記舊試卷引用的知識時間。
**明確技術前置：**S11。**直接依賴本期的後續 Stage：**—。

### 6. 暫定參考，暫時不作技術承諾

- 題型校本標準、外部權威查核方式待獨立審查。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

常識科 Topic、正確性、教材／事實有效日期、解釋題人工核對、專屬 PDF。

## Complete user flow

Admin→常識 Blueprint→Question Fact Review→Human Approval→PDF。

## Data / Source of Truth

B general_studies_questions/source_fact_checks/rubric_versions。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/subject-adapters/general-studies` (`createGeneralStudiesPaper`; auth=admin) — General Studies sourced fact/date validation


## Not in this Stage

不將 A 檢索當作事實已驗證，不順手改 I。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S14-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 學科題型 | 常識科多種題型完整生成及預覽 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 時效檢查 | 易變事實有來源/版本標記，無證據需人工核對 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 批改要求 | 短答／解釋題保留人手 Review | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 版本 | Rubric/Topic/Model/Prompt 版本可追溯 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 獨立測試 | 常識 Test Set 本科單獨驗收 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 邊界 | A/I/U 不變，B 舊科目及分數功能回歸成功 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 常識事實 | 使用有出版日/地區/來源的事實核對，變動題需人手 Review | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S14-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S11 產卷基礎 + S9 已核實 Evidence 片段（可選）。
- **不應重造的部分：**不能讓 A 原生問答直接承擔正式常識題目的正確性、引用有效性或評分責任。
- **Sunrise 仍須自己交付的能力：**B 常識科 Topic/fact-date/provenance/多答案 Rubric、人工查證。
- **當期風險／不可與前期撞：**有 Source citation 不代表當期事實正確；不同教材版本和地區課綱需標明。
- **後續 consumer／依賴影響：**S19 判分與 S20 Analytics topic grouping。
- **真實試用入口：**B local General Studies paper preview/PDF。正式 R14 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
