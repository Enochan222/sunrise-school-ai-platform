# Sunrise Education AI Platform — Stage 1 [A] Minimal Implementation Plan v1.1

**正式規劃交接版（唯一有效的 Stage 1 Builder Handoff）**  
**整合日期：**2026-11-11（Asia/Singapore）  
**Planning Gate：COMPLETE** · **Implementation：NOT_STARTED** · **S1-AT01–15：NOT_RUN** · **R01：NOT_APPROVED**  
**輸入：**《Stage 1 Engineering Planning Package v1.0》及《Stage 1 Minimum Necessary Implementation Review》。本文件取代兩份舊文件作為 Builder 操作次序、Scope 和工程驗收的單一交接版本；不修改或取代 GitHub `main` 的正式決策與 Stage Card。

## 0. 如何使用、權威來源與已核對事實

**給非技術 Owner：**先看 §1、§10、§11、§12；不需決定程式庫、SurrealDB query、Notebook ID 生成方式或錯誤處理 patch。要開始本地合成資料開發，只需在新 Builder Chat 發送 §11 的初始 Prompt；該 Prompt 本身即明確授權其限定範圍內的本地工作，**不授權 GitHub 寫入、公開部署、付費 API 或真實資料**。

**給 Builder：**按 §4 WP00→WP09 依賴執行；先解決 §5 三個定向技術試驗，完成每包局部驗收後才進下一包。正式 Acceptance 以 §6 為逐項追蹤表。任何設計與正式 GitHub `main` 衝突時，**GitHub `main`／已批准 D01–D08／正式 Stage Card 與 AT 優先**；不可自行降低 AT。

### 0.1 正式來源與版本

| 層級 | 來源／事實 | 證據性質 |
|---|---|---|
| GitHub 權威基線 | `Enochan222/sunrise-school-ai-platform` `main` = `744fbbd0ac3b479c80782d6a990c7bfed093f4dd`，Git Tree `ff8d9a99caab2f31be46156f7b5faa952b6d61f0`；本次唯讀重新核對 | 已核實 GitHub 狀態 |
| 批准 | `stage0/STAGE0_BASELINE.json`：Stage 0 `APPROVED/COMPLETE`；`docs/decisions/STAGE0_APPROVAL_DECISIONS.md`：D01–D08 八項 bounded architecture approval | 已批准的**規劃／架構原則**，不是 runtime/付款授權 |
| Stage 及 API | `AGENTS.md`、`docs/quality/STAGE_REGISTRY.json`、`docs/stages/STAGE_01.md`、`docs/architecture/API_INVENTORY.json`；S1 為 A Owner、R01、依賴 S0、15 個 AT、8 個候選 API operations | 正式目標和 AT 必守；API 路徑細節是候選，需實測 |
| Stage 依賴 | `docs/stages/STAGE_02/03/04/05/22/23/26.md`、`docs/product/ROADMAP.md`、`docs/architecture/BOUNDARY_RULES.md` | 已在前兩份 Review 中逐項核對；本次保留邊界 |
| 上游版本 | `lfnovo/open-notebook` Commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239`（v1.15.1），Git Tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af` | Git 原始碼已核實；**正式執行 Image Digest 與 Source/Dependency 等同性尚未驗證** |
| 實作狀態 | Stage 1 `NOT_STARTED`；Runtime、Security、Persistence、Restore、Owner UAT 均 `NOT_RUN` | 不得誤報成功 |

**需要讀的 GitHub 文件（Builder 開始時重新讀取當前 main）：**`AGENTS.md`、`stage0/STAGE0_BASELINE.json`、`docs/decisions/STAGE0_APPROVAL_DECISIONS.md`、`docs/delivery/STAGE1_START_CRITERIA.md`、`docs/delivery/STAGE_01_EXECUTION.md`、`docs/stages/STAGE_01.md`、`docs/product/STAGE_BOUNDARY_MATRIX.md`、`docs/product/ROADMAP.md`、`docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md`、`docs/architecture/BOUNDARY_RULES.md`、`docs/architecture/SECURITY_AND_AUTH.md`、`docs/architecture/API_INVENTORY.json`、`docs/delivery/QA_ENVIRONMENT.md`、`docs/quality/STAGE_REGISTRY.json`、`docs/quality/CONTRACT_GAP_REMEDIATION.md`，並核對 S2、S3、S4、S5、S22、S23、S26 卡。若最新 main 不同，先生成差異及影響報告、不要自行覆蓋新決策。

### 0.2 不得變動的 D01–D08 邊界

- **D01：**A Open Notebook/SurrealDB；B PostgreSQL；I API-only；U Frontend-only。S1 只修改 A，絕不修改 B/I/U runtime/schema/config。
- **D02：**未來 B Course 粒度為 `(school_id, academic_year, grade, subject, curriculum_stream)`；S1 A Shell 已保存同五維分類，但 **不是 B Course**；Shell↔Notebook 一對一，不依標題配對。
- **D03：**A `school_id`、Source ownership、rights、retention、approved-sharing、不可變初始版本/Hash、每次讀取前後授權。絕不暴露 raw ON 管理 API。
- **D04：**S1–S21 可用一個受控 Admin；必須保留 stable `actor_id`／School／Audit；只用合成資料。S22 才做教師／Staff IAM。
- **D05：**重用 v1.15.1 ON Notebook/Source/Worker/Extraction/Search；A-only 原檔下載及 Restore；Gemini/Cloud Embedding/AI Chat 默認 **OFF**，禁止未批費用或對外傳輸。
- **D06：**S4 才做 I 的 ADOPT_EXISTING / CREATE_NEW、跨庫 Saga 和 Cutover；S1 只負責**本地**安全冪等。
- **D07：**不授權付費服務、真實學校／學生資料、公開 Staging／Production、外部 AI。部署 Region、預算、權利／保留、隱私、Secret Store 等在真正 Hosted Gate 前另批，不阻止本地 Synthetic Dev。
- **D08：**不使用 GitHub Actions 或 Copilot；未獲單獨許可不對 GitHub 寫入；日後 A-only PR、Squash、手動可核對 QA；無可靠自動 Gate 時不可 unattended auto-merge。

## 1. 最小產品成果與 Architecture（Builder 不可加戲）

### 1.1 R01 唯一必要 User Journey

**一個受控 Admin，受保護 HTTPS 入口** → 建立 A Content Shell → 產生**唯一** ON Notebook → 上載經實測的 **born-digital、可抽文字 PDF** → 沿用 ON 抽取與原生 Worker → **同 Shell、非空 Scope 的 Text Search** → 取得**原始 PDF** → 非破壞性 Archive → Logout/Restart → A-only Backup → 在**隔離環境** Restore → 相同 ID、版權資料、初始 Version、SHA-256 和安全搜尋仍正確。

同一個 Admin 使用**兩個合成 School**（A/B）作授權負面測試：active School A 時，即使知道 School B 的 Shell/Source ID 也無權直接查；切換 School 必須透過可信 Session 流程，不接受單靠任意 request header 指定 school_id。

### 1.2 最少可行部署拓撲

```text
Browser（唯一 Admin；HTTPS；安全 Session、CSRF）
  -> A-owned Minimal Vault App（目標 1 個應用進程：小頁面 + 8 A API + Policy + Journal）
       -> A SurrealDB 中極少量 Sunrise 記錄
       -> Private Open Notebook API（原生 Notebook/Source/Extraction/Text Search）
            -> 現有 ON Worker + SurrealDB + 原始檔 Volume

其他外部入口：Native ON UI/API/Docs/Preview/SSE/DB/Worker 全部不可達。
外部 AI、B DB、I、U、另建 Queue、Vector Service、第二套 Extraction/Storage：無。
```

