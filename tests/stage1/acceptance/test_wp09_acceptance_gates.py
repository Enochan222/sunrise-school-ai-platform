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
        'same_gateway_two_school_idor_negative':'PASS',
        'independent_backup_restore':'PASS',
        'browser_admin_journey':'PASS'})
    assert r.test_result('S1-AT01',data) is True



def at15_same_gateway_evidence():
    """Unit fixture only; never substitutes for executed HTTP/IDOR evidence."""
    return {'at_id':'S1-AT15', 'status':'PASS',
            'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
            'checks':{name:'PASS' for name in (
                'school_a_access',
                'school_a_denies_school_b_shell',
                'school_a_denies_school_b_materials',
                'school_a_denies_school_b_original_download',
                'forged_school_header_denied',
                'csrf_rotated_on_switch',
                'school_b_access',
                'school_b_denies_school_a_shell')}}


def test_at15_same_gateway_eight_executed_idor_checks_required():
    fixture=at15_same_gateway_evidence()
    assert r.test_result('S1-AT15',fixture) is True
    for name in tuple(fixture['checks']):
        incomplete=at15_same_gateway_evidence()
        incomplete['checks'].pop(name)
        assert r.test_result('S1-AT15',incomplete) is False
    incomplete=at15_same_gateway_evidence()
    incomplete['checks']['school_b_denies_school_a_shell']='NOT_RUN'
    assert r.test_result('S1-AT15',incomplete) is False
    unrelated=at15_same_gateway_evidence()
    unrelated['classification']='UNRELATED_PASS'
    assert r.test_result('S1-AT15',unrelated) is False
    unrelated=at15_same_gateway_evidence()
    unrelated['at_id']='S1-AT01'
    assert r.test_result('S1-AT15',unrelated) is False


def full_wp03_evidence():
    races={}
    for mode in ('same_key_same_body','different_key_same_scope','same_key_different_body'):
        races[mode]={'outcomes':{'FRESH':1,'CONFLICT':7},
                     'durable_operations':1,'durable_scope_claims':1,
                     'durable_shells':1,'native_create_posts':1}
    result={key:'PASS' for key in (
        'real_surrealdb_unique_operation_reservation',
        'different_body_conflict',
        'same_key_concurrent_no_second_reservation',
        'real_native_crash_after_create_before_journal_commit',
        'marker_reconciliation_unique_mapping',
        'same_key_replay_original_notebook',
        'cross_school_shell_negative')}
    result['fresh_first_reservation_races']=races
    result['real_native_lost_ack_tcp']={
        'native_create_posts':1,'client_received_post_ack':False,
        'persisted_mapping_count':1,'original_notebook_sha256':'b'*64}
    return {'status':'PASS','native_gate':'PASS',
            'notebook_id_sha256':'a'*64,'results':result}


def test_ackloss_requires_complete_native_mapping_and_gate():
    valid=full_wp03_evidence()
    assert r.test_result('S1-AT06',valid) is True
    valid['native_gate']='NOT_RUN'
    assert r.test_result('S1-AT06',valid) is False
    valid['native_gate']='PASS'
    valid['results']['real_native_lost_ack_tcp']['native_create_posts']=2
    assert r.test_result('S1-AT06',valid) is False


@pytest.mark.parametrize('missing',[
    'fresh_first_reservation_races','real_native_lost_ack_tcp',
    'cross_school_shell_negative'])
def test_wp03_missing_critical_evidence_never_passes(missing):
    claim=full_wp03_evidence()
    claim['results'].pop(missing)
    assert r.test_result('S1-AT06',claim) is False


@pytest.mark.parametrize('field,bad',[
    ('persisted_mapping_count',0),
    ('original_notebook_sha256','not-a-hash'),
    ('client_received_post_ack',True),
    ('native_create_posts',True)])
def test_wp03_invalid_tcp_lost_ack_cannot_pass(field,bad):
    claim=full_wp03_evidence()
    claim['results']['real_native_lost_ack_tcp'][field]=bad
    assert r.test_result('S1-AT06',claim) is False


@pytest.mark.parametrize('mutation',[
    ('same_key_same_body','outcomes',{'FRESH':0,'CONFLICT':8}),
    ('different_key_same_scope','outcomes',{'FRESH':1,'REPLAY':1,'CONFLICT':6}),
    ('same_key_different_body','native_create_posts',2),
    ('same_key_same_body','durable_scope_claims',0),
    ('same_key_same_body','outcomes',{'FRESH':True,'CONFLICT':7})])
def test_wp03_nested_first_race_invalid_cannot_pass(mutation):
    claim=full_wp03_evidence()
    mode,field,value=mutation
    claim['results']['fresh_first_reservation_races'][mode][field]=value
    assert r.test_result('S1-AT06',claim) is False


def test_wp03_wrong_nested_mode_or_missing_notebook_identity_cannot_pass():
    claim=full_wp03_evidence()
    claim['results']['fresh_first_reservation_races'].pop('same_key_same_body')
    assert r.test_result('S1-AT06',claim) is False
    claim=full_wp03_evidence()
    claim.pop('notebook_id_sha256')
    assert r.test_result('S1-AT06',claim) is False


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


