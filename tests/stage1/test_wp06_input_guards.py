"""WP06 input and WP03 material-key negative contract · IMPLEMENTED_UNTESTED.

Source-only during the coding sprint; no test was executed for this revision.
"""
import sys
from pathlib import Path
from pydantic import ValidationError
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from vault_app import ShellInput,SearchInput
from surreal_store import SurrealStore
from store import Conflict


def test_shell_scope_canonicalization_before_immutable_claim():
    obj=ShellInput(academic_year=' 2026-2027 ',grade=' P4 ',
                   subject=' 小學數學 ',curriculum_stream=' HK ')
    assert obj.model_dump()=={'academic_year':'2026-2027','grade':'P4',
        'subject':'小學數學','curriculum_stream':'HK'}


@pytest.mark.parametrize('invalid',[
    {'academic_year':'２０２６'},
    {'academic_year':'2026/2027'},
    {'academic_year':'  '},
    {'grade':'P4\nWrong'},
    {'subject':'Math\u202eHidden'},
    {'curriculum_stream':'\u200b'},
])
def test_malformed_control_or_ambiguous_classification_rejected(invalid):
    data={'academic_year':'2026-2027','grade':'P4','subject':'Math','curriculum_stream':'HK'}
    data.update(invalid)
    with pytest.raises(ValidationError):
        ShellInput(**data)


@pytest.mark.parametrize('query',['',' ','\n','\x00','Algebra\nMath'])
def test_search_rejects_empty_or_control_text(query):
    with pytest.raises(ValidationError):
        SearchInput(query=query)


def test_unicode_text_search_remains_available_without_vector_fallback():
    assert SearchInput(query=' 繁體中文 數學 ').query=='繁體中文 數學'
    assert SearchInput(query='擴充漢字').query=='擴充漢字'


def test_same_actor_key_cross_shell_conflicts_before_native_side_effect():
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    journal._material_key_owner=lambda school,actor,key:{
        'school_id':school,'actor_id':actor,'idempotency_key':key,
        'shell_id':'synthetic-shell-a','payload_sha':'a'*64,'status':'PENDING'}
    def must_not_query(*args,**kwargs):
        raise AssertionError('DB transaction must not start with conflicting actor key')
    journal.query=must_not_query
    with pytest.raises(Conflict):
        journal.start_material('synthetic-school','synthetic-shell-b',
                               'same-key','a'*64,actor_id='synthetic-service')


def test_material_actor_scope_does_not_reuse_global_admin():
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    journal._material_key_owner=lambda school,actor,key: (
        {'school_id':school,'actor_id':'synthetic-service-b','shell_id':'synthetic-shell',
         'payload_sha':'a'*64} if actor=='synthetic-service-b' else None)
    journal._operation=lambda school,key,kind,scope,actor_id=None: None
    journal.query=lambda *args,**kwargs: []
    # A different service subject is a different idempotency key owner:
    assert journal.start_material('synthetic-school','synthetic-shell',
        'same-key','a'*64,actor_id='synthetic-service-a')==(None,True)
