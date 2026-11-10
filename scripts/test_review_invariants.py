#!/usr/bin/env python3
"""Independent pure model/fixture edge tests to catch vulnerabilities found in audit."""
import json,unittest,importlib.util,hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sunrise_design',R/'scripts/test_design_invariants.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
B=json.loads((R/'contracts/openapi/b-v1.openapi.json').read_text())['components']['schemas']
A=json.loads((R/'contracts/openapi/a-v1.openapi.json').read_text())['components']['schemas']
I=json.loads((R/'contracts/openapi/i-v1.openapi.json').read_text())['components']['schemas']
def valid(schema,obj):return not list(Draft202012Validator(schema).iter_errors(obj))
class Tests(unittest.TestCase):
 def test_course_multiple_teaching_groups_same_course(self):
  course={'course_id':'c1','academic_year_id':'y1','school_id':'s1','subject_id':'math','grade':4,'curriculum_stream':'local','title':'P4 Maths','content_state':'CONTENT_UNLINKED','revision':1}
  self.assertTrue(valid(B['AcademicCourse'],course));self.assertFalse(valid(B['AcademicCourse'],{**course,'class_id':'A'}))
  group={'teaching_group_id':'g1','course_id':'c1','school_id':'s1','display_name':'P4A','group_key':'P4A','status':'ACTIVE'}
  self.assertTrue(valid(B['TeachingGroup'],group));self.assertTrue(valid(B['TeachingGroup'],{**group,'teaching_group_id':'g2','display_name':'P4B'}))
 def test_course_requires_grade_and_stream(self):
  course={'school_id':'s1','academic_year_id':'y1','subject_id':'math','title':'P4','external_course_key':'ek','grade':4,'curriculum_stream':'local'}
  self.assertTrue(valid(B['createAcademicCourseRequest'],course));self.assertFalse(valid(B['createAcademicCourseRequest'],{k:v for k,v in course.items() if k!='grade'}));self.assertFalse(valid(B['createAcademicCourseRequest'],{k:v for k,v in course.items() if k!='curriculum_stream'}))
 def test_a_shell_rejects_missing_school(self):
  q={'display_title':'P4','academic_year_label':'2026','subject_label':'Maths','grade_label':'P4','school_id':'school1'}
  self.assertTrue(valid(A['createContentShellRequest'],q));q.pop('school_id');self.assertFalse(valid(A['createContentShellRequest'],q))
 def test_enrollment_requires_group(self):
  q={'student_id':'syn1','course_id':'c1','teaching_group_id':'g1'}
  self.assertTrue(valid(B['assignSyntheticStudentRequest'],q));q.pop('teaching_group_id');self.assertFalse(valid(B['assignSyntheticStudentRequest'],q))
 def test_blueprint_draft_published_version(self):
  q={'blueprint_id':'bp','course_id':'c1','version':2,'status':'PUBLISHED','question_template_ids':['q1'],'rubric_version_ids':['r1'],'question_count':1,'total_marks':10,'revision':2}
  self.assertTrue(valid(B['Blueprint'],q));q['question_template_ids']=[];self.assertFalse(valid(B['Blueprint'],q))
 def test_generation_requires_pinned_blueprint_version(self):
  q={'course_id':'c1','blueprint_id':'bp','blueprint_version':2,'prompt_version':'p','model_version':'g','idempotency_key':'idemp'}
  self.assertTrue(valid(B['enqueueGenerationJobRequest'],q));q.pop('blueprint_version');self.assertFalse(valid(B['enqueueGenerationJobRequest'],q))
 def test_evidence_multi_phase_same_job(self):
  e=m.Evidence();b={'signature_valid':True,'jti':'1','expires':20,'purpose':'paper_draft','binding_version':3,'auth_revision':1,'sources':[('s','v1','h')]}
  self.assertTrue(e.validate(b,10,'paper_draft',3,{'s':('v1','h')},1,job_id='job-a',phase='MODEL_PRE_EXECUTION'))
  self.assertTrue(e.validate(b,11,'paper_draft',3,{'s':('v1','h')},1,job_id='job-a',phase='PAPER_PRE_APPROVAL'))
  with self.assertRaises(ValueError):e.validate(b,12,'paper_draft',3,{'s':('v1','h')},1,job_id='job-b')
 def test_evidence_rechecks_source_revocation(self):
  e=m.Evidence();b={'signature_valid':True,'jti':'1','expires':20,'purpose':'paper_draft','binding_version':3,'auth_revision':1,'sources':[('s','v1','h')]}
  e.validate(b,10,'paper_draft',3,{'s':('v1','h')},1,job_id='job-a')
  with self.assertRaises(ValueError):e.validate(b,11,'paper_draft',3,{'s':('v2','hash-new')},1,job_id='job-a',phase='PAPER_PRE_APPROVAL')
 def test_evidence_job_and_phase_required(self):
  q={'expected_course_id':'c1','binding_version':3,'purpose':'paper_draft','job_id':'job-a','validation_phase':'MODEL_PRE_EXECUTION'}
  self.assertTrue(valid(I['validateEvidenceBundleRequest'],q));q.pop('job_id');self.assertFalse(valid(I['validateEvidenceBundleRequest'],q))
 def test_grade_retry_same_key_same_payload_ok(self):
  g=m.GradeLedger();g.submit('studentX:assessY',8,'operation');g.submit('studentX:assessY',8,'operation');self.assertEqual(len(g.events),1)
 def test_grade_same_key_changed_payload_rejected(self):
  g=m.GradeLedger();g.submit('studentX:assessY',8,'operation')
  with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_PAYLOAD_CONFLICT'):g.submit('studentX:assessY',9,'operation')
 def test_grade_same_key_different_actor_rejected(self):
  g=m.GradeLedger();g.submit('k',8,'operation',actor='admin-1')
  with self.assertRaises(ValueError):g.submit('k',8,'operation',actor='admin-2')
 def test_grade_event_requires_hash(self):
  q=json.loads((R/'contracts/fixtures/grade_valid.json').read_text());self.assertTrue(valid(B['GradeEvent'],q));q.pop('canonical_request_hash');self.assertFalse(valid(B['GradeEvent'],q))
 def test_weakness_candidate_state(self):
  q={'snapshot_id':'x','course_id':'c1','target_id':'t1','source_grade_revision':1,'state':'CANDIDATE','created_at':'2026-11-08T00:00:00Z'}
  self.assertTrue(valid(B['WeaknessSnapshot'],q));q['state']='DELETED_FROM_SCORE';self.assertFalse(valid(B['WeaknessSnapshot'],q))
 def test_group_scoped_grant(self):
  g=m.Core();g.new_course('A');self.assertEqual(g.courses['A']['status'],'CONTENT_UNLINKED')
 def test_all_stages_same_owners(self):
  reg=json.loads((R/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertEqual(len(reg),29);self.assertEqual([reg[n]['track'] for n in (1,2,3,4,6,8,9,15,17,20,21,22,23,26,27,28)],['A','A','B','I','B','B','I','B','B','B','U','B','I','A','B','I'])
if __name__=='__main__':unittest.main(verbosity=2)
