"""Positive and negative bootstrap tests; no claim of deployed runtime."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_stage0 import inspect

class Stage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/"stage0/STAGE0_BASELINE.json").read_text())

    def test_good_bootstrap(self):
        self.assertEqual(inspect(ROOT,self.base),[])

    def test_reject_old_github_owner(self):
        x=deepcopy(self.base);x["repository"]="IssacSitHk/sunrise-education-ai-platform"
        self.assertIn("INVALID_repository",inspect(ROOT,x))

    def test_reject_false_kit_import(self):
        x=deepcopy(self.base);x["full_master_kit_imported"]=True
        self.assertIn("BOOTSTRAP_MUST_NOT_CLAIM_KIT_IMPORTED",inspect(ROOT,x))

    def test_reject_false_stage0_approval(self):
        x=deepcopy(self.base);x["stage0_product_approval"]="OWNER_APPROVED"
        self.assertIn("BOOTSTRAP_MUST_NOT_CLAIM_APPROVAL",inspect(ROOT,x))

    def test_reject_candidate_without_real_kit(self):
        x=deepcopy(self.base)
        x["master_kit_phase"]="MASTER_CANDIDATE"
        x["full_master_kit_imported"]=True
        self.assertTrue(any(e.startswith("MISSING_MASTER:") for e in inspect(ROOT,x)))

if __name__=="__main__":
    unittest.main()
