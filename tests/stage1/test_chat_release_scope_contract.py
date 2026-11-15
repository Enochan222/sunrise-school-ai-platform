"""Only the three PR24 handoff artefacts may extend AT13 release scope.

Do not allow unrelated docs/stage1 or repo governance through this exception.
"""
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import release_manifest as release


@pytest.mark.parametrize('path', [
    'docs/stage1/CHAT_ENGINEERING_COMPLETION_REPORT.md',
    'docs/stage1/PORTABLE_STAGE1_TEST_HANDOFF.md',
    'docs/stage1/WORK_OR_LOCAL_RUNTIME_HANDOFF_PROMPT.md',
    'apps/a-vault/ui.js',
    'scripts/stage1/acceptance/http_boundaries.py',
    'tests/stage1/test_chat_at14_ui_regression_contract.py',
])
def test_expected_release_scope_path_allowed(path):
    assert release.allowed_stage1_change(path)


@pytest.mark.parametrize('path', [
    'docs/stage1/IMPLEMENTATION_PLAN.md',
    'docs/stage1/SOMETHING_ELSE.md',
    'docs/stage1/PORTABLE_STAGE1_TEST_HANDOFF.md/secret',
    'docs/stage0/OWNER_APPROVAL.md',
    '.github/workflows/ci.yml',
    'apps/other-app/main.py',
    'docs/stage1/CHAT_ENGINEERING_COMPLETION_REPORT.md.bak',
])
def test_unapproved_release_scope_path_denied(path):
    assert release.allowed_stage1_change(path) is False
