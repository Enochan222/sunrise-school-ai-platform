# Stage 25 [B] — Approved Real Student Data Gate

**Release:** `R25` | **Exactly one owner:** `B` | **Technical prerequisites:** S22, S23, S24 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

只有在校方及供應商／私隱要求完成後，B 才允許正式學生名冊、真實成績與 Evidence。

**完成後可親自試用：**在校方批准的隔離環境，以受授權用戶完成實名資料匯入、課程歸屬、成績及查閱；未批准則嚴格拒絕。

### 2. 驗收：甚麼情況才可以標記完成？

- 沒有具體校方資料／供應商／AI 處理批准時，所有 Real Import API 必須 Fail Closed。
- 校方／班級／科目權限與資料留存政策可實測；真實數據絕不入 A。
- 保留 Synthetic 與 Real 資料分離及事件血緣，備份／還原與撤權演練通過。
**本期原有驗收設計：**`S25-AT01–S25-AT08`（8 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 即使系統功能完成，法律／學校政策未批准也不能宣布正式上線使用真實學生資料。
- 模型 Provider 會否接觸學生資料需要獨立明確批准，不可依教材 Gemini 設定推定。
### 4. 不可以與之前已完成的功能撞／互相破壞

- S22–S24 教師權限與 UI 已須實際通過；不能再用單 Admin 共享帳號測真 PII。
- 不能將先前合成 Student 資料直接「改為真實」以繞過資料審核。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S27 年度結算／保留將以真實資料政策執行；不影響 A 教材保留。
- 更廣泛報表、AI 分析必須遵守已批准用途與 Access Scope。
**明確技術前置：**S22, S23, S24。**直接依賴本期的後續 Stage：**S27。

### 6. 暫定參考，暫時不作技術承諾

- 校方資料治理、法律依據、保存年期、Cloud Region 及供應商審批不是技術文件可先確定的內容。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

經校方和供應商政策批准後，B 才可匯入真實學生/成績及 Evidence；無批准維持 Synthetic。

## Complete user flow

School Signoff→Import Real Student→Course/Teacher Scope→Grade/Evidence→Audit。

## Data / Source of Truth

B real_student_profiles/evidence/retention_controls, no A storage。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/real-students/import` (`importRealStudents`; auth=admin) — Hard school policy/privacy approval gate


## Not in this Stage

不得未批准即加入 PII；不改 A/I。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S25-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 正式批准 | 沒有 Data Privacy/AI Provider Approval 時 Import 強制拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 隔離 | 真實學生的資料只在 B，不寫 A、AI context 有批准策略 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B 授權 | 跨班、跨學生、導出及 Analytics 權限測試 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 血緣 | Evidence 可追溯真實 Grade Event/Teacher Record | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 學年 | 真實資料有 Retention/Legal Hold 標記 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | B-only | A/I 不需 Schema/Code 改動即可使用本 Stage | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 正式 PII Gate | 未經校方 AI Provider/Privacy Data Terms 簽核絕不可匯入真實學生資料 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S25-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**S22 B staff grants, S24 U existing UI。
- **不應重造的部分：**不把 A 的來源 Notebook 當作真實學生及正式成績資料庫，亦不繞過校方隱私批准程序。
- **Sunrise 仍須自己交付的能力：**B real student/PII input behind school policy consent & provider terms, mandatory isolation/retention。
- **當期風險／不可與前期撞：**未經校方批准仍需 Fail Closed；由 synthetic 切 real 需完整授權／刪改稽核。
- **後續 consumer／依賴影響：**S27 B year closure/retention supports legal holds; A materials never affected。
- **真實試用入口：**B approved school environment, real-data UAT only after approval。正式 R25 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
