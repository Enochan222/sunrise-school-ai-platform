# v0.7.3 Stage Goals / Acceptance / Collision QA Review

**日期：2026-11-08。文件修訂：v0.7.3；產品 Release：無。所有 S1–S28 Runtime 驗收均 NOT RUN。**

## 修訂目的與內容

以原 v0.7.2 Engineering Reviewed ZIP 為來源，**保留 S0–S28、各 Owner、29 份 Stage Spec、80 個 API 候選 Operation、286 個舊 AT ID、既有 ADR／GitHub 遷移指令**。每個 Stage 新增具體「目標／可試用成果、必過 Gate、風險、不得撞以前、後續影響、技術細節待確認、Blocker」。

新增 `docs/quality/STAGE_CONTROL_MATRIX.json`（每期控制卡的機器可讀 Source of Truth）、`docs/product/STAGE_BOUNDARY_MATRIX.md`（29 期速覽）和 `docs/delivery/STAGE_DECISION_POLICY.md`（三層權威／何時可留待實作），並同步到 PRD、Roadmap、README、AGENTS、交接、Release Policy、Backlog、Work Prompts 及 CI。

**精確劃線：** 對安全／數據／授權／可用成果不可讓步；未經實際 Provider Test 的 OpenAPI DTO、Key 加密方式、模型、Queue、PDF Renderer、Hosting 配置等屬 `REFERENCE/TBD`。不能以「技術仍不確定」來免除本 Stage 的必過驗收。

## 已實際執行的文檔／模型 QA

| 檢查 | 結果 | 能證明甚麼／不能證明甚麼 |
|---|---|---|
| 29 Stage 控制卡獨立一致性 | **1,955 PASS / 0 FAIL** | Goal、Release Gates、Collision/Future Dependencies、原 286 個 AT ID 和詳細 Stage 文件對齊；未測 Runtime |
| Stage 控制卡 Mutation Test | **10/10 故意錯誤均被抓出** | 錯 Owner、漏 AT、漏風險、失去後續依賴、Stage ID 漏洞等能被發現 |
| 原有設計模型 | **40/40 PASS** | 只檢查純 Python 狀態模型，不代替真 DB/API |
| 原有 Schema Fixture | **6/6 PASS** | JSON Schema 正反樣本，不檢查簽章或部署 |
| Typed API Fixture | **22/22 PASS** | 規格樣本、權限／結果 Envelope，不等於 Provider Contract Freeze |
| OpenAPI 3.1 靜態型別／授權檢查 | **1,966 PASS / 0 FAIL** | 80 個候選 Operation 的 Path/Response/Auth 結構，自身不證明 Provider 實作 |
| 原有跨文件 Mutation Test | **9/9** | 舊路徑／Stage Owner／Release 範圍等錯誤會被辨認 |
| 原有 OpenAPI/Auth Mutation Test | **9/9** | 路徑參數／Staff／ServiceToken／Secret 洩漏等缺陷會被辨認 |
| Stage Acceptance Spec | **286 個設計案例，全部 NOT RUN** | 是實際施工後應執行的測試清單，未能宣稱完成 |

## 交付檔案 QA

在重新打包後，必須以 ZIP `testzip()` 確認 CRC，再在另一目錄解壓，核對每個來源／解壓 SHA-256，並從**解壓版本**重新執行上述文件、OpenAPI、模型及 Mutation Test。該完整結果由外部 `Sunrise_v0.7.3_delivery_qa.json` 記錄；ZIP 內容不應偽造產品部署或 GitHub Merge 成功。

## 仍然未做／不能標 PASS

- S0 Owner 人手批准、GitHub main Docs PR / 合併：**NOT VERIFIED / NOT PERFORMED**。
- S1 真 Open Notebook / SurrealDB，S3 真 PostgreSQL/Supabase，S4 API Saga／Dual Restore、S9 Evidence 簽章、S17 Grade DB Immutable、S23 Teacher Grant：**NOT RUN**。
- JSON Schema／OpenAPI 具體 DTO 欄位、Quota／費用、選用模型和法規／校方私隱政策：**REFERENCE 或待適用 Owner Stage 審批**。
- 真正獨立 EGM Goldfish／安全審查：**NOT RUN**。本文件 QA 與 28 項 Mutation 均屬內部設計檢查。

## 核心決策判準

若只有一個 Stage 的主要成果／安全／資料歸屬／回退未通過，該 Stage **FAIL/BLOCKED**；不能用「下一期補做」掩飾。若只是不影響目標的具體工具／模型／UI 細節尚未核實，留 `REFERENCE/TBD` 並記載接手者的確認時間點。**不要讓規劃說明變成未經驗證的技術保證。**
