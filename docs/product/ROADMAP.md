# Reviewed v0.7 — Single-owner Stage Roadmap

**Total Stage S0–S28, Release R01–R28. Stage0 is a documentation/Owner approval gate with NO Product Release.** Every runtime release changes exactly one owner component (A Content, B Learning, I API-only Bridge, U UI-only). Development across separate repos may proceed in parallel after contract freeze, but the Platform Release Manifest is sequential. Technical prerequisites are distinct from release-order predecessor.

| Stage | Owner | Target release | Technical dependencies | One independently usable deliverable |
|---:|:---:|:---:|---|---|
| [0](../stages/STAGE_00.md) | P | — | — | Planning Baseline & Security Decisions — 新 Enochan222 Repo 採 v0.7.5 docs-only PR；不遷移 IssacSitHk 歷史；S0 用本地可核對 QA、簽核 A/B/I/U 權責。 |
| [1](../stages/STAGE_01.md) | A | R01 | S0 | Secure Open Notebook Vault — Admin 可建立 Content Shell→唯一 Notebook，安全上載/搜尋/下載教材、原檔與 A-only 復原。 |
| [2](../stages/STAGE_02.md) | A | R02 | S1 | Versioned Content Catalog & A Contract Freeze — 可管理教材 Topic/Version/Publication、Source Provenance、source retention；提供 I 所需穩定 A API v1。 |
| [3](../stages/STAGE_03.md) | B | R03 | S0 | Independent Academic Course & B Contract Freeze — 獨立 B PostgreSQL/Supabase 有 School/Subject/AcademicYear/Grade/Course/Teaching Group，課程保持 CONTENT_UNLINKED；有原子 Reserve/Finalize 和 Operation Log API。 |
| [4](../stages/STAGE_04.md) | I | R04 | S2, S3 | Course–Content Linking & Core Recovery — 首次 I-only API 整合：安全接管已存在 Shell、新 Course Provisioning，B durable Op Log + A idempotent journal，可對帳及失敗恢復。 |
| [5](../stages/STAGE_05.md) | U | R05 | S4 | Sunrise Course & Content Admin Portal — 統一 Sunrise 初版 UI：Course List/Content Catalog、Upload/Search/Link Status，真正登入及安全 Session。 |
| [6](../stages/STAGE_06.md) | B | R06 | S3 | Question/Answer/Rubric Schema Studio — B 可建立、編輯、版本化 Blueprint/Question Schema/答案格式/Rubric，為四科與生成共用，並有 Draft Preview。 |
| [7](../stages/STAGE_07.md) | B | R07 | S3 | AI Provider Key & Capability Settings — Admin 輸入 Gemini Key、服務端驗證/保密保存、選 Model、實際 Test Request；顯示精準 READY/ERROR。 |
| [8](../stages/STAGE_08.md) | B | R08 | S6, S7 | Durable Generation Queue & Draft Review — B-only Queue→Prompt/Model→Question Schema+Domain validator→Draft→Human Approve，沒有 A Notebook 也可使用。 |
| [9](../stages/STAGE_09.md) | I | R09 | S4, S8 | Version-pinned Notebook Evidence Bridge — I 可選從 A 限定 Course/已發布版本檢索教材，建立簽名、可撤銷且有時效的 Evidence Bundle，B 接受前及使用前驗證。 |
| [10](../stages/STAGE_10.md) | U | R10 | S5, S9 | Sunrise Generation & Evidence Workspace — Sunrise UI 可以提交 B Generation Job，開關 I Evidence，見來源、AI 失敗及人工批准；不要求 B/I 調整程式。 |
| [11](../stages/STAGE_11.md) | B | R11 | S6, S8 | Mathematics Paper Builder & PDF — 數學卷 Blueprint/題目/幾何或圖表/答案驗證/版面 PDF，人工最後批准。 |
| [12](../stages/STAGE_12.md) | B | R12 | S11 | Chinese Language Paper Adapter — 中文科題型、閱讀理解/作文 Rubric、繁體中文 PDF 及人工覆核，獨立可試用。 |
| [13](../stages/STAGE_13.md) | B | R13 | S11 | English Language Paper Adapter — 英文 Grammar/Reading/Writing、Accepted Answers、專屬測試集、PDF 與人手覆核。 |
| [14](../stages/STAGE_14.md) | B | R14 | S11 | General Studies Paper Adapter — 常識科 Topic、正確性、教材／事實有效日期、解釋題人工核對、專屬 PDF。 |
| [15](../stages/STAGE_15.md) | B | R15 | S3 | Synthetic Student Roster — B 模擬學生、Enrollment 與班級名冊，完全不引入真實學生資料。 |
| [16](../stages/STAGE_16.md) | B | R16 | S6, S15 | Assessment & Score Drafts — B 使用既有 Question/Rubric Contract 建 Assessment、模擬分數 Draft、驗證總分與進度。 |
| [17](../stages/STAGE_17.md) | B | R17 | S16 | Append-only Grade Events & Corrections — 分數提交後舊事件不可修改；System Admin/唯一 Admin 只能追加帶原因／Actor／Revision 的更正。 |
| [18](../stages/STAGE_18.md) | B | R18 | S11, S17 | Submissions & Manual Marking — 模擬答卷提交/人工逐題評分/Review，完成後寫 Grade Event。 |
| [19](../stages/STAGE_19.md) | B | R19 | S18, S8 | AI-assisted Marking Benchmark & Review — AI 批改只作建議；人工 Gold Standard Benchmark 涵蓋 Extraction/Alignment/Partial Credit/誤差；最終人工確認。 |
| [20](../stages/STAGE_20.md) | B | R20 | S17 | Deterministic Analytics & Weakness Keep-two — Grade Events→Analytics Snapshot→候選弱點→Keep 最多兩份 Active Memory，舊 Grade 不刪。 |
| [21](../stages/STAGE_21.md) | U | R21 | S10, S17, S18, S19, S20 | Sunrise Assessment/Analytics Workspace — Sunrise U 加入合成學生、成績歷史、批改及 Weakness 操作入口；前端版本獨立試用。 |
| [22](../stages/STAGE_22.md) | B | R22 | S3, S17, S18, S20 | Staff IAM, Grants & B Authorization — B 建教師/Content Admin/System Admin 身份、B Course/班級 Grants、撤銷與 Audit；不開放 A 教材。 |
| [23](../stages/STAGE_23.md) | I | R23 | S4, S22 | Teacher Read-only Course Content — I 查 B Course Grant，以 A 只讀 API 搜尋/下載已授權教材；Revocation 即時拒絕。 |
| [24](../stages/STAGE_24.md) | U | R24 | S5, S21, S23 | Sunrise Teacher Portal UI — 新增 Teacher 與 Admin 分開的 Sunrise UI 導覽、資料來源及只讀教材頁，維持後端不變。 |
| [25](../stages/STAGE_25.md) | B | R25 | S22, S23, S24 | Approved Real Student Data Gate — 經校方和供應商政策批准後，B 才可匯入真實學生/成績及 Evidence；無批准維持 Synthetic。 |
| [26](../stages/STAGE_26.md) | A | R26 | S2 | Content Retention & Annual Archive Tools — A 後期教材年度封存、舊版保留、原檔校驗，S1 已先有基本 retention policy。 |
| [27](../stages/STAGE_27.md) | B | R27 | S17, S18, S20, S25 | Academic Year Closing & Grade Retention — B 獨立學年結算、成績事件保存/留存政策及稽核報告。 |
| [28](../stages/STAGE_28.md) | I | R28 | S4, S26, S27 | Cross-service Health/Restore Dashboard — I 顯示 A/B API 對帳和 Restore 狀態／告警；S4 已有最低必要 Core Recovery，本期只加管理工具。 |