現有反向代理／TLS／私有網絡設定可以沿用。**「一個 A App」只是成本目標，絕不能凌駕安全隔離；若需要獨立的最小 Gateway 或 ON 私有 patch 才可隔離 raw API，就必須保留並測試。** 不把 ON 原生 shared password 當 Sunrise School ACL。

### 1.3 最小 A 資料記錄（設計目標，需以 Runtime Constraints 證明）

| 記錄 | S1 必須保存／唯一性 | S1 不做 |
|---|---|---|
| `content_shell` | immutable `shell_id`, `school_id`, `academic_year`, `grade`, `subject`, `curriculum_stream`, stable external key（如使用）, immutable `notebook_id`, `created_by_actor_id`, archive status/time；School、學年、年級、科目、課程流五維 A classification 唯一、Notebook 不可重複掛 Shell | B Course / TeachingGroup、S4 Binding、全套 Cutover |
| `source_owner` | unique logical `source_id` → 同一 `school_id`,`shell_id`,`notebook_id`；`initial_version_id`／不可變初始 marker、原始 `sha256`、原檔 native locator、filename/type；rights owner、license、basic retention、`approved_sharing=false`、`ai_usage_allowed=false`、created_by_actor、archive/availability；ON 真實 `reference` 關係必須一致 | 多版本發布、完整版本 lineage、attestation、跨 Shell mutable Source 共享 |
| `vault_operation` | 唯一 `(school_id, actor_id, kind, idempotency_key)`、canonical request hash、state、穩定預留 ID／ON recovery marker、結果 locator、timestamps；同鍵同 Body 回原結果，撞 Body 409；中斷可 Read-back 或 Fail-closed Quarantine | 分布式 Saga、B operation log、通用 Job Queue |

**最低表數非硬限制。** 若安全稽核不能由耐久、可復核及已證明可 Restore 的 redacted log 實現，增設最小 A audit record；不可因追求「三表」放棄 D04。原檔不可由 Archive/Delete 意外清除。初始 Version ID／Hash 必須固定，不可用上游 `updated_at` 代替不可變版本。未完成 / 不一致的 Source 不應對 Search/Download/List 以 READY 狀態可見。

### 1.4 必須保留的八項 S1 A API（正式 Inventory **候選**）

| Method / Route | 最小語義（身份／Scope 完全 Server-side） |
|---|---|
| `GET /vault/v1/shells` | 只列 active School 的 Shell |
| `POST /vault/v1/shells` | 本地 idempotent Shell + 唯一 Notebook Create；同鍵異 Body 409 |
| `GET /vault/v1/shells/{shell_id}` | 有權 Shell 的資料／Archive 狀態 |
| `POST /vault/v1/shells/{shell_id}/archive` | 非硬刪；只封存，按基本權利政策仍可查合法歷史 |
| `GET /vault/v1/shells/{shell_id}/materials` | 權限／Owner／Native reference 每項確認；初始 version、hash、processing status |
| `POST /vault/v1/shells/{shell_id}/materials` | 有限 PDF 上載、server validate、safe native ingest，Hash、owner／operation 紀錄 |
| `GET /vault/v1/shells/{shell_id}/materials/{material_id}/download` | 校驗認證、School/Shell/Source、原檔 Hash/path，**傳任何 byte 前**決定授權；非公開 URL |
| `POST /vault/v1/shells/{shell_id}/search` | server 固定唯一 Notebook Scope、`type=text`、`search_sources=true`、`search_notes=false`，逐筆 Owner/Native Edge 二次驗證 |

**Service-auth 最小邊界（AT14）：**對 Inventory 標為 `admin_or_service` 的實際路由，實作一個**嚴格、可離線測試的 JWT ServiceToken 驗證器**，不建 Issuer 或發證平台。由受控離線測試程序預先簽發**合成測試 token**，verifier 驗簽並檢查固定 `alg`/可信 `kid`、issuer、audience、subject、exp/nbf、jti、列明 scope、school/resource ownership、具體 endpoint allowlist；失效／錯誤 Scope／錯 School／拿 AdminSession 冒充服務／拿原生 ON password 冒充均拒絕。Read Token 可重用但必須可審計；Mutation 用 durable operation/idempotency 防重播。生產金鑰與真實 provisioning 留 S2；若 S1 無法證明最小 verifier 安全，禁止先放行 Service 模式。AT14 的 Admin 和 Service 分支均需真測，不可當成「Service optional 所以跳過」。

**不公開**：Native ON UI、原生全庫 GET/POST/DELETE/Link、`/sources/json`、Preview、SSE、AI Ask、Vector、URL import、一般 Credentials 管理、Podcast、Transforms。對外 404/403 是**正確的 S1 負面驗收結果**；但原檔下載仍會串流 bytes，必須真正驗證首 byte 前授權。S2 的五項 API（Cutover/Provision/Operation/Manifest/Attest）**不在 S1 實作**。

## 2. 相對 v1.0 的最終差異（不可把舊包較廣指示帶入 Builder）

| 原 v1.0 做法 | v1.1 最終處理 | 分類／理由 |
|---|---|---|
| 每個 WP 對應一個 PR（10 個） | WP 仍 10 個 Gate，但建議 2–4 個審查邊界，PR 數由實作需要決定 | **SIMPLIFY**；PR 數不影響安全驗收 |
| Vault Gateway + 較完整獨立管理前端 | 目標單一 A Vault App + 最小 Admin Page；若需網絡隔離另加小 Gateway | **SIMPLIFY**；不要重建 S5 U |
| Shell / Owner / VersionSeed / Operation / Audit 五類獨立表 | 目標 `content_shell`、`source_owner`、`vault_operation`；initial version 併入 SourceOwner，Audit 可證明時重用日誌 | **SIMPLIFY**；資料不變性高於表數 |
| 完整 Upload State Machine、第二份暫存 blob 倉或 Queue | REUSE ON file/worker/status；只補必要 idempotent upload operation、孤兒 reconciliation | **SIMPLIFY/REUSE**；不能假裝破壞恢復已通過 |
| General Job listing / Cancellation API | 不做；native job status + 預設 worker 能力足夠，Retry 問題需定向修復 | **REMOVE**；上游 list/cancel 並非完成品 |
| Preview/SSE/Ask/Vector mediation | 不對外開放，對外做 route/byte-negative test | **REMOVE**；不須做安全 Streaming Proxy 功能 |
| 全套 AI provider / OCR / 更多檔案格式 | Gemini/Embedding/AI Chat OFF；born-digital PDF 必做，`.txt` 僅可選 | **DEFER**；PDF Hash 是 AT12，不可刪 |
| Full Auth/IAM/教師身份架構 | 單 Admin、Session、CSRF、受限 Service verifier；不建立 IdP、教師 Role/Grant | **SIMPLIFY/DEFER**；完整 IAM S22 |
| 全套 A Version / Publishing / Provenance Service | immutable initial ID/Hash/rights；正式多版本 Catalog/Publish/Attest S2 | **DEFER**；AT12/14 仍完整 |
| 本地冪等 + Cross A/B 編排 | 只做 A-local durable Create；I Saga/Cutover S4 | **DEFER**；AT06 仍必過 |
| 完整 Backup 平台／定時 Dashboard | 最少受控 Runbook、Consistency Point、密鑰保管及隔離 Restore 實測 | **SIMPLIFY**；AT05 不准降級 |
| 其他 Owner Runtime | 完全不建立／修改 | **REMOVE FROM S1**；D01 Single Owner |

