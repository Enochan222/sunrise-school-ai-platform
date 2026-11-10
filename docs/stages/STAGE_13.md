# Stage 13 [B] — English Language Paper Adapter

**Release:** `R13` | **Exactly one owner:** `B` | **Technical prerequisites:** S11 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 單獨交付英文 Grammar/Reading/Writing 試卷與答案／寫作 Rubric。

**完成後可親自試用：**Admin 能從英文 Blueprint 建卷、預覽 PDF 與答案／Rubric，人工審核 Writing。

### 2. 驗收：甚麼情況才可以標記完成？

- 英文三類題型有可用範本與輸出 Schema；客觀題答案及分數可核。
- Writing 只能有候選評語與人工覆核，不能作無審核自動評分。
- 英文科獨立 Fixture 與 PDF 實際驗證通過，既有數學／中文功能回歸。
**本期原有驗收設計：**`S13-AT01–S13-AT08`（8 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 英文可接受多種表達；不要把標準答案單一字串當全部正確答案。
- Rubric Version／本地化語言處理需保留。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不覆蓋 S12 中文的專用配置或 S11 數學答案計算規則。
- 不在同一 B Stage 偷做常識科／A 搜尋／U UI。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S19 AI Marking 對 Writing 需有分級人手 Gold Set；S18 會引用題目 ID。
- 英文卷與成績欄位要兼容 B 原有 Assessment/Grade Contract。
**明確技術前置：**S11。**直接依賴本期的後續 Stage：**—。

### 6. 暫定參考，暫時不作技術承諾

- 接受答案邊界、語法檢查工具及閱讀理解模板待樣本集決定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

英文 Grammar/Reading/Writing、Accepted Answers、專屬測試集、PDF 與人手覆核。

## Complete user flow

Admin→English Blueprint→Generate→Grammar/Writing Rubric Validate→Review/PDF。

## Data / Source of Truth

B english_adapter/schema/test_set。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/subject-adapters/english` (`createEnglishPaper`; auth=admin) — English grammar/writing rubric/PDF


## Not in this Stage

不順便改其他學科/A/I。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S13-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 英文題型 | Grammar、Reading、Writing 能分別建立 Blueprint | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 寫作審核 | 自由作文為 AI suggestion，不能自動確定分數 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 答案規則 | 客觀題標準答案與題目版本一致 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 格式 | 英文卷 PDF 換頁、字型及答案頁可讀 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 固定測試 | English-only Gold Sample Test 與誤差報告 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 邊界 | A/I/U 無任何新 code/schema/config 修改 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 英文獨立 | Grammar/Writing/Accepted Answer 等獨立測試集，作文保留人工審核 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S13-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S6 Contract + S11 B PDF service; Math-paper 某些答題形式可作類型參考。
- **不應重造的部分：**不複製一份英文專用資料庫／Queue，也不直接以其他科的答案判分器當成英文題目真值。
- **Sunrise 仍須自己交付的能力：**B 英文 Grammar/Reading/Writing validators、rubric、PDF。
- **當期風險／不可與前期撞：**英文寫作及閱讀理解可能有多個合理答案，須經獨立 Gold Dataset 與人工覆核，不能只憑 LLM 同意。
- **後續 consumer／依賴影響：**S19 英文 AI marking benchmark 題目對齊。
- **真實試用入口：**B local English paper preview/PDF。正式 R13 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
