# Stage 0–28：目標、驗收、前後衝突與風險總表

**用途：** 給校長／Owner、工程師及接手 AI 作每期 Go／No-Go 審批。以各 [Stage 詳細控制卡](../stages/STAGE_00.md) 及原有逐項 AT 作準，這裡是可快速核對的總覽。

**承重原則：** A/B/I/U 每 Stage 只改一個 Owner；I 只經 A/B API 作正常業務操作；U 不直接讀寫兩庫。S0 不部署；S1+ 真正可試用才算完成。未實測的 API／Database／Provider／UI 技術細節屬建議，不能當已批准的解法。

| Stage／Owner | 本期可試用目標 | 必過 Gate（摘要） | 避免與前期衝突 | 對後期的影響／預留 |
|---|---|---|---|---|
| [00 P](../stages/STAGE_00.md) | Owner 可按文件回答誰負責每項功能、目前做到哪一版、下一個 Stage 可否開始；不要求部署產品。 | PRD、S0–S28 Roadmap、ADR-011 起、Owner／依賴矩陣互相一致且簽名批准。 | 舊 v0.5 的共用 SurrealDB/Core 方案不能同新 A/B 實體隔離並存為兩套權威。 | S1 只限 A；S2/S3 各自發布 API 後 S4 才可連接。 |
| [01 A](../stages/STAGE_01.md) | 唯一 Admin 建立課程教材容器，系統生成專用 Notebook；放入校方教材後能重新登入、查詢、下載及封存。 | 完整 Course Shell→Notebook→Upload→Search／Download 可在受保護環境運作，資料重啟後存在。 | S0 只是文件審批，S1 不可說雙庫已完成。 | S2 要沿用 Shell／Notebook／Source ID 與版本關係，不能改成依標題配對。 |
| [02 A](../stages/STAGE_02.md) | Admin 修改教材分類與版本，舊版本仍可追查；以受控 API 查單一 Content Shell 已發布的教材及來源。 | Textbook／Note／Past Paper 類型、Topic、版本和發布／封存狀態能儲存及查詢。 | 保留 S1 Notebook 唯一、原檔 Hash、Archive 不 Delete 及 A-only Restore。 | S4 的 Adopt/Create、S5 材料列表／上載／下載、S9 Evidence、S23 Teacher Read 都依賴受控 A 契約。 |
| [03 B](../stages/STAGE_03.md) | Admin 只用 B 就能建立、檢視、封存正式課程；未接 A 的課程清楚顯示 CONTENT_UNLINKED。 | B PostgreSQL／Supabase 與 A 使用不同帳密、網絡、備份；B 單獨完成課程 CRUD／Restore。 | B Course 是正式學校業務物件，不能把 S1 A 的 Content Shell 當成同一資料表。 | S4 直接依賴 B Reserve／Finalize／Read-back 與 Operation log，S22 未來 IAM 要有 Actor/Scope 預留。 |
| [04 I](../stages/STAGE_04.md) | Admin 由 I 明確選 B Course 與 A Shell：預覽、接管、建立／查驗 Notebook；故障重試後連結仍唯一且可查。 | ADOPT_EXISTING 不創建第二本 Notebook；CREATE_NEW 先 B Reserve、再 A Create、最後 B Finalize/Read-back。 | 不得在 I 內重寫 S2 A / S3 B 合約；缺 API 必須回到該 Owner 另出版本。 | S5 U、S9 I Evidence、S23 教師讀取均依賴 Course→Shell 的完整可信 Binding。 |
| [05 U](../stages/STAGE_05.md) | Admin 從單一 Sunrise 入口進入 Course、教材列表、上載、搜尋、下載及 Link Status，錯誤有可理解的提示。 | Course/Content UI 真正呼叫 S4/B/A 受控 API，資料刷新後仍可見，無前端直接 DB 連線。 | S4 已完成 API Link/代理，U 不可為了畫面方便直接讀 SurrealDB／Postgres。 | S10 才加入 Generation Evidence UI；S21 才加入成績／分析；S24 才加入教師版面。 |
| [06 B](../stages/STAGE_06.md) | Admin 建 Blueprint、題型、答案約束和評分規則草稿，保存後可預覽並檢查有效性。 | 各類 Question/Answer/Rubric 可建立、保存版本、回讀及拒絕非法配置。 | 沿用 S3 正式 B Course ID；不得借 A Note 保存 Blueprint 或題目。 | S8 Queue 會引用版本，S11–S14 各科擴充要可加欄位而不破壞已批准題型。 |
| [07 B](../stages/STAGE_07.md) | Admin 輸入 Key→服務端驗證→選 Model→發起測試請求→清楚看到 READY/ERROR／撤銷狀態。 | Key 可加／換／撤銷，保密儲存且不會出現在前端、本地儲存、日誌或 API 回應。 | B Course 已 S3 建立，但本期不做 S8 Queue、不碰 A 的 AI 搜尋。 | S8 Queue 在送出任務時檢查 Provider 狀態與成本限制；S19 Marking 會重用能力設定。 |
| [08 B](../stages/STAGE_08.md) | Admin 在 B 測試入口輸入 Course/Blueprint，建立生成任務、查看 Queue/Retry/失敗、批准草稿，產物留 B。 | 有真實持久化 Queue、任務狀態與重試；重送不產生兩份正式已批准 Artifact。 | 依賴 S6 Schema、S7 Provider Key；不得在此期改 I 或偷偷使用 A RAG。 | S9 的可選 Evidence Bundle 要接入已定義的受限入口；若 B 缺失要在 B Owner 版本補齊，不能 S9 偷改。 |
| [09 I](../stages/STAGE_09.md) | Admin 在生成流程選「使用本課程教材」，可看到引用來源，過期或撤銷時任務安全失敗而非讀全庫。 | 關閉 Evidence 時不需 A；開啟時只讀該 Course 的已發布來源，無法偽造 Notebook/Source ID。 | 只能使用 S2 A 及 S8 B 已發布的 API，不可在 I Stage 修改兩邊 Credential／DB。 | S10 必須顯示引用／失效與可選狀態，S11–S14 可使用 Evidence 但仍要逐科 Validation。 |
| [10 U](../stages/STAGE_10.md) | Admin 在 Sunrise 選 Blueprint、生成、勾選或取消教材 Evidence、查看 Queue 狀態、引用和人工批准。 | U 按 S8/S9 API 顯示 Job／Draft／Evidence 狀態，不使用假進度。 | S5 Portal、S8 Queue、S9 Evidence 已可用，U 不可重寫其邏輯。 | S11–S14 紙本 PDF 及四科細節會增加 UI，但要按獨立 U Stage/Owner 安排，不能在 B Stage 偷改 U。 |
| [11 B](../stages/STAGE_11.md) | Admin 用既有 Blueprint 產生一份數學試卷並匯出可閱覽 PDF／答案卷。 | 數學題型與 Rubric/分數總和一致，客觀題答案可由確定性方法驗證。 | 只能使用 B Question Schema/S8 Queue，不能修改 A Notebook 或 I Evidence 模組。 | S12–S14 會共用基礎卷引擎但各科獨立驗收；S18 Submission 需要有穩定試卷／題目 ID。 |
| [12 B](../stages/STAGE_12.md) | Admin 可獨立設定中文科 Blueprint、生成試卷、預覽並批准 PDF。 | 中文閱讀／語文／作文題型可生成、分值及 Rubric 版本可查。 | 不可修改 S11 數學既有驗證結果或 S6 Rubric 原始版本。 | S18／S19 人工及 AI 建議改卷需要中文主觀題評分模型；本期先留下題目與 Rubric 引用。 |
| [13 B](../stages/STAGE_13.md) | Admin 能從英文 Blueprint 建卷、預覽 PDF 與答案／Rubric，人工審核 Writing。 | 英文三類題型有可用範本與輸出 Schema；客觀題答案及分數可核。 | 不覆蓋 S12 中文的專用配置或 S11 數學答案計算規則。 | S19 AI Marking 對 Writing 需有分級人手 Gold Set；S18 會引用題目 ID。 |
| [14 B](../stages/STAGE_14.md) | Admin 建常識科 Topic 試卷，看到待核的事實與來源標記，審核後生成 PDF。 | 常識科題型、Rubric、版本及分值可用並生成 PDF。 | 不能從 A Notebook 原文直接推斷已過事實查核；S9 Evidence 只證明來源，不等於真偽。 | S19 AI 改卷要有常識科特定 Benchmark，S20 Analytics 保留 Topic／Learning Objective。 |
| [15 B](../stages/STAGE_15.md) | Admin 匯入或建立虛構學生，查名冊及所屬 Course／Class，重試匯入不重複。 | 模擬名冊新增、列出、Enrollment 及匯入重試都可運作。 | 不得把學生放 A 或令 S4 Course Binding 變為 Student Binding。 | S16 Assessment、S17 Grade、S18 Submission 將引用 Student ID；建立穩定鍵與資料型別。 |
| [16 B](../stages/STAGE_16.md) | Admin 為虛構學生建立 Assessment、逐題草稿分數、檢查後保存，刷新仍可改。 | Assessment 與 Question/Rubric 版本可追蹤，Draft 可保存／查詢。 | 引用 S6 Schema／S15 合成名冊，不能重新定義學科題目或 Course ID。 | S17 需要不可重覆的 Submit／Correction 邊界、同一 Assessment/Student/Item Version。 |
| [17 B](../stages/STAGE_17.md) | Admin 提交一次模擬分數後，舊紀錄鎖定；用更正原因建立第二筆事件，歷史與最新成績都可查。 | 同請求重試不能重覆提交；正常 DB/API UPDATE/DELETE 既有 Grade Event 必須拒絕。 | S16 Draft 仍可編輯，但提交後不能以 Draft UI 覆蓋 Ledger。 | S18 Manual Marking、S19 AI Suggest 只能經 Ledger API 發分；S20 Weakness 必須隨更正失效。 |
| [18 B](../stages/STAGE_18.md) | Admin 上載或建立模擬答卷，按 Rubric 人工評分、覆核，再正式提交。 | 答卷與 Student／Assessment／Question Version 對應，重送不會覆蓋原答卷。 | 不能繞過 S17 直接 INSERT Current Grade；亦不覆寫 S16 Draft 歷史。 | S19 AI Marking 需保留人工正確答案與例外狀況作 Gold Set。 |
| [19 B](../stages/STAGE_19.md) | Admin 看到每題 AI Suggest／理由／置信與人工差異，能更正／拒絕並批准最終分數。 | AI 建議有 Rubric/Prompt/Model/Question/Submission Version 血緣，無法直接發正式分數。 | S18 手動改卷正常路徑必須保留作 fallback；AI 不能覆寫已提交 Grade。 | S20 Analytics 只能使用人工確認後的有效 Grade Event，不能直接用 AI Suggest。 |
| [20 B](../stages/STAGE_20.md) | Admin 看到各 Topic 的有依據弱點，點 Keep 後下次出卷可選 0–2 個版本；更正成績後舊弱點自動失效。 | 指標可用確定性方法獨立重算，分子／分母與有效成績來源可追溯。 | 只能依賴 S17 確認 Grade，不用 S16 Draft 或 S19 尚未批准的 AI Suggest。 | S21 UI 會顯示弱項兩版，S27 年終結算要保留 Score/Audit 歷史與快照狀態。 |
| [21 U](../stages/STAGE_21.md) | Admin 由 Sunrise UI 查看模擬學生、提交／查成績歷史、查 AI／人工批改結果和 Keep／Discard 弱項。 | 頁面真正讀寫已發布 B API，顯示 Score Draft／正式分數／Correction History 的差異。 | S5 原有 Course／Content 及 S10 Generation UI 不得被新頁面破壞。 | S24 將加入教師可用版面與 B/I 授權；S25 才可能載入真實學生。 |
| [22 B](../stages/STAGE_22.md) | System Admin 發出邀請、分配 Course／Teaching Group Grant；Teacher 登入後只能使用所屬 B 功能。 | 登入／停用／Grant／撤銷實際生效；跨 Course B API read/export/write 一律被拒絕。 | S1–S21 單 Admin 模式既有業務操作不能因增加身份而無故失效。 | S23 必須驗證實際 B Grants／Revocation，S24 UI 再公開教師教材介面。 |
| [23 I](../stages/STAGE_23.md) | 授權教師只讀其班級課程的教材；取消 Grant 後即使保存舊連結亦無法搜尋／下載。 | StaffSession 必須先經 B Grant API 驗證，且查 A 每個 Source/Download 仍受 Scope 限制。 | 依賴 S22 B Grant 查核與 S4 Course Binding；不能用 AdminToken 代表 Teacher。 | S24 將呈現教師 UI，權限決策必須由 I/B 服務端作出。 |
| [24 U](../stages/STAGE_24.md) | Teacher 登入只見自己課程及唯讀教材；Admin 仍可做原本管理，撤權後介面同步消失。 | 教師頁的 Course/Materials 搜尋、下載及唯讀顯示可真實使用。 | S5/S10/S21 的 Admin 入口及操作仍可用。 | S25 可加入實名學生資料頁，但需校方批准及完整權限 Gate，不能提前開放。 |
| [25 B](../stages/STAGE_25.md) | 在校方批准的隔離環境，以受授權用戶完成實名資料匯入、課程歸屬、成績及查閱；未批准則嚴格拒絕。 | 沒有具體校方資料／供應商／AI 處理批准時，所有 Real Import API 必須 Fail Closed。 | S22–S24 教師權限與 UI 已須實際通過；不能再用單 Admin 共享帳號測真 PII。 | S27 年度結算／保留將以真實資料政策執行；不影響 A 教材保留。 |
| [26 A](../stages/STAGE_26.md) | Admin 選學年進行 A 教材 Archive、查保留規則、執行原檔 Hash／A-only Restore 核對。 | Archive 後 Notebook／Source/Version/Hash 仍可依政策查閱，普通功能無直接 Delete。 | S1 起已有最低安全與基本保留資訊，S26 只加治理 UI/進階程序，不能推遲早期備份。 | S28 I 對帳要知道 A 來源封存狀態而非把 Archive 當刪除。 |
| [27 B](../stages/STAGE_27.md) | System Admin 預覽未完成 Assessment，將學年按合法狀態關閉／封存，保留 Grade History 和稽核紀錄。 | 結算 Open→Closing→Closed→Archived 及失敗回退可測，不合法轉換拒絕。 | 不能改動 S26 A 教材封存狀態；B Academic Year Close 不會自動 Delete Notebook。 | S28 的跨服務檢查依賴 B 的學年狀態與對帳 API。 |
| [28 I](../stages/STAGE_28.md) | 管理員查看 A/B Healthy、Course Binding、Source Version、Backup/Restore 報告及異常告警，能清楚定位哪邊需處理。 | 以既有 API 偵測缺 B Binding、孤兒 A Notebook、Source Hash/版本差異、Restore 時點不一致。 | 不能把 S4 已必需的 Saga Recovery 推遲到 S28；不得修改 S26 A/S27 B 的治理資料模型。 | 作為後續運維平台的 API-only 基線，異常跨 Owner 修復仍應拆 A-only/B-only 版本。 |