## 3. Builder 共同工程規則（每個 WP 均適用）

1. 優先使用已 pin 的 Open Notebook Notebook/Source/Worker/Extraction/Text Search/SurrealDB／既有 UI component。新增 A Code 只做 **Policy、唯一性、初始 provenance、必要 API/UI、秘密檢查、可恢復性**；不用新 broker、DB、Vector Engine、全新 Extraction Engine、額外外部 API。
2. 所有外部請求先 Authn→讀可信 active School/Actor→對 Shell/Source/Notebook 作 Authz→調用私有 ON→逐結果 Post-check；無法判斷 Ownership 則 fail closed。**Search limit／Scope 只由 server 生成**；不准 empty＝global，亦不接受 client 隨機 notebook/source ID 作權限。
3. 所有原生 endpoints / DB / ON UI 僅內部網絡。服務需在 Password、Encryption Key、DB Credential 缺失、空值、示例、root:root 或不安全配置時直接拒絕 serving；不要只記 warning。必要時最小 A-only patch，不修改上游大範圍。
4. 僅有限、合成、born-digital PDF：type/magic/size/path、危險內容、失敗 cleanup、原始檔不丟。禁止上傳真實教材、學生資訊／私隱資料。嚴禁向外部模型傳內容；部署及供應商配置不可默默開。
5. 建立及上載操作可重試且不產生錯誤重複、錯 Owner、跨 Shell Reference。故障後 readback／reconciliation；無法安全恢復則 quarantine 並向 Builder 技術 reviewer 升級，不 auto-delete notebook。
6. **每 WP 證據：**精確 Git SHA（若純本地未 commit 則明確記本地 snapshot/hash，不偽稱正式 Commit）、pin 的 ON commit/tree/實際 image digest、環境／依賴版本、測試指令及 exit code、UTC timestamp、匿名合成 fixture ID、redacted stdout/stderr／HTTP／DB 或檔案 SHA、正反例、回歸／修正追蹤，AT ID。失敗要標 FAIL/NOT_RUN，不可以文案代替測試。
7. 所有 A-only schema 變更需說明可 rollback/forward-fix 和 A Restore；其他 Owner runtime/image/schema digest 不變。未獲 Owner 許可不寫 GitHub，不建立 Issue/Branch/PR、無 Actions/Copilot/auto-merge。

## 4. WP00–WP09 — 可執行 Execution Checklist

> 每個 WP 是獨立 Review／Evidence Gate，**不是**要新建一個 Microservice。Builder 可先用本地 synthetic fixture 執行；實際 Hosted R01 Gate 仍在 WP09 才審核。

### WP00 — Pin、源碼與最小技術試驗（依賴 S0）

- [ ] 讀最新 `main`、正式 AT/owner/API 設計；記錄本地工作樹來源、固定 ON commit/tree/tag、第三方 LICENSE、Build/Dependency、最終 Image Digest 或 image build provenance；不能使用 moving `latest` 作 R01。
- [ ] 只讀列出 Native 路由和 Browser/DB/worker ingress／egress；標註哪些管理／SSE／Preview／Global Search 必須全封。識別 source→notebook graph link/unlink route；特別檢查刪 link 的方向是否一致。
- [ ] 執行 §5 的三個**最先** Runtime Spike：Notebook ACK-loss、`embed=True` Retry、Text Search fallback；Spike 只能用合成 fixture，無外部 AI。每條先記 Repro，再選最小修補法。
- [ ] **正例：**本地 pin 源能啟動且合成 PDF 處理、最小 scope probe 有可追蹤結果；**負例：**錯 tag/image、示例 secret、錯誤 native port 設定可被偵測。
- [ ] **Evidence：**Source/tree/image manifest、路由清單、3 個 Spike logs、可用性／patch 需求表。**STOP：**找不到來源等同性或某核心功能只能依賴未批 provider；停止對外準備，繼續在 sandbox 隔離調查或提交技術決策。

### WP01 — 封閉原生入口（依賴 WP00）

- [ ] 用現有 private network/TLS/reverse proxy 設定令**只有 A Vault 受控入口**可達；ON UI/API、SurrealDB port、Worker、Docs/OpenAPI、raw Preview/SSE、route aliases、debug 入口全部不公開。不建立永久 Network Dashboard。
- [ ] 從**Vault 以外的獨立測試網絡來源**探測 GET/POST/PUT/DELETE、source link/unlink、global list/search、DB port；記 HTTP／TCP 證據。Gateway 內網仍能呼叫 ON。
- [ ] **Evidence：**Network boundary diagram、綁定 address/firewall rules、external scan/traces（redacted）。**STOP：**任何非授權原生路徑在可達網絡成功，先隔離，不做 WP07 UI 或 staging expose。

### WP02 — 單 Admin、Secrets Fail-start、最小 Service 驗證（依賴 WP01）

- [ ] 用現成可靠 session/auth libraries 實作單 Admin Login／Logout／Expiry；HTTPS、Secure/HttpOnly/SameSite Cookie、CSRF protection、rate limiting、server-held active School context、redacted audit。不要建 teacher IAM、external IdP 或 Token Issuer。
- [ ] 啟動時拒絕缺失／空／示例值：`OPEN_NOTEBOOK_PASSWORD`、`OPEN_NOTEBOOK_ENCRYPTION_KEY`、A DB credentials、需要的 session signing secret；確保 DB `root:root` 不作正式密碼。On startup 不只 warning。
- [ ] Inventory 標為 `admin_or_service` 的端點沿用**同一個最小 JWT verifier**：offline-provisioned synthetic signed ServiceToken、固定 issuer/audience/signature/expiry/subject/jti/scope/School，endpoint allowlist、逐資源 ownership。讀取 token 可重用且會審計，寫入需 idempotency；不需要在線簽發平台。
- [ ] **正例：**Admin 登入、切換合成 School；受限 Service 可列出獲准資料。**負例：**匿名／偽 Session／過期／錯 audience/scope/school／仿造 ON password、CSRF、缺 secret 各自拒絕 serving 或 operation。
- [ ] **Evidence：**登入/登出/失效測試、JWT claims 負面矩陣、Startup fail logs、Audit sample。**STOP：**任一缺密鑰仍 serving，或 Service token 可越權，立即 Fail。

### WP03 — Shell↔Notebook 本地冪等（依賴 WP02；復用 ON Notebook）

- [ ] 建立最小 `content_shell`、`vault_operation`；唯一粒度包含 `(school_id,academic_year,grade,subject,curriculum_stream)`；保留 stable actor/shell/notebook ID；Archive 不釋放 identity 唯一鍵、不靠標題配對。
- [ ] 調用私有 ON Notebook Create；**需先證明** operation key 與 ON side effect 可原子識別／可 readback（詳 §5.1）。相同 operation key+canonical body replay 回同 ID；不同 body 409；並發只一 Notebook。
- [ ] **正例：**一 Shell 一 ON Notebook、重啟後查到；**負例：**kill after native create before ACK、parallel double create、跨 School/stream collision、改 payload reuse key。不得直接調用原生 Notebook hard-delete 補償。
- [ ] **Evidence：**事務／唯一索引證據、ON notebook ID count、fault-injection logs、before/after journal。**STOP：**會重複建 Notebook 或只能靠名字猜測識別；先作最小 A-local 技術修正。

### WP04 — Source Owner＋原始版本／版權（依賴 WP03）

