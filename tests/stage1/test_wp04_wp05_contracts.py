"""WP04/05 provenance, verified Worker state and private retry contracts.

IMPLEMENTED_UNTESTED. This file is SOURCE ONLY until Owner enables QA again.
"""
import asyncio
import hashlib
from pathlib import Path
import sys

import httpx
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native,NativeUnavailable
from surreal_store import SurrealStore,_record
from store import Indeterminate, Conflict


@pytest.mark.parametrize(('payload','expected'),[
    ({'status':'queued'},'PROCESSING'),
    ({'status':'running'},'PROCESSING'),
    ({'status':'failed'},'FAILED'),
    ({'status':'completed','full_text':'繁體中文測試'},'READY'),
    ({'status':'completed','full_text':''},'UNKNOWN'),
    ({'status':'completed','full_text':None},'UNKNOWN'),
    ({'status':'unknown'},'UNKNOWN'),
    ({'status':None,'full_text':'incomplete'},'UNKNOWN'),
    ({},'UNKNOWN'),
])
def test_source_readback_never_invents_ready(payload,expected):
    assert Native.processing_state(payload)==expected


def test_service_actor_is_opaque_scope_of_material_idempotency():
    admin=_record('vault_operation','synthetic-school','synthetic-admin','material','key1','shell1')
    service=_record('vault_operation','synthetic-school','synthetic-service','material','key1','shell1')
    assert admin!=service
    assert SurrealStore._material_actor('synthetic-service','synthetic-admin')=='synthetic-service'
    for bad in ('',None,'\nsubject','a'*300):
        if bad is None:
            assert SurrealStore._material_actor(bad,'synthetic-admin')=='synthetic-admin'
        else:
            with pytest.raises(ValueError):
                SurrealStore._material_actor(bad,'synthetic-admin')


def test_source_owner_preserves_rights_and_ai_disabled_for_authenticated_service_actor():
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    journal._operation=lambda school,key,kind,scope,actor_id=None: {
        'status':'PENDING','actor_id':actor_id,
        'native_source_id':'source:synthetic',
        'metadata':{'sha256':'a'*64,'title':'Synthetic title',
                    'original_name':'synthetic.pdf',
                    'license':'synthetic','retention':'short'}}
    journal.shell=lambda school,shell: {'notebook_id':'notebook:synthetic'}
    captured=[]
    journal.query=lambda sql,**bindings: captured.append((sql,bindings)) or []
    journal.finish_material('synthetic-school','synthetic-shell','synthetic-key',
        'source:synthetic','Synthetic title','a'*64,'synthetic.pdf','synthetic','short',
        actor_id='synthetic-service')
    statement,bindings=captured[0]
    data=bindings['material']
    assert data['school_id']=='synthetic-school' and data['shell_id']=='synthetic-shell'
    assert data['rights_owner_actor_id']=='synthetic-service'
    assert data['created_by_actor_id']=='synthetic-service'
    assert data['ai_usage_allowed'] is False and data['approved_sharing'] is False
    assert data['initial_version_id'] and data['sha256']=='a'*64
    assert data['native_locator']=='source:synthetic'
    assert 'BEGIN TRANSACTION;' in statement


def test_unapproved_retry_never_contacts_native():
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json={})
    native=Native('http://127.0.0.1:5055','synthetic-native-password',
                  transport=httpx.MockTransport(handler),text_only_verified=True)
    with pytest.raises(NativeUnavailable):
        asyncio.run(native.retry_failed_owned_source('source:1','notebook:1','a'*64))
    assert requests==[]


@pytest.mark.parametrize('status',['running','queued','unknown','completed',None])
def test_unproved_failed_status_never_retries_native(status):
    requests=[]
    def handler(request):
        requests.append((request.method,request.url.path))
        if request.url.path=='/api/sunrise-patch-status':
            return httpx.Response(200,json={'marker':'sunrise-a-text-only-no-vector-v1','text_only':True})
        if request.url.path=='/api/sources/source:1':
            return httpx.Response(200,json={'id':'source:1','notebooks':['notebook:1'],
                'status':status,'command_id':'command:existing'})
        return httpx.Response(500)
    native=Native('http://127.0.0.1:5055','synthetic-native-password',
                  transport=httpx.MockTransport(handler),text_only_verified=True)
    with pytest.raises(NativeUnavailable):
        asyncio.run(native.retry_failed_owned_source('source:1','notebook:1','a'*64,
                                                     operator_authorized=True))
    assert not any(method=='POST' for method,_ in requests)


