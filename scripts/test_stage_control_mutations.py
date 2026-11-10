#!/usr/bin/env python3
"""Negative tests that prove control-card checker detects independent logical defects."""
from pathlib import Path
from copy import deepcopy
import sys,json
from validate_stage_controls import inspect
root=Path(__file__).resolve().parents[1]
orig=json.loads((root/'docs/quality/STAGE_CONTROL_MATRIX.json').read_text(encoding='utf8'))
checks={
 'missing_critical_acceptance':lambda a:a[1]['gates'].clear(),
 'future_stage_out_of_range':lambda a:a[4]['future'].append('此項依賴 S999 才可完成，先不理會'),
 'wrong_owner_in_integration':lambda a:a[4].__setitem__('owner','A'),
 'missing_prior_collision':lambda a:a[17]['prior'].clear(),
 'no_explicit_future_impact':lambda a:a[20]['future'].clear(),
 'missing_technical_uncertainty':lambda a:a[7]['open'].clear(),
 'wrong_stage_dependencies':lambda a:a[9].__setitem__('depends_on',[8]),
 'wrong_backlinks':lambda a:a[3].__setitem__('downstream',[4,5]),
 'lost_acceptance_id':lambda a:a[1].__setitem__('acceptance_ids',a[1]['acceptance_ids'][:-1]),
 'duplicate_stage_record':lambda a:a[28].__setitem__('stage',27),
}
fail=[]
for name,mutate in checks.items():
 x=deepcopy(orig);mutate(x)
 _,errors=inspect(root,x,check_files=False)
 if not errors:fail.append(name)
print(json.dumps({'result':'PASS' if not fail else 'FAIL','mutants':len(checks),'caught':len(checks)-len(fail),'uncaught':fail,'scope':'in-memory mutation semantics, not runtime'},ensure_ascii=False,indent=2))
sys.exit(bool(fail))
