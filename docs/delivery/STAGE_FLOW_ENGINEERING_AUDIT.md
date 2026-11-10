# Stage 0–28 Reuse-first Flow and Dependency Engineering Audit

**Scope:** current v0.7.4 baseline, minimally revised as v0.7.5 (no renumbering, one owner per Stage). Tested with static source inspection plus dependency/negative model checks; no real services started. `S0` only docs and GitHub/Owner approval. `R01–R28` sequential **platform release manifests**; development can overlap independently after their technical prerequisites.

## Findings changing the engineering work plan

- **F01 duplicated A implementation risk:** Open Notebook already has upload, extraction, search, indexing, notes, provider keys and UI. Reuse them. Sunrise A work is **security, school scope, version and retention**; not writing a second Notebook app.
- **F02 false Queue equivalence:** ON internal background worker does *not* fulfill B's durable AI generation job semantics. Keep separate B Queue, but do not duplicate A ingestion jobs.
- **F03 S21 missing prerequisites:** S21 promised actual manual/AI marking UI but did not list B S18/S19 among technical prerequisites. **Changed to S10/S17/S18/S19/S20**.
- **F04 S22 B staff scope:** Teachers need existing marking/analytics resource checks; ensure S18 and S20 are released before S22 staff authorization. **Changed to S3/S17/S18/S20**.
- **F05 S24 UI reuse:** Teacher Portal should reuse the U S21 Assessment/Analytics view instead of making a new one. **Changed to S5/S21/S23**.
- **F06 S27 annual close:** Closing must consider incomplete manual marking (S18) and weakness snapshots (S20), not just ledger and real student import. **Changed to S17/S18/S20/S25**.
- **F07 Stage UX gate:** B Stage can be operated through a **protected B-local minimal trial screen** or authorized Admin operation client, while U is the distinct unified Sunrise UI. A fully usable school UI requires its own U Stage; do not claim a non-existent U feature after B releases S11–S14 or S18–S20.
- **F08 stages S1/S4 are still large:** split work into internal *non-released tasks* and failure-injection increments, but do not mark an insecure intermediate stage complete. Formal R01 and R04 acceptance remain intact.

## Cross-service flow (each API comes from an earlier owner)

`S0 identity/owner decision` → `S1 A native ON engine behind A policy` → `S2 A Source ownership/version API` + `S3 B independent Course/TeachingGroup/Reservation/identity` → `S4 I Create/Adopt & recovery` → `S5 U unified materials UI`.

Generation is **B-owned**: `S6 B Question/Rubric` + `S7 B Provider` → `S8 B durable generation` → `S9 I optional A evidence (scoped and versioned)` → `S10 U generation workflow` → `S11-14 B subject-specific validators/PDF`.

Assessment is **B-owned**: `S15 synthetic enrollment` → `S16 score drafts` → `S17 immutable grade event` → `S18 manual submission/marking` → `S19 AI marking suggestions` + `S20 deterministic analytics` → `S21 U combined learning UI`.

Permissions: `S22 B actual business StaffSession rights` → `S23 I teacher read-only A` → `S24 U Teacher Portal` → `S25 B school-approved real PII`.

Governance: `S26 A school content archive` + `S27 B year close` → `S28 I read-only health / restore dashboard`.

## Per-stage engineering judgement

