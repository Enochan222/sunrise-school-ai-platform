#!/usr/bin/env python3
"""Targeted semantic mutation tests that IGNORE SHA manifests; test new audit gates."""
from pathlib import Path
import json,tempfile,shutil,sys
from validate_review_contracts import inspect
R=Path(__file__).resolve().parents[1]
TESTS=[
 ('Teacher B endpoint loses StaffSession','contracts/openapi/b-v1.openapi.json',lambda z:z['paths']['/core/v1/assessments/{assessment_id}']['get'].update({'security':[{'AdminSession':[]}]}),'C16_REAL_STAFF_B_OP_getAssessment'),
 ('Evidence I validator accepts Admin impersonation','contracts/openapi/i-v1.openapi.json',lambda z:z['paths']['/link/v1/evidence-bundles/{bundle_id}/validate']['post'].update({'security':[{'AdminSession':[]}]}),'C12_I_WORKER_NOT_ADMIN'),
 ('Course reintroduces singular class_id','contracts/openapi/b-v1.openapi.json',lambda z:z['components']['schemas']['AcademicCourse']['properties'].update({'class_id':{'type':'string'}}),'C02_COURSE_GRAIN'),
 ('Blueprint API missing','docs/architecture/API_INVENTORY.json',lambda z:z['operations'].__setitem__(slice(None),[o for o in z['operations'] if o['operation_id']!='createBlueprint']),'C08_BLUEPRINT_API_createBlueprint'),
 ('Weakness Discard capability omitted','docs/architecture/API_INVENTORY.json',lambda z:z['operations'].__setitem__(slice(None),[o for o in z['operations'] if o['operation_id']!='discardWeaknessSnapshot']),'C14_WEAKNESS_discardWeaknessSnapshot'),
 ('Grade request omits canonical hash','contracts/openapi/b-v1.openapi.json',lambda z:z['components']['schemas']['submitGradeRequest']['required'].remove('canonical_request_hash'),'C13_GRADE_REQUEST_HASH'),
 ('Evidence cannot express two validation phases','contracts/openapi/i-v1.openapi.json',lambda z:z['components']['schemas']['validateEvidenceBundleRequest']['required'].remove('validation_phase'),'C11_EVIDENCE_PHASE_JOB'),
 ('A school ownership removed','contracts/openapi/a-v1.openapi.json',lambda z:z['components']['schemas']['ContentShell']['required'].remove('school_id'),'C06_A_SCHOOL_OWNERSHIP'),
 ('Teaching Group missing from Enrollment','contracts/openapi/b-v1.openapi.json',lambda z:z['components']['schemas']['Enrollment']['required'].remove('teaching_group_id'),'C05_ENROLLED_GROUP'),
 ('B staff activation permits early teacher','docs/architecture/API_INVENTORY.json',lambda z:next(o for o in z['operations'] if o['operation_id']=='getCurrentGrade').update({'staff_activation_stage':18}),'C16_REAL_STAFF_B_OP_getCurrentGrade'),
 ('A backup status first Stage removed','docs/architecture/API_INVENTORY.json',lambda z:next(o for o in z['operations'] if o['operation_id']=='getVaultBackupStatus').update({'first_stage':28}),'C20_A_HEALTH'),
]
with tempfile.TemporaryDirectory(prefix='sunrise_v074_mutation_') as td:
 q=Path(td)
 for f in ['docs/architecture/API_INVENTORY.json','contracts/openapi/a-v1.openapi.json','contracts/openapi/b-v1.openapi.json','contracts/openapi/i-v1.openapi.json','docs/quality/STAGE_REGISTRY.json','docs/architecture/EVIDENCE_REVALIDATION.md','docs/architecture/GRADE_IDEMPOTENCY.md','docs/product/PRD.md','docs/product/ROADMAP.md']:
  (q/f).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/f,q/f)
 successes=0
 for label,filename,fn,expected in TESTS:
  p=q/filename;orig=p.read_text();data=json.loads(orig)
  fn(data);p.write_text(json.dumps(data))
  checks,errors=inspect(q)
  assert expected in errors,(label,expected,errors)
  successes+=1;p.write_text(orig)
  print('PASS mutation caught:',label)
 print(f'{successes}/{len(TESTS)} new contract semantic mutants caught WITHOUT file hash checking. These are not live API tests.')
