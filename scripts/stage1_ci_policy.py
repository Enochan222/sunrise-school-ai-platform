"""Fail-closed guard for the *exact* Owner-authorized Stage 1 Light workflow.

The Owner approved one specific workflow and forbids changing its triggers,
permissions, action pins, jobs, runner or budget in the governance PR.  A
regular-expression-only YAML policy is unsafe: valid YAML has nested/job-level
permissions, flow mappings, duplicate keys and merge aliases.  Rather than
pretending that a subset parser understands GitHub Actions' effective YAML,
this guard pins the independently reviewed, unchanged workflow *bytes*.

ANY change, including an additional job, job permission, flow/block override,
YAML alias/merge, or duplicate key, must fail closed until separately reviewed
and an authorized policy amendment deliberately updates this pinned digest.
The checks below remain useful as explicit assertions of the pinned contract.
No non-standard YAML parser or network service is required.
"""
import hashlib
import re

# SHA-256 of the exact UTF-8 bytes in main's reviewed stage1-light.yml,
# GitHub blob dfbdf3cda321a98aa6cc6d3f21a12599c92d6ff5.
AUTHORIZED_LIGHT_CI_SHA256 = (
    '9b6c7916240289ac351e89f431f410623e3bc4aa80e9099481f8f50e48b60d27'
)
ALLOWED_PATHS = ('apps/a-vault/**', 'tests/stage1/**', 'scripts/stage1/**')
ALLOWED_TYPES = ('opened', 'synchronize', 'reopened', 'ready_for_review')


def check_light_ci(body):
    """Accept only the reviewed Draft-capable, same-repo, read-only workflow.

    The digest is a fail-closed *whole-document* allowlist, not a claim to
    implement a generic YAML validator.  Changing GitHub Actions YAML needs
    separate workflow authorization and a new review of the audited digest.
    """
    if not isinstance(body, str):
        return False
    try:
        digest = hashlib.sha256(body.encode('utf-8')).hexdigest()
    except UnicodeEncodeError:
        return False
    if digest != AUTHORIZED_LIGHT_CI_SHA256:
        return False
    # Defense in depth and readable approved policy, including exactly one job.
    if body.count('\npermissions:\n  contents: read\n') != 1:
        return False
    if body.count('\njobs:\n  stage1-light:\n') != 1:
        return False
    if len(re.findall(r'(?m)^\s+if:\s*', body)) != 1:
        return False
    if not re.search(
        r'(?m)^    if:\s*\$\{\{\s*github\.event\.pull_request\.head\.repo\.full_name\s*==\s*github\.repository\s*\}\}\s*$',
        body,
    ):
        return False
    if 'cancel-in-progress: true' not in body or 'persist-credentials: false' not in body:
        return False
    if not re.search(r'(?m)^on:\n  pull_request:\n    branches: \[main\]$', body):
        return False
    if not re.search(r'(?m)^    types: \[opened, synchronize, reopened, ready_for_review\]$', body):
        return False
    for path in ALLOWED_PATHS:
        if f"      - '{path}'" not in body:
            return False
    return True
