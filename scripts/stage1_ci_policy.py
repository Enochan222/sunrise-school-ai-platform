"""Static fail-closed guard for the 2026-11-14 *Draft-inclusive* Light CI.

This is a semantic check of the exact authorized workflow, not an Actions run.
The historical D08 remains untouched; only Stage1 Limited CI amendment applies.
"""
import re

ALLOWED_PATHS=("apps/a-vault/**","tests/stage1/**","scripts/stage1/**")
ALLOWED_TYPES=('opened','synchronize','reopened','ready_for_review')


def check_light_ci(body):
    """Require only the narrowly approved PR trigger and same-repo read-only job."""
    if not isinstance(body,str):return False
    if re.search(r'(?m)^\s*if:\s*.*github\.event\.pull_request\.draft',body):return False
    if re.search(r'\$\{\{\s*secrets\.',body):return False
    if re.search(r'(?m)^\s*(?:push|schedule|pull_request_target|workflow_run|workflow_call)\s*:',body):return False
    if not re.search(r'(?m)^on:\s*\n  pull_request:\s*$',body):return False
    if not re.search(r'(?m)^    branches:\s*\[main\]\s*$',body):return False
    types=re.findall(r'(?m)^    types:\s*\[([^\]]+)\]\s*$',body)
    if len(types)!=1 or tuple(x.strip() for x in types[0].split(','))!=ALLOWED_TYPES:return False
    path_block=re.search(r'(?m)^    paths:\s*\n((?:      - .*\n)+)',body)
    if not path_block:return False
    paths=tuple(re.findall(r"(?m)^      - ['\"]([^'\"]+)['\"]\s*$",path_block.group(1)))
    if paths!=ALLOWED_PATHS:return False
    if not re.search(r'(?m)^permissions:\s*\n  contents:\s*read\s*$',body):return False
    if 'cancel-in-progress: true' not in body:return False
    if not re.search(r'(?m)^\s*if:\s*\$\{\{\s*github\.event\.pull_request\.head\.repo\.full_name\s*==\s*github\.repository\s*\}\}\s*$',body):return False
    # A second condition can weaken the same-repo boundary or skip Draft.
    if len(re.findall(r'(?m)^\s*if:\s*',body))!=1:return False
    return True