- [ ] 建立最小 `source_owner`；上載前設定可信 school/shell/notebook、初始 version ID、原檔 SHA、license/rights-owner/retention、`ai_usage_allowed=false`、`approved_sharing=false`、actor/audit。不可在 Source 建立後靠 title 自動歸類。
- [ ] 只允許 native Source 對**一個** ON Notebook 擁有正式邏輯 ownership；驗證 native `reference` 圖實際方向。任何越權或異常多重關聯都拒絕讀取／標 quarantine。
- [ ] **正例：**兩 School 多 Shell、SourceOwner ↔ ON reference 一致；Archive 後仍留資料。**負例：**猜 Source ID、跨 Shell link、注入缺失／錯誤 Edge、改初始 SHA/Version。**Evidence：**Source/rights/graph snapshot、拒絕 trace。**STOP：**可讀錯學校檔或原生 Source 刪除令原檔流失。

### WP05 — 重用 Upload／Extraction／Worker，無 AI Retry（依賴 WP04）

- [ ] 上載**至少一種** born-digital searchable PDF；設 MIME/magic/size/path limit、malformed/oversized guards；保存原始 PDF（sha256），以 ON 原生 upload/extract/index/worker/status/search，`embed=false`、`delete_source=false`、transformations 空。`.txt` 屬選擇性本地額外 fixture。
- [ ] 確認 upload ACK 與 Extraction READY 分開；Source 在 owner/graph 確認前不可 visible。故障時維持操作 journal 最小狀態並能安全 resume/retry，不能造第二筆可見 Source。
- [ ] `retry` 的 embed-on 問題依 §5.2 測試/最小修正；**禁止**用 Cloud Embedding 來令測試變綠。若沒有模型仍能在 Worker restart 後恢復 extraction + text index，才可宣告該路徑完成。
- [ ] **Evidence：**PDF extract text/search/sha、worker restart/failed-job injection、duplicate/orphan/garbled file checks、no external provider calls。**STOP：**原檔損失、retry 需要 Embedding、外部網絡出站、不能安全恢復。

### WP06 — 八個受控 A API、Search/List/Download 前後查核（依賴 WP04/05）

- [ ] 實作／接通 §1.4 的 8 個候選 API；每個授權先認證→可信 active School→Shell→Source ownership→ON actual edge；搜尋由 server 強制唯一非空 Notebook ID，search type 必須 text、Search Notes 關閉、結果受限並逐筆 Post-check。
- [ ] 只開經認可的原檔 Download；**整份 Authorization 在 HTTP headers／body 首 byte 前完成**；不可回傳可持續繞過授權的直連 CDN/ON/file URL。
- [ ] Native Preview/SSE/Ask/Vector 完全不能從外部 ingress 調用；測試不需新建 Streaming API。含原檔的可用 Download 仍要做 first-byte negative test。
- [ ] **Evidence：**每 endpoint 正反 HTTP trace、各 School/Shell/Source Scope、惡意混入結果 fixture、download SHA/first-byte trace、synthetic Service Scope checks。**STOP：**空 scope 變全庫、外來 Source 任一 bytes 被送出、Native API 仍可公開呼叫。

### WP07 — 只需一個 A-only Admin Page（依賴 WP03/05/06）

- [ ] 最小頁面只提供：Login/Logout、選擇合成 School、Shell 列表/建立/詳情、Source Upload/Processing State、Search、Original Download、Archive；可復用安全的 ON 展示組件，但**所有 Client 必須只走 A API**。
- [ ] 不加入：Sunrise U Course Portal、B Course、Teacher、成績、生成、Preview/Ask/Embedding、一般 Notebook Create/Delete/Link、完整設計系統。
- [ ] **Evidence：**Owner 完成一條完整操作流程的 recording/screenshot+HTTP trace，頁面/Bundle 不含 ON 密碼、DB/Provider Key、原生 API URL；登入失效與錯 School UI fail-safe。**STOP：**任何頁面直接調用 raw ON 或顯示未推出功能為已可用。

### WP08 — A-only Backup/Restore Runbook + 獨立演練（設計始於 WP00，實測依賴 WP03–06）

- [ ] 設計「停止新寫入、停/Drain Worker、固定一致恢復點」程序；安全備份 **SurrealDB（含 A policy/operation + ON schema/index）、全部原檔/上傳 volume、必要的 extracted artifacts、config/migrations/image digest**；加 Manifest Hash；Encryption Key **安全分開保管但須在 Restore 可用**。不可假設 live copy RocksDB volume 就是一致快照。
- [ ] 在乾淨隔離 A-only 環境 Restore，逐筆比對 Shell/Notebook/Source/initial_version/rights/Hash/Archive、原始 PDF bytes、Notebook Op replay 與 Scoped Search；索引如需 rebuild 必須真測可靠。
- [ ] 注入錯 key／缺 file／DB-file 不同 snapshot／壞 index／過時 image；缺完整性時**絕不繼續對外提供資料**；不能以「備份文件寫好了」代替真 Restore。
- [ ] **Evidence：**精確命令、snapshot/recovery-point IDs、原檔 SHA manifest、worker pause logs、before/after diff、negative restore 日誌、redacted key escrow test。**STOP：**任意 ID/Hash/owner 錯配、DB-only 備份被當完成、key 不可恢復。

### WP09 — 15 個 AT + Regression + R01 Release Gate（依賴 WP00–08）

- [ ] 每項 S1-AT01–15 真正執行（見 §6），區分 Unit、Integration、Security Negative、Persistence、Restore、Regression、Owner UAT；每項具 Test Evidence，缺項為 NOT_RUN。
- [ ] 確認 A-only Release Manifest、其他 Owner image/schema/config 不變、無 Actions/Copilot、無未授權 deploy/AI/data、原版 ON 非授權路徑不可從網絡繞過。
- [ ] Owner UAT 必須真操作 Login→Shell→PDF→Text Search→Download→Archive→Restart/Restore；另要獨立 reviewer 審查至少 native API、IDOR、Operation fault、Backup 一組反例。不可假裝 Goldfish/獨立 reviewer 已執行。
- [ ] **Evidence：**15/15 帶時間與來源版本的 trace、錯誤修正及 regression、A Restore manifest、UAT 結果、one-owner diff、R01 Go/No-Go 簽核。**STOP：**任一 AT FAIL/NOT_RUN、High/Critical、Owner hosting/rights/region/budget 缺批、無真 protected Runtime evidence ⇒ R01 不 Release。

## 5. 三個上游交接問題：原始行為→第一個測試→最小修正→判準→Escalation

### 5.1 Native Notebook Create ACK-loss / 併發冪等（對應 WP03、S1-AT06）

**已從原始碼核實：**ON 有 `POST /notebooks` (`api/routers/notebooks.py:128`) 及 native Notebook persistence，但在目前檢查到的 router/API 路徑沒有建立 Sunrise `creation_op` 與 Native Notebook 的原子一對一保證。**尚未實測：**這個版本可否安全使用 caller-assigned record ID 或 durable creation marker，不得猜測成功。

**Builder 第一個 Runtime Test：**用同一 `Idempotency-Key` + Canonical Body 提交 Shell create；在 Native Notebook **已落庫後、A Journal 尚未保存回傳 Notebook ID 前**注入 timeout/crash/斷線；重啟後重送；另用同時兩請求、同鍵異 Body、不同學校/stream 同名測試。數 native Notebook 記錄、Shell 記錄、operation 狀態並比對 ID。

**最小修正優先次序：**(1) 優先證明可用 deterministic/native caller-assigned Notebook ID + A 唯一約束和 durable readback；(2) 若不支持，採用建立時寫入 ON Notebook 的獨立 immutable operation marker（必須可唯一定位，非 title/name），及安全的原子 reserve/unique strategy；(3) 只有必要才作狹窄 A-only adapter/schema patch。**純 `creation_op` 表 + create 成功前沒有標記**是不充分的；跨 API call 不等於同一 DB transaction。

