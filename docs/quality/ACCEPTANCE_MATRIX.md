# Stage Acceptance Matrix — v0.7.4 Targeted Contract Repair (NOT EXECUTED)

**Test designs only; runtime UAT and live provider contract freeze remain NOT RUN.**

| AT ID | Stage | Owner | Scenario | Expected behavior | Runtime status |
|---|---:|:---:|---|---|---|
| S0-AT01 | 0 | P | 來源版本 | 核對上游實際 Commit/License/Open Notebook scope／安全限制，留證據 | NOT RUN |
| S0-AT02 | 0 | P | 物理隔離 | 批准 A SurrealDB、B PostgreSQL 不共享連線、檔案、備份或帳密 | NOT RUN |
| S0-AT03 | 0 | P | Stage 單責任 | 依賴圖中每個 Release 只有一條 Workstream Owner | NOT RUN |
| S0-AT04 | 0 | P | S1 合格界線 | 明確 S1 A-only，S3 才有 B，S4 才有跨 API I | NOT RUN |
| S0-AT05 | 0 | P | Repo 控制 | PR 保護、Secrets 政策、Status/ADR/Templates 完整 | NOT RUN |
| S0-AT06 | 0 | P | 批准與未實測 | 清晰記下 Owner Signoff/NOT IMPLEMENTED，不能把文檔當部署 PASS | NOT RUN |
| S0-AT07 | 0 | P | 決策完整 | ADR-011..022、Course Grain、API Inventory、No-Actions 驗收紀錄全部審核，Owner 未簽核不得標 APPROVED | NOT RUN |
| S0-AT08 | 0 | P | Github 影響 | 新 Repo 權威、PR 保護及 No-Actions 測試紀錄清楚；不匯入舊 Repo 歷史 | NOT RUN |
| S0-AT09 | 0 | P | 無部署驗收 | S0-AT 僅要求文件、Repo、Owner 批准及可核對的設計證據 | NOT RUN |
| S0-AT10 | 0 | P | Course/TeachingGroup/Shell 決策 | 批准 Course 一個學年/級別/科目/stream 可多 Group，A Shell 有 school_id；Gemini S1 可選，S4 Cutover Owner 及 API 不混合 | NOT RUN |
| S1-AT01 | 1 | A | 完整操作 | Admin 建 Shell，唯一 Notebook，教材可上載搜尋下載 | NOT RUN |
| S1-AT02 | 1 | A | 防旁路 | 匿名／直接 Open Notebook POST、DELETE、global search 無法從公開網路使用 | NOT RUN |
| S1-AT03 | 1 | A | 範圍 | 非空 notebook scope，Course A 搜尋不返回 Course B Source | NOT RUN |
| S1-AT04 | 1 | A | 持久化 | 重新啟動 A DB/Worker 後檔案、索引／紀錄仍可讀 | NOT RUN |
| S1-AT05 | 1 | A | A Restore | 隔離環境還原 A DB + 原始檔+keys，驗證 Source/Hash | NOT RUN |
| S1-AT06 | 1 | A | 重試 | Notebook Create ACK 丟失後相同 operation id 不生成第二本 | NOT RUN |
| S1-AT07 | 1 | A | 基本安全 | 唯一 Admin、HTTPS、private DB/secret、無真實學生個資 | NOT RUN |
| S1-AT08 | 1 | A | Secrets Fail Startup | OPEN_NOTEBOOK_PASSWORD、Encryption Key、DB credential 缺任何一項或使用示例 root:root 即拒絕啟動 | NOT RUN |
| S1-AT09 | 1 | A | 原生旁路 | 直接 raw GET/POST/DELETE Notebook、source link 或全庫 Search 由公開端拒絕，僅私有服務可達 | NOT RUN |
| S1-AT10 | 1 | A | SSE 與 Preview 隔離 | 猜測 Source ID、下載、Preview、Stream 不輸出非目標 Shell 資料任何片段 | NOT RUN |
| S1-AT11 | 1 | A | 來源權威 | source_id→shell_id→notebook_id 映射與實際上游內容一致，Search 返回前二次校驗 | NOT RUN |
| S1-AT12 | 1 | A | 版權與備份 | Source 基本 Retention/License/AI-Usage flag、原始 PDF Hash 在 A-only Restore 後一致 | NOT RUN |
| S1-AT13 | 1 | A | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S1-AT14 | 1 | A | 教材列表契約正向與越權／異常負面測試 | GET A shell materials 由唯一 Admin 或特定 Service Scope 獲取、逐個 Source Owner 驗證，返回具版本與 Hash 的列表 | NOT RUN |
| S1-AT15 | 1 | A | A Shell 校級權限 | 兩個 School 的 Shell／Source / Scope 即使 ID 可猜到，A Gateway 仍拒絕跨校讀取 | NOT RUN |
| S2-AT01 | 2 | A | 教材分類 | 三類檔案均保存可查詢 Metadata、學年、Topic、來源版本 | NOT RUN |
| S2-AT02 | 2 | A | 版本規則 | 教材修訂產生新 Version，已發布舊版可追查 | NOT RUN |
| S2-AT03 | 2 | A | 唯一擁有者 | 同一 Source 不可跨 Shell Link 或進其他課程搜尋 | NOT RUN |
| S2-AT04 | 2 | A | API Contract | 提供 Shell 清單、單 Shell Manifest、受控 Create/查詢的 OpenAPI 及測試 | NOT RUN |
| S2-AT05 | 2 | A | 歸檔 | Archive 不硬刪 Notebook，Archive 不破壞歷史 Source/Hash | NOT RUN |
| S2-AT06 | 2 | A | 回歸 | 重跑 S1 全流程和單庫恢復；新版本資料可重建索引 | NOT RUN |
| S2-AT07 | 2 | A | I 準備 | 受控 create 使用外部冪等鍵、可由服務帳戶呼叫；此期不連接 B | NOT RUN |
| S2-AT08 | 2 | A | Canonical A API | 全部 Stage2 A operationId/path/method 對應 OpenAPI，Consumer Fixture 真實執行 | NOT RUN |
| S2-AT09 | 2 | A | 舊來源版本 | Version 3 被新 Version 4 替代後仍可按 immutable ID/hash/locator 取得合法受保留版本 | NOT RUN |
| S2-AT10 | 2 | A | 權限失效 | 來源被撤銷/封存時 A attest 返回可辨別狀態，禁止供外部 AI 使用 | NOT RUN |
| S2-AT11 | 2 | A | 冪等鍵差異 | 相同 Idempotency-Key 同 Body 重放回舊資源；不同 Body 回 409 | NOT RUN |
| S2-AT12 | 2 | A | Cutover 模式 | STANDALONE→FREEZE→MANAGED 經受控 Admin API，只封鎖新 Create，不封鎖舊 Search/Restore | NOT RUN |
| S2-AT13 | 2 | A | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S2-AT14 | 2 | A | 受控服務授權正向與越權／異常負面測試 | 所有供 I 使用的 A API 均用 service audience+scope+resource ownership，拒絕 Admin Token 借用或 ServiceToken 跨端點升權 | NOT RUN |
| S2-AT15 | 2 | A | 供 S4 的 Cutover 受控 API | A 已具獨立 Service scope、唯一 Create/Managed-mode 封鎖及 Manifest/Health 前置契約，I 不需改 A | NOT RUN |
| S3-AT01 | 3 | B | B-only 實例 | B Postgres 不共享 A Storage、Credentials、Docker Volume 或 Backup | NOT RUN |
| S3-AT02 | 3 | B | 課程管理 | Admin 可在獨立 B 畫面建立、列示、封存 Course | NOT RUN |
| S3-AT03 | 3 | B | 未連結清晰 | 未接 A 時狀態 CONTENT_UNLINKED；不假裝 Notebook 已建立 | NOT RUN |
| S3-AT04 | 3 | B | 引用預留 | B Binding Reserve/Finalize/Unique 約束用 Mock A reference 測試；不呼叫實際 A | NOT RUN |
| S3-AT05 | 3 | B | B Restore | 隔離環境備份還原 B Course + audit | NOT RUN |
| S3-AT06 | 3 | B | 最小權限 | B 不存 A Root Credential；B Web 禁用 Service Role | NOT RUN |
| S3-AT07 | 3 | B | 回歸 | S1、S2 A 發佈版本完全不變；B-only 部署可測可回退 | NOT RUN |
| S3-AT08 | 3 | B | 原子 Reserve | CREATE_NEW 以單一 B Transaction 建 Course+Operation，任一失敗雙雙回滾 | NOT RUN |
| S3-AT09 | 3 | B | 既有 Reserve | ADOPT_EXISTING 只鎖已存在 Course，不再 Create 第二個 Course | NOT RUN |
| S3-AT10 | 3 | B | Binder 唯一 | 對 course_id、A shell ID、notebook ID 的 UNIQUE constraint 與 null/status 策略可測 | NOT RUN |
| S3-AT11 | 3 | B | Course 粒度 | P4A/P4B 可共享同學年/年級/科目/教材流 Course，但不因此共享 Source 跨不同 Course | NOT RUN |
| S3-AT12 | 3 | B | Contract Freeze | B reserve/finalize/status/list API 有 machine-readable OpenAPI、Consumer Fixtures、Idempotency 錯 body 回 409 | NOT RUN |
| S3-AT13 | 3 | B | IAM 預留 | B school_id, course_id, subject, actor_id, created_by, access_scope, audit_actor 欄位及未來 Grant relation 有規格 | NOT RUN |
| S3-AT14 | 3 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S3-AT15 | 3 | B | 預留交易與服務權限正向與越權／異常負面測試 | B reserve 必須在一個 DB transaction 記錄 Course/Operation，I 只可用 narrow ServiceToken 調用，並在重試時維持唯一綁定 | NOT RUN |
| S3-AT16 | 3 | B | B Course／Group 粒度 | Course 保持 grade+curriculum_stream，不設 class_id；同 Course 多 TeachingGroup 皆由 B API 可建立及查詢 | NOT RUN |
| S3-AT17 | 3 | B | 新 Staff 角色前置鍵 | School/Course/TeachingGroup/Actor 欄位及 B 權限界面預留，S22 不需改 Course 身份 | NOT RUN |
| S4-AT01 | 4 | I | API-only | I 容器沒有 A SurrealDB/B Postgres DSN，防火牆禁止直連兩庫 | NOT RUN |
| S4-AT02 | 4 | I | 舊資料接管 | S1/S2 原 Notebook/Source/Hash 不變，B 唯一 Binding | NOT RUN |
| S4-AT03 | 4 | I | Create Saga | 新課程由 I 建 B Course+唯一 A Shell/Notebook，半成功可重試 | NOT RUN |
| S4-AT04 | 4 | I | 課程隔離 | Course A/B 假 ID、空 Scope、Source 夾帶均拒絕 | NOT RUN |
| S4-AT05 | 4 | I | Cutover | 啟用已預建 A `managed-mode`／B binding policy，停止不受管獨立建新的 A Shell | NOT RUN |
| S4-AT06 | 4 | I | 失敗回退 | I 停機仍保留原 A、B 資料；可讀回舊各自 UI；Orphan quarantine 不自動刪 Notebook | NOT RUN |
| S4-AT07 | 4 | I | 聯合對帳 | 用 API 比較 Manifest/Binding；不在本期修改 A 或 B Schema/Code | NOT RUN |
| S4-AT08 | 4 | I | B 先 A 後 | CREATE_NEW atomic B Reserve 才 A Provision，再 B Finalize；ADOPT_EXISTING 不做 A Create | NOT RUN |
| S4-AT09 | 4 | I | ACK 遺失 | A 已建而 I timeout、B 已 finalize 而 I timeout 都能根據雙方 operation ID 重放而無重複 | NOT RUN |
| S4-AT10 | 4 | I | 狀態機 | 合法 transition 與 RETRYABLE/CONFLICT/QUARANTINED 判斷符合機器可驗 contract | NOT RUN |
| S4-AT11 | 4 | I | 核心對帳 | ACTIVE 前 A/B 雙側 Read-after-write、link_key、binding_version、Source Hash 一致 | NOT RUN |
| S4-AT12 | 4 | I | Cutover 失敗 | 切換至 MANAGED 中途 I crash：封鎖新 Create，但 A/B 已有資料可讀且可恢復 | NOT RUN |
| S4-AT13 | 4 | I | 跨庫恢復 | 隔離環境各自 Restore A/B 後，用 I API Manifest 比對；不同 Snapshot／缺 Binding 阻止 READY | NOT RUN |
| S4-AT14 | 4 | I | 回退兼容 | I 停用後 A/B 只讀可繼續，永不因 Saga 補償刪 A Notebook | NOT RUN |
| S4-AT15 | 4 | I | 無 DB 接線 | I Runtime 無 SurrealDB/Postgres DSN、無直接 DB egress，API-only Contract 可驗 | NOT RUN |
| S4-AT16 | 4 | I | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S4-AT17 | 4 | I | I 教材列表代理正向與越權／異常負面測試 | 從 B Binding 驗證 Course，經 A service-only Scope 列出 Material metadata，不泄露其他 Shell | NOT RUN |
| S4-AT18 | 4 | I | I 教材上載代理正向與越權／異常負面測試 | Admin→I→A 上載用獨立 ServiceToken，驗證檔案類型／限額／Idempotency，I 不存原檔 | NOT RUN |
| S4-AT19 | 4 | I | I 限課程搜尋代理正向與越權／異常負面測試 | I 以 course_id 找出唯一 A Shell，拒絕空 Scope、跨 Shell、偽造 source_id，從不轉發任意 Notebook ID | NOT RUN |
| S4-AT20 | 4 | I | I 教材下載代理正向與越權／異常負面測試 | I Stream A 下載，每次驗證 B Binding+A Owner，阻止過期／偽造資源、Content-Disposition 安全 | NOT RUN |
| S4-AT21 | 4 | I | School+Group 跨服務完整性 | I Adopt/Create 核對 School ID 與 Course Key，跨校／模糊 Group 不可錯綁；Cutover 後不能由 A raw Create 旁路 | NOT RUN |
| S5-AT01 | 5 | U | 統一導覽 | R05 只可在同一介面操作 B Course、A 教材列表／上載／搜尋／下載及 Link 狀態；Assessment／Grades 尚未實作，須展示「未推出」，不假裝已有操作 | NOT RUN |
| S5-AT02 | 5 | U | 獨立程式 | A/B/I Code/Image/Digest 完全不變；只部署 U | NOT RUN |
| S5-AT03 | 5 | U | 無直連 | 瀏覽器不接 SurrealDB/Postgres/service_role/raw Notebook | NOT RUN |
| S5-AT04 | 5 | U | 響應式 | 手機／平板／桌面主要工作流與提示無遮擋 | NOT RUN |
| S5-AT05 | 5 | U | 失敗 UX | A 或 B 故障時顯示來源清楚、可重試，無假成功 | NOT RUN |
| S5-AT06 | 5 | U | UI 回歸 | Admin 原 A/B 功能仍可運作，E2E 檢查並保留版本 rollback | NOT RUN |
| S5-AT07 | 5 | U | Session Gate | Admin Browser Session 由後端驗證，過期、登出、CSRF 或未授權不得存取 A/B | NOT RUN |
| S5-AT08 | 5 | U | U-only | U PR/Image 更新時 A/B/I Git SHA、schema hash、image digest 不變 | NOT RUN |
| S5-AT09 | 5 | U | Responsive | 手機平板桌面交互、過期 Session、錯誤提示均可測 | NOT RUN |
| S5-AT10 | 5 | U | 失敗 UX | B Course 未綁教材顯示清晰狀態，不會誤顯示 A Notebook 已建立 | NOT RUN |
| S5-AT11 | 5 | U | Frontend coverage | R5 只表示 Course/Content Portal 已有；後續生成/成績/Teacher 對應新 U Stage | NOT RUN |
| S5-AT12 | 5 | U | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S6-AT01 | 6 | B | Question Schema | Numeric/Fraction/Choice/Text/Extended 型別均有 machine JSON Schema 且 Validator 會拒絕非法答案 | NOT RUN |
| S6-AT02 | 6 | B | Rubric version | Question 與 Rubric 分開 version，舊 Assessment 引用不能被覆寫 | NOT RUN |
| S6-AT03 | 6 | B | PDF contract | 圖表／幾何 Schema/Renderer Contract 有測試 Fixture；S11 可以沿用 | NOT RUN |
| S6-AT04 | 6 | B | 獨立 UI | B Question Studio 有實際可保存/查閱的模板 UI，不依賴 I/U 修改 | NOT RUN |
| S6-AT05 | 6 | B | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | NOT RUN |
| S6-AT06 | 6 | B | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | NOT RUN |
| S6-AT07 | 6 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S6-AT08 | 6 | B | Blueprint 全生命周期 | 建立／草稿編輯／發布／查詢 Blueprint 及 Versions；Question／Rubric 有穩定版本 ID | NOT RUN |
| S6-AT09 | 6 | B | 生成前置可重現 | S8 只引用已發布 blueprint_id+version，變更 Draft 不改舊 Job 結果 | NOT RUN |
| S7-AT01 | 7 | B | Key lifecycle | Gemini Key 只在 Admin 一次輸入；後續 Task 只用 Secret Ref/Server Worker；Rotate/Revoke 有測試 | NOT RUN |
| S7-AT02 | 7 | B | 五層 READY | 格式/認證/模型存取/配額/真推理成功分開顯示；一次 AUTH PASS 不能永久 READY | NOT RUN |
| S7-AT03 | 7 | B | 錯誤隔離 | 錯 Key/超額/模型不可用時 UI 有可讀 ERROR；log 與回應不洩露 Key | NOT RUN |
| S7-AT04 | 7 | B | A 獨立 | B Provider Secret 不直接交 A；A Vault 如需 embedding 有自己獨立受控 Provider 設定 | NOT RUN |
| S7-AT05 | 7 | B | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | NOT RUN |
| S7-AT06 | 7 | B | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | NOT RUN |
| S7-AT07 | 7 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S8-AT01 | 8 | B | 真 Queue | 崩潰重試及並發可完成，工作狀態真實 | NOT RUN |
| S8-AT02 | 8 | B | B-only 生成 | 沒有 A Notebook 也能由 Blueprint 產生有效 Draft | NOT RUN |
| S8-AT03 | 8 | B | 模型治理 | 固定 Prompt、Model、Schema Version，可追溯輸出 | NOT RUN |
| S8-AT04 | 8 | B | 結果驗證 | Schema、總分／題數／內容約束 FAIL 時不允許批准 | NOT RUN |
| S8-AT05 | 8 | B | 人工批准 | AI 不可直接 Publish，只有 Admin Approve | NOT RUN |
| S8-AT06 | 8 | B | 冪等 | Queue 重複投遞不會產生兩個正式 Artifact | NOT RUN |
| S8-AT07 | 8 | B | 資料隔離 | B Worker 不持 A DB 密碼、不讀 A Notebook | NOT RUN |
| S8-AT08 | 8 | B | Generic evidence input | B-only 無 Evidence 可生成；接收者支援 issuer/JWS/jti/purpose/binding_version + preuse validation hook（未開 I 時不用） | NOT RUN |
| S8-AT09 | 8 | B | Queue 防重 | 丟 ACK 或 Worker 重啟都不能雙重 Publish；避免聲稱 API exactly-once | NOT RUN |
| S8-AT10 | 8 | B | 檢查層次 | JSON Schema、Domain Answer、citation required if supplied、Human Review 四層獨立 Gate | NOT RUN |
| S8-AT11 | 8 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S8-AT12 | 8 | B | Evidence Service Token正向與越權／異常負面測試 | I S9 以 B `core.evidence.ingest` Service Scope 附簽名 Evidence，B 驗證 audience/purpose、使用期限、來源版本，不接受 Admin Token 代替 I | NOT RUN |
| S8-AT13 | 8 | B | Evidence Worker 正式前置 | B Worker 具獨立 ServiceToken 及 Source/Job Context，S9 上線前 Evidence OFF；上線後同 Job 可重新驗證 | NOT RUN |
| S9-AT01 | 9 | I | 可選檢索 | Use OFF 時不呼叫 A；ON 只查當前 Course 已發布來源 | NOT RUN |
| S9-AT02 | 9 | I | 隔離 | A Source 範圍、B Course Binding、空 Scope 均經 Server-side 驗證 | NOT RUN |
| S9-AT03 | 9 | I | 無全庫回退 | Notebook 無內容則明確回空或拒絕，不擴大為全庫搜尋 | NOT RUN |
| S9-AT04 | 9 | I | 來源證據 | B 只留受限 Provenance ID/Hash/版本，生成草稿有 Citation | NOT RUN |
| S9-AT05 | 9 | I | 故障 | A 斷線時 Job 明確失敗或降級需 Admin 授權，不生成假引用 | NOT RUN |
| S9-AT06 | 9 | I | 單線修改 | 本 Stage 只改 I Code/Config，A/B Deploy Digest 不變 | NOT RUN |
| S9-AT07 | 9 | I | Schema & Signature | Evidence Bundle 符合 JSON Schema，簽章/issuer/audience/kid/jti/exp/allowed_purpose 可驗；不能只驗格式 | NOT RUN |
| S9-AT08 | 9 | I | TOCTOU | A Source Revoked/新版本/Binding Revision 變更後，B Queue Pre-use revalidate → STALE/REJECT；Publish 前再檢查 | NOT RUN |
| S9-AT09 | 9 | I | Prompt Injection | PDF 文字「忽略上層指令／讀其他課程」被當資料，不觸發權限變更或跨 Course API | NOT RUN |
| S9-AT10 | 9 | I | Citation | 每個引用有 SourceID、VersionID、Hash、Locator、RetrievedAt、Prompt/Model/Schema 版本 | NOT RUN |
| S9-AT11 | 9 | I | 舊版保留 | A 保存受引用舊版資料或明確合法不可重現，B 不可悄悄改引用新版本 | NOT RUN |
| S9-AT12 | 9 | I | API-only | I 不能直接讀 A SurrealDB/B Postgres；教材長文不永久複製進 B | NOT RUN |
| S9-AT13 | 9 | I | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S9-AT14 | 9 | I | B Worker 專用身份 | B Worker 只能使用 ServiceToken+link.evidence.validate；AdminSession 不可冒用 | NOT RUN |
| S9-AT15 | 9 | I | Evidence 再次核驗 | 同 job 的 MODEL_PRE_EXECUTION／PAPER_PRE_APPROVAL 可驗；另一 job 重用 jti 拒絕，過期/撤銷每次重新檢查 | NOT RUN |
| S10-AT01 | 10 | U | Evidence Toggle | Use OFF 不觸發 A；Use ON 明確顯示 A 原教材出處與引用版本 | NOT RUN |
| S10-AT02 | 10 | U | U-only | A/B/I Image/Schema 完全不變，Browser 不持 Gemini Key | NOT RUN |
| S10-AT03 | 10 | U | UI 狀態 | Queue Pending/Retry/Failure 真實顯示和錯誤回復 | NOT RUN |
| S10-AT04 | 10 | U | Session | 使用者登出及舊 Session 輸入失效 | NOT RUN |
| S10-AT05 | 10 | U | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | NOT RUN |
| S10-AT06 | 10 | U | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | NOT RUN |
| S10-AT07 | 10 | U | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S11-AT01 | 11 | B | 出卷成功 | 按 Blueprint 真正生成可批准 Math Paper | NOT RUN |
| S11-AT02 | 11 | B | 分數約束 | 各題 max_score 加總 = full_mark，錯誤阻止發布 | NOT RUN |
| S11-AT03 | 11 | B | 答案可核 | 以計算或確定性測試驗證指定題型答案 | NOT RUN |
| S11-AT04 | 11 | B | PDF 正確 | A4／字型／頁碼／換行／答案卷實際 Render 檢查 | NOT RUN |
| S11-AT05 | 11 | B | 人工批准 | 可修改 Draft 但不覆寫已批准 Artifact Version | NOT RUN |
| S11-AT06 | 11 | B | B-only | 不用 A Notebook 亦能出卷，其他服務不因本期改動 | NOT RUN |
| S11-AT07 | 11 | B | 數學可驗 | 分數/Fraction/數值答案可確定性再計算，錯誤禁止發布 | NOT RUN |
| S11-AT08 | 11 | B | 原始引用 | 若使用 Evidence 必須保存 Source Version/Hash/Locator 而非浮動 SourceID | NOT RUN |
| S11-AT09 | 11 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S11-AT10 | 11 | B | 試卷檢視及 PDF，包含偽造範圍／失敗路徑 | GET Paper 需檢查正確 Course／Version，PDF 檔為可下載 Binary、頁碼、字體及 Hash 可核對；B 不改 A | NOT RUN |
| S12-AT01 | 12 | B | 中文題型 | 選擇題、閱讀理解及作文草稿符合中文 Schema | NOT RUN |
| S12-AT02 | 12 | B | 字元與排版 | 中文標點、繁體字、字型及試卷換行可驗證 | NOT RUN |
| S12-AT03 | 12 | B | 答案與評分 | 客觀題規則可核；作文人工覆核，不以 LLM 直接發分 | NOT RUN |
| S12-AT04 | 12 | B | 課綱對應 | 題目 Topic/Learning Objective 有可追查版本 | NOT RUN |
| S12-AT05 | 12 | B | 獨立測試 | 中文測試集不沿用數學通過結果 | NOT RUN |
| S12-AT06 | 12 | B | 回歸 | A/I/U 版本不變且 B 原流程仍可用 | NOT RUN |
| S12-AT07 | 12 | B | 中文獨立 | 繁體／標點／閱讀理解／作文 Rubric 資料集單獨驗收 | NOT RUN |
| S12-AT08 | 12 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S13-AT01 | 13 | B | 英文題型 | Grammar、Reading、Writing 能分別建立 Blueprint | NOT RUN |
| S13-AT02 | 13 | B | 寫作審核 | 自由作文為 AI suggestion，不能自動確定分數 | NOT RUN |
| S13-AT03 | 13 | B | 答案規則 | 客觀題標準答案與題目版本一致 | NOT RUN |
| S13-AT04 | 13 | B | 格式 | 英文卷 PDF 換頁、字型及答案頁可讀 | NOT RUN |
| S13-AT05 | 13 | B | 固定測試 | English-only Gold Sample Test 與誤差報告 | NOT RUN |
| S13-AT06 | 13 | B | 邊界 | A/I/U 無任何新 code/schema/config 修改 | NOT RUN |
| S13-AT07 | 13 | B | 英文獨立 | Grammar/Writing/Accepted Answer 等獨立測試集，作文保留人工審核 | NOT RUN |
| S13-AT08 | 13 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S14-AT01 | 14 | B | 學科題型 | 常識科多種題型完整生成及預覽 | NOT RUN |
| S14-AT02 | 14 | B | 時效檢查 | 易變事實有來源/版本標記，無證據需人工核對 | NOT RUN |
| S14-AT03 | 14 | B | 批改要求 | 短答／解釋題保留人手 Review | NOT RUN |
| S14-AT04 | 14 | B | 版本 | Rubric/Topic/Model/Prompt 版本可追溯 | NOT RUN |
| S14-AT05 | 14 | B | 獨立測試 | 常識 Test Set 本科單獨驗收 | NOT RUN |
| S14-AT06 | 14 | B | 邊界 | A/I/U 不變，B 舊科目及分數功能回歸成功 | NOT RUN |
| S14-AT07 | 14 | B | 常識事實 | 使用有出版日/地區/來源的事實核對，變動題需人手 Review | NOT RUN |
| S14-AT08 | 14 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S15-AT01 | 15 | B | 名冊 CRUD | 可建立、匯入、查找合成學生及選課 | NOT RUN |
| S15-AT02 | 15 | B | 外鍵 | Enrollment 必須指向有效 B Student 與 Course | NOT RUN |
| S15-AT03 | 15 | B | 重複匯入 | 同 Batch 重試不重複建立學生 | NOT RUN |
| S15-AT04 | 15 | B | 純合成 | 拒絕未核准真實學生 PII 載入；有測試資料標識 | NOT RUN |
| S15-AT05 | 15 | B | 還原 | B-only Restore 後 Roster/Enrollment 全部對帳 | NOT RUN |
| S15-AT06 | 15 | B | 隔離 | A 與 I 無更動、無新的 A Credentials | NOT RUN |
| S15-AT07 | 15 | B | 只許合成 | 真實學校名單/PII 即使從 CSV 上載也會拒絕 | NOT RUN |
| S15-AT08 | 15 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S15-AT09 | 15 | B | 合成名冊檢視，包含偽造範圍／失敗路徑 | GET B Student list 僅列合成學生、限制 Scope、分頁與排序；不能返回未批准真實學生資料 | NOT RUN |
| S15-AT10 | 15 | B | 分班 Enrollment | S15 Enrollment 必須含 teaching_group_id，且 Group/Student/Course/School 一致；錯班或跨校拒絕 | NOT RUN |
| S16-AT01 | 16 | B | Assessment CRUD | 完整建立 Assessment 與 Question Items | NOT RUN |
| S16-AT02 | 16 | B | 草稿算術 | 小題分數範圍合法且總分可確定重算 | NOT RUN |
| S16-AT03 | 16 | B | 不完整分數 | 缺值、超出上限、重複題 ID 阻止 Confirm | NOT RUN |
| S16-AT04 | 16 | B | Draft 回存 | 重開瀏覽器仍可讀 B Draft | NOT RUN |
| S16-AT05 | 16 | B | 無正式事件 | 此期不得把 Draft 誤標為正式成績 | NOT RUN |
| S16-AT06 | 16 | B | 回歸 | B Roster/Course 及 B-only Restore 通過 | NOT RUN |
| S16-AT07 | 16 | B | Schema 與舊題 | S6 Question/Rubric 版本可連到 Assessment Draft 且不能覆蓋原答案 | NOT RUN |
| S16-AT08 | 16 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S16-AT09 | 16 | B | Assessment 讀取，包含偽造範圍／失敗路徑 | 按 assessment_id 讀回題目／Rubric/Revision，偽造 Course 或未批准 Actor 時必須拒絕 | NOT RUN |
| S17-AT01 | 17 | B | 一次提交 | 同 idempotency key 只建立一條提交事件 | NOT RUN |
| S17-AT02 | 17 | B | 不可覆寫 | 普通 UPDATE/DELETE Grade Events 在 API+DB role 層失敗 | NOT RUN |
| S17-AT03 | 17 | B | 正式更正 | Admin 補上原因／actor／revision，原始事件完整保留 | NOT RUN |
| S17-AT04 | 17 | B | 現值正確 | Current Projection 可由 Event Ledger 重放重算 | NOT RUN |
| S17-AT05 | 17 | B | 並發 | 兩個更正衝突時有版本檢查與序號 | NOT RUN |
| S17-AT06 | 17 | B | B 恢復 | B-only Restore 及 Event Replay 產生相同 Current Grades | NOT RUN |
| S17-AT07 | 17 | B | DB Privileges | 非 Admin API 或普通 DB role DELETE/UPDATE old grade_events 拒絕 | NOT RUN |
| S17-AT08 | 17 | B | 同時更正 | 同一 Grade 相同 Revision 兩個不同 Correction 只有一個 CAS 成功，另一個 409 | NOT RUN |
| S17-AT09 | 17 | B | 投影重算 | Grade Events 完整重播可重建 Current Projection；Supabase service_role 權限與審計分開說明 | NOT RUN |
| S17-AT10 | 17 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S17-AT11 | 17 | B | Grade 現值及歷史，包含偽造範圍／失敗路徑 | 可按 Grade Key 讀有效現值及完整事件歷史，Correction 不能改寫第一次提交；跨 Course 拒絕 | NOT RUN |
| S17-AT12 | 17 | B | Grade Idempotency Payload 衝突 | 同 idempotency_key+相同 canonical_request_hash 返回同一 Event；同 key 不同 Payload 明確 409，不可默默忽略 | NOT RUN |
| S18-AT01 | 18 | B | 收卷 | 多份模擬提交按 Assessment+Student 配對 | NOT RUN |
| S18-AT02 | 18 | B | 重複提交 | Version/Retry 不覆蓋原始答卷 | NOT RUN |
| S18-AT03 | 18 | B | 人工改卷 | 逐題評分符合 Rubric/滿分上限 | NOT RUN |
| S18-AT04 | 18 | B | Ledger | 確認之後只新增 Grade Event；無直接 UPDATE | NOT RUN |
| S18-AT05 | 18 | B | 錯誤處理 | 缺頁／無效檔案／學生不符進 Review Queue | NOT RUN |
| S18-AT06 | 18 | B | 無 A | 答卷與分數只在 B private storage，完全不寫 A | NOT RUN |
| S18-AT07 | 18 | B | 對題校驗 | Submission OCR/題目 Alignment 不可靠時阻止自動提交分數 | NOT RUN |
| S18-AT08 | 18 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S18-AT09 | 18 | B | 提交可讀 | B 可查選定 Course 的 Submission，S22 後授權教師可讀獲授權 Group/學生；當期仍 Admin | NOT RUN |
| S18-AT10 | 18 | B | 逐題改卷型別及回讀 | B 逐題決定含 question_item_id、rubric_version、score、max_score、revision；人工覆核才可提交正式 Grade Event，不能直接覆寫正式分數 | NOT RUN |
| S18-AT11 | 18 | B | 逐題改卷型別及回讀 | B 逐題決定含 question_item_id、rubric_version、score、max_score、revision；人工覆核才可提交正式 Grade Event，不能直接覆寫正式分數 | NOT RUN |
| S19-AT01 | 19 | B | 建議可追查 | 每題 AI Suggest 連 Rubric/Model/Prompt Version | NOT RUN |
| S19-AT02 | 19 | B | 人工優先 | AI 不得直接發布正式分數 | NOT RUN |
| S19-AT03 | 19 | B | 分數驗證 | 人工採納後每題分與 Grade Ledger 約束一致 | NOT RUN |
| S19-AT04 | 19 | B | 爭議 | 低信心／答案不確定轉人工處理 | NOT RUN |
| S19-AT05 | 19 | B | 測試集 | 在固定合成 Gold Dataset 上評估精度與錯誤類型 | NOT RUN |
| S19-AT06 | 19 | B | 無 A | AI 改卷模型只讀 B submissions/rubric，不連 A DB | NOT RUN |
| S19-AT07 | 19 | B | Gold Benchmark | 人工 Gold Set 同時評估 Answer Extraction、Question Alignment、Score Partial Credit、Low Confidence | NOT RUN |
| S19-AT08 | 19 | B | 多次一致陷阱 | 三次 AI 一致但共同 OCR 錯誤的測試依然需要人手拒絕 | NOT RUN |
| S19-AT09 | 19 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S20-AT01 | 20 | B | 確定性 | 平均分／題目弱點統計與 SQL/人工獨立重算一致 | NOT RUN |
| S20-AT02 | 20 | B | 兩版上限 | 同 Course+Target Scope 不能有第 3 個 VALID ACTIVE | NOT RUN |
| S20-AT03 | 20 | B | 老師選擇 | 未經 Admin/教師 Keep 不可納入下一份卷 | NOT RUN |
| S20-AT04 | 20 | B | 更正失效 | Grade Correction 後受影響 Snapshot 標記 STALE | NOT RUN |
| S20-AT05 | 20 | B | 來源 | Snapshot 只引用 B Grade Events，A 無弱項內容 | NOT RUN |
| S20-AT06 | 20 | B | 一致重跑 | B Restore／重算不會將 Retired/Wrong Scope Profile 誤變 Active | NOT RUN |
| S20-AT07 | 20 | B | 記憶不等於數據 | Grade Event/Analytics Snapshot/Weakness Candidate/Weakness Memory 四者區分 | NOT RUN |
| S20-AT08 | 20 | B | Keep2 原則 | 最多兩個 Valid Active Memory，但不得刪 Event 或原始 Analytics；更正後 STALE | NOT RUN |
| S20-AT09 | 20 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S20-AT10 | 20 | B | Analytics／Weakness 讀取，包含偽造範圍／失敗路徑 | B 可讀已完成 Analytics 與每 Course 最多兩個有效 Weakness，STALE 或跨 Course 資料不會當作 Active | NOT RUN |
| S20-AT11 | 20 | B | Weakness 完整狀態 | B 有 Candidate／Active／STALE／RETIRED 查詢以及 Discard，既有分數不受影響 | NOT RUN |
| S21-AT01 | 21 | U | U-only Regression | U 使用已發布 B 資料/API，B/I/A 不作同 Stage 修改 | NOT RUN |
| S21-AT02 | 21 | U | 成績顯示 | 有真實 Synthetic Draft/Submitted/Correction History 的畫面 | NOT RUN |
| S21-AT03 | 21 | U | Weakness UI | Keep/Discard，兩版本和 STALE 狀態可見 | NOT RUN |
| S21-AT04 | 21 | U | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | NOT RUN |
| S21-AT05 | 21 | U | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | NOT RUN |
| S21-AT06 | 21 | U | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S21-AT07 | 21 | U | U UI 每種弱項狀態可用 | 從 B S20 API 真實取得 Candidate/Keep/Discard/STALE/RETIRED，無需在 U Stage 修改 B | NOT RUN |
| S22-AT01 | 22 | B | 多人身份 | 教師及不同管理角色可登入且退出／停用生效 | NOT RUN |
| S22-AT02 | 22 | B | B 權限 | 跨 Course B API read/write/export 被阻止 | NOT RUN |
| S22-AT03 | 22 | B | 成績 | Teacher 不可更新已提交 Grade，System Admin 可追加更正 | NOT RUN |
| S22-AT04 | 22 | B | A 尚未開放 | Teacher UI 不顯示可用 Content Vault，無任何 A token | NOT RUN |
| S22-AT05 | 22 | B | 服務角色 | B Service Secret 未暴露前端；RLS/Views/Functions 經檢查 | NOT RUN |
| S22-AT06 | 22 | B | 回歸 | Single Admin 歷史數據與工作流保留 | NOT RUN |
| S22-AT07 | 22 | B | 舊 Actor migration | S1/S3 預留 admin actor/scope，S22 首次多用戶 migration 前後所有事件歸屬不丟失 | NOT RUN |
| S22-AT08 | 22 | B | 權限撤銷 | B Course grant revoke 產生 version/epoch 並讓 I 可用 API 重新驗證 | NOT RUN |
| S22-AT09 | 22 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S22-AT10 | 22 | B | 個別教師授權服務 API正向與越權／異常負面測試 | B 以 ServiceToken + `core.grant.check` 對指定 staff_id+Course 實際核驗 Grant/epoch，教師不能取得該服務憑證 | NOT RUN |
| S22-AT11 | 22 | B | Teacher 真實業務操作 | 教師可用 StaffSession 讀獲授權 Course、TeachingGroup、Synthetic Roster、Assessment、Grades、Submissions；只可授權 Submit/Manual Mark，不可更正正式分數 | NOT RUN |
| S22-AT12 | 22 | B | Teacher 撤權與分組負面 | 停用/撤權時，舊 Token/舊列表/跨 Course/Group/Student 被 B 每一個業務 API 拒絕；無 AdminToken | NOT RUN |
| S23-AT01 | 23 | I | 教師只讀 | Teacher 只能查看所屬 B Course 的 A Source | NOT RUN |
| S23-AT02 | 23 | I | 跨課程負面 | 偽造 Course/Notebook/Source/Download ID 返回拒絕 | NOT RUN |
| S23-AT03 | 23 | I | 寫入禁止 | Teacher 不能用 I/A raw API upload/edit/create/delete/link | NOT RUN |
| S23-AT04 | 23 | I | 權限撤銷 | 撤銷 B Grant 後 I 新請求即時拒絕 | NOT RUN |
| S23-AT05 | 23 | I | I-only 修改 | 不改 B RBAC Schema／A Content Schema/Code | NOT RUN |
| S23-AT06 | 23 | I | 審計與回歸 | 授權 Trace/拒絕紀錄清晰、原 Admin 功能不退步 | NOT RUN |
| S23-AT07 | 23 | I | 即時撤銷 | Teacher Permission 撤銷後舊 Session/Cache/下載連結不能繼續授權 | NOT RUN |
| S23-AT08 | 23 | I | 讀取邊界 | 跨 Course／偽造 Notebook/Source ID 或上游直接存取全部禁止 | NOT RUN |
| S23-AT09 | 23 | I | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S23-AT10 | 23 | I | Teacher 與 Service 分離正向與越權／異常負面測試 | 教師只用 StaffSession 呼叫 I，I 使用獨立窄權 B Grant ServiceToken 與 A 唯讀 ServiceToken；拒絕 AdminSession 冒充 Teacher | NOT RUN |
| S23-AT11 | 23 | I | 教師搜尋 API，包含偽造範圍／失敗路徑 | StaffSession 按 Course Grant 向 I 搜尋 A 教材；過期或撤銷、偽造 Course/Source 必須拒絕 | NOT RUN |
| S23-AT12 | 23 | I | 教師下載 API，包含偽造範圍／失敗路徑 | 教師透過 I 下載二進位教材檔案；I 逐次驗證 B grant epoch + A Source Owner，不能用 AdminToken 代替 | NOT RUN |
| S23-AT13 | 23 | I | 教師授權端到端一致 | S23 I只讀 A，S22 B 的 Staff Grant 每次查核；舊 Stream/下載/快取 URL 過期及撤權測試 | NOT RUN |
| S24-AT01 | 24 | U | U-only Teacher Gate | 已獲授權教師登入可看 A 教材唯讀；U 不接觸原生 Admin Password | NOT RUN |
| S24-AT02 | 24 | U | 跨課程 UI | 沒有授權的 Course 及 Source 被隱藏且 API 同時拒絕 | NOT RUN |
| S24-AT03 | 24 | U | 撤銷 UI | Grant revoke 後舊 View/Download Cache 不能繼續使用 | NOT RUN |
| S24-AT04 | 24 | U | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | NOT RUN |
| S24-AT05 | 24 | U | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | NOT RUN |
| S24-AT06 | 24 | U | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S25-AT01 | 25 | B | 正式批准 | 沒有 Data Privacy/AI Provider Approval 時 Import 強制拒絕 | NOT RUN |
| S25-AT02 | 25 | B | 隔離 | 真實學生的資料只在 B，不寫 A、AI context 有批准策略 | NOT RUN |
| S25-AT03 | 25 | B | B 授權 | 跨班、跨學生、導出及 Analytics 權限測試 | NOT RUN |
| S25-AT04 | 25 | B | 血緣 | Evidence 可追溯真實 Grade Event/Teacher Record | NOT RUN |
| S25-AT05 | 25 | B | 學年 | 真實資料有 Retention/Legal Hold 標記 | NOT RUN |
| S25-AT06 | 25 | B | B-only | A/I 不需 Schema/Code 改動即可使用本 Stage | NOT RUN |
| S25-AT07 | 25 | B | 正式 PII Gate | 未經校方 AI Provider/Privacy Data Terms 簽核絕不可匯入真實學生資料 | NOT RUN |
| S25-AT08 | 25 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S26-AT01 | 26 | A | 學年封存 | Archive 保留 Notebook、Source、歷史版本 | NOT RUN |
| S26-AT02 | 26 | A | 不誤刪 | 普通 UI 不能硬刪 Notebook；Retention 須政策批准 | NOT RUN |
| S26-AT03 | 26 | A | 原檔校驗 | Source/Asset/File SHA 對帳可重跑 | NOT RUN |
| S26-AT04 | 26 | A | A 獨立恢復 | A-only Restore Drill 與內容索引可恢復 | NOT RUN |
| S26-AT05 | 26 | A | Admin 操作 | 有清楚保留與 Review 紀錄 | NOT RUN |
| S26-AT06 | 26 | A | 分線 | B/I/U 版本完全不變 | NOT RUN |
| S26-AT07 | 26 | A | 基本保留政策回歸 | 確認 S1 已有 Retention/License 初版；S26 只增加操作 UI 與年度封存 | NOT RUN |
| S26-AT08 | 26 | A | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S26-AT09 | 26 | A | A 健康及備份受控讀取 | A 提供最小 ServiceToken-only /health 和 /backup-status 含可核對 snapshot/restore 狀態；不可暴露檔案或 Root Key | NOT RUN |
| S27-AT01 | 27 | B | 結算狀態 | Open→Closing→Closed→Archived，非法轉換拒絕 | NOT RUN |
| S27-AT02 | 27 | B | 保留成績 | Grade Events/Corrections 不因 Keep2／Year Close 消失 | NOT RUN |
| S27-AT03 | 27 | B | 政策 | Legal Hold/Retention 未核准不可硬刪 PII | NOT RUN |
| S27-AT04 | 27 | B | B 恢復 | 學年結算與稽核可 B-only Restore/Rebuild | NOT RUN |
| S27-AT05 | 27 | B | 操作證據 | 每個 Close/Archive 有 Actor/Reason/Time | NOT RUN |
| S27-AT06 | 27 | B | 分線 | A/I/U 不修改，內容 Vault 不因此刪除 | NOT RUN |
| S27-AT07 | 27 | B | 影響範圍 | B Year Close 不可直接 Delete A Notebook 或 Grade Ledger Source | NOT RUN |
| S27-AT08 | 27 | B | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S27-AT09 | 27 | B | B 健康及備份受控讀取 | B 提供最小 ServiceToken-only /health 和 /backup-status 含 migration/snapshot/restore 時點；不能透出學生/成績內容 | NOT RUN |
| S28-AT01 | 28 | I | 一致性 | I 可列出每個 B Course 對應唯一 A Shell/Notebook/Source Hash | NOT RUN |
| S28-AT02 | 28 | I | 異常 | 找出孤兒 A Notebook、缺 B Binding、Duplicate Key 與未對齊版本 | NOT RUN |
| S28-AT03 | 28 | I | 失敗封閉 | 不明所有者的教材拒絕進出卷 Context | NOT RUN |
| S28-AT04 | 28 | I | 獨立復原 | A-only、B-only Restore 各自有證據，I 只讀 Manifest 並交叉核對 | NOT RUN |
| S28-AT05 | 28 | I | 界線 | I 不存任何 A/B DB Credentials，不修改 DB Schema 或直接 Restore | NOT RUN |
| S28-AT06 | 28 | I | 後向相容 | A/B/U 版本不動，完整平台回歸通過 | NOT RUN |
| S28-AT07 | 28 | I | S4 核心已存在 | 此 Stage 只加 Dashboard/Alert History，不在此期首次補救遺失 Binding 恢復能力 | NOT RUN |
| S28-AT08 | 28 | I | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | NOT RUN |
| S28-AT09 | 28 | I | I Dashboard 使用前置 API | I 只使用 S26 A 與 S27 B Health/Backup/Manifest Service API，不使用 SQL/SurrealDB 或 DB Restore 權限 | NOT RUN |
