# Stage 00 [P] — Planning Baseline & Security Decisions

**Release:** `—` | **Exactly one owner:** `P` | **Technical prerequisites:** None | **Status:** DOCUMENT PLANNING APPROVED / COMPLETE (2026-11-10); NO RUNTIME IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章屬文件審批，不代表已部署任何服務。** D01–D08 已獲 Owner 明確批准，見 [Stage0 正式簽核](../decisions/STAGE0_APPROVAL_DECISIONS.md)及 [逐項文件驗收證據](../delivery/STAGE0_EVIDENCE_2026-11-10.md)。此處完成的是 S0 文件／GitHub／決策驗收，不是 Stage1 服務驗收。

### 1. 目標：這一期完成甚麼？

批准唯一現行路線：A 教材、B 教學營運、I API 整合、U 介面；建立可交接的規格與 GitHub 文件審批基線。

**完成後可親自試用：**Owner 可按文件回答誰負責每項功能、目前做到哪一版、下一個 Stage 可否開始；不要求部署產品。

### 2. 驗收：甚麼情況才可以標記完成？

- PRD、S0–S28 Roadmap、ADR-011 起、Owner／依賴矩陣互相一致且簽名批准。
- 核對全新 Enochan222 GitHub main、PR、Ruleset、當前 No-Actions 測試證據及 CODEOWNERS；v0.7.5 僅以 docs-only PR 匯入，不搬舊 Repo 歷史。
- 有明確 S1 試用與安全驗收、未批准事項和人員責任表；真實部署一律 NOT RUN。
**本期原有驗收設計：**`S0-AT01–S0-AT10`（10 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 現有 main 與 ZIP 未必一致，確認實際 Repo 狀態後才決定是否合併。
- 架構批准不等於 A/B API 或硬件配置已可實作。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 舊 v0.5 的共用 SurrealDB/Core 方案不能同新 A/B 實體隔離並存為兩套權威。
- 新 Repo 未完成之驗收、Issue 與候選 ADR 不可寫成已批准或已部署。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S1 只限 A；S2/S3 各自發布 API 後 S4 才可連接。
- 如改動 S0 的 Owner／Stage 定義，必須全面重審其後 Release/AT/版本映射。
**明確技術前置：**None。**直接依賴本期的後續 Stage：**S1, S3。

### 6. 暫定參考，暫時不作技術承諾

- 確實的 Repo settings／審批人／Hosting Region／成本由 Owner 核准，不在本文視為已決。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

新的 Enochan222 Repo 以 docs-only PR 匯入 Reviewed v0.7.5；原 IssacSitHk GitHub 歷史不搬遷；S0 需簽核 A/B/I/U 權責。

## Complete user flow

核對新 Enochan222 Repo/PR/Ruleset→匯入 v0.7.5 候選文件→ADR-011..022→Owner 確認 API、Course 粒度、安全與 Stage0 文件驗收。

## Data / Source of Truth

文件、Contract、Owner 權限決策；沒有 Runtime DB。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- 本期無新增 Owner API；只使用已部署版本的受控 API。


## Not in this Stage

不部署 A/B、不要求 Restore/PoC；不聲稱舊 Stage0 Issue 完成。

## Real deployment and operations（原規劃參考與實測要求）

Stage0 is documents/Owner/Repo verification only; no running DB, Staging, Gateway or Restore PoC required.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S0-AT01 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 來源版本 | 核對上游實際 Commit/License/Open Notebook scope／安全限制，留證據 | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT02 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 物理隔離 | 批准 A SurrealDB、B PostgreSQL 不共享連線、檔案、備份或帳密 | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT03 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | Stage 單責任 | 依賴圖中每個 Release 只有一條 Workstream Owner | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT04 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | S1 合格界線 | 明確 S1 A-only，S3 才有 B，S4 才有跨 API I | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT05 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | Repo 控制 | PR 保護、Secrets 政策、Status/ADR/Templates 完整 | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT06 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 批准與未實測 | 清晰記下 Owner Signoff/NOT IMPLEMENTED，不能把文檔當部署 PASS | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT07 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 決策完整 | ADR-011..022、Course Grain、API Inventory、No-Actions 驗收紀錄全部審核，Owner 未簽核不得標 APPROVED | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT08 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 新 GitHub 影響 | 新 Repo 權威、PR 保護及 No-Actions 測試紀錄清楚；不匯入舊 Repo 歷史 | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT09 | 文件、Repo 與 Owner 人工可核資料（無部署前提） | 無部署驗收 | S0-AT 僅要求文件、Repo、Owner 批准及可核對的設計證據 | Document diff / reviewed source / Owner signoff (not runtime) |
| S0-AT10 | Owner 審核規格及 ADR，無運行環境前置 | Course/TeachingGroup/Shell 決策 | 批准 Course 一個學年/級別/科目/stream 可多 Group，A Shell 有 school_id；Gemini S1 可選，S4 Cutover Owner 及 API 不混合 | Spec/ADR Diff、Repo 文件及 Owner signoff |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**Open Notebook upstream knowledge/credentials/worker/REST；本 Repo 採獨立本地測試、不用 GitHub Actions。
- **不應重造的部分：**Stage 0 不部署任何 A/B/I/U Runtime 或雙庫 PoC，也不能把文檔批准當產品驗收。
- **Sunrise 仍須自己交付的能力：**批准 reuse-first A/B/I/U、Course 粒度、A-only S1 搜尋及 Provider Optional、S4 受控 Cutover、新 Enochan222 Repo v0.7.5 docs-only PR。
- **當期風險／不可與前期撞：**不得將上游「單使用者 Notebook」推定為學校 RBAC；來源 ZIP 的 git SHA 未核實。
- **後續 consumer／依賴影響：**S1 A、S3 B 都依本次 Owner 批准；Release 先後與技術依賴分開。
- **真實試用入口：**Owner 審批文件、GitHub Issue 與設計決策紀錄；沒有 Staging 部署。正式 S0 完成須有文件核驗、可追溯負面測試與 Owner 簽核（不需 Runtime）；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

Owner approval + docs/contract/Repo evidence; no product Release and no mandatory runtime test.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
