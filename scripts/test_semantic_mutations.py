#!/usr/bin/env python3
"""Inject contradictions into copies. Require SEMANTIC rejection with SHA check DISABLED."""
import json,tempfile,shutil,sys
from pathlib import Path
from verify_kit import validate
src=Path(__file__).resolve().parents[1]
M=[]
def T(label,path,mutate,must):M.append((label,path,mutate,must))
T('stale release range','docs/delivery/RELEASE_POLICY.md',lambda s:s.replace('R01–R28','R01..R21'), 'release policy max end R28')
T('API path mismatch','docs/architecture/API_CONTRACT.md',lambda s:s.replace('/core/v1/course-operations/reserve','/core/v1/bindings/reserve'),'canonical API Contract table exact inventory')
T('wrong route in Stage3','docs/stages/STAGE_03.md',lambda s:s.replace('/core/v1/course-operations/reserve','/core/v1/course-bindings/reserve'),'S3 only canonical API routes in Stage')
T('I owner becomes B','docs/quality/STAGE_REGISTRY.json',lambda s:s.replace('"track": "I",\n    "name": "Course–Content Linking', '"track": "B",\n    "name": "Course–Content Linking'),'critical one-owner Stage order map')
T('I depends on future stage','docs/quality/STAGE_REGISTRY.json',lambda s:s.replace('"depends_on": [\n      2,\n      3\n    ]','"depends_on": [\n      2,\n      8\n    ]',1), 'S4 dependency topological')
T('S0 requires Staging','docs/stages/STAGE_00.md',lambda s:s.replace('文件、Repo 與 Owner 人工可核資料（無部署前提）','Staging 已有真實資料庫連線',1),'Stage0 no runtime evidence/precondition')
T('wrong CODEOWNERS','/.github/CODEOWNERS',None,None) # handled specially below
T('teacher I precedes B permissions','docs/quality/STAGE_REGISTRY.json',lambda s:s.replace('"depends_on": [\n      4,\n      22\n    ]','"depends_on": [\n      4\n    ]',1),'S23 critical technical dependency')
T('remove U gate','docs/stages/STAGE_10.md',lambda s:s.replace('**Frontend Gate:**','**Page:**',1),'S10 U-only feature Gate')
passed=0
for label,path,fn,needle in M:
 with tempfile.TemporaryDirectory(prefix='sunrise_mutation_') as td:
  dst=Path(td);shutil.copytree(src,dst,dirs_exist_ok=True)
  p=dst/('{}.github/CODEOWNERS'.format('') if path.startswith('/') else path)
  if path.startswith('/'):
   old=p.read_text();new=old.replace('@IssacSitHk','@WrongUser');needle='new repo CODEOWNERS owner matches'
  else:
   old=p.read_text();new=fn(old)
  assert old!=new, f'{label}: mutation did not alter file'
  p.write_text(new)
  checks,errors=validate(dst,check_manifest=False)
  assert errors, f'{label}: semantic validator failed to detect mutation'
  assert any(needle in err for err in errors),f'{label}: rejected only for other reason: {errors[:9]}'
  print('PASS: caught',label,'=>',needle);passed+=1
print(f'{passed}/{len(M)} semantic mutations caught without SHA check. No HTTP/DB runtime involved.')