## 點樣用 Roadmap 做 Go／No-Go

[Stage 總表](STAGE_BOUNDARY_MATRIX.md) 的「**本期可試用目標／必過 Gate／撞舊功能／後期影響**」與各 `STAGE_XX.md` 的控制卡一同構成本版 Release 審查依據。下面所列排序是規劃性依賴與優先次序，不能因某技術參考寫得詳細就當已實作。每個 Stage 的最小可用成果、實際測試及保留前版功能同等重要。

## Critical ordering decisions

1. S1 A Vault hardens Open Notebook raw routes and S2 A publishes canonical API; S3 B publishes independent Course Registry/atomic operation API. **S4** Integration only after both pass contract freeze, and S5 U makes Sunrise Content Portal available. No synthetic grades needed before S4.
2. S6 B Question/Answer/Rubric/Diagram/PDF Contract precedes S7 AI Provider Settings and S8 B Queue Generation. S9 I Evidence is optional and version-pinned; S10 U adds the Generation UI only after S9. B can generate WITHOUT A evidence and S8 release remains independently usable.
3. S11–14 maths/chinese/english/general-studies each separate B Stage **before** multiuser and real students, with subject-specific test set. S15+ synthetic roster and graded assessments/marking/analytics remain B-only; UI expansion at S21.
4. S22 B IAM uses early reserved actor/scope fields. S23 I permits teacher A read-only only after B Grant API. S24 U Teacher Portal. S25 B school-approved real PII; S26 A retention UI, S27 B year-end, S28 I Dashboard (core recovery already S4).
5. If a later I/U feature requires an unimplemented owner API, the correct response is **insert a preceding A-only/B-only Stage** and renumber planned Releases with ADR approval. Do not break one-owner isolation by hidden dual deployment. `Release dependency` is not the same as `technical dependency`.

[S4 state machine](../architecture/PROVISIONING_STATE_MACHINE.md) · [API Inventory](../architecture/API_INVENTORY.json) · [Release Policy](../delivery/RELEASE_POLICY.md)


## v0.7.4 independent gap gate

Before considering each Owner Stage done, review [19-row contract gap register](../quality/CONTRACT_GAP_REMEDIATION.md) and confirm its API/identity/data-state prerequisites; the candidate interfaces are non-binding until real Provider/Consumer UAT.


**v0.7.5 analysis:** stage numbers and the one-owner release order are unchanged. Corrected technical prerequisites for S21/S22/S24/S27 to include actual B marking/UI/retention consumers. A already has ON content ingestion/search/credentials/worker; do not rebuild these. Read [Open Notebook Reuse](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md) and [Stage Flow Engineering Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md).
