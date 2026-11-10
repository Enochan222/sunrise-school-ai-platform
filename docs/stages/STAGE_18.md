# Stage 18 [B] — Submissions & Manual Marking

**Release:** `R18` | **Exactly one owner:** `B` | **Technical prerequisites:** S11, S17 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 支援合成學生收卷、人工逐題批改及提交 Grade Ledger。

**完成後可親自試用：**Admin 上載或建立模擬答卷，按 Rubric 人工評分、覆核，再正式提交。

### 2. 驗收：甚麼情況才可以標記完成？

- 答卷與 Student／Assessment／Question Version 對應，重送不會覆蓋原答卷。
- 人工逐題分數符合 Rubric／總分，缺頁和無法對應的答案走人工 Review。
- 批准評分後經 S17 append-only API 入賬；答卷 Artifact 只存 B。
**本期原有驗收設計：**`S18-AT01–S18-AT11`（11 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 先取得可靠 Submitted Paper／Rubric Version，不能把答卷內容放 A Vault。
- 批改 UI 暫用 B 原生試用流程，U 正式整合預定 S21。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不能繞過 S17 直接 INSERT Current Grade；亦不覆寫 S16 Draft 歷史。
- 只用 S15 合成學生，未有 S25 實名資料批准。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S19 AI Marking 需保留人工正確答案與例外狀況作 Gold Set。
- S21 Sunrise 成績工作台會讀本期的答卷／評分 API。
**明確技術前置：**S11, S17。**直接依賴本期的後續 Stage：**S19, S21, S22, S27。

### 6. 暫定參考，暫時不作技術承諾

- 支援的答卷格式、OCR 與題目對位工具先列候選，先保證人工流程可用。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

模擬答卷提交/人工逐題評分/Review，完成後寫 Grade Event。

## Complete user flow

Admin→Synthetic Submission→Question Alignment→Rubric→Manual Mark→Approve→Ledger。

## Data / Source of Truth

B submission_versions/answer_refs/marking_decisions and Grade Event ID。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/manual-marking` (`approveManualMarking`; auth=admin_or_staff) — Human verified and ledg ered score
- `POST /core/v1/submissions` (`createSubmission`; auth=admin) — Synthetic answer submissions
- `GET /core/v1/courses/{course_id}/submissions` (`listSubmissions`; auth=admin_or_staff) — Course-scoped submissions list, Teacher only after S22
- `POST /core/v1/submissions/{submission_id}/item-marking` (`markItemSubmission`; auth=admin) — S18 question-level scoring draft by rubric + revision; never direct final Grade update
- `GET /core/v1/submissions/{submission_id}/item-marking` (`listSubmissionItemMarking`; auth=admin) — S18 read item-level reviewed marks before final Grade submit


## Not in this Stage

不直接接真實學生、AI 改卷留 S19。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S18-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 收卷 | 多份模擬提交按 Assessment+Student 配對 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 重複提交 | Version/Retry 不覆蓋原始答卷 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 人工改卷 | 逐題評分符合 Rubric/滿分上限 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Ledger | 確認之後只新增 Grade Event；無直接 UPDATE | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 錯誤處理 | 缺頁／無效檔案／學生不符進 Review Queue | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 無 A | 答卷與分數只在 B private storage，完全不寫 A | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 對題校驗 | Submission OCR/題目 Alignment 不可靠時阻止自動提交分數 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S18-AT09 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 提交可讀 | B 可查選定 Course 的 Submission，S22 後授權教師可讀獲授權 Group/學生；當期仍 Admin | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |
| S18-AT10 | S18 獨立 B Runtime Staging 與合成答卷 | 逐題改卷型別及回讀 | B 逐題決定含 question_item_id、rubric_version、score、max_score、revision；人工覆核才可提交正式 Grade Event，不能直接覆寫正式分數 | Provider Contract/Database revision/Owner UAT |
| S18-AT11 | S18 獨立 B Runtime Staging 與合成答卷 | 逐題改卷型別及回讀 | B 逐題決定含 question_item_id、rubric_version、score、max_score、revision；人工覆核才可提交正式 Grade Event，不能直接覆寫正式分數 | Provider Contract/Database revision/Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S11 B Paper Item IDs + S17 Grade Ledger; PTH_Homework 流程可作研究。
- **不應重造的部分：**把 PTH_Homework 原來 public CORS / BYOK API 搬到生產當安全邊界。
- **Sunrise 仍須自己交付的能力：**B synthetic submissions、逐題 Rubric version／manual marking／human approval。
- **當期風險／不可與前期撞：**答卷重試不覆寫原文件、課程/student/item 不可錯配；不得直寫 current_grade。
- **後續 consumer／依賴影響：**S19 AI Suggestions ground truth；S21 U 顯示改卷結果。
- **真實試用入口：**B local submission/marking console。正式 R18 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
