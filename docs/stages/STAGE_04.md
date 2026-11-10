# Stage 04 [I] — Course–Content Linking & Core Recovery

**Release:** `R04` | **Exactly one owner:** `I` | **Technical prerequisites:** S2, S3 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

由獨立 I 服務透過 A/B 已發布 API 完成舊教材接管、新課程建立及可恢復的課程綁定。

**完成後可親自試用：**Admin 由 I 明確選 B Course 與 A Shell：預覽、接管、建立／查驗 Notebook；故障重試後連結仍唯一且可查。

### 2. 驗收：甚麼情況才可以標記完成？

- ADOPT_EXISTING 不創建第二本 Notebook；CREATE_NEW 先 B Reserve、再 A Create、最後 B Finalize/Read-back。
- 對 ACK 遺失、重試、撞 Key、孤兒資料、Scope 漏洞及兩邊不同時間 Restore 可以偵測／隔離，不靜默刪資料。
- I 部署沒有 A/B Database DSN，也不修改 A/B Schema/Code；全程只用已驗收的 Service API。
- S5 所需 Course Materials List/Upload/Search/Download 代理在授權與來源檢查下實際可用。
**本期原有驗收設計：**`S4-AT01–S4-AT21`（21 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- I API 呼叫兩邊是正常業務操作，與「單 Stage 改兩套 DB 程式／Schema」不同，必須在 PR 中分清。
- Cutover 中斷需保留唯讀與人工修復方法；不能以自動刪 Notebook 作 Saga 補償。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不得在 I 內重寫 S2 A / S3 B 合約；缺 API 必須回到該 Owner 另出版本。
- 保留已存 A 原檔/Hash、B Course ID／CONTENT_UNLINKED 史，無憑名字猜測配對。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S5 U、S9 I Evidence、S23 教師讀取均依賴 Course→Shell 的完整可信 Binding。
- S28 只是後期監控 Dashboard，S4 的核心對帳／恢復不能推遲。
**明確技術前置：**S2, S3。**直接依賴本期的後續 Stage：**S5, S9, S23, S28。

### 6. 暫定參考，暫時不作技術承諾

- Saga 補償、重試間隔、Queue 技術及 API 欄位細節是實作選項；唯一性、失敗封閉及保留資料是必守結果。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

首次 I-only API 整合：安全接管已存在 Shell、新 Course Provisioning，B durable Op Log + A idempotent journal，可對帳及失敗恢復。

## Complete user flow

Admin 選 B Course/A Shell→Dry-run→B reserve→A verify/adopt or provision→B finalize→Read-after-write verify→ACTIVE／Quarantine。

## Data / Source of Truth

