#!/usr/bin/env python3
"""Positive + negative JSON Schema fixture tests for typed OpenAPI responses/requests."""
import json,copy,sys
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
SPECS={o:json.loads((ROOT/f'contracts/openapi/{o.lower()}-v1.openapi.json').read_text()) for o in 'ABI'}
passed=0

def validate(name,owner,path,method,payload,expected=True,response=True):
 global passed
 spec=SPECS[owner];o=spec['paths'][path][method.lower()]
 if response:
  statuses=[x for x in o['responses'] if x.startswith('2')]
  assert len(statuses)==1,(name,statuses)
  schema=o['responses'][statuses[0]]['content']['application/json']['schema']
 else:
  schema=o['requestBody']['content']['application/json']['schema']
 # Use full OAS structure as root because refs use /components/schemas paths.
 wrapper={'$schema':'https://json-schema.org/draft/2020-12/schema','components':spec['components'],'properties':{'v':schema},'required':['v']}
 errors=list(jsonschema.Draft202012Validator(wrapper,format_checker=jsonschema.FormatChecker()).iter_errors({'v':payload}))
 valid=not errors
 assert valid==expected, f'{name} expected {expected}, got {valid}: '+ ('; '.join(e.message for e in errors[:3]))
 passed+=1
 print('PASS',name, 'accepted' if valid else 'rejected')

shell={'school_id':'sch-1','shell_id':'shell-1','external_course_key':'ec-1','notebook_id':'nb-1','display_title':'四年級數學','status':'READY','created_at':'2026-11-08T00:00:00Z'}
validate('A shell success typed','A','/vault/v1/shells','POST',{'request_id':'req-1','data':shell})
invalid=copy.deepcopy(shell);invalid.pop('notebook_id')
validate('A shell missing notebook reject','A','/vault/v1/shells','POST',{'request_id':'req-1','data':invalid},False)
validate('A unknown extra success field reject','A','/vault/v1/shells','POST',{'request_id':'req-1','data':{**shell,'secret':'leak'}},False)
course={'course_id':'c-1','academic_year_id':'y-1','school_id':'s-1','subject_id':'math','title':'P4 Maths','grade':4,'curriculum_stream':'local','content_state':'CONTENT_UNLINKED','revision':1}
validate('B independent course success','B','/core/v1/courses','POST',{'request_id':'req-1','data':course})
validate('B invalid course status reject','B','/core/v1/courses','POST',{'request_id':'req-1','data':{**course,'content_state':'FULLY_LINKED_FAKE'}},False)
provider={'provider_id':'p-1','kind':'gemini','secret_ref':'kms://credential-1','model_id':'model-A','status':'ACTIVE'}
validate('B provider response no plaintext','B','/core/v1/admin/ai-providers','POST',{'request_id':'req-1','data':provider})
validate('B provider secret leakage reject','B','/core/v1/admin/ai-providers','POST',{'request_id':'req-1','data':{**provider,'secret_value':'DO_NOT_RETURN'}},False)
validgrade=json.loads((ROOT/'contracts/fixtures/grade_valid.json').read_text())
validate('B grade event canonical','B','/core/v1/grades/submit','POST',{'request_id':'req-1','data':validgrade})
invalidgrade=json.loads((ROOT/'contracts/fixtures/grade_invalid_correction.json').read_text())
validate('B correction without reason rejected','B','/core/v1/admin/grade-corrections','POST',{'request_id':'req-1','data':invalidgrade},False)
validate('I unified create full request','I','/link/v1/course-provision','POST',{'school_id':'sch-1','academic_year_id':'y-1','subject_id':'math','course_title':'P4','shell_title':'P4教材','idempotency_key':'operation-key-1','actor_id':'admin-1'},True,False)
validate('I incomplete create request rejected','I','/link/v1/course-provision','POST',{'school_id':'sch-1','course_title':'P4'},False,False)
validpermission={'staff_id':'teacher-1','grant_epoch':1,'grants':[{'staff_id':'teacher-1','course_id':'c-1','permission':'MATERIAL_READ','grant_epoch':1,'active':True}],'checked_at':'2026-11-08T00:00:00Z'}
validate('B private staff grant result','B','/core/v1/staff/{staff_id}/permissions','GET',{'request_id':'req-1','data':validpermission})
validate('B fake staff permission denied by schema','B','/core/v1/staff/{staff_id}/permissions','GET',{'request_id':'req-1','data':{**validpermission,'grants':[{'staff_id':'teacher-1','course_id':'c-1','permission':'ROOT','grant_epoch':1,'active':True}]}},False)
teacher={'course_id':'c-1','grant_epoch':1,'materials':[],'read_only':True}
validate('I teacher content strictly read-only','I','/link/v1/teacher/content','GET',{'request_id':'req-1','data':teacher})
validate('I teacher writable content rejected','I','/link/v1/teacher/content','GET',{'request_id':'req-1','data':{**teacher,'read_only':False}},False)

synthetic={'student_id':'syn-1','pseudonym':'student-001','data_class':'SYNTHETIC','created_at':'2026-11-08T00:00:00Z'}
validate('B synthetic student read list','B','/core/v1/students','GET',{'request_id':'req-1','data':{'items':[synthetic]}})
validate('B real student leakage from synthetic list denied','B','/core/v1/students','GET',{'request_id':'req-1','data':{'items':[{**synthetic,'data_class':'REAL_APPROVED'}]}},False)
validate('B Grade history versioned','B','/core/v1/grades/{grade_key}/history','GET',{'request_id':'req-1','data':{'grade_key':'grade-1','events':[validgrade],'current_revision':1}})
validate('B Grade history missing version denied','B','/core/v1/grades/{grade_key}/history','GET',{'request_id':'req-1','data':{'grade_key':'grade-1','events':[validgrade]}},False)
validate('I teacher scoped search typed request','I','/link/v1/teacher/courses/{course_id}/search','POST',{'query':'課堂內容','limit':10},True,False)
validate('I teacher unscoped empty search denied','I','/link/v1/teacher/courses/{course_id}/search','POST',{'query':''},False,False)
# Binary download must advertise PDF explicitly: paper delivery is not a generic JSON response.
paper_pdf=SPECS['B']['paths']['/core/v1/papers/{paper_id}/pdf']['get']
assert paper_pdf['responses']['200']['content']['application/pdf']['schema']=={'type':'string','format':'binary'}
passed+=1;print('PASS paper PDF binary media contract')
print(f'{passed}/{passed} typed operation JSON schema fixture cases passed. Auth signature and real API NOT RUN.')
