"""Signed Stage0 contract invariants; no runtime services are claimed."""
from copy import deepcopy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_stage0 import inspect


class S0GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = json.loads((ROOT / 'stage0/STAGE0_BASELINE.json').read_text())

    def expect_rejection(self, key, value):
        altered = deepcopy(self.good)
        altered[key] = value
        self.assertIn('INVALID_' + key, inspect(ROOT, altered))

    def test_good_signed_stage0(self):
        self.assertEqual(inspect(ROOT, self.good), [])

    def test_wrong_owner(self):
        self.expect_rejection('repository', 'IssacSitHk/sunrise-education-ai-platform')

    def test_missing_owner_approval(self):
        self.expect_rejection('stage0_product_approval', 'PENDING')

    def test_invalid_approval_alias(self):
        self.expect_rejection('stage0_product_approval', 'OWNER_APPROVED')

    def test_missing_decision(self):
        self.expect_rejection('stage0_approved_decisions', self.good['stage0_approved_decisions'][:-1])

    def test_duplicate_decision(self):
        self.expect_rejection('stage0_approved_decisions', self.good['stage0_approved_decisions'] + ['D08'])

    def test_false_approval_evidence(self):
        bad = deepcopy(self.good['stage0_approval_evidence'])
        bad['github_issue_comment_id'] = 123
        self.expect_rejection('stage0_approval_evidence', bad)

    def test_false_runtime_success(self):
        self.expect_rejection('runtime_tests', 'PASS')

    def test_false_stage1_start(self):
        self.expect_rejection('stage1_status', 'DEPLOYED')

    def test_fake_stage0_completion_without_evidence(self):
        self.expect_rejection('stage0_status', 'PENDING')

    def test_false_source_state(self):
        self.expect_rejection('full_master_kit_imported', False)

    def test_unauthorized_paid_services(self):
        self.expect_rejection('paid_services_authorized', True)

    def test_unauthorized_deployment(self):
        self.expect_rejection('runtime_deployment_authorized', True)

    def test_unauthorized_student_data(self):
        self.expect_rejection('real_student_data_authorized', True)


if __name__ == '__main__':
    unittest.main()
