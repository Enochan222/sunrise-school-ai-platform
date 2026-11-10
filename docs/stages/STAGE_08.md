# Stage 08 [B] — Durable Generation Queue & Draft Review

**Release:** `R08` | **Exactly one owner:** `B` | **Technical prerequisites:** S6, S7 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

在 B 完成不用 Notebook 也能工作的 Queue→Prompt→Schema Validation→Draft→人工批准。

**完成後可親自試用：**Admin 在 B 測試入口輸入 Course/Blueprint，建立生成任務、查看 Queue/Retry/失敗、批准草稿，產物留 B。

### 2. 驗收：甚麼情況才可以標記完成？

- 有真實持久化 Queue、任務狀態與重試；重送不產生兩份正式已批准 Artifact。
- Prompt/Model/Blueprint/Rubric Version 可追溯，格式／題數／分值錯誤不能發布。
- 沒有 A Service／Notebook 時仍能 B-only 生成；人工批准前產物只是草稿。
**本期原有驗收設計：**`S8-AT01–S8-AT13`（13 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- AI 生成可錯；必須保留人工審核與成本／失敗可見性，不可直接當試卷發布。
- Queue 不保證 exactly-once 模型執行，需防重複提交與資料污染。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 依賴 S6 Schema、S7 Provider Key；不得在此期改 I 或偷偷使用 A RAG。
- B 原有 Course 及 Assessment 草稿概念不能被 AI Job 偷換主鍵／狀態。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S9 的可選 Evidence Bundle 要接入已定義的受限入口；若 B 缺失要在 B Owner 版本補齊，不能 S9 偷改。
- S10 UI、S11–S14 學科出卷與 S19 Marking 會沿用 Job／Model／Draft 版本。
**明確技術前置：**S6, S7。**直接依賴本期的後續 Stage：**S9, S11, S19。

### 6. 暫定參考，暫時不作技術承諾

- 具體 Queue／Worker、Prompt 模板、LLM SDK、成本控制策略屬實測選型；最低可試用能力和資料歸屬不可改。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B-only Queue→Prompt/Model→Question Schema+Domain validator→Draft→Human Approve，沒有 A Notebook 也可使用。

## Complete user flow

Admin→Blueprint/Topic→Queue Job→Generate→Validate→Review/Edit→B Artifact。

## Data / Source of Truth

B jobs/prompt_version/model_id/question_versions/artifacts/provider_reference; optional **disabled-by-default** evidence input contract。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/evidence-bundles` (`ingestEvidenceBundle`; auth=service; scope=core.evidence.ingest) — Signed generic evidence intake; MUST revalidate at job use via issuer callback
- `GET /core/v1/evidence-bundles/{bundle_id}/status` (`getEvidenceBundleStatus`; auth=admin_or_service; scope=core.evidence.read) — Short-lived evidence validation status
- `POST /core/v1/generation-jobs` (`enqueueGenerationJob`; auth=admin_or_service; scope=core.job.enqueue) — Durable B-only queue; optional evidence off by default
- `GET /core/v1/generation-jobs/{job_id}` (`getGenerationJob`; auth=admin_or_service; scope=core.job.read) — Job status/provider/model/prompt/version/citations
- `POST /core/v1/generation-jobs/{job_id}/approve` (`approveGenerationJob`; auth=admin) — Human approval only


## Not in this Stage

不調用 A；不假稱 RAG 已完成；API Key 不傳入 Job Payload。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Independent B trial:** This Stage provides a protected B local Admin interface and persistent test workflow. It must remain testable even without new U work.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S8-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 真 Queue | 崩潰重試及並發可完成，工作狀態真實 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B-only 生成 | 沒有 A Notebook 也能由 Blueprint 產生有效 Draft | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 模型治理 | 固定 Prompt、Model、Schema Version，可追溯輸出 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 結果驗證 | Schema、總分／題數／內容約束 FAIL 時不允許批准 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 人工批准 | AI 不可直接 Publish，只有 Admin Approve | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 冪等 | Queue 重複投遞不會產生兩個正式 Artifact | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 資料隔離 | B Worker 不持 A DB 密碼、不讀 A Notebook | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Generic evidence input | B-only 無 Evidence 可生成；接收者支援 issuer/JWS/jti/purpose/binding_version + preuse validation hook（未開 I 時不用） | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT09 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Queue 防重 | 丟 ACK 或 Worker 重啟都不能雙重 Publish；避免聲稱 API exactly-once | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT10 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 檢查層次 | JSON Schema、Domain Answer、citation required if supplied、Human Review 四層獨立 Gate | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT11 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S8-AT12 | 已部署該 Stage 相應服務與專用測試資料 | Evidence Service Token正向與越權／異常負面測試 | I S9 以 B `core.evidence.ingest` Service Scope 附簽名 Evidence，B 驗證 audience/purpose、使用期限、來源版本，不接受 Admin Token 代替 I | HTTP Traces / Consumer Contract / SHA / Timestamp / Owner UAT |
| S8-AT13 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | Evidence Worker 正式前置 | B Worker 具獨立 ServiceToken 及 Source/Job Context，S9 上線前 Evidence OFF；上線後同 Job 可重新驗證 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON 內部 surreal-commands 僅用於 A 文件處理；可借鑑任務狀態 UI。
- **不應重造的部分：**將 A Worker Queue 直接當 B durable paper/marking queue；聲稱 upstream job cancel 完整可用。
- **Sunrise 仍須自己交付的能力：**B durable Queue + idempotent jobs/attempts + Prompt Model audit + Draft validators + Human approval。
- **當期風險／不可與前期撞：**ON `CommandService.list_command_jobs()` 仍返回空列表，`cancel_command_job()` 只 log/return True；與 B 完整 job lifecycle 不等價。
- **後續 consumer／依賴影響：**S9 I 可選 Evidence；S11–14 用既有 Job 基礎；S19 Marking 借用 B Queue。
- **真實試用入口：**B-local job console，真實 draft 可批准保存。正式 R08 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

**候選現成依賴（須本期驗證）：**可優先評估 Supabase Queues（pgmq durable logged queue）而非自行實作訊息佇列；visibility timeout 仍會重送，正式 Artifact 必須靠 B 冪等交易防重。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
