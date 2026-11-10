#!/usr/bin/env python3
"""Independent negative mutation tests, deliberately ignoring ZIP SHA checks."""
import json,tempfile,shutil,sys
from pathlib import Path
from validate_openapi_contracts import inspect
SRC=Path(__file__).resolve().parents[1]

TESTS=[
 ('missing templated Path Parameter','I', '/link/v1/courses/{course_id}/materials/{material_id}/download','get',
  lambda o:o['parameters'].pop(0),'MISSING_OR_EXTRA_PATH_PARAMETER'),
 ('untype successful B Course response','B','/core/v1/courses','post',
  lambda o:o['responses'][next(c for c in o['responses'] if c.startswith('2'))].pop('content'),'UNTYPED_SUCCESS_RESPONSE'),
 ('bypass service authentication','A','/vault/v1/internal/provision','post',
  lambda o:o.update({'security':[{'AdminSession':[]}]}),'ACTOR_SECURITY'),
 ('remove service scope','B','/core/v1/course-operations/{operation_id}/finalize','post',
  lambda o:o['x-auth-policy'].update({'required_service_scope':None}),'SERVICE_SCOPE'),
 ('teacher impersonation via AdminSession','I','/link/v1/teacher/content','get',
  lambda o:o.update({'security':[{'AdminSession':[]}]}),'ACTOR_SECURITY'),
 ('teacher missing required course query','I','/link/v1/teacher/content','get',
  lambda o:o.update({'parameters':[]}), 'REQUIRED_QUERY_PARAMETER'),
 ('accept untyped free-form input','I','/link/v1/course-provision','post',
  lambda o:o['requestBody']['content']['application/json'].update({'schema':{'type':'object','additionalProperties':True}}),'UNTYPED_REQUEST'),
 ('add secret to successful provider DTO','B','/core/v1/admin/ai-providers','post',
  lambda o:o.update({'x-attack-add-secret':True}),'SECRET_VALUE_IN_PROVIDER_RESPONSE'),
 ('I evidence accepted with Admin authority','B','/core/v1/evidence-bundles','post',
  lambda o:o.update({'security':[{'AdminSession':[]}]}),'ACTOR_SECURITY'),
]
passed=0
for label,own,path,method,mutate,expected in TESTS:
 with tempfile.TemporaryDirectory(prefix='openapi_mutation_') as td:
  tgt=Path(td)
  # Copy only files needed for OpenAPI validation, do NOT use prior manifest to detect mutation
  (tgt/'contracts/openapi').mkdir(parents=True)
  (tgt/'docs/architecture').mkdir(parents=True)
  shutil.copy2(SRC/'docs/architecture/API_INVENTORY.json',tgt/'docs/architecture/API_INVENTORY.json')
  for code in 'abi':shutil.copy2(SRC/f'contracts/openapi/{code}-v1.openapi.json',tgt/f'contracts/openapi/{code}-v1.openapi.json')
  f=tgt/f'contracts/openapi/{own.lower()}-v1.openapi.json';spec=json.loads(f.read_text())
  item=spec['paths'][path][method]
  if label=='add secret to successful provider DTO':
   spec['components']['schemas']['AiProvider']['properties']['secret_value']={'type':'string'}
  else:mutate(item)
  f.write_text(json.dumps(spec))
  checks,errors,_=inspect(tgt, thorough=False)
  assert any(expected in e for e in errors),f'{label}: expected {expected}, actual {errors[:12]}'
  print('PASS mutation detected:',label)
  passed+=1
print(f'{passed}/{len(TESTS)} independent OpenAPI semantic mutations caught; manifest bypassed by design.')
