# Stage 01 [A] — Secure Open Notebook Vault

**Release:** `R01` | **Exactly one owner:** `A` | **Technical prerequisites:** S0 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

交付真正可登入、可上載、可搜尋／下載、可恢復的 A-only Open Notebook 教材庫。

**完成後可親自試用：**唯一 Admin 建立課程教材容器，系統生成專用 Notebook；放入校方教材後能重新登入、查詢、下載及封存。

### 2. 驗收：甚麼情況才可以標記完成？

- 完整 Course Shell→Notebook→Upload→Search／Download 可在受保護環境運作，資料重啟後存在。
- 直接呼叫原生 Notebook Create／Delete／Link、空範圍搜尋、猜 Source ID、串流與下載均不能繞過防線。
- 故障重送不產生第二個 Notebook；A DB＋原檔恢復後 ID／檔案 Hash 可核對。
**本期原有驗收設計：**`S1-AT01–S1-AT15`（15 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Open Notebook 原生 Shared Password 不是教師權限系統；未設 Secrets 或示例密碼必須阻止啟動。
- 內容來源和學生個資要分清；教材與已生成學生試卷／成績不能混存。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S0 只是文件審批，S1 不可說雙庫已完成。
- 不用另開一般 Notebook 新增／刪除入口；課程教材容器是唯一正規建立入口。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S2 要沿用 Shell／Notebook／Source ID 與版本關係，不能改成依標題配對。
- S4 需要 A 的可靠 Scope/Actor/Idempotency；S23 需要安全唯讀途徑；本期不開教師。
**明確技術前置：**S0。**直接依賴本期的後續 Stage：**S2。

### 6. 暫定參考，暫時不作技術承諾

- A 的精確部署方式、模型供應商與 Gemini Embedding 是否啟用都屬待測方案；S1 不依賴 B BYOK。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

Admin 可建立 Content Shell→唯一 Notebook，安全上載/搜尋/下載教材、原檔與 A-only 復原。

## Complete user flow

Admin Login→Create Content Shell→Private ON Adapter→Upload/Index/Search/Download→Archive。

## Data / Source of Truth

A SurrealDB+Original File Volume；source_owner、content_shell、actor/scope/sha256；無 B。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `GET /vault/v1/shells` (`listContentShells`; auth=admin) — Scoped list; no whole notebook list
- `POST /vault/v1/shells` (`createContentShell`; auth=admin) — Idempotent A-only Content Shell and Notebook creation
- `GET /vault/v1/shells/{shell_id}` (`getContentShell`; auth=admin_or_service; scope=vault.shell.read) — Admin view single owned shell
- `POST /vault/v1/shells/{shell_id}/archive` (`archiveContentShell`; auth=admin) — Archive only, never native delete
- `GET /vault/v1/shells/{shell_id}/materials` (`listVaultMaterials`; auth=admin_or_service; scope=vault.materials.read) — List material metadata scoped to one shell
- `POST /vault/v1/shells/{shell_id}/materials` (`uploadVaultMaterial`; auth=admin_or_service; scope=vault.materials.write) — Validated typed file upload+hash
- `GET /vault/v1/shells/{shell_id}/materials/{material_id}/download` (`downloadVaultMaterial`; auth=admin_or_service; scope=vault.materials.read) — Scoped source-owner verified file download
- `POST /vault/v1/shells/{shell_id}/search` (`searchContentShell`; auth=admin_or_service; scope=vault.search.read) — Nonempty notebook scope and post-filter source owner


## Not in this Stage

不開 Supabase/B/學生資料/I Service；上游 raw Admin API 不能公開。

## Real deployment and operations（原規劃參考與實測要求）

This is a A-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S1-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 完整操作 | Admin 建 Shell，唯一 Notebook，教材可上載搜尋下載 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 防旁路 | 匿名／直接 Open Notebook POST、DELETE、global search 無法從公開網路使用 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍 | 非空 notebook scope，Course A 搜尋不返回 Course B Source | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 持久化 | 重新啟動 A DB/Worker 後檔案、索引／紀錄仍可讀 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | A Restore | 隔離環境還原 A DB + 原始檔+keys，驗證 Source/Hash | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 重試 | Notebook Create ACK 丟失後相同 operation id 不生成第二本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 基本安全 | 唯一 Admin、HTTPS、private DB/secret、無真實學生個資 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Secrets Fail Startup | OPEN_NOTEBOOK_PASSWORD、Encryption Key、DB credential 缺任何一項或使用示例 root:root 即拒絕啟動 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 原生旁路 | 直接 raw GET/POST/DELETE Notebook、source link 或全庫 Search 由公開端拒絕，僅私有服務可達 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | SSE 與 Preview 隔離 | 猜測 Source ID、下載、Preview、Stream 不輸出非目標 Shell 資料任何片段 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 來源權威 | source_id→shell_id→notebook_id 映射與實際上游內容一致，Search 返回前二次校驗 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT12 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 版權與備份 | Source 基本 Retention/License/AI-Usage flag、原始 PDF Hash 在 A-only Restore 後一致 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT13 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S1-AT14 | 已部署該 Stage 相應服務與專用測試資料 | 教材列表契約正向與越權／異常負面測試 | GET A shell materials 由唯一 Admin 或特定 Service Scope 獲取、逐個 Source Owner 驗證，返回具版本與 Hash 的列表 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S1-AT15 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | A Shell 校級權限 | 兩個 School 的 Shell／Source / Scope 即使 ID 可猜到，A Gateway 仍拒絕跨校讀取 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON notebooks CRUD, existing Next.js components, Sources upload, Text Search, async job status, notes and archive。
- **不應重造的部分：**Notebook 引擎、來源上載管線、全文抽取及原生 UI 組件。
- **Sunrise 仍須自己交付的能力：**A Policy Gateway + ContentShell→Notebook 映射、Session、密碼 fail-start、原生 API 不暴露、Source 單一擁有者、A Restore。
- **當期風險／不可與前期撞：**原生 Notebook POST/DELETE、Source 多 Notebook reference、無 scope 全庫搜尋及來源列舉；`delete_source` 不能誤刪原檔。
- **後續 consumer／依賴影響：**S2 Version/Source Manifest 依賴穩定 ID；S4 依賴可靠 A 服務操作；S23 不可使用原生 Admin Password。
- **真實試用入口：**A-owned受保護教學內容頁（可重用 ON UI 組件，必須換 API Client）。正式 R01 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
