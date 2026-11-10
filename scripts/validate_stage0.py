#!/usr/bin/env python3
"""Stage 0 CI gate. A green BOOTSTRAP_ONLY check is not Stage 0 acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def inspect(root, baseline=None):
    root = Path(root)
    errors = []
    try:
        baseline = baseline if baseline is not None else json.loads((root / "stage0/STAGE0_BASELINE.json").read_text())
    except (ValueError, OSError) as exc:
        return [f"BASELINE_NOT_READABLE: {exc}"]
    expected = {"repository":"Enochan222/sunrise-school-ai-platform",
                "source_repository_history_imported":False,
                "master_kit_target":"v0.7.5",
                "stage_count_if_imported":29,
                "candidate_api_operations_if_imported":100,
                "planned_acceptance_cases_if_imported":310,
                "runtime_tests":"NOT_RUN"}
    for k, value in expected.items():
        if baseline.get(k) != value:
            errors.append("INVALID_" + k)
    phase = baseline.get("master_kit_phase")
    if phase not in ("BOOTSTRAP_ONLY","MASTER_CANDIDATE"):
        errors.append("BAD_PHASE")
    if baseline.get("stage0_product_approval") not in ("PENDING","OWNER_APPROVED"):
        errors.append("BAD_APPROVAL")
    if phase == "BOOTSTRAP_ONLY":
        if baseline.get("full_master_kit_imported") is not False:
            errors.append("BOOTSTRAP_MUST_NOT_CLAIM_KIT_IMPORTED")
        if baseline.get("stage0_product_approval") != "PENDING":
            errors.append("BOOTSTRAP_MUST_NOT_CLAIM_APPROVAL")
    if phase == "MASTER_CANDIDATE" and baseline.get("full_master_kit_imported") is not True:
        errors.append("CANDIDATE_MUST_BE_IMPORTED")
    paths = ["README.md","AGENTS.md",".github/workflows/validate-docs.yml",
             "docs/delivery/STAGE0_CHECKLIST.md","docs/delivery/IMPORT_V075.md",
             "scripts/validate_stage0.py","stage0/STAGE0_BASELINE.json"]
    for rel in paths:
        if not (root/rel).is_file():
            errors.append("MISSING_BOOTSTRAP:"+rel)
    flow = root/".github/workflows/validate-docs.yml"
    if flow.is_file() and ("pull_request:" not in flow.read_text() or "validate-docs:" not in flow.read_text()):
        errors.append("MISSING_REAL_PR_CI")
    if flow.is_file() and "pull_request_target:" in flow.read_text():
        errors.append("UNSAFE_PR_TARGET")
    if phase == "BOOTSTRAP_ONLY":
        r = root/"README.md"
        if r.is_file() and "MASTER KIT v0.7.5 NOT YET IMPORTED" not in r.read_text():
            errors.append("README_FALSE_BOOTSTRAP_CLAIM")
    # Fast fail for common sensitive files; no special privileges or repository secrets needed.
    for p in root.rglob("*"):
        if p.is_file() and (p.name in {".env",".env.local",".env.production","service-account.json","credentials.json","id_rsa"} or p.suffix in {".pem",".p12",".pfx"}):
            errors.append("SECRET_FILE:"+str(p.relative_to(root)))
    if phase == "MASTER_CANDIDATE":
        needed = ["docs/quality/STAGE_REGISTRY.json",
                  "docs/architecture/API_INVENTORY.json",
                  "docs/quality/STAGE_CONTROL_MATRIX.json","FILE_MANIFEST.sha256"]
        for rel in needed:
            if not (root/rel).is_file():
                errors.append("MISSING_MASTER:"+rel)
        if not errors:
            try:
                reg = json.loads((root/needed[0]).read_text())
                ops = json.loads((root/needed[1]).read_text())["operations"]
                if len(reg)!=29 or [s["stage"] for s in reg]!=list(range(29)):
                    errors.append("BAD_STAGE_ORDER")
                if sum(len(s["acceptance_ids"]) for s in reg)!=310:
                    errors.append("BAD_ACCEPTANCE_COUNT")
                if len(ops)!=100:
                    errors.append("BAD_API_COUNT")
                for n in range(29):
                    if not (root/f"docs/stages/STAGE_{n:02d}.md").is_file():
                        errors.append("MISSING_STAGE:"+str(n))
                for entry in (root/"FILE_MANIFEST.sha256").read_text().splitlines():
                    digest,rel = entry.split("  ",1)
                    p=(root/rel).resolve()
                    if not p.is_relative_to(root.resolve()) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                        errors.append("MANIFEST_FAIL:"+rel)
            except (OSError,ValueError,KeyError) as exc:
                errors.append("INVALID_MASTER:"+str(exc))
        suite = ["validate_docs.py","validate_stage_controls.py","validate_openapi_contracts.py",
                 "validate_review_contracts.py","validate_reuse_stage_logic.py",
                 "test_design_invariants.py","test_review_invariants.py",
                 "test_typed_contract_fixtures.py","test_reuse_stage_mutations.py",
                 "test_semantic_mutations.py","test_openapi_mutations.py",
                 "test_stage_control_mutations.py","test_review_mutations.py"]
        if not errors:
            for script in suite:
                path=root/"scripts"/script
                if not path.is_file():
                    errors.append("MISSING_TEST:"+script)
                    continue
                try:
                    out=subprocess.run([sys.executable,str(path)],cwd=root,capture_output=True,text=True,timeout=120)
                except subprocess.TimeoutExpired:
                    errors.append("TEST_TIMEOUT:"+script)
                    continue
                if out.returncode:
                    errors.append("TEST_FAILED:"+script+" "+(out.stdout+out.stderr)[-180:])
    return errors

if __name__=="__main__":
    issues=inspect(ROOT)
    phase=json.loads((ROOT/"stage0/STAGE0_BASELINE.json").read_text())["master_kit_phase"]
    print(json.dumps({"status":"PASS" if not issues else "FAIL",
        "scope":"BOOTSTRAP ONLY; MASTER KIT NOT IMPORTED" if phase=="BOOTSTRAP_ONLY" else "MASTER DOCUMENT TESTS, NOT RUNTIME",
        "issues":issues},indent=2))
    sys.exit(bool(issues))