## 使用方式

1. **開始前**核對本 Stage 的依賴、Owner、現行 Release Manifest，檢查上一版真正已通過的功能。
2. **實作時**只選屬於本 Owner 的一項可試用主流程；列出的技術細節只屬參考，未有測試證據不得視作已確認。
3. **驗收時**先檢查本期控制卡的必要 Gate，再執行下方原有全部 AT、負面案例、資料持久化與回退／恢復；有核心 Gate 失敗不得因 UI 方便或下一 Stage 計畫而延期修復。
4. **完成後**將未完成而不影響核心要求的非承重建議列入後續 Issue，附帶對將來 API／Schema／權限的相容性影響。

## 限制

這是規劃級別的責任矩陣，不代表已經在 GitHub 合併，也不是 Docker／SurrealDB／Postgres 實測報告。任何業務範圍改動均需更新 Stage Card、Registry、AT、PRD、Roadmap、ADR 與相關依賴並重新驗證。


## v0.7.4 first-stage-to-consumer crosscheck

**S0:** approve Course vs TeachingGroup, A school ownership, Gemini A-only optional, S4 Cutover.
**S3 → S4:** B Course+Group and A Shell school scope, B Reserve/Finalize, A Create/Manifest API; I consumes only frozen providers.
**S6 → S8:** B Blueprint, QuestionTemplate, Rubric versions with read/publish API and pinned `blueprint_version`.
**S8 → S9:** B Worker ServiceToken to I `link.evidence.validate`, same-Job multi-phase checks.
**S15 → S16/17:** Group enrollment exact school/course/student ownership.
**S17 → S18/20:** Grade idempotency canonical hash, immutable corrections, weakness invalidation.
**S20 → S21:** Candidate/Keep/Discard and Stale/Retired actual read API, no U backdoor.
**S22 → S23:** Staff actually authorized on B business endpoints, then I grants read-only Vault access.
**S26 + S27 → S28:** A/B owner-only health/backup read; I only dashboard via APIs.

## v0.7.5 — 真正技術依賴補漏（維持原 Release 編號）

| Stage | 原有 Dependencies | 修正後 Dependencies | 原因及 Gate |
|---|---|---|---|
| S21 U | S10/S17/S20 | **S10/S17/S18/S19/S20** | UI 聲稱顯示人工／AI 改卷結果，必須等相應 B API 已存在；不得在 U 偷改 B。 |
| S22 B | S3/S17 | **S3/S17/S18/S20** | Teacher B 權限需 cover 原有提交、評分、課程名冊及 Analytics 資源；B 內部一次授權正確而不借 AdminToken。 |
| S24 U | S5/S23 | **S5/S21/S23** | Teacher Portal 重用 S21 Assessment/Analytics UI 的已建組件／受控 API，不能再做一套不兼容的入口。 |
| S27 B | S17/S25 | **S17/S18/S20/S25** | 學年結算須檢查未完成手動評分及弱點保留／失效的政策，不能只管 Grade Ledger。 |

上面是實際資料消費與功能依賴，不等同所有技術上可獨立開發的工作都必須等待前一個 Release 才能開始編碼。規格仍須以 Stage Registry 為唯一權威，並以真實 Consumer Contract Test 作發佈 Gate。
