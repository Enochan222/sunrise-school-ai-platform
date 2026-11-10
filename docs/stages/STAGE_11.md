# Stage 11 [B] — Mathematics Paper Builder & PDF

**Release:** `R11` | **Exactly one owner:** `B` | **Technical prerequisites:** S6, S8 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 交付可試用數學卷：題目、可核答案、分數約束、人工批准及 PDF。

**完成後可親自試用：**Admin 用既有 Blueprint 產生一份數學試卷並匯出可閱覽 PDF／答案卷。

### 2. 驗收：甚麼情況才可以標記完成？

- 數學題型與 Rubric/分數總和一致，客觀題答案可由確定性方法驗證。
- PDF 含數學式／圖表／頁面，實際渲染檢查排版、截斷和答案版本。
- 未經人工批准不能標正式；B 存 Artifact，A 保持教材專用。
**本期原有驗收設計：**`S11-AT01–S11-AT10`（10 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 圖形題、幾何及多解題型應有人工覆核，不可以用 LLM 自信度當正確證明。
- PDF 字型／版面測試係正式驗收，不可單靠 API 成功回傳。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 只能使用 B Question Schema/S8 Queue，不能修改 A Notebook 或 I Evidence 模組。
- S6 既有題目／Rubric 版本不得因數學擴展變成失效。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S12–S14 會共用基礎卷引擎但各科獨立驗收；S18 Submission 需要有穩定試卷／題目 ID。
- 數學卷 PDF 版本一旦學生提交答卷就不能無痕覆蓋。
**明確技術前置：**S6, S8。**直接依賴本期的後續 Stage：**S12, S13, S14, S18。

### 6. 暫定參考，暫時不作技術承諾

- 採用哪個 PDF 引擎、幾何繪圖及題庫插件屬後續工程評估。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

數學卷 Blueprint/題目/幾何或圖表/答案驗證/版面 PDF，人工最後批准。

## Complete user flow

Admin→Math Blueprint→B Queue→數值/分數答案驗證→PDF→Review。

## Data / Source of Truth

B math_questions/answer_specs/rubrics/PDF_version and selected provenance refs。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/papers/math` (`createMathPaper`; auth=admin) — Math blueprint/validator/answer/PDF
- `GET /core/v1/papers/{paper_id}` (`getPaper`; auth=admin) — Read B paper with owner and version checks
- `GET /core/v1/papers/{paper_id}/pdf` (`downloadPaperPdf`; auth=admin) — Download B paper artifact as validated PDF binary


## Not in this Stage

不動 I、不把出卷輸出放 A。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S11-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 出卷成功 | 按 Blueprint 真正生成可批准 Math Paper | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 分數約束 | 各題 max_score 加總 = full_mark，錯誤阻止發布 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 答案可核 | 以計算或確定性測試驗證指定題型答案 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | PDF 正確 | A4／字型／頁碼／換行／答案卷實際 Render 檢查 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 人工批准 | 可修改 Draft 但不覆寫已批准 Artifact Version | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B-only | 不用 A Notebook 亦能出卷，其他服務不因本期改動 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 數學可驗 | 分數/Fraction/數值答案可確定性再計算，錯誤禁止發布 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 原始引用 | 若使用 Evidence 必須保存 Source Version/Hash/Locator 而非浮動 SourceID | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S11-AT10 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | 試卷檢視及 PDF，包含偽造範圍／失敗路徑 | GET Paper 需檢查正確 Course／Version，PDF 檔為可下載 Binary、頁碼、字體及 Hash 可核對；B 不改 A | HTTP/schema/provider test + Commit SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON 可渲染 KaTeX、來源文字；Math-paper 題目/答案/圖像 schema 作設計參考。
- **不應重造的部分：**以 ON note/Transformation 冒充正式數學卷或將 Math-paper 前端整包移植。
- **Sunrise 仍須自己交付的能力：**B Math question renderer、確定性答案檢查、Fullmark constraint、PDF export、Answer key。
- **當期風險／不可與前期撞：**S8 模型答覆可能錯；圖表、分數、引用、PDF 裁切均需實測，不改 A。
- **後續 consumer／依賴影響：**S18 Submission 引用不可變 Paper/Item Version；U 要有獨立呈現安排。
- **真實試用入口：**B local paper preview / PDF download。正式 R11 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
