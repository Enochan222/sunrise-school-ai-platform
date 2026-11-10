# Stage 06 [B] — Question/Answer/Rubric Schema Studio

**Release:** `R06` | **Exactly one owner:** `B` | **Technical prerequisites:** S3 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

在 B 建立跨學科共用的題目、答案與 Rubric Schema／版本工作室，不實際產生 AI 試卷。

**完成後可親自試用：**Admin 建 Blueprint、題型、答案約束和評分規則草稿，保存後可預覽並檢查有效性。

### 2. 驗收：甚麼情況才可以標記完成？

- 各類 Question/Answer/Rubric 可建立、保存版本、回讀及拒絕非法配置。
- 已發布的 Schema/Rubric 不會被新修改靜默覆寫，舊草稿仍有引用版本。
- S8 Generation、S11–S14 四科可引用明確版本的通用合約，且 B-only 可試用。
**本期原有驗收設計：**`S6-AT01–S6-AT09`（9 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Schema 要兼容數學題、作文與解釋題，不能假設只有選擇題或固定答案。
- PDF 的完整渲染及 AI Provider 不是本期工作。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 沿用 S3 正式 B Course ID；不得借 A Note 保存 Blueprint 或題目。
- 此 Stage 不能順便整合外部 Math-paper 整套應用／其資料庫。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S8 Queue 會引用版本，S11–S14 各科擴充要可加欄位而不破壞已批准題型。
- S16 Assessment 會引用 Rubric；變更分值規則需留 Migration/Compatibility 策略。
**明確技術前置：**S3。**直接依賴本期的後續 Stage：**S8, S11, S16。

### 6. 暫定參考，暫時不作技術承諾

- JSON Schema 精確欄位與 PDF layout contract 先作參考，直到本期真 fixture 與 Provider 測試通過才 Freeze。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B 可建立、編輯、版本化 Blueprint/Question Schema/答案格式/Rubric，為四科與生成共用，並有 Draft Preview。

## Complete user flow

Admin→Question Template Editor→Numeric/Fraction/Choice/Text Answer→Rubric→Validate/Save Version。

## Data / Source of Truth

B question_schema、answer_spec、marking_rubric、diagram_spec、pdf_render_contract、created_by、scope。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/question-schemas/validate` (`validateQuestionSchema`; auth=admin) — Deterministic structural/answer/pdf-contract validation
- `POST /core/v1/question-templates` (`createQuestionTemplate`; auth=admin) — Versioned question + rubric + math/diagram schema
- `POST /core/v1/blueprints` (`createBlueprint`; auth=admin) — Create independent versioned B Blueprint draft
- `GET /core/v1/blueprints/{blueprint_id}` (`getBlueprint`; auth=admin) — Read immutable Blueprint current published/draft ref
- `PUT /core/v1/blueprints/{blueprint_id}/draft` (`updateBlueprintDraft`; auth=admin) — Optimistic edit of DRAFT, published versions immutable
- `POST /core/v1/blueprints/{blueprint_id}/publish` (`publishBlueprint`; auth=admin) — Approve a versioned Blueprint reference for Generation
- `GET /core/v1/blueprints/{blueprint_id}/versions` (`listBlueprintVersions`; auth=admin) — List all Blueprint versions for traceable S8 generation
- `GET /core/v1/question-templates/{template_id}` (`getQuestionTemplate`; auth=admin) — Read Question Template pinned by Blueprint
- `POST /core/v1/rubric-versions` (`createRubricVersion`; auth=admin) — Create immutable Rubric version with criteria
- `GET /core/v1/rubric-versions/{rubric_id}/{version_id}` (`getRubricVersion`; auth=admin) — Read Rubric exact version for Blueprint


## Not in this Stage

不直接移植 Math-paper 整個應用、不做模型呼叫。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Independent B trial:** This Stage provides a protected B local Admin interface and persistent test workflow. It must remain testable even without new U work.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S6-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Question Schema | Numeric/Fraction/Choice/Text/Extended 型別均有 machine JSON Schema 且 Validator 會拒絕非法答案 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Rubric version | Question 與 Rubric 分開 version，舊 Assessment 引用不能被覆寫 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | PDF contract | 圖表／幾何 Schema/Renderer Contract 有測試 Fixture；S11 可以沿用 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 獨立 UI | B Question Studio 有實際可保存/查閱的模板 UI，不依賴 I/U 修改 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S6-AT08 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Blueprint 全生命周期 | 建立／草稿編輯／發布／查詢 Blueprint 及 Versions；Question／Rubric 有穩定版本 ID | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |
| S6-AT09 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 生成前置可重現 | S8 只引用已發布 blueprint_id+version，變更 Draft 不改舊 Job 結果 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON custom Transformations/Prompt 管線只作參考；Math-paper Question Schema 想法。
- **不應重造的部分：**在 A Transformations 儲存正式 Question/Blueprint/Rubric、複製整個 Math-paper App。
- **Sunrise 仍須自己交付的能力：**B Blueprint / Question / Answer / Rubric 的版本化 CRUD、Validators 及學科擴展接口。
- **當期風險／不可與前期撞：**ON Transforms 不支援正式 item score/answer rubric version；不能把 Markdown 當正式 Question contract。
- **後續 consumer／依賴影響：**S8 Queue 只引用已 Published blueprint_version；S11–14 逐科穩定擴充。
- **真實試用入口：**B-local question/blueprint editor + validation。正式 R06 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