def test_native_retry_retains_source_and_original_hash_without_repeat():
    original=b'%PDF-1.4\nSYNTHETIC ONLY\n%%EOF'
    digest=hashlib.sha256(original).hexdigest()
    observed={'source_reads':0,'native_posts':0,'pdf_gets':0}
    def handler(request):
        path=request.url.path
        if path=='/api/sunrise-patch-status':
            return httpx.Response(200,json={'marker':'sunrise-a-text-only-no-vector-v1','text_only':True})
        if path=='/api/sources/source:1' and request.method=='GET':
            observed['source_reads']+=1
            return httpx.Response(200,json={'id':'source:1','notebooks':['notebook:1'],
                'status':'failed' if observed['source_reads']==1 else 'queued',
                'command_id':'command:previous' if observed['source_reads']==1 else 'command:new'})
        if path=='/api/sources/source:1/download':
            observed['pdf_gets']+=1
            return httpx.Response(200,content=original)
        if path=='/api/sources/source:1/retry':
            observed['native_posts']+=1
            return httpx.Response(200,json={'id':'source:1','status':'queued',
                'command_id':'command:new'})
        return httpx.Response(404)
    native=Native('http://127.0.0.1:5055','synthetic-native-password',
                  transport=httpx.MockTransport(handler),text_only_verified=True)
    receipt=asyncio.run(native.retry_failed_owned_source('source:1','notebook:1',digest,
                                                         operator_authorized=True))
    assert receipt['state']=='RETRY_SUBMITTED_NOT_COMPLETED'
    assert observed=={'source_reads':2,'native_posts':1,'pdf_gets':2}


@pytest.mark.parametrize(('native_receipt','metadata_override','exception'),[
    (None,None,Indeterminate),
    ('source:different',None,Indeterminate),
    ('source:synthetic',{'title':'other title'},Conflict),
    ('source:synthetic',{},Indeterminate),
])
def test_finish_material_rejects_unknown_ack_or_mismatched_original_metadata(
        native_receipt,metadata_override,exception):
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    metadata={'sha256':'a'*64,'title':'Synthetic title','original_name':'synthetic.pdf',
              'license':'synthetic','retention':'short'}
    if metadata_override is not None:
        metadata.update(metadata_override)
    journal._operation=lambda school,key,kind,scope,actor_id=None: {
        'status':'PENDING','actor_id':actor_id,
        'native_source_id':native_receipt,'metadata':metadata}
    journal.shell=lambda school,shell: {'notebook_id':'notebook:synthetic'}
    called=[]
    journal.query=lambda sql,**params: called.append((sql,params)) or []
    with pytest.raises(exception):
        journal.finish_material('synthetic-school','synthetic-shell','synthetic-key',
            'source:synthetic','Synthetic title','a'*64,'synthetic.pdf',
            'synthetic','short',actor_id='synthetic-service')
    assert not called, 'Must not write SourceOwner without exact durable receipt and metadata'


def test_native_receipt_conditional_write_requires_confirmed_single_row():
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    operation={'status':'PENDING','native_source_id':None}
    journal._operation=lambda school,key,kind,scope,actor_id=None: operation
    calls=[]
    journal.query=lambda sql,**params: calls.append((sql,params)) or [[]]
    with pytest.raises(Indeterminate):
        journal.record_material_receipt('synthetic-school','synthetic-shell',
            'synthetic-key','source:synthetic',actor_id='synthetic-service')
    assert len(calls)==1
    assert 'native_source_id IS NULL' in calls[0][0]
    assert 'native_source_id IS NONE' in calls[0][0]


def test_native_receipt_does_not_overwrite_an_existing_different_source():
    journal=SurrealStore.__new__(SurrealStore)
    journal.actor_id='synthetic-admin'
    journal._operation=lambda school,key,kind,scope,actor_id=None: {
        'status':'PENDING','native_source_id':'source:original'}
    journal.query=lambda sql,**params: (_ for _ in ()).throw(
        AssertionError('Unexpected Native receipt overwrite'))
    with pytest.raises(Conflict):
        journal.record_material_receipt('synthetic-school','synthetic-shell',
            'synthetic-key','source:replacement',actor_id='synthetic-service')
