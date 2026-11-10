# Stage 19 [B] — AI-assisted Marking Benchmark & Review

**Release:** `R19` | **Exactly one owner:** `B` | **Technical prerequisites:** S18, S8 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 對答卷產生 AI 批改建議並用人手 Gold Standard 衡量誤差，最終仍須人工確認。

**完成後可親自試用：**Admin 看到每題 AI Suggest／理由／置信與人工差異，能更正／拒絕並批准最終分數。

### 2. 驗收：甚麼情況才可以標記完成？

- AI 建議有 Rubric/Prompt/Model/Question/Submission Version 血緣，無法直接發正式分數。
- 至少用固定、教師核准 Gold Samples 分析抽取／題目對位／部分給分／誤差，保留失敗例子。
- 人工決定後仍走 S17 Ledger，錯誤和低信心提交人工處理。
**本期原有驗收設計：**`S19-AT01–S19-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- AI 與自己多次輸出一致不等於正確；不可用模型互評取代 Gold Standard。
- 客觀題與作文／開放題要分別衡量，不能用一個總 Accuracy 掩蓋高風險錯誤。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S18 手動改卷正常路徑必須保留作 fallback；AI 不能覆寫已提交 Grade。
- 不存學生作答在 A；不得把 RAG 教材 Context 當作學生答案。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S20 Analytics 只能使用人工確認後的有效 Grade Event，不能直接用 AI Suggest。
- S22 教師權限需決定誰可批核／覆核／提出更正，不能提前假裝有 Teacher Grant。
**明確技術前置：**S18, S8。**直接依賴本期的後續 Stage：**S21。

### 6. 暫定參考，暫時不作技術承諾

- Benchmark 指標、最低可接受品質和模型方案需與學校／教師共同定義；目前不能保證準確率。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

AI 批改只作建議；人工 Gold Standard Benchmark 涵蓋 Extraction/Alignment/Partial Credit/誤差；最終人工確認。

## Complete user flow

Admin→AI Mark Job→Extract/Align→Suggest→Flag Dispute→Teacher Review→Ledger。

## Data / Source of Truth

B marking_jobs/suggestions/model_version/benchmark_goldset/audit_actor。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/marking-jobs` (`createAiMarkingJob`; auth=admin) — AI suggestion with extraction/alignment benchmark
- `POST /core/v1/marking-reviews` (`reviewAiMarkingJob`; auth=admin) — Human final decision only


## Not in this Stage

不以 AI 多次一致當作準確，不自動提交分數。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S19-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 建議可追查 | 每題 AI Suggest 連 Rubric/Model/Prompt Version | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 人工優先 | AI 不得直接發布正式分數 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 分數驗證 | 人工採納後每題分與 Grade Ledger 約束一致 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 爭議 | 低信心／答案不確定轉人工處理 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 測試集 | 在固定合成 Gold Dataset 上評估精度與錯誤類型 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 無 A | AI 改卷模型只讀 B submissions/rubric，不連 A DB | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Gold Benchmark | 人工 Gold Set 同時評估 Answer Extraction、Question Alignment、Score Partial Credit、Low Confidence | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 多次一致陷阱 | 三次 AI 一致但共同 OCR 錯誤的測試依然需要人手拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S19-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**PTH_Homework multi-pass candidate reasoning，人工誤差比較概念。
- **不應重造的部分：**用兩／三次 LLM 一致當正確；直接採用其 HTTP API / BYOK/CORS。
- **Sunrise 仍須自己交付的能力：**B AI Suggest, alignment/partial-credit benchmark, confidence, human acceptance + ledger API。
- **當期風險／不可與前期撞：**人工 Gold Set 覆核，OCR/抽取錯即使多模型一致也可能錯。
- **後續 consumer／依賴影響：**S21 U 讀標記結果／S22 Staff grant 功能。
- **真實試用入口：**B local AI marking review console。正式 R19 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
