#!/usr/bin/env python3
"""Independent targeted contract audit. STATIC design checks ONLY, no live API/SQL claims."""
from pathlib import Path
import json,re,sys, argparse
ROOT=Path(__file__).resolve().parents[1]

def inspect(root):
 root=Path(root);inv=json.loads((root/'docs/architecture/API_INVENTORY.json').read_text())['operations']
 specs={own:json.loads((root/f'contracts/openapi/{own.lower()}-v1.openapi.json').read_text()) for own in 'ABI'}
 byid={op['operation_id']:op for op in inv};errors=[];count=0
 def ck(cond,code):
  nonlocal count
  count+=1
  if not cond:errors.append(code)
 def field(model,name):return name in model.get('properties',{}) and name in model.get('required',[])
 b=specs['B']['components']['schemas'];a=specs['A']['components']['schemas'];i=specs['I']['components']['schemas']
 ck(len(inv)==100,'C01_100_OPS')
 ck(field(b['AcademicCourse'],'grade') and field(b['AcademicCourse'],'curriculum_stream') and 'class_id' not in b['AcademicCourse']['properties'],'C02_COURSE_GRAIN')
 ck(field(b['createAcademicCourseRequest'],'grade') and field(b['createAcademicCourseRequest'],'curriculum_stream') and 'class_id' not in b['createAcademicCourseRequest']['properties'],'C03_COURSE_CREATE_GRAIN')
 ck(all(field(b['TeachingGroup'],v) for v in ('course_id','school_id','teaching_group_id')),'C04_GROUP_OWNERSHIP')
 ck(field(b['Enrollment'],'teaching_group_id') and field(b['assignSyntheticStudentRequest'],'teaching_group_id'),'C05_ENROLLED_GROUP')
 ck(field(a['ContentShell'],'school_id') and field(a['createContentShellRequest'],'school_id'),'C06_A_SCHOOL_OWNERSHIP')
 ck(byid.get('createTeachingGroup',{}).get('first_stage')==3 and byid.get('listTeachingGroups',{}).get('first_stage')==3,'C07_B_GROUP_API_STAGE')
 for k in ('createBlueprint','getBlueprint','updateBlueprintDraft','publishBlueprint','listBlueprintVersions','getQuestionTemplate','createRubricVersion','getRubricVersion'):
  ck(byid.get(k,{}).get('first_stage')==6 and byid.get(k,{}).get('owner')=='B','C08_BLUEPRINT_API_'+k)
 ck(field(b['GenerationJob'],'blueprint_id') and field(b['GenerationJob'],'blueprint_version') and field(b['enqueueGenerationJobRequest'],'blueprint_version'),'C09_JOB_PIN_BLUEPRINT_VERSION')
 evid=byid.get('validateEvidenceBundle',{})
 ck(evid.get('auth')=='service' and evid.get('service_scope')=='link.evidence.validate' and evid.get('first_stage')==9,'C10_WORKER_SERVICE_ONLY')
 val=i['validateEvidenceBundleRequest']
 ck(all(field(val,k) for k in ('job_id','validation_phase','expected_course_id','binding_version')) and val['properties']['validation_phase'].get('enum')==['MODEL_PRE_EXECUTION','PAPER_PRE_APPROVAL'],'C11_EVIDENCE_PHASE_JOB')
 ck(specs['I']['paths']['/link/v1/evidence-bundles/{bundle_id}/validate']['post']['security']==[{'ServiceToken':[]}],'C12_I_WORKER_NOT_ADMIN')
 ck(field(b['submitGradeRequest'],'canonical_request_hash') and field(b['GradeEvent'],'canonical_request_hash'),'C13_GRADE_REQUEST_HASH')
 for k in ('listWeaknessCandidates','getWeaknessSnapshot','discardWeaknessSnapshot'):
  ck(byid.get(k,{}).get('first_stage')==20 and byid.get(k,{}).get('owner')=='B','C14_WEAKNESS_'+k)
 ck(all(s in b['WeaknessSnapshot']['properties']['state']['enum'] for s in ('CANDIDATE','VALID_ACTIVE','RETIRED','STALE')),'C15_WEAKNESS_STATE')
 permitted=['listAcademicCourses','getAcademicCourse','getAssessment','getCurrentGrade','getGradeHistory','submitGrade','listSubmissions','approveManualMarking','listSyntheticStudents']
 for k in permitted:
  op=byid.get(k,{});z=specs['B']['paths'][op['path']][op['method'].lower()] if op else {}
  ck(op.get('auth') in ('admin_or_staff','admin_staff_or_service') and bool(op.get('staff_scope')) and op.get('staff_activation_stage')==22 and {'StaffSession':[]} in z.get('security',[]),'C16_REAL_STAFF_B_OP_'+k)
 for k in ('correctGrade','grantStaffCourse','revokeStaffGrant'):
  ck(byid.get(k,{}).get('auth')=='admin','C17_ADMIN_ONLY_'+k)
 ck(byid['getStaffPermissionsService'].get('auth')=='service' and byid['getUserGrants'].get('auth')=='staff','C18_I_GRANT_PRIVATE')
 ck(all(byid[k]['first_stage']==18 and byid[k]['owner']=='B' for k in ('markItemSubmission','listSubmissionItemMarking')),'C19_ITEM_MARKING')
 ck(all(byid[k]['first_stage']==26 and byid[k]['owner']=='A' for k in ('getVaultHealth','getVaultBackupStatus')),'C20_A_HEALTH')
 ck(all(byid[k]['first_stage']==27 and byid[k]['owner']=='B' for k in ('getCoreHealth','getCoreBackupStatus')),'C21_B_HEALTH')
 reg=json.loads((root/'docs/quality/STAGE_REGISTRY.json').read_text()); ck(len(reg)==29 and [x['stage'] for x in reg]==list(range(29)),'C22_STAGES_PRESERVED')
 ck(reg[4]['track']=='I' and reg[9]['track']=='I' and reg[23]['track']=='I' and reg[28]['track']=='I','C23_I_OWNER')
 ck('link.evidence.validate' in (root/'docs/architecture/EVIDENCE_REVALIDATION.md').read_text() and 'same' in (root/'docs/architecture/EVIDENCE_REVALIDATION.md').read_text().lower(),'C24_EVIDENCE_SEMANTICS_DOC')
 ck('IDEMPOTENCY_PAYLOAD_CONFLICT' in (root/'docs/architecture/GRADE_IDEMPOTENCY.md').read_text(),'C25_GRADE_CONFLICT_DOC')
 ck('Stage 0' in (root/'docs/product/PRD.md').read_text() or 'S0' in (root/'docs/product/ROADMAP.md').read_text(),'C26_S0_DECISION')
 return count,errors
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));q=ap.parse_args()
 n,e=inspect(Path(q.root));print(json.dumps({'result':'PASS' if not e else 'FAIL','checks':n,'failures':len(e),'codes':e,'scope':'planning contracts only; no live provider tests'},indent=2))
 sys.exit(bool(e))
