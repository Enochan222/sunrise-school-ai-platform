"""Adversarial policy tests using the real, complete, approved Actions YAML.

Modified variants are syntactically valid GitHub Actions YAML (including the
ambiguous YAML forms that the fail-closed digest deliberately rejects).
"""
from pathlib import Path
import hashlib
import pytest
from stage1_ci_policy import AUTHORIZED_LIGHT_CI_SHA256, check_light_ci

GOOD = (Path(__file__).resolve().parents[1] / '.github/workflows/stage1-light.yml').read_text(encoding='utf-8')


def with_job(text):
    return GOOD.replace('    runs-on: ubuntu-24.04\n', text + '    runs-on: ubuntu-24.04\n', 1)


def with_step(text):
    return GOOD.replace('    steps:\n', '    steps:\n' + text, 1)


def test_current_authorized_workflow_and_draft_same_repo():
    assert hashlib.sha256(GOOD.encode('utf-8')).hexdigest() == AUTHORIZED_LIGHT_CI_SHA256
    assert check_light_ci(GOOD)
    assert 'github.event.pull_request.draft' not in GOOD
    assert 'github.event.pull_request.head.repo.full_name == github.repository' in GOOD
    assert 'types: [opened, synchronize, reopened, ready_for_review]' in GOOD


@pytest.mark.parametrize('variant', [
    pytest.param(with_job('    permissions: {contents: write}\n'), id='inline-job-contents-write'),
    pytest.param(with_job('    permissions:\n      contents: write\n'), id='block-job-contents-write'),
    pytest.param(with_job('    permissions: {id-token: write}\n'), id='inline-job-id-token-write'),
    pytest.param(with_job('    permissions:\n      id-token: write\n'), id='block-job-id-token-write'),
    pytest.param(with_job('    permissions: {actions: write}\n'), id='inline-job-actions-write'),
    pytest.param(with_job('    permissions:\n      actions: write\n'), id='block-job-actions-write'),
    pytest.param(with_job('    permissions: write-all\n'), id='job-write-all'),
    pytest.param(GOOD.replace('permissions:\n  contents: read\n', 'permissions: write-all\n', 1), id='root-write-all'),
    pytest.param(GOOD.replace('permissions:\n  contents: read\n', 'permissions: {contents: write}\n', 1), id='inline-root-write'),
    pytest.param(GOOD.replace('permissions:\n  contents: read\n', 'permissions:\n  contents: write\n', 1), id='block-root-write'),
    pytest.param(GOOD + '\npermissions: {contents: write}\n', id='duplicate-root-permissions'),
    pytest.param(with_job('    permissions: {contents: read}\n    permissions: {contents: write}\n'), id='duplicate-job-permissions'),
    pytest.param(GOOD + '\njobs:\n  elevated:\n    runs-on: ubuntu-24.04\n    permissions: {contents: write}\n    steps:\n      - run: echo synthetic\n', id='duplicate-jobs-key'),
    pytest.param(GOOD + '\nextra_unused: null\n', id='unapproved-root-key'),
    pytest.param(GOOD + '\n', id='benign-edit-still-must-review'),
    pytest.param(GOOD.replace('  stage1-light:\n', '  stage1-light: &safe_job\n', 1) + '  elevated:\n    <<: *safe_job\n    permissions: {contents: write}\n', id='yaml-job-anchor-merge'),
    pytest.param(GOOD.replace('jobs:\n', 'jobs:\n  elevated:\n    runs-on: ubuntu-24.04\n    permissions: {id-token: write}\n    steps:\n      - run: echo synthetic\n', 1), id='additional-elevated-job'),
    pytest.param(GOOD.replace('jobs:\n', 'jobs:\n  harmless:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: echo synthetic\n', 1), id='additional-unreviewed-job'),
    pytest.param(GOOD.replace('on:\n  pull_request:', 'on:\n  push:\n    branches: [main]\n  pull_request:', 1), id='add-push-event'),
    pytest.param(GOOD.replace('on:\n  pull_request:', 'on:\n  schedule:\n    - cron: "0 2 * * *"\n  pull_request:', 1), id='add-schedule-event'),
    pytest.param(GOOD.replace('on:\n  pull_request:', 'on:\n  pull_request_target:\n    branches: [main]\n  pull_request:', 1), id='add-target-event'),
    pytest.param(GOOD.replace('on:\n  pull_request:', 'on:\n  workflow_call:\n  pull_request:', 1), id='add-workflow-call'),
    pytest.param(GOOD.replace('    branches: [main]', '    branches: [develop]', 1), id='branch-change'),
    pytest.param(GOOD.replace('    types: [opened, synchronize, reopened, ready_for_review]', '    types: [opened, synchronize, reopened, ready_for_review, edited]', 1), id='extra-event-type'),
    pytest.param(GOOD.replace("      - 'apps/a-vault/**'", "      - 'docs/**'", 1), id='paths-widen'),
    pytest.param(GOOD.replace("      - 'scripts/stage1/**'", "      - 'scripts/**'", 1), id='scripts-widen'),
    pytest.param(GOOD.replace('    if: ${{ github.event.pull_request.head.repo.full_name == github.repository }}', '    if: ${{ github.event.pull_request.head.repo.full_name != github.repository }}', 1), id='fork-guard-invert'),
    pytest.param(GOOD.replace('    if: ${{ github.event.pull_request.head.repo.full_name == github.repository }}', '    if: ${{ !github.event.pull_request.draft }}', 1), id='skip-draft'),
    pytest.param(GOOD.replace('  cancel-in-progress: true', '  cancel-in-progress: false', 1), id='disable-concurrency-cancel'),
    pytest.param(GOOD.replace('persist-credentials: false', 'persist-credentials: true', 1), id='persist-github-token'),
    pytest.param(GOOD.replace('    timeout-minutes: 5', '    timeout-minutes: 60', 1), id='extend-timeout'),
    pytest.param(GOOD.replace('    runs-on: ubuntu-24.04', '    runs-on: self-hosted', 1), id='runner-change'),
    pytest.param(GOOD.replace('11bd71901bbe5b1630ceea73d27597364c9af683', 'v4', 1), id='floating-checkout-action'),
    pytest.param(with_step('      - name: Unapproved deployment\n        run: echo deploy\n'), id='additional-step'),
    pytest.param(with_step('      - name: Read secrets\n        env:\n          API_KEY: ${{ secrets.SYNTHETIC_KEY }}\n        run: echo synthetic\n'), id='secrets-exposure'),
    pytest.param(GOOD.replace('  pull_request:\n', '  pull_request: &pr\n', 1).replace('permissions:\n  contents: read', 'permissions:\n  contents: read', 1) + '\non: {pull_request: *pr}\n', id='duplicate-on-alias'),
])
def test_valid_yaml_security_and_scope_mutations_rejected(variant):
    assert variant != GOOD
    assert not check_light_ci(variant)


@pytest.mark.parametrize('variant', ['', False, None, 42, {}, b'name: bad', '\ud800'])
def test_invalid_inputs_rejected(variant):
    assert not check_light_ci(variant)
