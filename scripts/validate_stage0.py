#!/usr/bin/env python3
"""Stage0 verifier: no GitHub Actions; never conflate bootstrap with full import."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def inspect(root, baseline=None):
    root=Path(root)
    errors=[]
    try:
        baseline=baseline if baseline is not None else json.loads((root/"stage0/STAGE0_BASELINE.json").read_text())
    except (ValueError,OSError) as exc:
        return ["BASELINE_NOT_READABLE:"+str(exc)]
    required={"repository":"Enochan222/sunrise-school-ai-platform",
      "source_repository_history_imported":False,"master_kit_target":"v0.7.5",
      "stage_count_if_imported":29,"candidate_api_operations_if_imported":100,
      "planned_acceptance_cases_if_imported":310,"runtime_tests":"NOT_RUN"}
    for key,value in required.items():
        if baseline.get(key)!=value:errors.append("INVALID_"+key)
    phase=baseline.get("master_kit_phase")
    if phase not in ("BOOTSTRAP_ONLY","MASTER_CANDIDATE"):errors.append("BAD_PHASE")
    if baseline.get("stage0_product_approval") not in ("PENDING","OWNER_APPROVED"):errors.append("BAD_APPROVAL")
    if phase=="BOOTSTRAP_ONLY":
        if baseline.get("full_master_kit_imported") is not False:errors.append("BOOTSTRAP_MUST_NOT_CLAIM_KIT_IMPORTED")
        if baseline.get("stage0_product_approval")!="PENDING":errors.append("BOOTSTRAP_MUST_NOT_CLAIM_APPROVAL")
    if phase=="MASTER_CANDIDATE" and baseline.get("full_master_kit_imported") is not True:errors.append("CANDIDATE_MUST_BE_IMPORTED")
    for rel in ("README.md","AGENTS.md","docs/delivery/STAGE0_CHECKLIST.md",
                "scripts/validate_stage0.py","stage0/STAGE0_BASELINE.json"):
        if not (root/rel).is_file():errors.append("MISSING_BOOTSTRAP:"+rel)
    if any((root/".github/workflows").rglob("*.yml")) or any((root/".github/workflows").rglob("*.yaml")):
        errors.append("ACTIONS_WORKFLOW_FORBIDDEN")
    if phase=="BOOTSTRAP_ONLY" and (root/"README.md").is_file():
        if "Master Kit is NOT YET uploaded" not in (root/"README.md").read_text():
            errors.append("README_FALSE_BOOTSTRAP_CLAIM")
    for p in root.rglob("*"):
        if p.is_file() and (p.name in {".env",".env.local",".env.production","service-account.json","credentials.json","id_rsa"} or p.suffix in {".pem",".p12",".pfx"}):
            errors.append("SECRET_FILE:"+str(p.relative_to(root)))
    if phase=="MASTER_CANDIDATE":
        needed=["docs/quality/STAGE_REGISTRY.json","docs/architecture/API_INVENTORY.json",
                "docs/quality/STAGE_CONTROL_MATRIX.json","FILE_MANIFEST.sha256"]
        for rel in needed:
            if not (root/rel).is_file():errors.append("MISSING_MASTER:"+rel)
        if not errors:
            try:
                reg=json.loads((root/needed[0]).read_text())
                ops=json.loads((root/needed[1]).read_text())["operations"]
                if len(reg)!=29 or [s["stage"] for s in reg]!=list(range(29)):errors.append("BAD_STAGE_ORDER")
                if sum(len(s["acceptance_ids"]) for s in reg)!=310:errors.append("BAD_ACCEPTANCE_COUNT")
                if len(ops)!=100:errors.append("BAD_API_COUNT")
                for i in range(29):
                    if not (root/f"docs/stages/STAGE_{i:02d}.md").is_file():errors.append("MISSING_STAGE:"+str(i))
                for line in (root/"FILE_MANIFEST.sha256").read_text().splitlines():
                    digest,rel=line.split("  ",1);candidate=(root/rel).resolve()
                    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest()!=digest:errors.append("MANIFEST_FAIL:"+rel)
            except (OSError,ValueError,KeyError) as exc:
                errors.append("INVALID_MASTER:"+str(exc))
    return errors

if __name__=="__main__":
    issues=inspect(ROOT)
    baseline=json.loads((ROOT/"stage0/STAGE0_BASELINE.json").read_text())
    print(json.dumps({"status":"PASS" if not issues else "FAIL",
      "scope":"BOOTSTRAP ONLY; MASTER KIT NOT UPLOADED" if baseline["master_kit_phase"]=="BOOTSTRAP_ONLY" else "MASTER DOCUMENT CONTRACTS, NOT RUNTIME",
      "issues":issues},indent=2))
    sys.exit(bool(issues))
