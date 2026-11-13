"""A-owned SurrealDB v2 durable journal for Stage 1 (NOT SQLite).

The only identity source of truth for formal runtime is this A SurrealDB database.
Every claim is a CREATE ONLY, with deterministic opaque record IDs and UNIQUE indexes.
SQL is static; every untrusted value is sent as an RPC bound parameter. No generic
SQL interface, public DB endpoint, mutable native notebook title lookup, or queue.

Runtime gates: SurrealDB v2.3.10 / RocksDB / concurrency / restart / crash injection
MUST be run on an isolated real service before this component can be accepted.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit

from websockets.sync.client import connect
from websockets.exceptions import WebSocketException
from store import Conflict, Indeterminate
from native import checked_id

_SAFE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')
_COLUMNS = ('academic_year', 'grade', 'subject', 'curriculum_stream')

# Require explicit existence of indexes. Do not silently accept an unindexed DB.
SCHEMA = '''
DEFINE TABLE IF NOT EXISTS content_shell SCHEMALESS;
DEFINE TABLE IF NOT EXISTS vault_operation SCHEMALESS;
DEFINE TABLE IF NOT EXISTS vault_scope_claim SCHEMALESS;
DEFINE TABLE IF NOT EXISTS source_owner SCHEMALESS;
DEFINE TABLE IF NOT EXISTS vault_session SCHEMALESS;
DEFINE INDEX IF NOT EXISTS shell_scope_unique ON TABLE content_shell FIELDS school_id, academic_year, grade, subject, curriculum_stream UNIQUE;
DEFINE INDEX IF NOT EXISTS shell_notebook_unique ON TABLE content_shell FIELDS notebook_id UNIQUE;
DEFINE INDEX IF NOT EXISTS op_key_unique ON TABLE vault_operation FIELDS school_id, actor_id, kind, idempotency_key UNIQUE;
DEFINE INDEX IF NOT EXISTS scope_key_unique ON TABLE vault_scope_claim FIELDS school_id, scope_key UNIQUE;
DEFINE INDEX IF NOT EXISTS source_id_unique ON TABLE source_owner FIELDS source_id UNIQUE;
'''


class SurrealUnavailable(Indeterminate):
    """Connection/transaction acknowledgement uncertain; never blindly resend."""


def _digest(*parts):
    return hashlib.sha256(json.dumps(list(parts), ensure_ascii=False,
        separators=(',', ':'), sort_keys=True).encode('utf-8')).hexdigest()


def _record(table, *parts):
    # Record IDs are built only from fixed table names and SHA-256 hex, never user text.
    assert table in ('content_shell','vault_operation','vault_scope_claim','source_owner','vault_session')
    return f'{table}:{_digest(*parts)}'


def _now():
    return int(time.time())


def _clean(row):
    if not isinstance(row, dict):
        raise SurrealUnavailable('Unexpected SurrealDB row')
    return {k: v for k, v in row.items() if k != 'id'}


@dataclass(frozen=True)
class SurrealConfig:
    ws_url: str
    user: str
    password: str
    namespace: str = 'open_notebook'
    database: str = 'open_notebook'
    timeout: int = 8

    def validate(self):
        url = urlsplit(self.ws_url)
        if (url.scheme != 'ws' or url.path != '/rpc' or url.query or url.fragment or
            url.username or url.password or url.hostname not in ('127.0.0.1','localhost','surrealdb')):
            raise ValueError('SurrealDB must be a private ws:// loopback/Docker address ending /rpc')
        if len(self.user) < 3 or self.user.lower() in ('root:root','changeme'):
            raise ValueError('Missing/unsafe A database user')
        if len(self.password) < 24 or self.password == 'root':
            raise ValueError('Missing/unsafe A database password')
        if not all(_SAFE.fullmatch(v) for v in (self.namespace, self.database)):
            raise ValueError('Unsafe database namespace/name')
        return self


class RPC:
    """One authenticated RPC socket per transaction to avoid shared-session races."""
    def __init__(self, cfg:SurrealConfig):
        self.cfg=cfg.validate()

    def query(self, sql:str, variables:dict|None=None):
        # Close on transport ambiguity: one request contains the *entire* transaction.
        try:
            with connect(self.cfg.ws_url, subprotocols=["json"], open_timeout=self.cfg.timeout,
                         close_timeout=2, max_size=4*1024*1024) as ws:
                counter=0
                def call(method, params):
                    nonlocal counter
                    counter+=1
                    ws.send(json.dumps({'id':counter,'method':method,'params':params},
                        separators=(',',':'),ensure_ascii=False))
                    envelope=json.loads(ws.recv(timeout=self.cfg.timeout))
                    if envelope.get('id')!=counter or 'error' in envelope:
                        raise SurrealUnavailable('SurrealDB RPC authentication/query error')
                    return envelope.get('result')
                call('signin',[{'user':self.cfg.user,'pass':self.cfg.password}])
                call('use',[self.cfg.namespace,self.cfg.database])
                response=call('query',[sql,variables or {}])
        except (OSError,TimeoutError,WebSocketException,ValueError,KeyError) as exc:
            raise SurrealUnavailable('SurrealDB RPC connection/receipt uncertain') from exc
        if not isinstance(response,list):
            raise SurrealUnavailable('SurrealDB returned unexpected statement envelope')
        # A SurrealQL statement error must fail the *entire* operation: no partial success.
        if any(not isinstance(s,dict) or s.get('status')!='OK' for s in response):
            raise SurrealUnavailable('SurrealDB statement/transaction failed; read back before retry')
        return [s.get('result') for s in response]


class SurrealStore:
    is_durable=True
    def __init__(self, cfg:SurrealConfig, actor_id:str):
        self.rpc=RPC(cfg)
        if not _SAFE.fullmatch(actor_id):
            raise ValueError('Stable actor ID required')
        self.actor_id=actor_id
        self.migrate()

    def query(self, sql, **vars):
        return self.rpc.query(sql,vars)

    @staticmethod
    def _first(results):
        if not results: return None
        block=results[-1]
        if isinstance(block,list):
            return _clean(block[0]) if block else None
        return _clean(block) if isinstance(block,dict) else None

    def migrate(self):
        self.rpc.query(SCHEMA)
        # Fail-start on drift/absence of durable unique indexes.
        for table, expected in (
            ('content_shell',('shell_scope_unique','shell_notebook_unique')),
            ('vault_operation',('op_key_unique',)),
            ('vault_scope_claim',('scope_key_unique',)),
            ('source_owner',('source_id_unique',))):
            res=self.rpc.query(f'INFO FOR TABLE {table};')
            if not res or not isinstance(res[-1],dict):
                raise SurrealUnavailable('Cannot inspect A unique indexes')
            indexes=res[-1].get('indexes')
            if not isinstance(indexes,dict) or any(name not in indexes or
                    'UNIQUE' not in str(indexes[name]).upper() for name in expected):
                raise SurrealUnavailable(f'A unique indexes unverified: {table}')

    @staticmethod
    def _validate_key(school,key):
        if not isinstance(school,str) or not _SAFE.fullmatch(school):
            raise ValueError('Unsafe school id')
        if not isinstance(key,str) or not _SAFE.fullmatch(key):
            raise ValueError('Unsafe idempotency key')

    def _operation(self,school,key,kind,scope=''):
        rid=_record('vault_operation',school,self.actor_id,kind,key,scope)
        return self._first(self.query('SELECT * FROM type::record($rid);',rid=rid))

    def operation(self,school,key,kind,scope=''):
        return self._operation(school,key,kind,scope)

    def start_shell(self,school_id,key,payload):
        self._validate_key(school_id,key)
        if not isinstance(payload,dict) or any(not isinstance(payload.get(k),str) or
                not payload[k].strip() for k in _COLUMNS):
            raise ValueError('Invalid Content Shell classification')
        scope={k:payload[k] for k in _COLUMNS}
        canonical=_digest(scope)
        op_id=_record('vault_operation',school_id,self.actor_id,'shell',key,'')
        claim_id=_record('vault_scope_claim',school_id,scope)
        existing=self._operation(school_id,key,'shell')
        if existing:
            if existing.get('payload_sha') != canonical:raise Conflict('Idempotency-Key/body mismatch')
            if existing.get('status')=='COMMITTED':
                shell=self.shell(school_id,existing['shell_id'])
                if shell and shell.get('notebook_id')==existing.get('notebook_id'):
                    return shell,False
                raise Indeterminate('Committed native mapping absent or invalid')
            raise Indeterminate('Native creation pending; marker readback required')
        shell_id=str(uuid.uuid4())
        marker='sunrise-a-op-v1:'+_digest(school_id,self.actor_id,key,canonical)
        op={'school_id':school_id,'actor_id':self.actor_id,'kind':'shell','idempotency_key':key,
            'payload_sha':canonical,'shell_id':shell_id,'marker':marker,'notebook_id':None,
            'status':'PENDING','created_at':_now(),'updated_at':_now()}
        claim={'school_id':school_id,'scope_key':canonical,'shell_id':shell_id,'operation_id':op_id}
        try:
            self.query('BEGIN TRANSACTION; CREATE ONLY type::record($op_id) CONTENT $op; '
                       'CREATE ONLY type::record($claim_id) CONTENT $claim; COMMIT TRANSACTION;',
                       op_id=op_id,claim_id=claim_id,op=op,claim=claim)
        except SurrealUnavailable:
            # Could be unique conflict, lost transaction ACK, or bad DB: never create notebook
            # until a fresh readback proves this exact reservation committed.
            existing=self._operation(school_id,key,'shell')
            if existing and existing.get('payload_sha')!=canonical:
                raise Conflict('Idempotency-Key/body mismatch')
            scope_row=self._first(self.query('SELECT * FROM type::record($rid);',rid=claim_id))
            if scope_row and scope_row.get('operation_id') != op_id:
                raise Conflict('School/scope already claimed by another operation')
            raise Indeterminate('Reservation conflict/ack uncertainty; no native creation')
        return {'shell_id':shell_id,'school_id':school_id,'creation_marker':marker,**scope},True

    def complete_shell(self,school_id,key,record,notebook_id):
        checked_id(notebook_id,'notebook')
        op=self._operation(school_id,key,'shell')
        if not op or op.get('shell_id')!=record.get('shell_id'):
            raise Indeterminate('Reservation identity mismatch')
        if op['status']=='COMMITTED':
            if op.get('notebook_id')==notebook_id:
                return self.shell(school_id,record['shell_id'])
            raise Conflict('Different notebook mapping already committed')
        if op['status'] not in ('PENDING','QUARANTINED'):
            raise Indeterminate('Unverifiable notebook create status')
        shell={'shell_id':op['shell_id'],'school_id':school_id,'academic_year':record['academic_year'],
               'grade':record['grade'],'subject':record['subject'],
               'curriculum_stream':record['curriculum_stream'],
               'notebook_id':notebook_id,'created_by_actor_id':self.actor_id,
               'created_at':_now(),'archived':0,'archived_at':None}
        shell_rid=_record('content_shell',school_id,op['shell_id'])
        op_rid=_record('vault_operation',school_id,self.actor_id,'shell',key,'')
        # Compare-and-set on the same operation record in the transaction. Native readback
        # and unique notebook_id index are additionally required by the Gateway.
        try:
            self.query('BEGIN TRANSACTION; '
                       'IF (SELECT VALUE status FROM type::record($op_rid))[0] NOT IN ["PENDING", "QUARANTINED"] '
                       'THEN { THROW "unexpected shell operation state"; }; '
                       'CREATE ONLY type::record($shell_rid) CONTENT $shell; '
                       'UPDATE type::record($op_rid) SET status="COMMITTED", notebook_id=$notebook_id,updated_at=time::unix(); '
                       'COMMIT TRANSACTION;', op_rid=op_rid,shell_rid=shell_rid,shell=shell,notebook_id=notebook_id)
        except SurrealUnavailable as e:
            now=self._operation(school_id,key,'shell')
            actual=self.shell(school_id,op['shell_id'])
            if now and actual and now.get('status')=='COMMITTED' and actual.get('notebook_id')==notebook_id:
                return actual
            raise Indeterminate('Notebook commit uncertain; reconciliation required') from e
        return self.shell(school_id,op['shell_id'])

    def quarantine(self,school_id,key):
        rid=_record('vault_operation',school_id,self.actor_id,'shell',key,'')
        self.query('UPDATE type::record($rid) SET status="QUARANTINED", updated_at=time::unix() '
                   'WHERE status="PENDING";',rid=rid)

    def shell(self,school_id,shell_id):
        rid=_record('content_shell',school_id,shell_id)
        row=self._first(self.query('SELECT * FROM type::record($rid) WHERE school_id=$school;',
                                   rid=rid,school=school_id))
        return row

    def list_shells(self,school_id):
        res=self.query('SELECT * FROM content_shell WHERE school_id=$school ORDER BY academic_year,grade,subject,curriculum_stream;',school=school_id)
        return [_clean(r) for r in (res[-1] or [])]

    def archive(self,school_id,shell_id):
        rid=_record('content_shell',school_id,shell_id)
        self.query('UPDATE type::record($rid) SET archived=1,archived_at=time::unix() '
                   'WHERE school_id=$school;',rid=rid,school=school_id)
        return self.shell(school_id,shell_id)

    def add_session(self,sid,school_id,csrf,seconds=3600):
        rid=_record('vault_session',sid)
        self.query('CREATE ONLY type::record($rid) CONTENT $doc;',rid=rid,
                   doc={'sid_hash':_digest(sid),'school_id':school_id,'csrf':csrf,'expires':_now()+seconds})

    def session(self,sid,school_id):
        rid=_record('vault_session',sid)
        row=self._first(self.query('SELECT * FROM type::record($rid) WHERE school_id=$school AND expires>$now;',
                rid=rid,school=school_id,now=_now()))
        return row

    def del_session(self,sid):
        self.query('DELETE type::record($rid);',rid=_record('vault_session',sid))

    def start_material(self,school_id,shell_id,key,digest):
        self._validate_key(school_id,key)
        op=self._operation(school_id,key,'material',shell_id)
        if op:
            if op.get('payload_sha')!=digest:raise Conflict('Upload key reused with different body')
            if op['status']=='COMMITTED':
                m=self.material(op['source_id'],shell_id,school_id)
                if m: return m,False
                raise Indeterminate('Material committed without ownership record')
            raise Indeterminate('Unconfirmed source upload; no unsafe replay')
        opid=_record('vault_operation',school_id,self.actor_id,'material',key,shell_id)
        claimid=_record('vault_scope_claim',school_id,shell_id,digest)
        op={'school_id':school_id,'actor_id':self.actor_id,'kind':'material','idempotency_key':key,
            'shell_id':shell_id,'payload_sha':digest,'status':'PENDING','source_id':None,
            'created_at':_now(),'updated_at':_now()}
        claim={'school_id':school_id,'scope_key':_digest(shell_id,digest),'operation_id':opid}
        try:
            self.query('BEGIN TRANSACTION; CREATE ONLY type::record($opid) CONTENT $op; '
                       'CREATE ONLY type::record($cid) CONTENT $claim; COMMIT TRANSACTION;',
                       opid=opid,op=op,cid=claimid,claim=claim)
        except SurrealUnavailable as e:
            raise Indeterminate('Source upload reservation conflict/uncertain') from e
        return None,True

    def finish_material(self,school_id,shell_id,key,source_id,title,sha256,filename,license,retention):
        checked_id(source_id,'source')
        opid=_record('vault_operation',school_id,self.actor_id,'material',key,shell_id)
        op=self._operation(school_id,key,'material',shell_id)
        if not op or op['status']!='PENDING': raise Indeterminate('Source operation not reserved')
        if not self.shell(school_id,shell_id):raise Indeterminate('Shell disappeared during upload')
        m={'source_id':source_id,'school_id':school_id,'shell_id':shell_id,
           'notebook_id':self.shell(school_id,shell_id)['notebook_id'],
           'title':title,'sha256':sha256,'original_name':filename,'version':1,
           'initial_version_id':_digest(source_id,sha256),
           'license':license,'retention':retention,'approved_sharing':False,
           'ai_usage':False,'created_by_actor_id':self.actor_id,'state':'PENDING',
           'created_at':_now()}
        sid=_record('source_owner',source_id)
        try:
            self.query('BEGIN TRANSACTION; CREATE ONLY type::record($sid) CONTENT $material; '
                       'UPDATE type::record($opid) SET status="COMMITTED",source_id=$source_id,updated_at=time::unix(); '
                       'COMMIT TRANSACTION;',sid=sid,material=m,opid=opid,source_id=source_id)
        except SurrealUnavailable as e:
            raise Indeterminate('Source ownership transaction uncertain') from e

    def quarantine_material(self,school_id,shell_id,key):
        rid=_record('vault_operation',school_id,self.actor_id,'material',key,shell_id)
        self.query('UPDATE type::record($rid) SET status="QUARANTINED",updated_at=time::unix() WHERE status="PENDING";',rid=rid)

    def material(self,source_id,shell_id,school_id):
        rid=_record('source_owner',source_id)
        return self._first(self.query('SELECT * FROM type::record($rid) WHERE school_id=$school AND shell_id=$shell;',
                                     rid=rid,school=school_id,shell=shell_id))

    def list_materials(self,school_id,shell_id):
        res=self.query('SELECT * FROM source_owner WHERE school_id=$school AND shell_id=$shell ORDER BY title;',
                       school=school_id,shell=shell_id)
        return [_clean(r) for r in (res[-1] or [])]