**PASS：**兩 School/stream collision、ACK-loss、並發、重啟、same-key replay 仍唯一 Shell↔Notebook；same key changed body 回 409；無誤刪。**FAIL/STOP：**雙 Notebook、孤兒無從確定、靠標題猜測、無原子性安全證明；停止 Create 功能並向技術 reviewer 提交最小設計差異與重現日志。只有若必須改 D02 或增加跨 Owner/付費能力才升 Owner。

### 5.2 Retry 把 Embedding 強制打開（對應 WP05、S1-AT04）

**已核實原始碼：**`api/routers/sources.py:195` Upload `embed` 預設 `false`，但 `:1004–1008` 的 retry input 強制 `embed=True`；`commands/source_commands.py` 將該 flag 傳入 Processing graph；原生完整 Job List/Cancel 不可靠（`api/command_service.py:71–90` 回傳佔位值）。

**第一個測試：**完全不設 Embedding Model/Provider，封鎖外部 Egress，上載有文字的合成 PDF（`embed=false`），將 Source processing/worker 在確定性節點打斷，再經**允許的 A-only recovery route** Retry，核對同一 Source ID、原 PDF SHA、extracted text、Text Index/Search、Worker restart 及出站連線記錄。

**最小修正：**Raw `/sources/{id}/retry` 永遠不公開；先查是否能以現有 CommandService 對同一 Source 安全提交 `embed=false`；若無法，對 pinned native A-adapter 的 retry flag 作**最小定向 patch**、回歸測試 upstream 合理行為，禁用 AI transformation。不得造第二條 Queue 或啟用 Gemini。原生 upload/worker/status/processor 照舊沿用。

**PASS：**無模型、零外部 AI 呼叫下，失敗重試復用原 Source/檔案/Ownership 並可文字搜尋；無重複可見 Source。**FAIL/STOP：**需要 embedding 才能恢復、原檔 Hash/owner 變、出現重複/越權或無法界定 safe retry 時，停止恢復 API，技術 reviewer 決定單點 patch/限制；跨越 D05 才升 Owner，不能偷偷啟用 Provider。

### 5.3 Text Search 在特定錯誤 fallback Vector（對應 WP06、S1-AT03/04）

**已核實原始碼：**`open_notebook/domain/notebook.py:834–886` 的 `text_search()` 遇到 `position overflow` 會自動呼叫 `vector_search()`；而 Vector 需要生成 embedding。空 Notebook Scope 亦會變成 global（`:775–831`）。這意味只有正常輸入能搜尋並不保證異常路徑在 Embedding OFF 時正確。

**第一個測試：**完全無 Embedding／Cloud Provider，固定非空唯一 Notebook，對 born-digital PDF、繁體中文／多 byte 內容、長文本、特殊字元、可重現的 highlight overflow fixture 執行 Text Search。檢查結果的 Source Ownership、是否出站、錯誤類型、是否意外呼叫 vector、是否回傳不可信空結果。預期的正常文件搜尋必須成功。

**最小修正：**A API 強制 `type=text`、空 Scope 立即拒絕、每筆結果二次授權；若 Native overflow fallback 產生模型依賴，優先以最小 pinned A-only patch 讓 Text Search 異常**安全返回明確錯誤**，並優先修正／繞開造成 highlight 溢出的 text-only 處理（不是向量 fallback）。不能回傳虛假的 `[]`、不能擴大 scope。若受支持的 PDF/中文內容搜尋仍不可靠，必須修復至成功或縮小經 Owner 確認的**格式/尺寸支持邊界**；不能把核心 Text Search 當成 Optional。

**PASS：**支持格式的正常文本可準確 scope 搜尋，異常輸入不外洩/不觸發雲端／vector，錯誤可辨，無跨 School result。**FAIL/STOP：**要用 Embedding 才能完成必要 PDF Text Search、Scope 擴大、外部呼叫、核心中文 fixture 無法搜尋或 safe error 變無聲漏失；暫停 Search Release，記錄 reproducible test，按 A-only 技術決策修 patch；涉及正式範圍改動才升 Owner。

**額外低成本 upstream 邊界檢查：**`api/routers/notebooks.py` 對 Source link/unlink 的 `reference` 查詢方向在原始碼片段中不一致；不新增一般 Link/Unlink API，但在 WP04 對 native graph 做增刪、查詢及 mismatch 負測，避免使用名稱或不可靠 Delete 做安全清理。

## 6. S1-AT01–AT15 Traceability Matrix（正式 Acceptance 不變，全部目前 NOT_RUN）

記號：**U** Unit；**I** Integration；**N** Security Negative；**P** Persistence；**R** Restore；**G** Regression；**O** Owner UAT。每行需保留 `Requirement → WP → A Implementation Owner → Test → Evidence → Release Gate`。所有 Gate 都是 **MUST PASS**，且不能用文件驗證代替 Runtime。

| AT | 正式要求的最小可觀察證據 | WP（A Owner） | 類型 | 必交 Evidence | R01 Gate |
|---|---|---|---|---|---|
| **S1-AT01** | Admin→Shell→唯一 Notebook→PDF extract/search/download；Archive 也要能操作 | 02–07 | I,N,O | UI+HTTP+Notebook/Source/原檔 SHA | MUST PASS |
| **S1-AT02** | 匿名、直接 ON POST/DELETE/global search 從外網拒絕 | 01,02,06 | N | 非 Gateway 來源外部探測 trace | MUST PASS |
| **S1-AT03** | 非空 server Scope；School/Shell A 搜尋不返回 B Source，含惡意混入結果 | 04,06 | U,I,N | request scope、DB edge、mixed response test | MUST PASS |
| **S1-AT04** | A DB＋Worker 重啟後 Source/原檔/Index/Text Search 保持可用，Retry 無 AI | 05,08 | P,G | Restart 前後 IDs/Hash/Search/worker logs | MUST PASS |
| **S1-AT05** | 隔離 A-only DB＋原檔＋Keys Restore，一致 ID/Hash/ownership | 08 | R,N | Backup Manifest、恢復指令及差異校驗 | MUST PASS |
| **S1-AT06** | ACK-loss/並發/same-key 重放不產生第二 Notebook；改 Body 409 | 03 | U,I,N,P | 故障注入、唯一索引及 DB Notebook 數量 | MUST PASS |
| **S1-AT07** | 唯一受控 Admin、真 HTTPS、private DB/Secret、合成資料 | 01,02 | I,N,O | TLS、network、secret redaction、fixture 清單 | MUST PASS |
| **S1-AT08** | Password/Encryption Key/DB credentials 缺失、空白、示例 root:root 拒啟動 | 02 | U,I,N | fail-start Exit Code/Log，不含秘密明文 | MUST PASS |
| **S1-AT09** | Raw GET/POST/DELETE Notebook、Source Link、全庫 list/search、管理 endpoints 不對外 | 01,06 | N,G | 按上游版本路由逐條網絡 probe | MUST PASS |
| **S1-AT10** | Guess Source ID、Preview、SSE、Download 不輸出任何 foreign byte；停用功能真的不可達 | 01,04,06 | N,I | 首 byte 探測、拒絕響應／外網 route table | MUST PASS |
| **S1-AT11** | 每個 Source→Shell→Notebook 的 owner 和 ON 真實 reference 一致，Search 二次查核 | 04,05,06 | U,I,N | edge snapshot、錯配注入及拒絕 trace | MUST PASS |
| **S1-AT12** | rights/retention/license/AI-use/initial version/PDF SHA 在 Restore 後一致 | 04,08 | P,R,N | Metadata＋原檔前後 SHA／權利欄位比較 | MUST PASS |
| **S1-AT13** | 只修改 A；其他 Owner manifest/digest 不變；Smoke/Regression/Restore 通過 | 00,08,09 | G,R | owner diff、R01 manifest、完整 runner logs | MUST PASS |
| **S1-AT14** | `GET shell materials`：Admin 和受限 Service 在有效 Scope 返回 owned version/hash；無效/跨校/錯 Scope 拒絕 | 02,04,06 | I,N,O | Admin + Synthetic ServiceToken／Consumer HTTP tests | MUST PASS |
| **S1-AT15** | 兩 School、一 Admin；active A 不能讀 B Shell/Source，可信切換後按授權才可讀 | 02,04,06 | I,N,O | two-school IDOR/Session-switch traces | MUST PASS |

