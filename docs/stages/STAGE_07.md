# Stage 07 [B] — AI Provider Key & Capability Settings

**Release:** `R07` | **Exactly one owner:** `B` | **Technical prerequisites:** S3 | **Status:** PLANNED / NOT IMPLEMENTED.

## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）

**本章係 Stage 規劃級別的正式目標／驗收邊界；實作細節未經 Provider/Consumer 真實測試前均屬暫定。**

### 1. 目標：這一期完成甚麼？

在 B 建立安全的 Gemini／模型供應商 BYOK 與可用狀態管理，供未來生成使用。

**完成後可親自試用：**Admin 輸入 Key→服務端驗證→選 Model→發起測試請求→清楚看到 READY/ERROR／撤銷狀態。

### 2. 驗收：甚麼情況才可以標記完成？

- Key 可加／換／撤銷，保密儲存且不會出現在前端、本地儲存、日誌或 API 回應。
- 真正 Provider Test 能區分 Key 無效、模型不可用、額度／網絡／權限錯誤，而不是只有格式驗證。
- 不影響 A 模型憑證；B 只讀自己的 Key／Provider 設定，失效後 S8 Job 必須可拒絕。
**本期原有驗收設計：**`S7-AT01–S7-AT07`（7 項）。以上是 Release Gate 摘要；以下原有逐項 AT 仍需全部實測，不能只選幾項。

### 3. 需要特別留意的風險

- Gemini Key「通過」不代表所有模型能力／Quota 都可用；應有可檢驗的能力狀態。
- 避免將 A Embedding Key 和 B Generation Key 當成共享 secret。
### 4. 不可以與之前已完成的功能撞／互相破壞

- B Course 已 S3 建立，但本期不做 S8 Queue、不碰 A 的 AI 搜尋。
- 不能把憑證寫入 Git、URL、job payload 或 UI。
### 5. 對之後 Stage 的影響／現在應預留但不提早做

- S8 Queue 在送出任務時檢查 Provider 狀態與成本限制；S19 Marking 會重用能力設定。
- 供應商變更、可用模型名稱與收費不確定，必須保持可替換。
**明確技術前置：**S3。**直接依賴本期的後續 Stage：**S8。

### 6. 暫定參考，暫時不作技術承諾

- Gemini 只是第一候選 Provider；SDK/Model ID/Key 加密方案、預算上限在本期實測決定。
原有文件以下的 API Path、Schema、工具／供應商、狀態機及範例，皆是工程設計參考；其不可改的是**資料 Owner、可用成果、必要授權與隔離、驗收結果**。實作若需改細節，先記錄決策與相容性影響，使用本 Owner 的 PR/ADR；若會改到另一 Owner，必須拆開 Stage，不能在同一 Stage 直接修改兩邊。

### 7. 這一期的停工／退回判準

- 以上任何核心驗收失敗、出現原始資料遺失／錯用 Scope／未批准跨 Owner 變更：**BLOCKED**，不能用「留待後面 Stage」繞過。
- 缺真實 Staging／回歸／Owner 批准（S0 為文件批准）或無法證明現有功能不受影響：**NOT DONE**。
- 尚未確定、但不影響本 Stage 安全與可試用結果的細節：明列 `TBD/REFERENCE`，留 Owner 在實作前按證據選型，不因未知細節而預先凍結全部架構。

## User-visible product deliverable

Admin 輸入 Gemini Key、服務端驗證/保密保存、選 Model、實際 Test Request；顯示精準 READY/ERROR。

## Complete user flow

Admin→AI Provider Settings→Input masked key→Store Server-side→Test Authentication/Model/Quota/Call→Revoke/Rotate。

## Data / Source of Truth

B credential_reference in server-side Secret Store, provider_config, capability_test_log with redaction; A own key independent。

## Owner API 合約（候選規格，需 Owner 真實 Provider／Consumer UAT 後才 Freeze）

- `POST /core/v1/admin/ai-providers` (`saveAiProvider`; auth=admin) — Server-side masked secret reference and provider config
- `POST /core/v1/admin/ai-providers/revoke` (`revokeAiProvider`; auth=admin) — Revoke provider credential and halt use
- `POST /core/v1/admin/ai-providers/test` (`testAiProvider`; auth=admin) — Distinguish auth/model/quota/live inference; no permanent fake ready


