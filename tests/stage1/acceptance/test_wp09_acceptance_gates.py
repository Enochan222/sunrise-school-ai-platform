"""WP09 purely local fail-closed verdict tests. IMPLEMENTED_UNTESTED.

These checks are not the real Docker/Native acceptance. Tests not executed
during Owner's coding-only sprint.
"""
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import run_stage1 as r


def full_component_journey():
    return {
        'admin_login_and_private_session':'PASS',
        'surreal_durable_native_notebook_unique':'PASS',
        'same_key_replay_and_body_conflict':'PASS',
        'native_pdf_upload_original_sha':'PASS',
        'worker_extracted_synthetic_pdf':'PASS',
        'server_scoped_text_only_search':'PASS',
        'original_pdf_hash_and_authorization':'PASS',
        'archive_non_destructive':'PASS',
        'logout_session_revocation':'PASS'}


def test_partial_native_journey_never_passes_formal_at01():
    incomplete={'result':'PARTIAL_PASSED_WITH_UNRUN_GATES',
                'formal_s1_at01_15':'NOT_RUN',
                'results':full_component_journey()}
    assert r.test_result('S1-AT01',incomplete) is False


def test_all_passing_component_claims_without_browser_restore_or_school_never_pass_at01():
    data={'result':'FULL_NATIVE_UI_HTTP_JOURNEY_PASS',
          'formal_s1_at01_15':'S1-AT01_CANDIDATE_EXECUTED',
          'results':full_component_journey()}
    assert r.test_result('S1-AT01',data) is False
    data['results'].update({
        'gateway_restart_persistence':'PASS',
        'school_b_separate_gateway_negative':'PASS',
        'independent_backup_restore':'PASS',
        'browser_admin_journey':'PASS'})
    assert r.test_result('S1-AT01',data) is True


def test_ackloss_requires_real_journal_status_and_native_gate():
    valid={'status':'PASS','native_gate':'PASS',
        'results':{key:'PASS' for key in (
            'real_surrealdb_unique_operation_reservation',
            'different_body_conflict',
            'same_key_concurrent_no_second_reservation',
            'real_native_crash_after_create_before_journal_commit',
            'marker_reconciliation_unique_mapping',
            'same_key_replay_original_notebook')}}
    valid['results']['real_native_lost_ack_tcp']={
        'native_create_posts':1,'client_received_post_ack':False}
    assert r.test_result('S1-AT06',valid) is True
    valid['native_gate']='NOT_RUN'
    assert r.test_result('S1-AT06',valid) is False
    valid['native_gate']='PASS'
    valid['results']['real_native_lost_ack_tcp']['native_create_posts']=2
    assert r.test_result('S1-AT06',valid) is False


def test_native_graph_must_have_link_unlink_duplicate_and_hash():
    claim={'status':'PASS','native_unlink':'PASS',
           'native_link_and_duplicate':'PASS',
           'original_hash_preserved':'PASS'}
    assert r.test_result('S1-AT11',claim) is True
    claim['original_hash_preserved']='NOT_RUN'
    assert r.test_result('S1-AT11',claim) is False


def test_scenario_cannot_override_evidence_destination_or_pass_arrays():
    with pytest.raises(r.IncompleteAT):
        r.pairs({'--out':'/tmp/passed.json'})
    with pytest.raises(r.IncompleteAT):
        r.pairs({'--flags':['--skip-tests']})
    with pytest.raises(r.IncompleteAT):
        r.pairs({'--bad arg':'x'})
    assert r.pairs({'--project':'synthetic-test'})==['--project','synthetic-test']