I 不持權威 DB；B 操作記錄、A 建立操作；兩套源資料完全獨立。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /link/v1/adoptions/commit` (`commitAdoption`; auth=admin) — Non-destructive adoption API saga
- `POST /link/v1/adoptions/dry-run` (`dryRunAdoption`; auth=admin) — Explicit B Course + A Shell stable key preview
- `POST /link/v1/course-provision` (`createUnifiedCourse`; auth=admin) — Provision B course and A shell over existing APIs
- `GET /link/v1/courses/{course_id}/content` (`listLinkedCourseContent`; auth=admin) — Server resolved course binding and A source owner check
- `GET /link/v1/courses/{course_id}/materials` (`listCourseMaterials`; auth=admin) — List materials after B binding and A owner verification
- `POST /link/v1/courses/{course_id}/materials` (`uploadCourseMaterial`; auth=admin) — Admin upload through controlled I to owner A API
- `GET /link/v1/courses/{course_id}/materials/{material_id}/download` (`downloadCourseMaterial`; auth=admin) — Download A material after B course + A source check
- `POST /link/v1/courses/{course_id}/search` (`searchCourseMaterials`; auth=admin) — Course-scoped A search via I verifying B binding
- `GET /link/v1/operations/{operation_id}` (`getIntegrationOperation`; auth=admin) — Read B+A operation statuses via APIs
- `POST /link/v1/operations/{operation_id}/retry` (`retryIntegrationOperation`; auth=admin) — Idempotent retry after crash/timeout
- `GET /link/v1/reconciliation` (`getCoreReconciliation`; auth=admin) — S4 mandatory core repair/orphan/partial operations report


## Not in this Stage

不得在 I 期改 A/B schema/code/network/credentials 或執行資料庫直連。

## Real deployment and operations（原規劃參考與實測要求）

This is a I-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Contract Freeze:** 需在本期提交可驗證 OpenAPI JSON、Context/Idempotency Fixture、Consumer Contract Test。不得一邊做 I 一邊修改 A/B。

**Critical:** S4 has two separate `ADOPT_EXISTING` and `CREATE_NEW` state flows and mandatory Core Reconciliation. See [state machine](../architecture/PROVISIONING_STATE_MACHINE.md). The dashboard is S28; *correctness is S4*.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S4-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | API-only | I 容器沒有 A SurrealDB/B Postgres DSN，防火牆禁止直連兩庫 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 舊資料接管 | S1/S2 原 Notebook/Source/Hash 不變，B 唯一 Binding | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Create Saga | 新課程由 I 建 B Course+唯一 A Shell/Notebook，半成功可重試 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 課程隔離 | Course A/B 假 ID、空 Scope、Source 夾帶均拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Cutover | 啟用已預建 A `managed-mode`／B binding policy，停止不受管獨立建新的 A Shell | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 失敗回退 | I 停機仍保留原 A、B 資料；可讀回舊各自 UI；Orphan quarantine 不自動刪 Notebook | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 聯合對帳 | 用 API 比較 Manifest/Binding；不在本期修改 A 或 B Schema/Code | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B 先 A 後 | CREATE_NEW atomic B Reserve 才 A Provision，再 B Finalize；ADOPT_EXISTING 不做 A Create | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | ACK 遺失 | A 已建而 I timeout、B 已 finalize 而 I timeout 都能根據雙方 operation ID 重放而無重複 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 狀態機 | 合法 transition 與 RETRYABLE/CONFLICT/QUARANTINED 判斷符合機器可驗 contract | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 核心對帳 | ACTIVE 前 A/B 雙側 Read-after-write、link_key、binding_version、Source Hash 一致 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT12 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Cutover 失敗 | 切換至 MANAGED 中途 I crash：封鎖新 Create，但 A/B 已有資料可讀且可恢復 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT13 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 跨庫恢復 | 隔離環境各自 Restore A/B 後，用 I API Manifest 比對；不同 Snapshot／缺 Binding 阻止 READY | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT14 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 回退兼容 | I 停用後 A/B 只讀可繼續，永不因 Saga 補償刪 A Notebook | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT15 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 無 DB 接線 | I Runtime 無 SurrealDB/Postgres DSN、無直接 DB egress，API-only Contract 可驗 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT16 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S4-AT17 | 已部署該 Stage 相應服務與專用測試資料 | I 教材列表代理正向與越權／異常負面測試 | 從 B Binding 驗證 Course，經 A service-only Scope 列出 Material metadata，不泄露其他 Shell | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S4-AT18 | 已部署該 Stage 相應服務與專用測試資料 | I 教材上載代理正向與越權／異常負面測試 | Admin→I→A 上載用獨立 ServiceToken，驗證檔案類型／限額／Idempotency，I 不存原檔 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S4-AT19 | 已部署該 Stage 相應服務與專用測試資料 | I 限課程搜尋代理正向與越權／異常負面測試 | I 以 course_id 找出唯一 A Shell，拒絕空 Scope、跨 Shell、偽造 source_id，從不轉發任意 Notebook ID | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S4-AT20 | 已部署該 Stage 相應服務與專用測試資料 | I 教材下載代理正向與越權／異常負面測試 | I Stream A 下載，每次驗證 B Binding+A Owner，阻止過期／偽造資源、Content-Disposition 安全 | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S4-AT21 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | School+Group 跨服務完整性 | I Adopt/Create 核對 School ID 與 Course Key，跨校／模糊 Group 不可錯綁；Cutover 後不能由 A raw Create 旁路 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S2 A service API + S3 B service API only。
- **不應重造的部分：**自行建第二套 Notebook／從 I 直連兩個 DB／將 ON raw Secret 放 I。
- **Sunrise 仍須自己交付的能力：**I Create/Adopt Saga、A/B immutable IDs、冪等、故障查詢/重試/隔離、跨服務讀回與最小 restore reconciliation。
- **當期風險／不可與前期撞：**S3 B Reserve/Course 原子操作；A Create ACK loss；S4 Cutover 半完成；不能自動 Delete 已建 Notebook。
- **後續 consumer／依賴影響：**S5 U 與 S9/S23 檢索均靠 ACTIVE Binding；不以同名 Course 自動配對。
- **真實試用入口：**I-only Link Console + 兩邊既存 API 操作紀錄。正式 R04 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
