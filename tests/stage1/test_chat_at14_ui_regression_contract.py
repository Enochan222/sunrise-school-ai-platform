"""Non-native contract checks for AT14 and UI session hydration.

The real HTTPS/JWT and Firefox journeys remain Runtime-only evidence.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_service_jwt_acceptance_requires_all_negative_claims_and_private_clients():
    source = (ROOT / 'scripts/stage1/acceptance/http_boundaries.py').read_text()
    at14 = source.split('def case_14(', 1)[1].split('def case_15(', 1)[0]
    for name in ('EXPIRED', 'WRONG_AUDIENCE', 'WRONG_SCOPE', 'FOREIGN_SCHOOL',
                 'INVALID_SIGNATURE', 'NOT_YET_VALID', 'MISSING_CLAIMS'):
        assert 'VAULT_TEST_SERVICE_' + name in at14
    assert 'follow_redirects=False' in at14
    assert "trust_env=False" in at14
    assert "set(owned)==set(by_id)" in at14
    assert "actual.get('sha256')==baseline.get('sha256')" in at14


def test_admin_search_cannot_start_while_session_hydrates():
    source = (ROOT / 'apps/a-vault/ui.js').read_text()
    sync = source.split('function syncControls() {', 1)[1].split('function renderList()', 1)[0]
    assert "$('search-submit').disabled = state.sessionBusy || " in sync
    search = source.split('async function search(event) {', 1)[1].split('async function ', 1)[0]
    assert 'if (!state.session || state.sessionBusy || !id || state.searching) return;' in search


def test_formal_regression_runs_complete_tests_directory():
    source = (ROOT / 'scripts/stage1/acceptance/regression.py').read_text()
    assert "'-q','tests']" in source