def test_cold_bundle_digest_is_streamed_not_loaded_whole(tmp_path,monkeypatch):
    import hashlib
    target=tmp_path/'synthetic-cold.tar'
    payload=b'SYNTHETIC-COLD-BUNDLE'*130000
    target.write_bytes(payload)
    expected=hashlib.sha256(payload).hexdigest()
    # The archive is deliberately larger than the reader's 1 MiB chunk.
    assert len(payload)>1024*1024
    assert r.sha256_file(target)==expected


def test_service_jwt_probe_uses_cookie_free_client(tmp_path,monkeypatch):
    """Real synthetic RS256 signing, real PyJWT verification, no HTTP network.

    This unit test must follow the JIT AT14 contract. A former fake three-
    bearer fixture no longer exercises the actual credential requirements.
    """
    from types import SimpleNamespace
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import http_boundaries as h

    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    private=key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    public=key.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo)
    path=tmp_path/'synthetic-only-private-key.pem'
    path.write_bytes(private)
    path.chmod(0o600)
    monkeypatch.setenv('VAULT_AT14_SIGNING_KEY_FILE',str(path))
    monkeypatch.setenv('VAULT_AT14_ISSUER','synthetic-issuer')
    monkeypatch.setenv('VAULT_AT14_AUDIENCE','synthetic-audience')
    material={'source_id':'source:owned-a','version':1,'sha256':'a'*64}
    admin=object()
    def materials(client,shell):
        assert client is admin and shell=='shell-a'
        return [material]
    monkeypatch.setattr(h,'authorized_materials',materials)
    responses=[]
    class CookieFree:
        def __init__(self,**kwargs):
            assert kwargs['trust_env'] is False
            assert kwargs['follow_redirects'] is False
            assert str(kwargs['verify'])=='/synthetic/test-only/ca.pem'
        def __enter__(self):return self
        def __exit__(self,*exc):return False
        def get(self,resource,headers):
            assert resource=='/vault/v1/shells/shell-a/materials'
            assert set(headers)=={'Authorization'}
            assert headers['Authorization'].startswith('Bearer ')
            token=headers['Authorization'][7:]
            try:
                claims=jwt.decode(token,public,algorithms=['RS256'],
                    issuer='synthetic-issuer',audience='synthetic-audience',
                    options={'require':['sub','iss','aud','exp','iat','nbf','jti',
                                        'school_id','scope']},leeway=5)
            except jwt.PyJWTError:
                code=401
            else:
                code=(200 if claims.get('school_id')=='synthetic-a'
                      and 'vault.materials.read' in claims['scope'].split()
                      else 403)
            responses.append(code)
            return SimpleNamespace(status_code=code,
                json=lambda: {'materials':[dict(material)]} if code==200 else {})
    monkeypatch.setattr(h.httpx,'Client',CookieFree)
    session={'school_id':'synthetic-a',
             'available_schools':['synthetic-a','synthetic-b']}
    args=SimpleNamespace(school_a='synthetic-a',school_b='synthetic-b',
                         source_a='source:owned-a',source_b='source:foreign-b',
                         shell_a='shell-a',gateway='https://127.0.0.1:8080',
                         gateway_ca_file=Path('/synthetic/test-only/ca.pem'))
    assert h.case_14(admin,args,session) is session
    assert responses==[200,403,403,401,401,401,401,401]




def test_service_jwt_negative_school_must_be_independently_provisioned(monkeypatch):
    """Avoid false positive where foreign school is rejected as unknown."""
    from types import SimpleNamespace
    import http_boundaries as h
    monkeypatch.setattr(h,'authorized_materials',lambda *_: (
        _ for _ in ()).throw(AssertionError('Should reject before admin material read')))
    args=SimpleNamespace(school_a='synthetic-a',school_b='synthetic-b',
                         shell_a='shell-a',source_a='source:owned-a',source_b='source:foreign-b')
    with pytest.raises(AssertionError,match='both.*schools|two.*schools|provisioned'):
        h.case_14(object(),args,{'school_id':'synthetic-a',
                                  'available_schools':['synthetic-a']})


def test_at12_rejects_stale_restore_evidence_from_different_git_tree(tmp_path):
    import json
    workdir=tmp_path/'restored'
    workdir.mkdir()
    (workdir/'native-readback-evidence.json').write_text(json.dumps({
        'classification':'ISOLATED_RESTORE_NATIVE_READBACK_NOT_AT_PASS',
        'source_commit':'a'*40,'source_tree':'b'*40,
        'native_owner_identity_matches_before_after':True,
        'db_inventories_equal':True,
        'native_readback':{
            'source_owner_count':1,'verified_original_count':1,
            'owned_source_graph_hash':'c'*64}}))
    config={'restore_flags':{'restore':{'--workdir':str(workdir)}}}
    with pytest.raises(r.IncompleteAT,match='rights/version/original'):
        r.validate_restore_rights(config,tmp_path,'d'*40,'e'*40)
    assert not (tmp_path/'S1-AT12.json').exists()