| Stage / owner | Tech prerequisites | Reuse / avoid rebuilding | Sunrise-only work + acceptance focus | Collision / downstream |
|---|---|---|---|---|
| S00 **P** | — | Open Notebook upstream knowledge/credentials/worker/REST; GitHub existing docs CI. **Do not:** 任何 Runtime 服務或雙庫 PoC | 批准 reuse-first A/B/I/U、Course 粒度、A-only S1 搜尋及 Provider Optional、S4 受控 Cutover、GitHub v0.5 → 新 Baseline 的 docs-only PR | 不得將上游「單使用者 Notebook」推定為學校 RBAC；來源 ZIP 的 git SHA 未核實 **Next:** S1 A、S3 B 都依本次 Owner 批准；Release 先後與技術依賴分開 |
| S01 **A** | S0 | ON notebooks CRUD, existing Next.js components, Sources upload, Text Search, async job status, notes and archive. **Do not:** Notebook 引擎、來源上載管線、全文抽取及原生 UI 組件 | A Policy Gateway + ContentShell→Notebook 映射、Session、密碼 fail-start、原生 API 不暴露、Source 單一擁有者、A Restore | 原生 Notebook POST/DELETE、Source 多 Notebook reference、無 scope 全庫搜尋及來源列舉；`delete_source` 不能誤刪原檔 **Next:** S2 Version/Source Manifest 依賴穩定 ID；S4 依賴可靠 A 服務操作；S23 不可使用原生 Admin Password |
| S02 **A** | S1 | ON Source topics, timestamps, source list/filter/search, embeddings, text/vector search, ingestion status. **Do not:** 第二套 PDF 抽取器、Embedding Store、搜尋引擎或一般來源列表 UI | 版本化內容 Catalog、School/Source 權屬、發布狀態、原檔 Hash、權利政策、A versioned scoped service APIs、Consumer Fixtures | 上游 updated_at 不等同不可變 SourceVersion；Search results 為動態 Dict，引用 Locator 不保證長期穩定 **Next:** S4 I Create/Adopt、S5 I Proxy、S9 Evidence、S23 Teacher Read 用同一 A Manifest/Scope；不直接連 B DB |
| S03 **B** | S0 | PostgreSQL/Supabase 原生 database/Auth capabilities（非 Open Notebook）. **Do not:** 透過 SurrealDB 模擬校務 SQL／以 ON notebook 當 School Course | B School/Subject/Year/Course/TeachingGroup、UNLINKED 狀態、原子 Reserve/Finalize/operation log、B-only Restore、服務端 Admin Session Issuer | Course 不等於 Class；一個 Course 多 TeachingGroups；即使尚未安裝 A 也可用 B Admin CRUD **Next:** S4 不得依賴新 B API；S6/15/22 永遠保留 Course grain |
| S04 **I** | S2, S3 | S2 A service API + S3 B service API only. **Do not:** 自行建第二套 Notebook／從 I 直連兩個 DB／將 ON raw Secret 放 I | I Create/Adopt Saga、A/B immutable IDs、冪等、故障查詢/重試/隔離、跨服務讀回與最小 restore reconciliation | S3 B Reserve/Course 原子操作；A Create ACK loss；S4 Cutover 半完成；不能自動 Delete 已建 Notebook **Next:** S5 U 與 S9/S23 檢索均靠 ACTIVE Binding；不以同名 Course 自動配對 |
| S05 **U** | S4 | ON Next.js UI 的檔案表格/搜尋/Notebook context UI pattern；S4 API facades. **Do not:** 另寫整套 A Source 搜尋或暴露 ON 全功能原生 UI | Sunrise U Course / Materials / Upload / Search / Download／link-state／Session UX | 重用元件不能重用直接呼叫原生 ON API 的 Client；不預先顯示 Assessment / Grades **Next:** S10 U 生成、S21 U 成績、S24 U 教師分別另出前端版本 |
| S06 **B** | S3 | ON custom Transformations/Prompt 管線只作參考；Math-paper Question Schema 想法. **Do not:** 在 A Transformations 儲存正式 Question/Blueprint/Rubric、複製整個 Math-paper App | B Blueprint / Question / Answer / Rubric 的版本化 CRUD、Validators 及學科擴展接口 | ON Transforms 不支援正式 item score/answer rubric version；不能把 Markdown 當正式 Question contract **Next:** S8 Queue 只引用已 Published blueprint_version；S11–14 逐科穩定擴充 |
| S07 **B** | S3 | ON 已有 Gemini 等 Provider Key/Models Connection Test/Encryption Code 供設計參考. **Do not:** 第二套 A Gemini Key 管理頁或把 Open Notebook Key 直接交 B | B 獨立 Generation Provider Secret 設定、Test、Revocation、Model Readiness、成本/配額狀態 | A Key 與 B Key 係兩個憑證域；同一 Admin 輸入未代表兩服務可共享；不得直接查 SurrealDB Key **Next:** S8 B generation uses B provider; S19 marking uses provider policy |
| S08 **B** | S6, S7 | ON 內部 surreal-commands 僅用於 A 文件處理；可借鑑任務狀態 UI. **Do not:** 將 A Worker Queue 直接當 B durable paper/marking queue；聲稱 upstream job cancel 完整可用 | B durable Queue + idempotent jobs/attempts + Prompt Model audit + Draft validators + Human approval | ON `CommandService.list_command_jobs()` 仍返回空列表，`cancel_command_job()` 只 log/return True；與 B 完整 job lifecycle 不等價 **Next:** S9 I 可選 Evidence；S11–14 用既有 Job 基礎；S19 Marking 借用 B Queue |
| S09 **I** | S4, S8 | ON `POST /search` text/vector/Ask, Source provenance; S4 I binding. **Do not:** 重建 RAG Retriever/Embedding Engine；把 ON Ask 原文當作正式引用正確性證明 | I server-side Course authorization、綁定版本、Evidence bundle、簽名／revalidation／撤銷／注入防護 | ON scope 省略即全庫；SearchResponse results 為 Dict 而非凍結 Citations；相同 Job 可以再驗證不可當 replay **Next:** S10 U 用 I Evidence；S11–14 B Paper 仍需 Domain/Human proof |
| S10 **U** | S5, S9 | ON Chat/context/Ask UI 可作交互模式參考；S8/B S9/I APIs. **Do not:** 把 A Chat workflow 當 B 出卷儲存或在 U 寫生成業務規則 | Sunrise U Task/Blueprint/Evidence/Approval 純展示/操作入口 | U 不持 provider secret；S9 A 斷線要明確提示，而非假成功或全庫 fallback **Next:** 後續四科試卷 UI 只可在各自 B-local Console 或另開 U-only stage 呈現 |
| S11 **B** | S6, S8 | ON 可渲染 KaTeX、來源文字；Math-paper 題目/答案/圖像 schema 作設計參考. **Do not:** 以 ON note/Transformation 冒充正式數學卷或將 Math-paper 前端整包移植 | B Math question renderer、確定性答案檢查、Fullmark constraint、PDF export、Answer key | S8 模型答覆可能錯；圖表、分數、引用、PDF 裁切均需實測，不改 A **Next:** S18 Submission 引用不可變 Paper/Item Version；U 要有獨立呈現安排 |
| S12 **B** | S11 | S6 Question Contract + B Maths PDF pipeline. **Do not:** 複製一份中文專屬 Queue、重寫數學共用 PDF 引擎 | B 中文 Question Type、繁體字版面、閱讀理解、寫作 Rubric、人審 Gold Cases | 不能只改 Prompt；主觀題不得自動斷言唯一答案 **Next:** S18/S19 Marking 支援中文作文／人工驗收 |
| S13 **B** | S11 | S6 Contract + S11 B PDF service; Math-paper 某些答題形式可作類型參考. **Do not:** 複製英文專用儲存或直接把其他科答案判分器共用作真值 | B 英文 Grammar/Reading/Writing validators、rubric、PDF | 英語主觀題、接受答案表述需人工，不能單靠模型互評 **Next:** S19 英文 AI marking benchmark 題目對齊 |
| S14 **B** | S11 | S11 產卷基礎 + S9 已核實 Evidence 片段（可選）. **Do not:** 讓 A 原生問答直接承擔正式常識題目正確性 | B 常識科 Topic/fact-date/provenance/多答案 Rubric、人工查證 | 有 Source citation 不代表當期事實正確；不同教材版本和地區課綱需標明 **Next:** S19 判分與 S20 Analytics topic grouping |
| S15 **B** | S3 | B S3 TeachingGroup/Course IDs；原生 Supabase DB/RLS 可作工具. **Do not:** 將學生個資寫入 A/Notebook；過早上線實名學生 | B synthetic Student/Enrollment with exact TeachingGroup, import idempotency and full school scope | Demo data 必須確認合成、班級不等 Course；重新匯入不可重複 **Next:** S16 Assessment S17 Grades S18 Submission 全部引用穩定合成 Student ID |
| S16 **B** | S6, S15 | B S6 Question/Blueprint/Rubric、S15 Synthetic Students. **Do not:** 重新開一套成績 DB 或讓 ON notes 保存草稿 | B Assessment versions、Score Draft CRUD、分數校驗與歷史 | Draft 可改但未正式提交，不能對後續 ledger 構成權威 grade **Next:** S17 Grade immutable submit，S18 manual marking |
| S17 **B** | S16 | Postgres constraints/transactions/RLS + S16 Draft. **Do not:** 用 ON Source、一般可覆寫 row、前端限制代替 immutable score | B append-only Grade Event + correction with canonical_request_hash + CAS revision + replay projection | 同 key 不同 payload 應 409；DB 超級用戶無法被一般 append-only 保證約束 **Next:** S18 manual grading / S20 analytics／S27 retention 視 Grade ledger 為真值 |
| S18 **B** | S11, S17 | S11 B Paper Item IDs + S17 Grade Ledger; PTH_Homework 流程可作研究. **Do not:** 把 PTH_Homework 原來 public CORS / BYOK API 搬到生產當安全邊界 | B synthetic submissions、逐題 Rubric version／manual marking／human approval | 答卷重試不覆寫原文件、課程/student/item 不可錯配；不得直寫 current_grade **Next:** S19 AI Suggestions ground truth；S21 U 顯示改卷結果 |
| S19 **B** | S18, S8 | PTH_Homework multi-pass candidate reasoning，人工誤差比較概念. **Do not:** 用兩／三次 LLM 一致當正確；直接採用其 HTTP API / BYOK/CORS | B AI Suggest, alignment/partial-credit benchmark, confidence, human acceptance + ledger API | 人工 Gold Set 覆核，OCR/抽取錯即使多模型一致也可能錯 **Next:** S21 U 讀標記結果／S22 Staff grant 功能 |
| S20 **B** | S17 | B S17 ledger immutable event + S6 Topic metadata; no A data. **Do not:** 讓 ON RAG Score 或模型猜測取代 deterministic SQL analytics | B metrics Snapshot/Candidate/Keep2/Discard/STALE/RETIRED and watermark | Weakness Keep2 只限 ACTIVE 記憶，不可刪真正的 Grades／統計 **Next:** S21 UI 要候選／Discard／Stale 讀寫，S27 Closing 要能 Retire |
| S21 **U** | S10, S17, S18, S19, S20 | S10 U Generation + S15–20 B Existing APIs. **Do not:** U 直接 SQL；為了 UI 方便偷開新 B endpoints | Sunrise U Roster/Assessment/Grade History/manual+AI Marking/Weakness Dashboard | S18 S19 要成為明確 Technical prerequisites；不能用未發布的 B Marking read APIs **Next:** S24 Teacher-specific extension 重用此 UI 頁與針對 Staff scope 逐項禁權 |
| S22 **B** | S3, S17, S18, S20 | B existing Supabase Auth/RLS patterns + early school/course/group model. **Do not:** 重造 A multi-user ACL 或讓教師共用 ON admin key | B StaffSession/MFA(按政策)/invitation/grants + backend resource checks, revoke epoch | 教師需有真實可用 B operations，不只查自身 Grant；不能自動授權 A **Next:** S23 I Staff course-level read；S24 U staff portal；S25 real PII gate |
| S23 **I** | S4, S22 | S4 I Binding, S22 B grants, S2 A search/download API. **Do not:** 在 A 原生 API 開 teacher password 或在 I 直接查 B 資料庫 | I StaffSession→B service Grant lookup→A scoped read only（含 search/download） | 舊 token/cache 撤銷失效；Cross School/Course/Group 需要負面測試 **Next:** S24 U teacher content UI/S25 real PII preconditions |
| S24 **U** | S5, S21, S23 | S5 U Course, S21 U Assessment workspace + S23 I teacher read. **Do not:** 重寫 A Notebook page，或在 U 幫 B 補角色授權 | U Teacher dashboard/read-only materials＋B permitted assignment/marking UI | 客戶端隱藏按鈕不構成安全控制，B/I server-side 仍須授權；無權時不能誤顯資料 **Next:** S25 real student readiness / staff onboarding workflow |
| S25 **B** | S22, S23, S24 | S22 B staff grants, S24 U existing UI. **Do not:** 把 A 資料庫用作學生／正式分數的存放 | B real student/PII input behind school policy consent & provider terms, mandatory isolation/retention | 未經校方批准仍需 Fail Closed；由 synthetic 切 real 需完整授權／刪改稽核 **Next:** S27 B year closure/retention supports legal holds; A materials never affected |
| S26 **A** | S2 | ON notebook archived field / Source updated/topics + A source files. **Do not:** 自行重建整個 ON notebook 檔案存儲/備份引擎，或藉 archive 直接 hard-delete | A retention policies, source version retention, hash/backup-status read APIs and archive UI | S1 已需最小 backup+restore；來源版權政策先定，不能等到 S26 **Next:** S28 I health/backup view only through API; no DB access |
| S27 **B** | S17, S18, S20, S25 | B grade ledger/projections/assessment state, Postgres backup tools. **Do not:** 從 B 發命令刪 A notebook / 藉 closing 清除 Grade Events | B year-close transition, pending assessment checks, grade audit/retention, health/backup service status | S18 pending marking/S20 weakness stale scope 需進入 Closing Gate；不同 A 年度封存互不觸發 **Next:** S28 I dashboard consumes owner-only read status |
| S28 **I** | S4, S26, S27 | S4 I core reconcile + S26 A and S27 B health/backups APIs. **Do not:** 新增 I 管理 DB 用於跨服務 SQL、代替 A/B 自己 Restore | I read-only health/version/backup manifest dashboards and mismatch/quarantine alerts | A/B 各自 restore+cross snapshot discrepancy impossible to hide, I no DB credentials **Next:** 運維後續以此基線做事件響應/告警，不改兩邊 backup |