> AT02/09/10 允許以**封閉／不公開** Preview/SSE/raw API 作合法的負面完成方式；但不得藉此關掉正規 Upload、Download、Search。AT14 的 Service 權限不能假稱 Optional；AT08 Startup Fail 不是僅限 Gateway log warning。S1 本地跑過仍不是 protected Staging + Owner UAT。

## 7. S2–S28 邊界與後續可用契約（S1 不先做）

| 後續 Stage | S1 **現在必須保留** | 必須後置的完整能力 |
|---|---|---|
| **S2 A/R02** | A Shell/Notebook/Source/initial Version ID/hash/rights/ownership、stable actor、安全 A API seeds | 多版本 lineage、Publish/Revoke/Attest、5 個 S2 API、正式 Service Provisioning/Consumer Contract Freeze、Managed Cutover |
| **S3 B/R03** | Shell 5 維分類含 `curriculum_stream`；A Shell **不是** B Course | B Course/TeachingGroup、Postgres、B Reserve/Finalize、Operation Log |
| **S4 I/R04** | 一對一 Shell↔Notebook、local ACK-loss 操作 journal 可 readback；S2 後提供正式 A 接口 | A/B Saga、ADOPT_EXISTING、CREATE_NEW、Reserve/Finalize、I Read-after-write/Quarantine、Cross DB Restore 對帳 |
| **S5 U/R05** | 最小 A-owned Admin UI 和安全八 API；A 的 Archive 操作保留 | Sunrise Unified Portal、Course/Link Status 等，U 只用已發布 API |
| **S22 B/R22** | 單 Admin stable actor_id、School IDs、可核審 audit | Staff/Teacher User/Role/Grant、邀請、撤權、B IAM |
| **S23 I/R23** | A server-side Shell/Source/School 權限、受限 Service Read verifier，沒有 Native Password 外洩 | Teacher StaffSession→B Grant→I→A readonly；Per-request revoke/epoch、Teacher APIs |
| **S26 A/R26** | 初始 Rights/Retention、Archive 不刪、原檔 Hash/Restore | Annual Archive、Legal Hold、Retention Review Dashboard、Health/Backup Status APIs |
| **其餘 S6–S21、S24–S25、S27–S28** | 只保留穩定 Resource IDs、資料 Owner 分離與追蹤欄位 | 試卷、出卷、學生、成績、全面 Teacher Portal、跨服務監控一律按原正式 Stage 再做 |

**額外可安全延後：**OCR/掃描 PDF、EPUB、網址匯入、轉換/Notes/Chat/Podcast、Embedding、LLM、完整職員 IAM、頁面設計系統、Generic Worker Listing/Cancel、定時 Backup Dashboard。這些並非自動屬 S2 或 S26；如未來需要新 A 用途，必須另按該階段或獨立獲批 A-only 變更處理，不能在 R01 夾帶。

## 8. Security / Backup 最小不退讓 Gate

| 威脅／故障 | 必備控制及驗證 | 一票否決 |
|---|---|---|
| 原生 API / DB 旁路 | 完整路由清單與外部 private network probe | 任意 Native Create/Delete/Link/Global Search 可公開執行 |
| 空 Scope / Cross School / Guess Source | Server-only Notebook Scope、Pre/Post SourceOwner + Native Edge，兩 School 反例 | 任一 foreign result/byte |
| 下載首 byte 外洩 | Download auth+owner+hash+path 先於 response headers/byte；禁止公開源檔鏈接 | 未授權 client 收到任何教材 bytes |
| Missing Secret / Weak Admin Session | Fail-start、嚴格 session、CSRF、TLS、redacted Audit | root:root/示例密碼起得動或可繞過認證 |
| ACK-loss / Workers crash | Durable idempotency、Read-back、Quarantine、Retry 無 AI | 重複 Notebook、錯 Owner Source、無法安全恢復 |
| 原始 PDF、索引、Keys | Coherent stopped/consistent A snapshot、可獨立 Restore、SHA verify | 只 DB backup、檔案/keys 缺失、Hash 不一致仍 serving |
| 未授權部署／付費／資料 | Synthetic local only；公開環境及版權／Region／Budget／Provider 各自批准 | 任何未批公開/付費/真實資料使用 |

**A-only Restore 最小完整步驟：**準備兩 synthetic School + 兩 Shell + 各自 Source + archived item + broken worker case → 阻止新寫入並 Drain/Stop Worker → 維持 SurrealDB+全部 originals+必要 keys/config/migrations/index 的同一 logical recovery point（密鑰另安全保管）→ 產生 checksum/rights/idempotency manifest → 在乾淨 private A instance 恢復 → 重跑 ID/Hash/owner/rights/Archive/Operation replay/Text Search → 錯 key／缺原檔／不同時間 snapshot／壞 index 需明確阻止 serving → 留下實際指令、時間、exit code、差異及 reviewer。**絕不能以一份寫好的 Runbook、DB dump 或文件 QA 代替真正隔離 Restore。**

## 9. 文件差異、未決技術點與正式 Owner Decision Request

