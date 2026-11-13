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
DEFINE TABLE IF NOT EXISTS vault_audit SCHEMALESS;
DEFINE INDEX IF NOT EXISTS shell_scope_unique ON TABLE content_shell FIELDS school_id, academic_year, grade, subject, curriculum_stream UNIQUE;
DEFINE INDEX IF NOT EXISTS shell_notebook_unique ON TABLE content_shell FIELDS notebook_id UNIQUE;
DEFINE INDEX IF NOT EXISTS op_key_unique ON TABLE vault_operation FIELDS school_id, actor_id, kind, idempotency_key UNIQUE;
DEFINE INDEX IF NOT EXISTS scope_key_unique ON TABLE vault_scope_claim FIELDS school_id, scope_key UNIQUE;
DEFINE INDEX IF NOT EXISTS source_id_unique ON TABLE source_owner FIELDS source_id UNIQUE;
'''


# Exact, ordered A-only index contracts; an index with the correct name but
# different columns MUST NOT be allowed to satisfy fail-start attestation.
EXPECTED_INDEXES = {
    'content_shell': {
        'shell_scope_unique': ('school_id', 'academic_year', 'grade', 'subject', 'curriculum_stream'),
        'shell_notebook_unique': ('notebook_id',),
    },
    'vault_operation': {
        'op_key_unique': ('school_id', 'actor_id', 'kind', 'idempotency_key'),
    },
    'vault_scope_claim': {
        'scope_key_unique': ('school_id', 'scope_key'),
    },
    'source_owner': {
        'source_id_unique': ('source_id',),
    },
}

# SurrealDB v2 INFO FOR TABLE can return either SQL strings or {"sql": ...}
# for each index, depending on server/client representation.
_INDEX_SQL_RE = re.compile(
    r'\s*DEFINE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?'
    r'(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+ON\s+(?:TABLE\s+)?'
    r'(?P<table>[A-Za-z_][A-Za-z0-9_]*)\s+'
    r'(?:FIELDS|COLUMNS)\s+(?P<fields>[A-Za-z_][A-Za-z0-9_]*'
    r'(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s+UNIQUE\s*;?\s*',
    re.IGNORECASE,
)


def verify_unique_index_definitions(table: str, indexes: dict) -> None:
    """Reject altered table/name/order/columns/uniqueness or unrecognised SQL.

    Never perform a silent ALTER/OVERWRITE migration over a drifted index.
    Follow this with actual v2 duplicate-insert and commit-conflict probes.
    """
    expected = EXPECTED_INDEXES.get(table)
    if expected is None or not isinstance(indexes, dict) or set(indexes) != set(expected):
        raise SurrealUnavailable('A unique indexes missing, extra or altered: ' + str(table))
    for name, fields in expected.items():
        definition=indexes[name]
        sql=definition.get('sql') if isinstance(definition,dict) else definition
        match=_INDEX_SQL_RE.fullmatch(sql) if isinstance(sql,str) else None
        if (match is None or match.group('table') != table or match.group('name') != name
                or tuple(re.split(r'\s*,\s*',match.group('fields'))) != fields):
            raise SurrealUnavailable(f'A unique index definition mismatch: {table}.{name}')


class SurrealUnavailable(Indeterminate):
    """Connection/transaction acknowledgement uncertain; never blindly resend."""


def _digest(*parts):
    return hashlib.sha256(json.dumps(list(parts), ensure_ascii=False,
        separators=(',', ':'), sort_keys=True).encode('utf-8')).hexdigest()


def _record(table, *parts):
    # Record IDs are built only from fixed table names and SHA-256 hex, never user text.
    assert table in ('content_shell','vault_operation','vault_scope_claim','source_owner','vault_session','vault_audit')
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


# SurrealDB 2.x calls this two-argument constructor type::thing(table,key).
_RECORD_EXPR = re.compile(r'type::record\(\$([a-zA-Z][a-zA-Z0-9_]*)\)')
_RECORD_ID = re.compile(r'^(content_shell|vault_operation|vault_scope_claim|source_owner|vault_session):([a-f0-9]{64})$')


def prepare_surreal_v2(sql: str, variables: dict | None = None) -> tuple[str, dict]:
    if not isinstance(sql,str):
        raise ValueError('SQL required')
    params=dict(variables or {})
    for name in set(_RECORD_EXPR.findall(sql)):
        value=params.get(name)
        matched=_RECORD_ID.fullmatch(value) if isinstance(value,str) else None
        if matched is None:
            raise ValueError('Invalid opaque A record binding: '+name)
        a,b=name+'_table',name+'_key'
        if a in params or b in params:
            raise ValueError('Record binding parameter collision')
        params[a],params[b]=matched.groups()
        sql=sql.replace('type::record($'+name+')','type::thing($'+a+', $'+b+')')
    if 'type::record(' in sql:
        raise ValueError('Unknown SurrealDB 3 constructor in v2 query')
    return sql,params


class RPC:
    """One authenticated RPC socket per transaction to avoid shared-session races."""
    def __init__(self, cfg:SurrealConfig):
        self.cfg=cfg.validate()

    def query(self, sql:str, variables:dict|None=None):
        sql, variables = prepare_surreal_v2(sql, variables)
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
                response=call('query',[sql,variables])
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
        # Check full v2 schema identity, not simply the index name/UNIQUE substring.
        for table in EXPECTED_INDEXES:
            res=self.rpc.query(f'INFO FOR TABLE {table};')
            if not res or not isinstance(res[-1],dict):
                raise SurrealUnavailable('Cannot inspect A unique indexes')
            verify_unique_index_definitions(table,res[-1].get('indexes'))

    @staticmethod
    def _validate_key(school,key):
        if not isinstance(school,str) or not _SAFE.fullmatch(school):
            raise ValueError('Unsafe school id')
        if not isinstance(key,str) or not _SAFE.fullmatch(key):
            raise ValueError('Unsafe idempotency key')

    @staticmethod
    def _material_actor(actor_id, fallback):
        # The authenticated JWT subject, not the process-wide Admin identity,
        # scopes service material operations. It is hashed into opaque record IDs.
        actor=actor_id if actor_id is not None else fallback
        if (not isinstance(actor,str) or not actor.strip() or len(actor)>256
                or any(ord(char)<32 for char in actor)):
            raise ValueError('Invalid authenticated material actor')
        return actor

    def _operation(self,school,key,kind,scope='',*,actor_id=None):
        actor=self._material_actor(actor_id,self.actor_id)
        rid=_record('vault_operation',school,actor,kind,key,scope)
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
                       '{ THROW "unexpected shell operation state" }; '
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

    def session(self,sid,school_id=None):
        rid=_record('vault_session',sid)
        if school_id is None:
            return self._first(self.query(
                'SELECT * FROM type::record($rid) WHERE expires>$now;',
                rid=rid,now=_now()))
        return self._first(self.query(
            'SELECT * FROM type::record($rid) WHERE school_id=$school AND expires>$now;',
            rid=rid,school=school_id,now=_now()))

    def switch_school(self,sid,old_school,new_school,old_csrf,new_csrf,actor_id):
        # One compare-and-set of the active session is authoritative.
        # A stale/replayed CSRF cannot flip school; caller reads active school
        # from this server-held record, NEVER from any browser header.
        rid=_record('vault_session',sid)
        results=self.query(
            'UPDATE type::record($rid) SET school_id=$new_school,csrf=$new_csrf '
            'WHERE school_id=$old_school AND csrf=$old_csrf AND expires>$now;',
            rid=rid,new_school=new_school,new_csrf=new_csrf,old_school=old_school,
            old_csrf=old_csrf,now=_now())
        changed=results[-1] if results else None
        if not isinstance(changed,list) or len(changed)!=1:
            raise Indeterminate('Concurrent school switch or stale CSRF; session must be rechecked')
        confirmed=self.session(sid,new_school)
        if not confirmed or confirmed.get('csrf')!=new_csrf:
            raise Indeterminate('School context rotation not durably verified')
        # Audit has no raw cookie or CSRF; an audit failure blocks normal success.
        audit_id=_record('vault_audit',sid,new_school,new_csrf)
        self.query('CREATE ONLY type::record($rid) CONTENT $doc;',rid=audit_id,
            doc={'kind':'admin_school_switch','actor_id':actor_id,
                 'previous_school':old_school,'active_school':new_school,
                 'session_hash':_digest(sid),'created_at':_now()})
        return {'school_id':new_school,'csrf':new_csrf}

    def del_session(self,sid):
        self.query('DELETE type::record($rid);',rid=_record('vault_session',sid))

    def _material_key_owner(self,school_id,actor,key):
        # Formal unique scope: School + Actor + Kind + Key, not Shell.
        blocks=self.query(
            'SELECT * FROM vault_operation WHERE school_id=$school AND actor_id=$actor '
            'AND kind="material" AND idempotency_key=$key LIMIT 2;',
            school=school_id,actor=actor,key=key)
        rows=blocks[-1] if blocks else None
        if not isinstance(rows,list) or len(rows)>1:
            raise SurrealUnavailable('Unverifiable material key uniqueness')
        return _clean(rows[0]) if rows else None

    def start_material(self,school_id,shell_id,key,digest,*,actor_id=None,metadata=None):
        self._validate_key(school_id,key)
        actor=self._material_actor(actor_id,self.actor_id)
        if metadata is not None:
            if (not isinstance(metadata,dict) or
                set(metadata)!=set(('sha256','title','license','retention','original_name')) or
                not re.fullmatch(r'[a-f0-9]{64}',str(metadata.get('sha256','')))):
                raise ValueError('Canonical upload metadata invalid')
            computed=hashlib.sha256(json.dumps(
                [metadata['sha256'],metadata['title'],metadata['license'],
                 metadata['retention'],metadata['original_name']],
                separators=(',',':')).encode('utf-8')).hexdigest()
            if computed!=digest:
                raise Conflict('Upload payload fingerprint/metadata mismatch')
        any_op=self._material_key_owner(school_id,actor,key)
        if any_op and (any_op.get('shell_id')!=shell_id or
                       any_op.get('payload_sha')!=digest):
            raise Conflict('Material Idempotency-Key reused across Shell or payload')
        op=self._operation(school_id,key,'material',shell_id,actor_id=actor)
        if op:
            if op.get('payload_sha')!=digest:raise Conflict('Upload key reused with different body')
            if op['status']=='COMMITTED':
                m=self.material(op['source_id'],shell_id,school_id)
                if m: return m,False
                raise Indeterminate('Material committed without ownership record')
            raise Indeterminate('Unconfirmed source upload; no unsafe replay')
        opid=_record('vault_operation',school_id,actor,'material',key,shell_id)
        claimid=_record('vault_scope_claim',school_id,shell_id,digest)
        op={'school_id':school_id,'actor_id':actor,'kind':'material','idempotency_key':key,
            'shell_id':shell_id,'payload_sha':digest,'status':'PENDING',
            'source_id':None,'native_source_id':None,
            'material_marker':'sunrise-a-material-v1:'+_digest(school_id,actor,key,digest),
            'metadata':metadata or {},'created_at':_now(),'updated_at':_now()}
        claim={'school_id':school_id,'scope_key':_digest(shell_id,digest),'operation_id':opid}
        try:
            self.query('BEGIN TRANSACTION; CREATE ONLY type::record($opid) CONTENT $op; '
                       'CREATE ONLY type::record($cid) CONTENT $claim; COMMIT TRANSACTION;',
                       opid=opid,op=op,cid=claimid,claim=claim)
        except SurrealUnavailable as e:
            # A failed COMMIT can mean a uniqueness conflict or a lost ACK.
            # Read back the actor-key and scope; never blindly retry CREATE.
            found=self._material_key_owner(school_id,actor,key)
            if found and (found.get('shell_id')!=shell_id or
                          found.get('payload_sha')!=digest):
                raise Conflict('Material Idempotency-Key already reserved for another request') from e
            claim=self._first(self.query('SELECT * FROM type::record($rid);',rid=claimid))
            if claim and claim.get('operation_id')!=opid:
                raise Conflict('Same material content already claimed by another operation') from e
            raise Indeterminate('Source upload reservation conflict/ACK uncertain') from e
        return None,True

    def record_material_receipt(self,school_id,shell_id,key,source_id,*,actor_id=None):
        """Persist exact native Source ID before ownership/finish. Never infer one."""
        checked_id(source_id,'source')
        actor=self._material_actor(actor_id,self.actor_id)
        op=self._operation(school_id,key,'material',shell_id,actor_id=actor)
        if not op or op.get('status') not in ('PENDING','QUARANTINED'):
            raise Indeterminate('No safe operation for Native Source receipt')
        old=op.get('native_source_id')
        if old and old!=source_id:
            raise Conflict('Different Native Source receipt for same operation')
        if old==source_id:return
        rid=_record('vault_operation',school_id,actor,'material',key,shell_id)
        # Native receipt is initially JSON null (NULL in SurrealQL), not
        # NONE. Refuse to overwrite an existing receipt under concurrency.
        result=self.query('UPDATE type::record($rid) SET native_source_id=$source,updated_at=time::unix() '
                   'WHERE status="PENDING" AND (native_source_id IS NONE OR native_source_id IS NULL);',
                   rid=rid,source=source_id)
        changes=result[-1] if result else None
        if not isinstance(changes,list) or len(changes)!=1:
            raise Indeterminate('Native receipt was not atomically claimed; inspect durable operation')
        after=self._operation(school_id,key,'material',shell_id,actor_id=actor)
        if not after or after.get('native_source_id')!=source_id:
            raise Indeterminate('Native Source receipt persistence is unconfirmed')

    def finish_material(self,school_id,shell_id,key,source_id,title,sha256,filename,license,retention,*,actor_id=None):
        checked_id(source_id,'source')
        actor=self._material_actor(actor_id,self.actor_id)
        opid=_record('vault_operation',school_id,actor,'material',key,shell_id)
        op=self._operation(school_id,key,'material',shell_id,actor_id=actor)
        if not op or op.get('status') not in ('PENDING','QUARANTINED'):
            raise Indeterminate('Source operation not safely recoverable')
        if op.get('native_source_id')!=source_id:
            raise Indeterminate('Native Source ID is not recorded in durable operation')
        metadata=op.get('metadata')
        if not isinstance(metadata,dict) or not metadata:
            raise Indeterminate('Canonical upload metadata missing; quarantine')
        if any(metadata.get(a)!=b for a,b in (
            ('sha256',sha256),('title',title),('original_name',filename),
            ('license',license),('retention',retention))):
            raise Conflict('Original upload receipt metadata mismatch')
        if not self.shell(school_id,shell_id):raise Indeterminate('Shell disappeared during upload')
        m={'source_id':source_id,'school_id':school_id,'shell_id':shell_id,
           'notebook_id':self.shell(school_id,shell_id)['notebook_id'],
           'title':title,'sha256':sha256,'original_name':filename,'version':1,
           'initial_version_id':_digest(source_id,sha256),
           'license':license,'retention':retention,
           'rights_owner_actor_id':actor,'created_by_actor_id':actor,
           'original_mime_type':'application/pdf','native_locator':source_id,
           'approved_sharing':False,'ai_usage_allowed':False,'ai_usage':False,
           'state':'PENDING','created_at':_now()}
        sid=_record('source_owner',source_id)
        try:
            self.query('BEGIN TRANSACTION; CREATE ONLY type::record($sid) CONTENT $material; '
                       'UPDATE type::record($opid) SET status="COMMITTED",source_id=$source_id,updated_at=time::unix(); '
                       'COMMIT TRANSACTION;',sid=sid,material=m,opid=opid,source_id=source_id)
        except SurrealUnavailable as e:
            raise Indeterminate('Source ownership transaction uncertain') from e

    def quarantine_material(self,school_id,shell_id,key,*,actor_id=None):
        actor=self._material_actor(actor_id,self.actor_id)
        rid=_record('vault_operation',school_id,actor,'material',key,shell_id)
        self.query('UPDATE type::record($rid) SET status="QUARANTINED",updated_at=time::unix() WHERE status="PENDING";',rid=rid)

    def material(self,source_id,shell_id,school_id):
        rid=_record('source_owner',source_id)
        return self._first(self.query('SELECT * FROM type::record($rid) WHERE school_id=$school AND shell_id=$shell;',
                                     rid=rid,school=school_id,shell=shell_id))

    def list_materials(self,school_id,shell_id):
        res=self.query('SELECT * FROM source_owner WHERE school_id=$school AND shell_id=$shell ORDER BY title;',
                       school=school_id,shell=shell_id)
        return [_clean(r) for r in (res[-1] or [])]
