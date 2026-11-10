#!/usr/bin/env python3
"""Stage0 static gate with NO GitHub Actions. This cannot enforce GitHub merges."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
def inspect(root=ROOT,baseline=None):
 root=Path(root);issues=[]
 try:b=baseline if baseline is not None else json.loads((root/'stage0/STAGE0_BASELINE.json').read_text())
 except Exception as e:return ['BASELINE_NOT_READABLE:'+str(e)]
 expected={'repository':'Enochan222/sunrise-school-ai-platform','master_kit_target':'v0.7.5',
   'master_kit_phase':'MASTER_CANDIDATE','full_master_kit_imported':True,'stage_count_if_imported':29,
   'candidate_api_operations_if_imported':100,'planned_acceptance_cases_if_imported':310,
   'runtime_tests':'NOT_RUN','stage0_product_approval':'PENDING',
   'source_repository_history_imported':False}
 for k,v in expected.items():
  if b.get(k)!=v:issues.append('INVALID_'+k)
 for rel in ['README.md','AGENTS.md','docs/delivery/NEW_REPO_STAGE0.md','docs/quality/STAGE_REGISTRY.json',
  'docs/architecture/API_INVENTORY.json','docs/quality/STAGE_CONTROL_MATRIX.json',
  'docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256','FILE_MANIFEST.sha256',
  'stage0/IMPORT_PROVENANCE.json']:
  if not (root/rel).is_file():issues.append('MISSING:'+rel)
 for n in range(29):
  if not (root/f'docs/stages/STAGE_{n:02d}.md').is_file():issues.append('MISSING_STAGE:'+str(n))
 for p in (root/'.github/workflows').glob('*'):
  if p.is_file():issues.append('UNWANTED_GITHUB_ACTIONS:'+str(p.relative_to(root)))
 try:
  reg=json.loads((root/'docs/quality/STAGE_REGISTRY.json').read_text());inv=json.loads((root/'docs/architecture/API_INVENTORY.json').read_text())['operations']
  if len(reg)!=29 or sum(len(r['acceptance_ids']) for r in reg)!=310 or len(inv)!=100:issues.append('BAD_SOURCE_TOTALS')
 except (OSError,ValueError,KeyError):issues.append('BAD_SOURCE_STRUCTURE')
 return issues
if __name__=='__main__':
 issues=inspect();print(json.dumps({'result':'PASS' if not issues else 'FAIL','scope':'STATIC ONLY, NO GITHUB ACTIONS, NO RUNTIME','issues':issues},indent=2));sys.exit(bool(issues))
