#!/usr/bin/env python3
"""In-memory adversarial state models ONLY; NOT real SQL/API/cryptographic tests."""
import unittest,json,hashlib,copy,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class Vault:
 def __init__(self):self.shells={};self.create_ops={};self.sources={};self.cutover='STANDALONE'
 def create(self,key,op,body='x',service=False):
  h=hashlib.sha256(body.encode()).hexdigest()
  if op in self.create_ops:
   prev=self.create_ops[op]
   if prev['hash']!=h:raise ValueError('409 same key different body')
   return prev['shell']
  if self.cutover=='FREEZE' or self.cutover=='MANAGED' and not service:raise PermissionError('create policy')
  if key in self.shells:raise ValueError('existing key different operation')
  shell={'id':'A-'+key,'external_key':key,'notebook_id':'NB-'+key,'status':'READY'}
  self.shells[key]=shell;self.create_ops[op]={'hash':h,'shell':shell};return shell
 def source(self,shell_key,source_id,version,content_hash,public=True):
  if source_id in self.sources and self.sources[source_id]['owner']!=shell_key:raise PermissionError('cross-shell source')
  self.sources[source_id]={'owner':shell_key,'version':version,'hash':content_hash,'public':public}
 def lookup(self,key,source):
  if not key or key not in self.shells:raise PermissionError('empty/unknown scope')
  data=self.sources.get(source)
  if not data or data['owner']!=key:raise PermissionError('source owner mismatch')
  return data

class Core:
 def __init__(self):self.courses={};self.operations={};self.bindings={};self.used_a={}
 def new_course(self,key):return self.courses.setdefault(key,{'course_id':'C-'+key,'status':'CONTENT_UNLINKED'})
 def reserve(self,mode,course_key,op,link_key,body='x'):
  h=hashlib.sha256(body.encode()).hexdigest()
  if op in self.operations:
   prior=self.operations[op]
   if prior['hash']!=h or prior['link_key']!=link_key:raise ValueError('409 body mismatch')
   return prior
  if mode=='ADOPT_EXISTING' and course_key not in self.courses:raise ValueError('cannot adopt nonexisting B Course')
  # Simulates the one B SQL transaction: if insertion of op fails, course also rolls back.
  proposed_courses=copy.deepcopy(self.courses);proposed_courses.setdefault(course_key,{'course_id':'C-'+course_key,'status':'CONTENT_UNLINKED'})
  record={'mode':mode,'course_key':course_key,'link_key':link_key,'status':'RESERVED','hash':h}
  self.courses=proposed_courses;self.operations[op]=record
  return record
 def finalize(self,op,shell,source_manifest=None):
  r=self.operations[op];course=r['course_key'];a_key=shell['external_key']
  if course in self.bindings:
   if self.bindings[course]!=a_key:raise ValueError('409 Course different Shell')
   return self.bindings[course]
  if a_key in self.used_a:raise ValueError('409 Shell already bound')
  if r['link_key']!=a_key:raise ValueError('409 link key mismatch')
  self.bindings[course]=a_key;self.used_a[a_key]=course;r['status']='ACTIVE';self.courses[course]['status']='ACTIVE'
  return a_key

class Bridge:
 def __init__(self,vault,core):self.a=vault;self.b=core # Bridge has NO durable own store.
 def create(self,course_key,op):
  link='link-'+course_key
  self.b.reserve('CREATE_NEW',course_key,op,link,body=course_key)
  shell=self.a.create(link,op,body=course_key,service=True)
  return self.b.finalize(op,shell)
 def adopt(self,course_key,existing_shell_key,op):
  self.b.reserve('ADOPT_EXISTING',course_key,op,existing_shell_key,body=course_key+'|'+existing_shell_key)
  return self.b.finalize(op,self.a.shells[existing_shell_key])

