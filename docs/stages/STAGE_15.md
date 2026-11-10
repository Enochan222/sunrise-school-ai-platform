# Stage 15 [B] — Synthetic Student Roster

**Release:** `R15` | **Exactly one owner:** `B` | **Technical prerequisites:** S3 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

B 開始管理完全合成的 Student/Enrollment，供後續成績測試。

**完成後可親自試用：**Admin 匯入或建立虛構學生，查名冊及所屬 Course／Class，重試匯入不重複。

### 2. 驗收：甚麼情況才可以標記完成？

- 模擬名冊新增、列出、Enrollment 及匯入重試都可運作。
- 資料明確標 SYNTHETIC，拒絕當期真實學生個資輸入。
- 學生／Course FK 有效，B-only Restore 後名冊一致。
**本期原有驗收設計：**`S15-AT01–S15-AT10`（10 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- 姓名像真不等於匿名資料；必須使用真正合成的身份值。
- Class/TeachingGroup 由 S3 定義，不要於學生 Stage 建第二套課程結構。
### 4. 不可以與之前已完成的功能撞／互相破壞

- 不得把學生放 A 或令 S4 Course Binding 變為 Student Binding。
- S5/S10 不得提前顯示已有真實學生／分數。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S16 Assessment、S17 Grade、S18 Submission 將引用 Student ID；建立穩定鍵與資料型別。
- S25 真實學生 Import 必須另有批准和資料類型隔離，不可簡單把 Synthetic 改旗標。
**明確技術前置：**S3。**直接依賴本期的後續 Stage：**S16。

### 6. 暫定參考，暫時不作技術承諾

- Roster 欄位與校本匯入格式只作參考，正式 PII 接入規則留 S25。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

B 模擬學生、Enrollment 與班級名冊，完全不引入真實學生資料。

## Complete user flow

Admin→Create Synthetic Roster→Assign Course/Teaching Group→List/Edit/Import。

## Data / Source of Truth

B students.synthetic_profiles/enrollments with school/actor/scope。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/enrollments` (`assignSyntheticStudent`; auth=admin) — B Course/Class enrollment
- `GET /core/v1/students` (`listSyntheticStudents`; auth=admin_or_staff) — List B synthetic students only; no real PII until S25
- `POST /core/v1/students` (`createSyntheticStudent`; auth=admin) — Synthetic-only student roster and groups


## Not in this Stage

無真實學生／不改 A。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S15-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 名冊 CRUD | 可建立、匯入、查找合成學生及選課 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 外鍵 | Enrollment 必須指向有效 B Student 與 Course | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 重複匯入 | 同 Batch 重試不重複建立學生 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 純合成 | 拒絕未核准真實學生 PII 載入；有測試資料標識 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 還原 | B-only Restore 後 Roster/Enrollment 全部對帳 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 隔離 | A 與 I 無更動、無新的 A Credentials | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 只許合成 | 真實學校名單/PII 即使從 CSV 上載也會拒絕 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT08 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S15-AT09 | 相應 Stage 真實 Staging、授權用戶及測試資料可用 | 合成名冊檢視，包含偽造範圍／失敗路徑 | GET B Student list 僅列合成學生、限制 Scope、分頁與排序；不能返回未批准真實學生資料 | HTTP/schema/provider test + Commit SHA + Owner UAT |
| S15-AT10 | 該 Stage 的 Provider/Consumer Staging 及受控測試資料準備 | 分班 Enrollment | S15 Enrollment 必須含 teaching_group_id，且 Group/Student/Course/School 一致；錯班或跨校拒絕 | 真實服務／權限／DB 或隔離樣本 + Git SHA + Owner UAT |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**B S3 TeachingGroup/Course IDs；原生 Supabase DB/RLS 可作工具。
- **不應重造的部分：**將學生個資寫入 A/Notebook；過早上線實名學生。
- **Sunrise 仍須自己交付的能力：**B synthetic Student/Enrollment with exact TeachingGroup, import idempotency and full school scope。
- **當期風險／不可與前期撞：**Demo data 必須確認合成、班級不等 Course；重新匯入不可重複。
- **後續 consumer／依賴影響：**S16 Assessment S17 Grades S18 Submission 全部引用穩定合成 Student ID。
- **真實試用入口：**B 本地受保護的虛構學生名冊與 TeachingGroup 選課操作頁。正式 R15 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
