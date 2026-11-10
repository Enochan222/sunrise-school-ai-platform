#!/usr/bin/env python3
"""Stage 0 signed-document gate. It cannot enforce GitHub PR merges (Actions off)."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = [f'D{i:02d}' for i in range(1, 9)]


def inspect(root=ROOT, baseline=None):
    root = Path(root)
    issues = []
    try:
        b = baseline if baseline is not None else json.loads(
            (root / 'stage0/STAGE0_BASELINE.json').read_text(encoding='utf-8')
        )
        if not isinstance(b, dict):
            raise ValueError('baseline must be an object')
    except (OSError, ValueError) as exc:
        return ['BASELINE_NOT_READABLE:' + str(exc)]

    expected = {
        'repository': 'Enochan222/sunrise-school-ai-platform',
        'source_repository_history_imported': False,
        'master_kit_target': 'v0.7.5',
        'master_kit_phase': 'MASTER_CANDIDATE',
        'full_master_kit_imported': True,
        'stage_count_if_imported': 29,
        'candidate_api_operations_if_imported': 100,
        'planned_acceptance_cases_if_imported': 310,
        'stage0_product_approval': 'APPROVED',
        'stage0_status': 'COMPLETE',
        'stage0_approved_decisions': DECISIONS,
        'stage1_status': 'NOT_STARTED',
        'runtime_tests': 'NOT_RUN',
        'paid_services_authorized': False,
        'runtime_deployment_authorized': False,
        'real_student_data_authorized': False,
    }
    for key, wanted in expected.items():
        if b.get(key) != wanted:
            issues.append('INVALID_' + key)

    approval = b.get('stage0_approval_evidence')
    expected_approval = {
        'date': '2026-11-10',
        'scope': 'BOUNDED_PLANNING_ARCHITECTURE_SECURITY_ONLY',
        'source': 'OWNER_EXPLICIT_CHAT_APPROVAL_RECORDED_BY_ASSISTANT',
        'github_issue': 10,
        'github_issue_comment_id': 6762722630,
    }
    if approval != expected_approval:
        issues.append('INVALID_stage0_approval_evidence')

    required = [
        'README.md', 'AGENTS.md',
        'docs/delivery/NEW_REPO_STAGE0.md',
        'docs/delivery/STAGE0_EVIDENCE_2026-11-10.md',
        'docs/delivery/STAGE1_START_CRITERIA.md',
        'docs/decisions/STAGE0_APPROVAL_DECISIONS.md',
        'docs/quality/STAGE_REGISTRY.json',
        'docs/architecture/API_INVENTORY.json',
        'docs/quality/STAGE_CONTROL_MATRIX.json',
        'docs/quality/V075_ORIGINAL_SOURCE_MANIFEST.sha256',
        'FILE_MANIFEST.sha256',
        'stage0/IMPORT_PROVENANCE.json',
    ]
    for rel in required:
        if not (root / rel).is_file():
            issues.append('MISSING:' + rel)
    for stage in range(29):
        if not (root / f'docs/stages/STAGE_{stage:02d}.md').is_file():
            issues.append('MISSING_STAGE:' + str(stage))
    for ext in ('*.yml', '*.yaml'):
        for p in (root / '.github/workflows').glob(ext):
            if p.is_file():
                issues.append('UNWANTED_GITHUB_ACTIONS:' + str(p.relative_to(root)))

    try:
        reg = json.loads((root / 'docs/quality/STAGE_REGISTRY.json').read_text())
        inv = json.loads((root / 'docs/architecture/API_INVENTORY.json').read_text())['operations']
        if len(reg) != 29 or sum(len(r['acceptance_ids']) for r in reg) != 310 or len(inv) != 100:
            issues.append('BAD_SOURCE_TOTALS')
    except (OSError, ValueError, KeyError, TypeError):
        issues.append('BAD_SOURCE_STRUCTURE')

    packet = root / 'docs/decisions/STAGE0_APPROVAL_DECISIONS.md'
    evidence = root / 'docs/delivery/STAGE0_EVIDENCE_2026-11-10.md'
    handoff = root / 'docs/delivery/STAGE1_START_CRITERIA.md'
    if packet.is_file():
        txt = packet.read_text(encoding='utf-8')
        phrases = ('**Decision state: APPROVED', 'comment `6762722630`',
                   'Confirmed decision IDs: **D01, D02, D03, D04, D05, D06, D07, D08**',
                   'NOT AUTHORIZED', 'not** an Owner-authored GitHub signature')
        for phrase in phrases:
            if phrase not in txt:
                issues.append('MISSING_SIGNOFF_PROOF:' + phrase)
    if evidence.is_file():
        txt = evidence.read_text(encoding='utf-8')
        if 'S0 DOCUMENT PLANNING COMPLETE' not in txt or 'S1 is **NOT STARTED**' not in txt:
            issues.append('STAGE0_EVIDENCE_NOT_CLOSED')
    if handoff.is_file():
        txt = handoff.read_text(encoding='utf-8')
        if ('S1 STATUS: NOT STARTED' not in txt or
                'offline/local synthetic-data experiments' not in txt or
                'hosting location' not in txt or
                'no public service' not in txt):
            issues.append('STAGE1_PREDEPLOYMENT_GATE_MISSING')
    return issues


if __name__ == '__main__':
    issues = inspect()
    print(json.dumps({
        'result': 'PASS' if not issues else 'FAIL',
        'stage0': 'BOUNDED PLANNING APPROVED; NO DEPLOYMENT/DATA AUTHORIZATION',
        'scope': 'STATIC DOCUMENT AND OWNER SIGNOFF ONLY; NO GITHUB ACTIONS; NO RUNTIME',
        'issues': issues,
    }, ensure_ascii=False, indent=2))
    sys.exit(bool(issues))