class GradeLedger:
 def __init__(self):self.events=[];self.revisions={};self.opids={}
 def submit(self,key,score,op,actor='admin'):
  canonical=json.dumps({'key':key,'score':score,'actor':actor},sort_keys=True,separators=(',',':'))
  digest=hashlib.sha256(canonical.encode()).hexdigest()
  if op in self.opids:
   if self.opids[op]!=digest:raise ValueError('409 IDEMPOTENCY_PAYLOAD_CONFLICT')
   return
  if key in self.revisions:raise ValueError('grade already submitted')
  self.opids[op]=digest;self.revisions[key]=1;self.events.append({'key':key,'score':score,'rev':1,'event':'SUBMIT'})
 def correct(self,key,score,expected_rev,reason):
  if not reason or self.revisions.get(key)!=expected_rev:raise ValueError('409 revision/reason')
  self.revisions[key]+=1;self.events.append({'key':key,'score':score,'rev':self.revisions[key],'event':'CORRECT','reason':reason})
 def current(self,key):return [e['score'] for e in self.events if e['key']==key][-1]

class Weakness:
 def __init__(self):self.history=[];self.active={}
 def keep(self,scope,version):
  a=self.active.setdefault(scope,[])
  if version not in a:a.append(version);self.history.append((scope,version))
  while len(a)>2:a.pop(0)
 def stale(self,scope,version):
  if version in self.active.get(scope,[]):self.active[scope].remove(version)

class Evidence:
 def __init__(self):self.claims={}
 def validate(self,b,now,purpose,binding_version,current_sources,auth_revision,job_id='job-1',phase='MODEL_PRE_EXECUTION'):
  # In-memory semantics only; no actual asymmetric crypto or provider permissions.
  if not b['signature_valid']:raise ValueError('invalid signature')
  if phase not in ('MODEL_PRE_EXECUTION','PAPER_PRE_APPROVAL'):raise ValueError('invalid validation phase')
  if now>=b['expires'] or b['purpose']!=purpose or b['binding_version']!=binding_version or b['auth_revision']!=auth_revision:raise ValueError('expired/stale/wrong scope')
  for src,version,sha in b['sources']:
   if current_sources.get(src)!=(version,sha):raise ValueError('revoked/changed source')
  # Evidence jti may be REVALIDATED by the SAME job in different phases. A new job cannot claim it.
  bound=self.claims.get(b['jti'])
  if bound is not None and bound!=(job_id,purpose):raise ValueError('409 different job reused Evidence jti')
  self.claims[b['jti']]=(job_id,purpose)
  return True

