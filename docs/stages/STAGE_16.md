# Stage 16 [B] — Assessment & Score Drafts

**Release:** `R16` | **Exactly one owner:** `B` | **Technical prerequisites:** S6, S15 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 讓 Admin 建 Assessment 與可編輯分數草稿，確認總分／缺漏，但尚未提交正式成績。

**完成後可親自試用：**Admin 為虛構學生建立 Assessment、逐題草稿分數、檢查後保存，刷新仍可改。

### 2. 驗收：甚麼情況才可以標記完成？

- Assessment 與 Question/Rubric 版本可追蹤，Draft 可保存／查詢。
- 分數過大、缺題、Rubric 錯配或非有效 Enrollment 必須拒絕。
- 本期不產生正式 Grade Event；B-only Restore 後 Draft 不丟失。
**本期原有驗收設計：**`S16-AT01–S16-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Draft 是可改資料，與 S17 正式已提交事件的不可改規則不同。
- 題目分數及 Assessment Full Mark 需確定性計算，不交給 AI 決定。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 引用 S6 Schema／S15 合成名冊，不能重新定義學科題目或 Course ID。
- 不以更新草稿方式修改任何既有正式 Grade Event。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S17 需要不可重覆的 Submit／Correction 邊界、同一 Assessment/Student/Item Version。
- S18 Manual Marking 會由提交／答卷轉為草稿／正式分數，資料血緣要清楚。
**明確技術前置：**S6, S15。**直接依賴本期的後續 Stage：**S17。

### 6. 暫定參考，暫時不作技術承諾

- 草稿修改紀錄詳細度、UI 表格格式和匯入欄位待現場試用確認。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B 使用既有 Question/Rubric Contract 建 Assessment、模擬分數 Draft、驗證總分與進度。

## Complete user flow

Admin→Assessment→Items→Score Draft→Validate/Preview/Save。

## Data / Source of Truth

B assessment/items/grade_drafts, answer_schema versions, synthetic data。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/assessments` (`createAssessment`; auth=admin) — B Assessment drafts from canonical question schema
- `GET /core/v1/assessments/{assessment_id}` (`getAssessment`; auth=admin_or_staff) — Read assessment and rubric after course authorization
- `POST /core/v1/score-drafts` (`createScoreDraft`; auth=admin) — Validated synthetic score drafts


## Not in this Stage

此期分數未提交成正式 Grade Event。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S16-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Assessment CRUD | 完整建立 Assessment 與 Question Items | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 草稿算術 | 小題分數範圍合法且總分可確定重算 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 不完整分數 | 缺值、超出上限、重複題 ID 阻止 Confirm | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Draft 回存 | 重開瀏覽器仍可讀 B Draft | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 無正式事件 | 此期不得把 Draft 誤標為正式成績 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回歸 | B Roster/Course 及 B-only Restore 通過 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Schema 與舊題 | S6 Question/Rubric 版本可連到 Assessment Draft 且不能覆蓋原答案 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S16-AT09 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | Assessment 讀取，包含偽造範圍／失敗路徑 | 按 assessment_id 讀回題目／Rubric/Revision，偽造 Course 或未批准 Actor 時必須拒絕 | HTTP/schema/provider test + Commit SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**B S6 Question/Blueprint/Rubric、S15 Synthetic Students。
- **不應重造的部分：**重新開一套成績 DB 或讓 ON notes 保存草稿。
- **Sunrise 仍須自己交付的能力：**B Assessment versions、Score Draft CRUD、分數校驗與歷史。
- **當期風險／不可與前期撞：**Draft 可改但未正式提交，不能對後續 ledger 構成權威 grade。
- **後續 consumer／依賴影響：**S17 Grade immutable submit，S18 manual marking。
- **真實試用入口：**B local assessment / draft editor。正式 R16 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
