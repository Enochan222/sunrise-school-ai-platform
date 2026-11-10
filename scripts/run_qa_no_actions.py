#!/usr/bin/env python3
"""Manual or GPT-invoked local QA runner; NO GitHub Actions and no CI enforcement."""
import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scripts=['validate_docs.py', 'validate_stage_controls.py', 'validate_openapi_contracts.py', 'validate_review_contracts.py', 'validate_reuse_stage_logic.py', 'test_design_invariants.py', 'test_review_invariants.py', 'test_typed_contract_fixtures.py', 'test_reuse_stage_mutations.py', 'test_semantic_mutations.py', 'test_openapi_mutations.py', 'test_stage_control_mutations.py', 'test_review_mutations.py']
results=[]
for name in scripts+['validate_contract_fixtures.py','validate_stage0.py']:
 command=[sys.executable,str(root/'scripts'/name)]
 proc=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=180)
 print(f'=== {name}: {"PASS" if proc.returncode==0 else "FAIL"} ===',flush=True)
 if proc.returncode:print((proc.stdout+proc.stderr)[-3000:],flush=True)
 results.append({'script':name,'exit_code':proc.returncode})
proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],cwd=root,text=True,capture_output=True,timeout=180)
print(f'=== unittest: {"PASS" if proc.returncode==0 else "FAIL"} ===',flush=True)
if proc.returncode:print((proc.stdout+proc.stderr)[-3000:],flush=True)
results.append({'script':'unittest','exit_code':proc.returncode})
print(json.dumps({'result':'PASS' if all(r['exit_code']==0 for r in results) else 'FAIL', 'scope':'STATIC DOCUMENT/CONTRACT/MUTATION ONLY, GITHUB DOES NOT ENFORCE', 'results':results},indent=2),flush=True)
sys.exit(not all(r['exit_code']==0 for r in results))