class TestDesignModels(unittest.TestCase):
 def setUp(self):self.a=Vault();self.b=Core()
 def test_a_idempotent(self):self.assertEqual(self.a.create('x','o'),self.a.create('x','o'));self.assertEqual(len(self.a.shells),1)
 def test_a_conflicting_request_hash(self):
  self.a.create('x','o','body')
  with self.assertRaises(ValueError):self.a.create('x','o','changed')
 def test_a_no_duplicate_same_external_key(self):
  self.a.create('x','o')
  with self.assertRaises(ValueError):self.a.create('x','other')
 def test_a_standalone_cutover(self):
  self.a.cutover='MANAGED'
  with self.assertRaises(PermissionError):self.a.create('x','o')
  self.assertEqual(self.a.create('x','o',service=True)['notebook_id'],'NB-x')
 def test_freeze_blocks_all_new_writes(self):
  self.a.cutover='FREEZE'
  with self.assertRaises(PermissionError):self.a.create('x','o',service=True)
 def test_source_cross_shell_rejected(self):
  self.a.source('x','S','v1','sha')
  with self.assertRaises(PermissionError):self.a.source('y','S','v1','sha')
 def test_empty_scope(self):
  with self.assertRaises(PermissionError):self.a.lookup('','unknown')
 def test_wrong_shell_lookup(self):
  self.a.create('x','o');self.a.source('x','S','v1','h')
  with self.assertRaises(PermissionError):self.a.lookup('y','S')
 def test_course_unlinked_before_integration(self):self.assertEqual(self.b.new_course('C')['status'],'CONTENT_UNLINKED')
 def test_b_atomic_concept_record(self):
  self.b.reserve('CREATE_NEW','C','o','link-C');self.assertIn('C',self.b.courses);self.assertIn('o',self.b.operations)
 def test_adopt_needs_existing_course(self):
  with self.assertRaises(ValueError):self.b.reserve('ADOPT_EXISTING','C','o','link')
 def test_b_reserve_retry(self):
  r=self.b.reserve('CREATE_NEW','C','o','link-C',body='x');self.assertIs(r,self.b.reserve('CREATE_NEW','C','o','link-C',body='x'))
 def test_b_idempotent_key_wrong_body_rejected(self):
  self.b.reserve('CREATE_NEW','C','o','link-C',body='x')
  with self.assertRaises(ValueError):self.b.reserve('CREATE_NEW','C','o','link-C',body='y')
 def test_i_new_course_saga(self):
  x=Bridge(self.a,self.b);x.create('C','o');self.assertEqual(self.b.bindings['C'],'link-C');self.assertEqual(len(self.a.shells),1)
 def test_i_replay_after_finalize_ack_loss(self):
  Bridge(self.a,self.b).create('C','o');Bridge(self.a,self.b).create('C','o');self.assertEqual(len(self.b.bindings),1);self.assertEqual(len(self.a.shells),1)
 def test_i_recovery_from_a_created_b_unfinished(self):
  self.b.reserve('CREATE_NEW','C','o','link-C',body='C');self.a.create('link-C','o',body='C',service=True)
  Bridge(self.a,self.b).create('C','o');self.assertEqual(self.b.operations['o']['status'],'ACTIVE')
 def test_i_adopt_does_not_create_a(self):
  self.b.new_course('C');self.a.create('legacy','opA');Bridge(self.a,self.b).adopt('C','legacy','opI');self.assertEqual(len(self.a.shells),1)
 def test_i_two_courses_cannot_bind_same_shell(self):
  self.b.new_course('C');self.b.new_course('D');self.a.create('old','opA');Bridge(self.a,self.b).adopt('C','old','opI')
  with self.assertRaises(ValueError):Bridge(self.a,self.b).adopt('D','old','op2')
 def test_i_finalized_wrong_key_conflict(self):
  self.b.reserve('CREATE_NEW','C','o','link-C');self.a.create('different','opA')
  with self.assertRaises(ValueError):self.b.finalize('o',self.a.shells['different'])
 def test_grade_submit_retry(self):
  g=GradeLedger();g.submit('k',8,'op');g.submit('k',8,'op');self.assertEqual(len(g.events),1)
 def test_grade_overwrite_rejected(self):
  g=GradeLedger();g.submit('k',8,'op')
  with self.assertRaises(ValueError):g.submit('k',9,'new')
 def test_grade_correction_preserves_original(self):
  g=GradeLedger();g.submit('k',8,'op');g.correct('k',9,1,'reason');self.assertEqual([x['score'] for x in g.events],[8,9])
 def test_grade_concurrent_cas(self):
  g=GradeLedger();g.submit('k',8,'op');g.correct('k',9,1,'reason')
  with self.assertRaises(ValueError):g.correct('k',10,1,'stale correction')
 def test_grade_correction_reason_required(self):
  g=GradeLedger();g.submit('k',8,'op')
  with self.assertRaises(ValueError):g.correct('k',9,1,'')
 def test_keep_two_only_memory(self):
  w=Weakness();[w.keep('C',i) for i in (1,2,3)];self.assertEqual(w.active['C'],[2,3]);self.assertEqual(len(w.history),3)
 def test_stale_removes_from_active_not_history(self):
  w=Weakness();w.keep('C','v1');w.stale('C','v1');self.assertEqual(w.active['C'],[]);self.assertEqual(w.history,[('C','v1')])
 def test_evidence_preuse_valid(self):
  e=Evidence();b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')]);self.assertTrue(e.validate(b,10,'paper_draft',3,{'s':('v3','h')},1))
 def test_evidence_expired_rejected(self):
  b=dict(signature_valid=True,jti='j1',expires=10,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  with self.assertRaises(ValueError):Evidence().validate(b,10,'paper_draft',3,{'s':('v3','h')},1)
 def test_evidence_version_revoked(self):
  b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  with self.assertRaises(ValueError):Evidence().validate(b,10,'paper_draft',3,{'s':('v4','h2')},1)
 def test_evidence_stale_binding(self):
  b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  with self.assertRaises(ValueError):Evidence().validate(b,10,'paper_draft',4,{'s':('v3','h')},1)
 def test_evidence_revoked_grant(self):
  b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  with self.assertRaises(ValueError):Evidence().validate(b,10,'paper_draft',3,{'s':('v3','h')},2)
 def test_evidence_replay_rejected(self):
  e=Evidence();b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')]);e.validate(b,10,'paper_draft',3,{'s':('v3','h')},1)
  with self.assertRaises(ValueError):e.validate(b,10,'paper_draft',3,{'s':('v3','h')},1,job_id='different-job')
 def test_evidence_same_job_two_phases(self):
  e=Evidence();b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  self.assertTrue(e.validate(b,10,'paper_draft',3,{'s':('v3','h')},1,job_id='job-a',phase='MODEL_PRE_EXECUTION'))
  self.assertTrue(e.validate(b,11,'paper_draft',3,{'s':('v3','h')},1,job_id='job-a',phase='PAPER_PRE_APPROVAL'))
 def test_evidence_revalidation_revoked_after_first_check(self):
  e=Evidence();b=dict(signature_valid=True,jti='j1',expires=20,purpose='paper_draft',binding_version=3,auth_revision=1,sources=[('s','v3','h')])
  e.validate(b,10,'paper_draft',3,{'s':('v3','h')},1,job_id='job-a')
  with self.assertRaises(ValueError):e.validate(b,11,'paper_draft',3,{'s':('v4','h2')},1,job_id='job-a',phase='PAPER_PRE_APPROVAL')
 def test_grade_same_key_different_payload_conflict(self):
  g=GradeLedger();g.submit('k',8,'op')
  with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_PAYLOAD_CONFLICT'):g.submit('k',9,'op')
 def test_release_one_runtime_owner(self):
  before=dict(A='a1',B='b1',I='i1',U='u1');after={**before,'I':'i2'};self.assertEqual(sum(before[k]!=after[k] for k in before),1)
 def test_mixed_release_detected(self):
  before=dict(A='a1',B='b1',I='i1',U='u1');after={**before,'A':'a2','B':'b2'};self.assertNotEqual(sum(before[k]!=after[k] for k in before),1)
 def test_stage_order_and_roles(self):
  reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertEqual(len(reg),29)
  self.assertEqual([reg[i]['track'] for i in (1,2,3,4,5,6,7,8,9,10)],list('AABIUBBBIU'))
 def test_subjects_independent(self):
  reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertEqual([reg[i]['track'] for i in (11,12,13,14)],['B']*4)
  self.assertEqual(len({reg[i]['name'] for i in (11,12,13,14)}),4)
 def test_iam_before_teacher_read(self):
  reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertIn(22,reg[23]['depends_on'])
 def test_real_pii_after_iam(self):
  reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertIn(22,reg[25]['depends_on']);self.assertIn(23,reg[25]['depends_on'])
 def test_u_gates_explicit(self):
  reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text());self.assertEqual([reg[i]['track'] for i in (5,10,21,24)],['U']*4)
 def test_machine_transitions(self):
  sm=json.loads((ROOT/'contracts/state_machines/course_binding.json').read_text());self.assertNotIn('ACTIVE',sm['transitions']['UNLINKED']);self.assertIn('VERIFYING',sm['transitions']['PROVISIONING'])

if __name__=='__main__':unittest.main(verbosity=2)