## Potential traps that do NOT justify inventing a new mandatory Stage today

- **S1 provider / Gemini:** if A uses embeddings, ON's existing encrypted provider settings can be reused behind A-only Admin gateway; define this optional gate in S0. B S7 provider management remains independent, not a duplicated A implementation.
- **S2 catalog:** native `Source.topics` can cover early Topic labels, but publish/rights/immutable provenance still requires A adapter. Do not overload native `updated` as version ID.
- **S5 U reuse:** Open Notebook Next.js components may accelerate layout; reuse UI *presentation*, replace raw API access. Whole upstream Admin UI cannot remain publicly reachable.
- **S9 evidence:** A Source content can be retrieved with existing search, but the school-specific release/version/hash/permission/TOCTOU contract is I-owned.
- **S11–S14 Maths and other papers:** native Transformations can make informal drafts, but B owns official Question Schema/PDF/Grade lineage. Trying to reuse native notes as assessments would make grade authority inconsistent.
- **S22 Teacher:** ON Auth is a single shared password. StaffSession/School/Course/Group access and grant revocation belongs to B + I even if upstream later adds generic users; require actual contract tests.

## Smaller work packets without reducing formal Gate

**S1 internal implementation order (non-release subtasks):** pinned ON deploy + backup inventory → private network/secrets/own session → A Shell/Source owner mapping & scoped Adapter → native upload+search+download with failure/partial-processing tests → A original+DB restore → complete security bypass regression. Do not publish an intermediate raw ON UI as a completed Sunrise release.

