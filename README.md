# Sunrise School AI Platform — v0.7.5 Reuse-first Planning Candidate

**Active repository:** https://github.com/Enochan222/sunrise-school-ai-platform  
**Delivery:** Stage S0 is **documentation-only**. S1–S28 are **NOT IMPLEMENTED / NOT DEPLOYED**.  
**GitHub Actions:** **HISTORICALLY DISABLED (D08); LIMITED STAGE 1 [A] TWO-WORKFLOW EXCEPTION** (see [addendum](docs/decisions/STAGE1_LIMITED_CI_ADDENDUM.md)). **GitHub Copilot:** **NOT USED.**
**Release/Stage approval:** **PENDING**; static checks do not count as runtime acceptance or approval.

Read [AI development rules](AGENTS.md), [Stage0 handover](docs/delivery/NEW_REPO_STAGE0.md), [PRD](docs/product/PRD.md), [S0–S28 Roadmap](docs/product/ROADMAP.md), [Stage Registry](docs/quality/STAGE_REGISTRY.json), [API Inventory](docs/architecture/API_INVENTORY.json), [Reuse-first audit](docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md), [Stage logic audit](docs/delivery/STAGE_FLOW_ENGINEERING_AUDIT.md).

## Four boundaries

- **A:** Open Notebook / SurrealDB secure Content Vault. Reuse upstream ingestion, search, worker and notebook foundations; Sunrise must add school/source/shell policy. Never expose raw upstream service publicly.
- **B:** Independent PostgreSQL/Supabase Learning Operations for Course, TeachingGroup, Question, generation, immutable grade history, marking and analytics.
- **I:** API-only A/B orchestrator; no direct A/B DB credentials or table migrations.
- **U:** API-only Sunrise UI; no raw databases or private provider secrets.

S0 contains architecture and repository design only. S1 first deploys A vault. S2/S3 deliver A/B APIs separately; S4 is I Course↔Shell Saga; S5 U Course/Content portal; remaining Stages add independent B/I/U/A functions, each with one Owner and actual tests. The candidate includes 29 Stage specs S0–S28, 100 **proposed** APIs, 310 **designed** acceptance tests; these are NOT runtime passes.

## Manual validation and the bounded Stage 1 CI exception

Preferred repeatable environment: run `sh scripts/run_qa_docker.sh` with Docker installed (see [QA environment](docs/delivery/QA_ENVIRONMENT.md)); the container build has not been exercised in this ChatGPT environment. Fallback with Python 3.11+ and `jsonschema` installed: run `python scripts/run_qa_no_actions.py` from the repository root. The runner executes 13 static, semantic, contract and mutation scripts plus the Stage0 status gate, saves no secrets, and fails nonzero on failed checks. Results require an explicit record with commit SHA and logs attached to the PR by GPT or developer. **Historical Stage 0 QA is manual:** the later Stage 1 limited CI addendum permits only two separately approved workflows. Do not auto-merge or assert CI PASS without actual run evidence.

**Source provenance:** Original ZIP `Sunrise_Master_Project_Kit_v0.7.5_Reuse_First_Stage_Logic_Reviewed.zip`, SHA-256 `ee4d07d9e4d46fb9bf8c8b8f26c22413a4d2b0cca58acd0a45fc937da0b95bd5`; original source hashes at [`docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256`](docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256). Output manifest covers the adapted tree, so this is NOT byte-identical to the original kit.
