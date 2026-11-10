# Stage 目標與驗收決策政策 — v0.7.3

## 三層權威：先定功能、再定合約、最後按證據決定細節

**第一層：產品必守／不可打折（MUST）**：A/B 物理資料分離、I 只經雙方已發布的授權 API、每 Stage 一個 Runtime Owner、Notebook 只能經受控課程流程建立、教師教材唯讀、正式 Grade 不直接 UPDATE、真實學生 S25 Approval Gate。這些會影響資料正確／私隱／未來遷移，實作不能自行變更。

**第二層：本 Stage 可用成果與驗收（RELEASE GATE）**：每個 Stage 的完整用戶流程、必須有／不能有的功能、隔離、故障、恢復、回歸、Owner 批准，寫在 `STAGE_XX.md` 的「Stage 目標、驗收與跨 Stage 邊界」及原有逐項 AT。Release Gate 屬交付條件，不應降低以追求進度；如果本 Stage 過大，只能經 ADR/Owner 拆開 Stage。

**第三層：尚未完成技術驗證的實作參考（REFERENCE/TBD）**：OpenAPI DTO 細欄位、具體 Endpoint 名稱、授權 Token TTL、Queue／Worker 選型、Supabase Schema 分組、Gateway 包裝方式、Gemini Model、Prompt、PDF Renderer、監控閾值等。文件可以記錄候選方案方便接手，不可宣稱已 Freeze／正式決定。若相關參考是安全 Gate 的唯一可行方案，該方案仍需 Runtime PoC／負面測試才可成正式技術決策。

## 每個 Stage 的七個必填項

1. **目標**：一個可演示的業務成果，而不是「完成技術設定」。
2. **驗收**：最少三條有實際可觀察結果的 Go/No-Go，逐項 AT 仍全部適用。
3. **特別注意**：本 Stage 最可能令結果失效的技術／資料／授權風險。
4. **不能撞以前**：前 Stage 已有的資料、Contract、流程或權限不得退步；負面回歸須有證據。
5. **影響以後**：哪些 Stage 依賴其 API／ID／Version／事件，哪些新功能明確不可提早做。
6. **參考與未決**：列出尚未獲真實測試／Owner 批准的技術細節，不預先假定必然成功。
7. **停工條件**：跨 Owner、資料遺失、缺失合約或核心驗收未過，要停止並寫 Blocker。

## 實務工作順序與避免影響後期的檢查

開始 Issue 前：讀本期及所有直接依賴 Stage 的控制卡；列出 Schema／Endpoint／資料 Owner 及前版 Release SHA，核實是否真的存在。實作中：只修改 Owner 自己的服務；I/U 如需要另一 Backend 新 API，開獨立 A/B Stage/Issue（需要改 Release 順序時先做 ADR）。完成時：用兩條不同驗證路徑檢查成果，如實際 API/UI 測試 + 資料重建／Restore／負面案例；交付真 UAT 紀錄與 Owner 批准。

**「暫時不決定」不等於「暫時不用驗證」。** 與當期成果直接相關的安全、來源隔離、成績不可覆寫或資料可恢復，不能移作後期參考；只能把具體技術實作方式留待該期選定。

[29 Stage 總表](../product/STAGE_BOUNDARY_MATRIX.md) · [Release Policy](RELEASE_POLICY.md) · [Contract Checklist](../architecture/CONTRACT_FREEZE_CHECKLIST.md)


## v0.7.4 decision versus reference

**Must specify before implementation:** Course+TeachingGroup cardinality; school/source ownership; repeatable Evidence validation same-job/other-job rules; grade canonical hash and 409 on mismatch; B staff business API grants; Weakness state lifecycle. **May remain reference until Stage:** concrete path naming/DTO serialization, Gemini model/embedding and A-side BYOK optional approval, queue/provider, exact token lifetime, SQL indexes and PDF engine. S0 is documents only; S1 indexed search required, optional A Gemini requires separate consent/key/approval; B S7 Gemini Key never retroactively supplies A.


**v0.7.5 REUSE-FIRST Rule:** For A, decide REUSE/WRAP/BUILD with upstream source evidence before coding. Native ON ingestion/embedding/search/credentials/UI components are reusable but native password and notebook scopes do not meet School IAM. B school paper/grade/queue are not present in ON. B-only release needs a usable B-local trial client; no automatic U update. See `docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md`.