**S2:** reuse native topics/status → add version and rights/release metadata → implement and test A service API (+ citation provenance) → fixture/consumer contract freeze.

**S3:** B Course/Group identity & local CRUD → transactionally reserve/finalize operation → service principal/identity contract → independent B backup/restore → consumer fixtures.

**S4:** read-only Adoption preview → Create/Adopt two saga flows → ACK-loss/Crash fault injection + idempotency → quarantine + read-back → cutover rules → separate backups and cross-service manifest match. I never patches B or A.

**S8:** B blueprint IDs → provider availability check → durable Queue & job dedup → draft/approve/version → failure/retry evidence → no A references required.

**S22:** B IAM user & grant schema → per-operation staff permissions → cross-group/student negative cases → grant revoke & stale-session checks → ensure Admin regression. S23 then consumes only B grant-check API.

## Release readiness decision table

- S0 PASS = Owner signed architecture/docs; not Docker or dual DB PoC.
- S1–S3 PASS = actual A-only/B-only healthy product and isolated restore, owner API tests and reproducible upstream pin.
- S4/S9/S23 PASS = running A and B provider/consumer checks plus I-only diff, no DB driver/credential in I; negative/mismatch recovery tested.
- S5/S10/S21/S24 PASS = actual visible U flow, current API contract, authorization, mobile/desktop and regression; U never stores data authority.
- B S6–S8/S11–S20/S22/S25/S27 PASS = B-local trial tool or already released U consumer can execute full workflow; if the only way to use a B feature is an internal debugger unavailable to users, mark **API READY but PRODUCT NOT ACCEPTED** until approved trial surface exists.
- S28 PASS = I-only read-only monitoring with A/B real independent restore evidence; do not treat dashboard as database recovery engine.

