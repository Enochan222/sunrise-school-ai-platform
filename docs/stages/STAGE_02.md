# Stage 02 [A] — Versioned Content Catalog & A Contract Freeze

**Release:** `R02` | **Exactly one owner:** `A` | **Technical prerequisites:** S1 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

在 A 完成教材分類、版本／發布與可用的穩定 API，為日後整合預留安全邊界。

**完成後可親自試用：**Admin 修改教材分類與版本，舊版本仍可追查；以受控 API 查單一 Content Shell 已發布的教材及來源。

### 2. 驗收：甚麼情況才可以標記完成？

- Textbook／Note／Past Paper 類型、Topic、版本和發布／封存狀態能儲存及查詢。
- 同一 Source 不會同時屬於兩個 Shell；版本變動不令引用失效或指錯原檔。
- S4 所需 A API 由 A 自己提供 Provider／Consumer 合約測試；確認 Service Token 範圍及錯誤回應。
**本期原有驗收設計：**`S2-AT01–S2-AT15`（15 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 「Contract Freeze」係本 Stage 實際通過測試後的結果，唔係現有 JSON 文件寫好就等於已 Freeze。
- 避免原生 Open Notebook 搜尋的 Empty Scope 回退全庫；索引遷移需可恢復。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 保留 S1 Notebook 唯一、原檔 Hash、Archive 不 Delete 及 A-only Restore。
- 不得將生成試卷、學生、成績或 B Course Business Record 搬入 A。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S4 的 Adopt/Create、S5 材料列表／上載／下載、S9 Evidence、S23 Teacher Read 都依賴受控 A 契約。
- 如 S4 提出新 A API，應開獨立 A Owner 變更版本，不能在 I Stage 偷改 A。
**明確技術前置：**S1。**直接依賴本期的後續 Stage：**S4, S26。

### 6. 暫定參考，暫時不作技術承諾

- 欄位名稱、API 分頁方式、檔案上限和內容版本策略只是參考，實測與 Owner 決策後才鎖定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

可管理教材 Topic/Version/Publication、Source Provenance、source retention；提供 I 所需穩定 A API v1。

## Complete user flow

Admin→分類→新版本→Publish→只讀 Manifest/Search→Archive→測試 idempotent Provision。

## Data / Source of Truth

A Source Version immutable content hash、license/AI usage policy、retention state、shell/owner manifests。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /vault/v1/admin/cutover-policy` (`setVaultCutoverPolicy`; auth=admin_or_service; scope=vault.cutover.manage) — Atomic create permission switch to managed I, reversible freeze mode
- `POST /vault/v1/internal/provision` (`provisionVaultShell`; auth=service; scope=vault.shell.provision) — Private idempotent creation for I, no raw ON create
- `GET /vault/v1/operations/{operation_id}` (`getVaultOperation`; auth=service; scope=vault.operation.read) — Idempotent A create operation journal lookup
- `GET /vault/v1/shells/{shell_id}/manifest` (`getVaultSourceManifest`; auth=admin_or_service; scope=vault.manifest.read) — Immutable source versions/sha/locator/license/status
- `POST /vault/v1/source-versions/{version_id}/attest` (`attestVaultVersion`; auth=service; scope=vault.source.attest) — Provenance/usage permission/immutable version status with hash


## Not in this Stage

不建立 B Binding、不寫 B 成績、不部署 I。

## Real deployment and operations（原規劃參考與實測要求）

This is a A-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Contract Freeze:** 需在本期提交可驗證 OpenAPI JSON、Context/Idempotency Fixture、Consumer Contract Test。不得一邊做 I 一邊修改 A/B。

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S2-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 教材分類 | 三類檔案均保存可查詢 Metadata、學年、Topic、來源版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 版本規則 | 教材修訂產生新 Version，已發布舊版可追查 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 唯一擁有者 | 同一 Source 不可跨 Shell Link 或進其他課程搜尋 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | API Contract | 提供 Shell 清單、單 Shell Manifest、受控 Create/查詢的 OpenAPI 及測試 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 歸檔 | Archive 不硬刪 Notebook，Archive 不破壞歷史 Source/Hash | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回歸 | 重跑 S1 全流程和單庫恢復；新版本資料可重建索引 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | I 準備 | 受控 create 使用外部冪等鍵、可由服務帳戶呼叫；此期不連接 B | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Canonical A API | 全部 Stage2 A operationId/path/method 對應 OpenAPI，Consumer Fixture 真實執行 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 舊來源版本 | Version 3 被新 Version 4 替代後仍可按 immutable ID/hash/locator 取得合法受保留版本 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 權限失效 | 來源被撤銷/封存時 A attest 返回可辨別狀態，禁止供外部 AI 使用 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 冪等鍵差異 | 相同 Idempotency-Key 同 Body 重放回舊資源；不同 Body 回 409 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT12 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Cutover 模式 | STANDALONE→FREEZE→MANAGED 經受控 Admin API，只封鎖新 Create，不封鎖舊 Search/Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT13 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S2-AT14 | 已部署該 Stage 相應服務與專用測試資料 | 受控服務授權正向與越權／異常負面測試 | 所有供 I 使用的 A API 均用 service audience+scope+resource ownership，拒絕 Admin Token 借用或 ServiceToken 跨端點升權 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S2-AT15 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 供 S4 的 Cutover 受控 API | A 已具獨立 Service scope、唯一 Create/Managed-mode 封鎖及 Manifest/Health 前置契約，I 不需改 A | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON Source topics, timestamps, source list/filter/search, embeddings, text/vector search, ingestion status。
- **不應重造的部分：**第二套 PDF 抽取器、Embedding Store、搜尋引擎或一般來源列表 UI。
- **Sunrise 仍須自己交付的能力：**版本化內容 Catalog、School/Source 權屬、發布狀態、原檔 Hash、權利政策、A versioned scoped service APIs、Consumer Fixtures。
- **當期風險／不可與前期撞：**上游 updated_at 不等同不可變 SourceVersion；Search results 為動態 Dict，引用 Locator 不保證長期穩定。
- **後續 consumer／依賴影響：**S4 I Create/Adopt、S5 I Proxy、S9 Evidence、S23 Teacher Read 用同一 A Manifest/Scope；不直接連 B DB。
- **真實試用入口：**A-local source metadata editor + 同 Scope 結果／版本查詢。正式 R02 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
