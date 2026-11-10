#!/usr/bin/env python3
"""Mutation test the NEW v0.7.5 consumer-dependency rules independent of file hashes.
Uses dynamic copies of Stage registry and reuse records, checks invariants.
"""
import json, unittest
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'docs/quality/STAGE_REGISTRY.json').read_text())
reuse=json.loads((ROOT/'docs/quality/STAGE_REUSE_MAP.json').read_text())

def audit(a,b):
 reasons=[]
 for n in range(29):
  if b[n]['owner']!=a[n]['track']: reasons.append('owner')
  if b[n]['depends_on']!=a[n]['depends_on']:reasons.append('mapped-dependency')
  if any(d>=n for d in a[n]['depends_on']):reasons.append('future-dependency')
  if len(b[n]['do_not_rebuild'])<25:reasons.append('reuse-decision')
  if len(b[n]['sunrise_owner_gap'])<25:reasons.append('sunrise-gap')
 for n,expect in {21:{18,19},22:{18,20},24:{21},27:{18,20}}.items():
  if not expect.issubset(set(a[n]['depends_on'])):reasons.append('consumer-dependency')
 return reasons

class ReuseMutations(unittest.TestCase):
 def test_baseline(self):self.assertFalse(audit(reg,reuse))
 def test_01_S21_manual_marking_missing(self):
  x=deepcopy(reg);x[21]['depends_on'].remove(18);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_02_S21_ai_marking_missing(self):
  x=deepcopy(reg);x[21]['depends_on'].remove(19);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_03_staff_marking_missing(self):
  x=deepcopy(reg);x[22]['depends_on'].remove(18);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_04_staff_analytics_missing(self):
  x=deepcopy(reg);x[22]['depends_on'].remove(20);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_05_teacher_ui_must_reuse_assessment_ui(self):
  x=deepcopy(reg);x[24]['depends_on'].remove(21);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_06_year_close_needs_marking(self):
  x=deepcopy(reg);x[27]['depends_on'].remove(18);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_07_year_close_needs_memory(self):
  x=deepcopy(reg);x[27]['depends_on'].remove(20);self.assertIn('consumer-dependency',audit(x,reuse))
 def test_08_owner_mismatch(self):
  x=deepcopy(reuse);x[4]['owner']='B';self.assertIn('owner',audit(reg,x))
 def test_09_future_dep(self):
  x=deepcopy(reg);x[2]['depends_on']=[4];self.assertIn('future-dependency',audit(x,reuse))
 def test_10_missing_no_rebuild(self):
  x=deepcopy(reuse);x[1]['do_not_rebuild']='';self.assertIn('reuse-decision',audit(reg,x))
 def test_11_missing_sunrise_gap(self):
  x=deepcopy(reuse);x[1]['sunrise_owner_gap']='';self.assertIn('sunrise-gap',audit(reg,x))
if __name__=='__main__':unittest.main(verbosity=2)