## Not in this Stage

不在前端 LocalStorage 保存完整 Key，不部署 A 的模型憑證。

## Real deployment and operations（原規劃參考與實測要求）

This is a B-only runtime deployment with its own health, stable data, failure/retry, backup and rollback plan. Other owners remain at pinned versions. Run negative authorization and data isolation tests; independent owner Restore and regression are required for release.

**Independent B trial:** This Stage provides a protected B local Admin interface and persistent test workflow. It must remain testable even without new U work.

## Acceptance Test Specification (NOT EXECUTED)

| AT ID | Given / 前置條件 | When / 測試行為 | Then / 可觀察結果 | Evidence |
|---|---|---|---|---|
| S7-AT01 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Key lifecycle | Gemini Key 只在 Admin 一次輸入；後續 Task 只用 Secret Ref/Server Worker；Rotate/Revoke 有測試 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT02 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 五層 READY | 格式/認證/模型存取/配額/真推理成功分開顯示；一次 AUTH PASS 不能永久 READY | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT03 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 錯誤隔離 | 錯 Key/超額/模型不可用時 UI 有可讀 ERROR；log 與回應不洩露 Key | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT04 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | A 獨立 | B Provider Secret 不直接交 A；A Vault 如需 embedding 有自己獨立受控 Provider 設定 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT05 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 範圍回歸 | 完整驗證本 Stage 用戶工作流，包括持久化/權限與負面路徑 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT06 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | Owner 隔離 | 其餘 A/B/I/U Runtime Image/Schema/Digest 無變更 | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |
| S7-AT07 | 上一階段 Release 依賴已通過；相應 Staging／合成 Fixture 與受控用戶可用 | 單 Owner Release | 只有所屬服務 Code/Schema/Config 改變，其餘 Runtime 版本維持 Manifest 固定；運行 Smoke/Regress/Owner Restore | Actual UI/HTTP/DB or negative test + commit SHA + UTC + owner-local restore/regression as relevant |

## v0.7.5 — Reuse-first 工程決策（參照原始碼；須於本 Stage 實測）

- **Open Notebook／已發布基礎可沿用：**ON 已有 Gemini 等 Provider Key/Models Connection Test/Encryption Code 供設計參考。
- **不應重造的部分：**第二套 A Gemini Key 管理頁或把 Open Notebook Key 直接交 B。
- **Sunrise 仍須自己交付的能力：**B 獨立 Generation Provider Secret 設定、Test、Revocation、Model Readiness、成本/配額狀態。
- **當期風險／不可與前期撞：**A Key 與 B Key 係兩個憑證域；同一 Admin 輸入未代表兩服務可共享；不得直接查 SurrealDB Key。
- **後續 consumer／依賴影響：**S8 B generation uses B provider; S19 marking uses provider policy。
- **真實試用入口：**B-local Provider Settings + 試用結果。正式 R07 完成須有實際持久化功能及負面測試；原始碼已存在不等於本服務已交付。

詳細原始碼核對及不可直接重用的原因：[Open Notebook Reuse Audit](../architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md)；依賴反例：[Stage Logic Audit](../delivery/STAGE_FLOW_ENGINEERING_AUDIT.md)。來源選型是暫定 Reference，技術關鍵之安全／權限／資料要求仍是 Release Gate。

**候選現成依賴（須本期驗證）：**可研究直接使用 Esperanto SDK 統一呼叫 Gemini 等模型；B Provider Secrets 必須由 B 獨立託管，不能讀 A Credential DB。

## Release / Rollback Gate

All current ATs PASS on real protected Staging with the named Owner only changed, no Critical/High defects, API contract compatibility and Schema rollback/forward-fix verified, preceding user flows regress, signed Release Manifest, Owner UAT and actual Restore evidence. Rollback cannot delete A Notebook or override B grade events.

[Roadmap](../product/ROADMAP.md) · [Boundary Rules](../architecture/BOUNDARY_RULES.md) · [Canonical API](../architecture/API_INVENTORY.json) · [Acceptance Matrix](../quality/ACCEPTANCE_MATRIX.md)