| 精確來源 | 問題／正式影響 | v1.1 建議處理（不改 GitHub） | 決策者／阻擋時間 |
|---|---|---|---|
| `docs/delivery/STAGE_01_EXECUTION.md` 第 2 點 vs `docs/decisions/STAGE0_APPROVAL_DECISIONS.md` D02 | Shell 的 external key 範例只列 School/Year/Grade/Subject，**遺漏 `curriculum_stream`**；未來撞 B Course 粒度 | S1 直接在 A Shell 分類及唯一性加 stream；保留 D02，建議下次正式 docs PR 補字 | Builder 依 D02 實作；非新 Owner product decision |
| `docs/stages/STAGE_01.md` **S1-AT14**／`docs/architecture/API_INVENTORY.json` 5 個 S1 `admin_or_service` routes vs `docs/architecture/SECURITY_AND_AUTH.md` Service JWT contract | 極簡單 Admin 若刪除 Service path，會有正式 AT/API 授權缺口 | **ODR-S1-01（確認建議）**：S1 先有最小 scoped Service JWT verifier + 合成測試；S2 才正式發證／Consumer Freeze，不建 IAM 平台。不准略過 AT14 | **Owner 確認 v1.1 Scope 時可一併確認**；不阻止 Builder 本地做 verifier |
| `docs/architecture/SECURITY_AND_AUTH.md` 「Password/MFA protected」vs D04 一個 Admin | 未來 Hosted S1 MFA 強度可能需明確政策 | 最小實作使用強密碼、Session/TLS/CSRF；為 Hosted R01 **推薦標準 TOTP MFA**（不另起 IdP）。若要**免 MFA**，必須 Owner 明確確認其與正式 Security doc 兼容，不能 Builder 默默略去 | Owner **Hosted Security Signoff** 前；不阻本地 synthetic 開發 |
| `docs/stages/STAGE_01.md` AT12/14 + D03 vs `docs/stages/STAGE_02.md` AT02/09 | S1 immutable initial provenance 與 S2 multi-version/publish 易混淆 | 初始 Source version ID + original SHA + policy 在 S1；後續 lineage/publish S2；不改 AT | Builder 技術實作；無需 Owner 再批架構 |
| `docs/architecture/BOUNDARY_RULES.md` 的 `live main still v0.5` vs 本次 GitHub main/Stage0 baseline | 過時版本敘述，可能誤導 | 下次獲批的 docs-only PR 更正；不是 Stage 1 Builder 起工阻擋 | 文件維護，後續處理 |
| `docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md` 舊 ZIP audit 非 pinned vs `docs/delivery/STAGE1_START_CRITERIA.md` pin tree | 上游 Image 來源尚未全量證明 | WP00 驗證完整 source/build/digest、license；不能用 moving latest Release | Builder 技術 Gate，R01 前必過，不阻 synthetic spike |
| `docs/stages/STAGE_01.md` AT07/13 + `docs/delivery/STAGE1_START_CRITERIA.md` + D07 | Runtime Staging/Owner UAT vs 未獲外部部署、Region/Cost/Content 授權 | **ODR-S1-02**：本地 synthetic dev 可先做；受保護外部 Staging/Release 分開明確授權；不把未授權 Staging 視作已完成 | Owner 在 Hosted Gate 前簽核 |

**以下屬 Builder 技術選型，**不要轉嫁給非技術 Owner：Notebook deterministic ID／marker／transaction 的選擇、Retry `embed=false` 修補方法、Text Search highlight 修正、JWT verifier library、是否需要安全用小 Gateway、SurrealDB index/transaction、Native graph edge direction、PDF parser 容錯、Recovery Runbook 具體命令。只要不改批准的 D01–D08、不引入新付費/外部資料/跨 Owner、不降低 AT，Builder 應用重現測試自行選擇並留證據。

## 10. 四種狀態與 Builder 可以開始的最低條件

| Gate | 需要甚麼 | 現狀／後續授權 |
|---|---|---|
| **1 — Planning Complete** | D01–D08 固定、最小 Scope、10 WP、8 API、15 AT、關鍵上游風險、S2+ 邊界、Builder Prompt、Escalation / Owner Gates 都明確 | **COMPLETE**：不以還未跑 Runtime/擇定內部 patch 作延長 Planning 的理由 |
| **2 — Builder Local Development Authorized** | Owner 在新 Builder Chat **明確發送 §11 Prompt**，同意只做本地 synthetic code/test，無 GitHub 寫入／付費／外部公開服務 | **PENDING OWNER ACTIVATION**；一經發送、Builder 核實倉庫/工具和授權邊界後即可開始。**不需要先通過 Runtime/R01 Gate** |
| **3 — Runtime Acceptance Passed** | 完成實作、使用受控候選 Runtime、15/15 S1 AT 真測、Negative／Persistence／Restore／Regression／Owner UAT 全部留證；未獲 Hosted 授權只可在本地私有 Runtime 做非部署測試，不能稱完整 Hosted Acceptance | **NOT_RUN**；後續 Builder/Runtime Gate |
| **4 — R01 Release Approved** | 在 Gate 3 + Owner 的 Hosting/Region/Network/Secret/Budget/Privacy/Rights + Signoff 與安全缺陷清零之後明確批准 | **NOT_APPROVED**；正式 Release 禁止 |

**準確的階段語義：**`Planning COMPLETE` 不等於 `Stage 1 COMPLETE`；`Builder Local Development Authorized` 不等於可以 Push/PR/Deploy。Builder 可以先用本地 Docker（若有）和 synthetic PDF 實作、測試。只要在安全、未公開、無付費界線內，**不必先獲得未來正式 Hosting/Content/R01 批准**。

## 11. 給下一個 GPT Builder 的初始 Prompt（可直接複製）

> 你接手 Sunrise Education AI Platform Stage 1 [A] 的**本地合成資料實作**。我在本 Prompt **明確授權**你在可用的本地／隔離 workspace 編寫、修改及執行 **A Owner** 程式和 synthetic tests；**不授權** GitHub 寫入（Branch/Issue/PR/Commit/Push/Merge）、公開 Staging/Production 部署、付費 API、Gemini/Cloud Embedding/AI Chat、上載真實教材或真實學校／學生資料。GitHub 只能唯讀。**不得使用 GitHub Actions 或 Copilot。**
>
> 唯一工作基線是本附件《Sunrise Stage 1 Minimal Implementation Plan v1.1》和 GitHub 正式 `Enochan222/sunrise-school-ai-platform` 最新 `main`；正式 GitHub D01–D08、Stage Card、S1-AT01–15 的權威性高於交接文件。先核對 `main`，已知 SHA `744fbbd0ac3b479c80782d6a990c7bfed093f4dd`；pin Open Notebook v1.15.1 commit `5e285b7a2e435895c4ee99ad7e4b8d2af64c3239` / tree `2d101001de594c7d6a0e4aaeb8e85ac4c52980af`，不可使用 moving latest。若 `main` 有變更，先報告受影響 scope。
>
> 只實作一條 A-only user journey：Secure single-Admin→Content Shell→唯一 Notebook→born-digital synthetic PDF Upload/Extraction→Scoped Text Search→Original Download→Archive→Restart→A-only Backup/isolated Restore。目標最小 A App/3 類 A 紀錄/8 個 S1 候選 API；用原生 ON Notebook/Source/Worker/SurrealDB，**安全優先於組件數量**。絕對不能提早做 S2 多版本發布、S3 B Course、S4 跨服務 Saga、S5 U Portal、S22 IAM、S23 Teacher 或 S26 年度治理。
>
> 按 **WP00–WP09** 執行，每個 WP 記錄正反測試、SHA/時間、環境及 Evidence。WP00 第一時間以合成 fault injection 實測三項上游風險：Notebook ACK-loss 重複、Native Retry `embed=True`、Text Search 的 Vector fallback；**先重現→最小修正→回歸**，不可以為過測試啟動 AI/付費。按 v1.1 §5 的 PASS/STOP 辦。所有 raw native UI/API、非授權全庫搜尋、SSE/Preview、DB Port 不可從外部 bypass。S1-AT01–15 原封不動，逐項真測與留證；不做或失敗寫 NOT_RUN／FAIL，不能聲稱完成。
>
> 我不懂 Coding，請每個 WP 用簡短語句說「改了甚麼、重用了甚麼、測試如何、結果、風險、下一步」，清楚區分技術修補與真正需要 Owner 決策。技術細節先自行採用最小安全方案；只有涉及批准邊界、數據／費用／外部部署、跨 Owner/重大 scope 變更才升級問我。**這個 Chat 只允許本地合成資料實作，不允許 GitHub 寫入或 Release。**

## 12. Builder Stop／Escalation + 一頁非技術 Owner Signoff

### 12.1 Builder 何時停（先報事實，不自行越界）