**STOP RULE:** API Client requires a new A/B endpoint not present in earlier owner release → return to A/B one-owner issue/release. Never add ad hoc DB call from I/U. This is a planning review, not evidence runtime works.

## B use-existing-tooling opportunities and caveats

| B Stage | Possible ready-made infrastructure | What Sunrise must still implement / verify |
|---|---|---|
| S3 | PostgreSQL SQL constraints, Supabase Auth, RLS patterns | Course/TeachingGroup business objects, B Reserve/Finalize atomic log, service scopes and real Restore; cannot treat generic RLS as domain permissions |
| S7 | Esperanto multi-provider SDK for Gemini/structured LLM calls; approved server Secret Store | B-owned credential lifecycle, READY vs real model/quota/billing tests, no A secret sharing |
| S8 | Supabase Queues/pgmq durable **logged** queue; Postgres job state | Work lease, retries, deduplicated artifact effects, billing controls, human approvals. Exactly-once within visibility window is NOT globally exactly-once LLM execution |
| S11–S14 | Reuse S6 schemas and S11 B common PDF renderer | Four different subject validators, answer formats and human review, not 4 queues or 4 databases |
| S15–S25 | Supabase Auth/RLS/Postgres FK, B local storage buckets | Teacher course/group rights, data minimisation, real student school policy, append-only Ledger and approved marking |

S3/S7/S8 should decide whether these tools are fit at **their own Owner Stage**, not specify untested implementation details during S0. Provider version/cost/region must be checked at deployment.
