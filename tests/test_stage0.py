from copy import deepcopy
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from validate_stage0 import inspect
class S0GateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.good=json.loads((ROOT/'stage0/STAGE0_BASELINE.json').read_text())
 def test_good(self):self.assertEqual(inspect(ROOT,self.good),[])
 def test_wrong_owner(self):
  b=deepcopy(self.good);b['repository']='IssacSitHk/sunrise-education-ai-platform';self.assertIn('INVALID_repository',inspect(ROOT,b))
 def test_false_approval(self):
  b=deepcopy(self.good);b['stage0_product_approval']='OWNER_APPROVED';self.assertIn('INVALID_stage0_product_approval',inspect(ROOT,b))
 def test_false_runtime(self):
  b=deepcopy(self.good);b['runtime_tests']='PASS';self.assertIn('INVALID_runtime_tests',inspect(ROOT,b))
 def test_false_source_state(self):
  b=deepcopy(self.good);b['full_master_kit_imported']=False;self.assertIn('INVALID_full_master_kit_imported',inspect(ROOT,b))
if __name__=='__main__':unittest.main()