**立即停止相關功能及任何外部暴露**：raw ON API/DB/Source 路徑可繞過；空 Scope/猜 ID/跨校有任何 byte 露出；缺 Secret 仍能 serving；ACK-loss 雙 Notebook；Source hash/Owner mismatch；Retry/搜尋必須啟用未批准 AI；Restore 無法恢復正確 ID/Hash/keys；任何 Critical/High 未修；無法確認 pinned image、只剩 moving latest；企圖觸及其他 Owner runtime；缺正式部署/真實資料/付費授權卻需要越界。保留 redacted reproducer、影響、最小替代方案。

**僅需 Builder 技術 Review／修正、毋須 Owner 即時決定**：Notebook ID/marker 交易方法、Text Search highlight patch、Embedding-off retry path、Graph edge bug、內部 JWT library、測試工具及每包 PR 數。不能為減少 Code 而要求 Owner 放寬 AT。

**必須向 Owner 升級**：要改 D01–D08 / 正式 S1-AT／Stage Owner；要做付費/AI/外部資料/公開網絡；要改 School Course 粒度；提早引入 B/I/U runtime；正式 Hosting Region/Budget/rights/privacy/RPO/RTO 政策；或確實無法用合理最小 A-only 方案達到核心 S1 Goal。Owner 批准範圍以書面記錄，未批准維持 blocked。

### 12.2 一頁 Owner 決策表（建議預設；可勾選）

| 真正需要 Owner 授權的事項 | 推薦預設方案 | 何時必須簽核 | 本次狀態 |
|---|---|---|---|
| **O1. Builder 本地合成資料工作** | **同意：**只在隔離本地環境修改 A 及測試；GitHub 唯讀；無付費/真材/部署。直接把 §11 Prompt 交新 Builder 即算明確授權 | **開始本地編碼前** | 待由 Owner 發送 Prompt 啟動 |
| **O2. S1-AT14 最小 Service 權限範圍** | **採納：**S1 只做合成離線可測 JWT verifier 與 Admin+Service 正反例；S2 才正式 Issuing／Provisioning／Consumer Contract Freeze；不做教師 IAM | v1.1 Scope 簽核；不必等 hosted runtime | 建議採納，尚非正式 master 修訂 |
| **O3. 對外環境安全政策（含 MFA）** | **預設無任何外部部署**。將來如 R01 hosted：優先私有網絡／最小 public ingress、TLS、管理密鑰庫、標準 TOTP MFA（或等效受審控制），明確選 Region/Provider | 公開或受控 Hosted Staging **之前** | 未批准，不阻本地開發 |
| **O4. 支出上限／外部 AI** | **$0 新付費服務；全部 Gemini/Embedding/AI Chat OFF**。任何新增成本／模型需獨立明確批准，**不因 Stage 1 完成而默認開啟** | 首個可計費資源建立／Provider 啟用前 | 保持 OFF／無消費授權 |
| **O5. 真實教材、版權、隱私與保留政策** | **Synthetic-only**；本地合成 PDF。實際教材須校方對使用權、retention、sharing、資料所在地和隱私另行批准；不接真學生資料 | 真實教材匯入／學校實際使用前 | 未批准，不阻 Synthetic |
| **O6. A-only Backup 的 Hosted 運維承擔** | 先要求**完整隔離 Restore 成功**；正式 Hosted 前再書面選備份頻率、可接受 RPO/RTO、Key Escrow/Operator；不可只說已有 DB Backup | Hosted R01 Release 前 | Runtime 待測；Hosted 指標未批准 |
| **O7. 正式 R01 Release** | **不同意自動放行**：只在 15/15 真測 PASS、Staging/Restore/Security/Regression/Owner UAT 有證據、Zero Critical/High 且 O3–O6 已批後，另作明確 R01 簽核 | **最後** | NOT_APPROVED |

> **Owner 不需選** Gateway 用哪個框架、幾張 DB Table、生成 Notebook deterministic ID 的方法、怎樣 patch `embed=True`、如何處理 Vector fallback、JWT 套件、PDF 解析、PR 數量；這些必須由 Builder 以證據做最小安全選型。若 O2 採建議，亦不等於 D01–D08 有任何變更。**本交接文件不是對 O3–O7 的自動批准。**

---

## 13. Planning Gate 最終核驗與停止條件

| 規劃驗收項目 | 結果 |
|---|---|
| GitHub main SHA、S0 D01–D08、Registry S0–S28 | **PASS**（GitHub 唯讀，與指定基線相同） |
| S1 1 條真實可操作 User Journey | **PASS**（可執行描述） |
| 優先 REUSE 上游／不複製 ON 引擎／AI OFF | **PASS**（規劃） |
| v1.0 與 Minimum Review 矛盾清除、WP00–09 分工 | **PASS**（規劃） |
| 八項 S1 API、15 項 S1-AT 原義保留及逐項 Traceability | **PASS**（規劃；實測全部 NOT_RUN） |
| 三項上游風險有第一測試、最小修正、PASS/STOP | **PASS**（規劃；Runtime 未驗證） |
| AT14 最小 Service verifier、S2 Freeze 分界、Owner clarification | **PASS**（規劃；Hosted 合約仍待驗收） |
| S2/S3/S4/S5/S22/S23/S26 及其他後續 Owner 邊界 | **PASS**（規劃） |
| Builder 啟動權限與 Runtime/Release Gate 分開 | **PASS**（規劃） |
| Runtime security / Restart / Restore / 15 AT / Owner UAT | **NOT_RUN**（非 Planning Gate、待 Builder／獲准環境） |
| R01 部署／預算／真材／Provider／Release 批准 | **NOT_APPROVED**（非本地開發前置） |

**最終結論：STAGE 1 PLANNING COMPLETE。沒有發現需要在本地 Synthetic Implementation 開始前另開架構規劃或先跑 R01 Runtime Test 的阻擋條件。** Builder 一旦收到 §11 的明確本地授權即可開始 WP00；本文件的技術疑點都在 Builder 試驗／局部 Stop Gate 解決，不反覆要求非技術 Owner 決定內部 Code 路徑。**Stage 1 Runtime 尚未開始，R01 絕對不能 Release。**

**Referenced at exact GitHub main commit：**

- [Stage 0 Decisions](https://github.com/Enochan222/sunrise-school-ai-platform/blob/744fbbd0ac3b479c80782d6a990c7bfed093f4dd/docs/decisions/STAGE0_APPROVAL_DECISIONS.md)
- [Stage 1 Official Spec / 15 AT](https://github.com/Enochan222/sunrise-school-ai-platform/blob/744fbbd0ac3b479c80782d6a990c7bfed093f4dd/docs/stages/STAGE_01.md)
- [API Inventory](https://github.com/Enochan222/sunrise-school-ai-platform/blob/744fbbd0ac3b479c80782d6a990c7bfed093f4dd/docs/architecture/API_INVENTORY.json)
- [Stage Registry](https://github.com/Enochan222/sunrise-school-ai-platform/blob/744fbbd0ac3b479c80782d6a990c7bfed093f4dd/docs/quality/STAGE_REGISTRY.json)
- [Upstream v1.15.1 Source Tree](https://github.com/lfnovo/open-notebook/tree/5e285b7a2e435895c4ee99ad7e4b8d2af64c3239)
- [Native Retry](https://github.com/lfnovo/open-notebook/blob/5e285b7a2e435895c4ee99ad7e4b8d2af64c3239/api/routers/sources.py)
- [Native Text Search / Empty Scope](https://github.com/lfnovo/open-notebook/blob/5e285b7a2e435895c4ee99ad7e4b8d2af64c3239/open_notebook/domain/notebook.py)
- [Native Notebook API](https://github.com/lfnovo/open-notebook/blob/5e285b7a2e435895c4ee99ad7e4b8d2af64c3239/api/routers/notebooks.py)
