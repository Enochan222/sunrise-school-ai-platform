from pathlib import Path
import pytest
from stage1_ci_policy import check_light_ci

# Exact workflow structure independently read at main PR26 baseline.
GOOD='''name: Stage 1 A - Light Unit and Component
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]
    paths:
      - 'apps/a-vault/**'
      - 'tests/stage1/**'
      - 'scripts/stage1/**'
permissions:
  contents: read
concurrency:
  group: stage1-light-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  stage1-light:
    if: ${{ github.event.pull_request.head.repo.full_name == github.repository }}
    runs-on: ubuntu-24.04
    timeout-minutes: 5
'''

def test_current_draft_inclusive_workflow():
    assert check_light_ci(GOOD)

@pytest.mark.parametrize('bad',[ 
    "    if: ${{ !github.event.pull_request.draft }}",
    "    branches: [develop]",
    "    types: [opened, synchronize, reopened, ready_for_review, edited]",
    "      - 'docs/**'",
    "      - 'scripts/**'",
    "  contents: write",
    "  cancel-in-progress: false",
    "    if: ${{ github.event.pull_request.head.repo.full_name != github.repository }}",
])
def test_unapproved_policy_changes_rejected(bad):
    content=GOOD
    target={'    branches: [develop]':'    branches: [main]',
            "    types: [opened, synchronize, reopened, ready_for_review, edited]":'    types: [opened, synchronize, reopened, ready_for_review]',
            "      - 'docs/**'":"      - 'apps/a-vault/**'",
            "      - 'scripts/**'":"      - 'scripts/stage1/**'",
            '  contents: write':'  contents: read',
            '  cancel-in-progress: false':'  cancel-in-progress: true',
            "    if: ${{ github.event.pull_request.head.repo.full_name != github.repository }}":
            "    if: ${{ github.event.pull_request.head.repo.full_name == github.repository }}"}
    if 'draft' in bad:content=content.replace("    if: ${{ github.event.pull_request.head.repo.full_name == github.repository }}",bad)
    else:content=content.replace(target[bad],bad)
    assert not check_light_ci(content)

@pytest.mark.parametrize('extra',["push:\n", "  pull_request_target:\n", "  schedule:\n",
    "  if: ${{ github.event.pull_request.draft }}\n", "    if: ${{ github.event.pull_request.draft }}\n"])
def test_unapproved_event_or_second_conditional_rejected(extra):
    assert not check_light_ci(GOOD+extra)

@pytest.mark.parametrize('version',['',False,None,42])
def test_invalid_workflow_source_rejected(version):
    assert not check_light_ci(version)
