"""Temporary local synthetic A-owned journal. NOT formal SurrealDB persistence / S1 acceptance.

Safety trade-off: outbound native notebook creation never auto-retries an unknown ACK.
An uncertain operation is QUARANTINED until independently reconciled.
"""
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path


class Conflict(Exception):
    pass


class Indeterminate(Exception):
    pass


class Store:
    def __init__(self, filename):
        self.path = str(filename)
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (sid TEXT PRIMARY KEY, school_id TEXT NOT NULL, csrf TEXT NOT NULL, expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS shells (shell_id TEXT PRIMARY KEY, school_id TEXT NOT NULL, academic_year TEXT NOT NULL,
                grade TEXT NOT NULL, subject TEXT NOT NULL, curriculum_stream TEXT NOT NULL,
                notebook_id TEXT UNIQUE NOT NULL, archived INTEGER NOT NULL DEFAULT 0,
                UNIQUE(school_id,academic_year,grade,subject,curriculum_stream));
            CREATE TABLE IF NOT EXISTS operations (school_id TEXT NOT NULL, op_key TEXT NOT NULL, payload_sha TEXT NOT NULL,
                shell_id TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY(school_id,op_key));
            CREATE TABLE IF NOT EXISTS shell_claims (school_id TEXT NOT NULL, scope_hash TEXT NOT NULL, op_key TEXT NOT NULL,
                PRIMARY KEY(school_id,scope_hash));
            CREATE TABLE IF NOT EXISTS material_operations (school_id TEXT NOT NULL, shell_id TEXT NOT NULL, op_key TEXT NOT NULL, payload_sha TEXT NOT NULL,
                status TEXT NOT NULL, source_id TEXT, PRIMARY KEY(school_id,shell_id,op_key));
            CREATE TABLE IF NOT EXISTS material_claims (school_id TEXT NOT NULL, shell_id TEXT NOT NULL,
                payload_sha TEXT NOT NULL, op_key TEXT NOT NULL, PRIMARY KEY(school_id,shell_id,payload_sha));
            CREATE TABLE IF NOT EXISTS materials (source_id TEXT PRIMARY KEY, shell_id TEXT NOT NULL, school_id TEXT NOT NULL,
                title TEXT NOT NULL, sha256 TEXT NOT NULL, original_name TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
                license TEXT NOT NULL, retention TEXT NOT NULL, ai_usage INTEGER NOT NULL DEFAULT 0,
                state TEXT NOT NULL DEFAULT 'PENDING', FOREIGN KEY(shell_id) REFERENCES shells(shell_id));
            ''')

    def connect(self):
        c=sqlite3.connect(self.path,timeout=8,isolation_level=None)
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA busy_timeout=8000')
        return c

    def add_session(self,sid,school_id,csrf,seconds=3600):
        with self.connect() as c:
            c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(sid,school_id,csrf,int(time.time())+seconds))

    def session(self,sid,school_id=None):
        with self.connect() as c:
            r=(c.execute('SELECT * FROM sessions WHERE sid=? AND expires>?',(sid,int(time.time()))).fetchone()
               if school_id is None else
               c.execute('SELECT * FROM sessions WHERE sid=? AND school_id=? AND expires>?',
                         (sid,school_id,int(time.time()))).fetchone())
            return dict(r) if r else None

    def switch_school(self,sid,old_school,new_school,old_csrf,new_csrf,actor_id):
        # Synthetic SQLite test double only. Atomic session update + audit.
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            updated=c.execute('UPDATE sessions SET school_id=?, csrf=? WHERE sid=? '
                'AND school_id=? AND csrf=? AND expires>?',
                (new_school,new_csrf,sid,old_school,old_csrf,int(time.time())))
            if updated.rowcount!=1:
                c.execute('ROLLBACK')
                raise Indeterminate('Stale session/school/CSRF; reauthenticate')
            c.execute('CREATE TABLE IF NOT EXISTS session_school_audit '
                      '(sid_sha TEXT, actor_id TEXT, old_school TEXT, new_school TEXT, event_utc INTEGER)')
            c.execute('INSERT INTO session_school_audit VALUES(?,?,?,?,?)',
                (hashlib.sha256(sid.encode()).hexdigest(),actor_id,old_school,new_school,int(time.time())))
            c.execute('COMMIT')
            return {'school_id':new_school,'csrf':new_csrf}

    def del_session(self,sid):
        with self.connect() as c:
            c.execute('DELETE FROM sessions WHERE sid=?',(sid,))

    def start_shell(self,school_id,key,payload):
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            op=c.execute('SELECT * FROM operations WHERE school_id=? AND op_key=?',(school_id,key)).fetchone()
            if op:
                if op['payload_sha']!=digest: raise Conflict('Idempotency key reused with different payload')
                if op['status']!='COMMITTED': raise Indeterminate('Operation pending or unconfirmed; no automatic replay')
                row=c.execute('SELECT * FROM shells WHERE shell_id=? AND school_id=?',(op['shell_id'],school_id)).fetchone()
                if not row: raise Indeterminate('Operation mapping missing')
                return dict(row),False
            exists=c.execute('SELECT 1 FROM shells WHERE school_id=? AND academic_year=? AND grade=? AND subject=? AND curriculum_stream=?',
                (school_id,*[payload[k] for k in ('academic_year','grade','subject','curriculum_stream')])).fetchone()
            if exists: raise Conflict('Shell classification already exists; use a new idempotency key only for a new classification')
            # A new key cannot bypass a PENDING/QUARANTINED notebook operation.
            claimed=c.execute('SELECT op_key FROM shell_claims WHERE school_id=? AND scope_hash=?',(school_id,digest)).fetchone()
            if claimed:raise Conflict('Shell scope already claimed by another operation; manual reconciliation required')
            shell_id=str(uuid.uuid4())
            c.execute('INSERT INTO shell_claims VALUES(?,?,?)',(school_id,digest,key))
            c.execute('INSERT INTO operations VALUES(?,?,?,?,?)',(school_id,key,digest,shell_id,'PENDING'))
            c.execute('COMMIT')
            return {'shell_id':shell_id,'school_id':school_id,**payload},True

    def complete_shell(self,school_id,key,record,notebook_id):
        if not notebook_id.startswith('notebook:'):
            raise Indeterminate('Native notebook id invalid')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            op=c.execute('SELECT * FROM operations WHERE school_id=? AND op_key=?',(school_id,key)).fetchone()
            if not op or op['status']!='PENDING': raise Indeterminate('Operation changed during native creation')
            c.execute('INSERT INTO shells VALUES(?,?,?,?,?,?,?,0)',(record['shell_id'],school_id,
                record['academic_year'],record['grade'],record['subject'],record['curriculum_stream'],notebook_id))
            c.execute("UPDATE operations SET status='COMMITTED' WHERE school_id=? AND op_key=?",(school_id,key))
            c.execute('COMMIT')
        return self.shell(school_id,record['shell_id'])

    def quarantine(self,school_id,key):
        with self.connect() as c:
            c.execute("UPDATE operations SET status='QUARANTINED' WHERE school_id=? AND op_key=? AND status='PENDING'",(school_id,key))

    def list_shells(self,school_id):
        with self.connect() as c:
            return [dict(r) for r in c.execute('SELECT * FROM shells WHERE school_id=? ORDER BY academic_year,grade,subject,curriculum_stream',(school_id,))]

    def shell(self,school_id,shell_id):
        with self.connect() as c:
            r=c.execute('SELECT * FROM shells WHERE school_id=? AND shell_id=?',(school_id,shell_id)).fetchone()
            return dict(r) if r else None

    def archive(self,school_id,shell_id):
        with self.connect() as c:
            c.execute('UPDATE shells SET archived=1 WHERE school_id=? AND shell_id=?',(school_id,shell_id))
            return self.shell(school_id,shell_id)

    def add_material(self,source_id,shell_id,school_id,title,sha256,filename,license,retention):
        with self.connect() as c:
            c.execute('INSERT INTO materials(source_id,shell_id,school_id,title,sha256,original_name,license,retention) VALUES(?,?,?,?,?,?,?,?)',
                (source_id,shell_id,school_id,title,sha256,filename,license,retention))

    def material(self,source_id,shell_id,school_id):
        with self.connect() as c:
            r=c.execute('SELECT * FROM materials WHERE source_id=? AND shell_id=? AND school_id=?',(source_id,shell_id,school_id)).fetchone()
            return dict(r) if r else None

    def list_materials(self,school_id,shell_id):
        with self.connect() as c:
            return [dict(r) for r in c.execute('SELECT * FROM materials WHERE school_id=? AND shell_id=? ORDER BY title',(school_id,shell_id))]

    def start_material(self,school_id,shell_id,key,digest):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            op=c.execute('SELECT * FROM material_operations WHERE school_id=? AND shell_id=? AND op_key=?',
                (school_id,shell_id,key)).fetchone()
            if op:
                if op['payload_sha']!=digest:raise Conflict('Upload idempotency key reused with different content/metadata')
                if op['status']!='COMMITTED':raise Indeterminate('Upload pending or ACK lost; never automatically resend')
                existing=self.material(op['source_id'],shell_id,school_id)
                if not existing:raise Indeterminate('Upload material mapping missing')
                c.execute('COMMIT')
                return existing,False
            claimed=c.execute('SELECT op_key FROM material_claims WHERE school_id=? AND shell_id=? AND payload_sha=?',
                (school_id,shell_id,digest)).fetchone()
            if claimed:raise Conflict('Material payload already claimed by another operation; manual reconciliation required')
            c.execute('INSERT INTO material_claims VALUES(?,?,?,?)',(school_id,shell_id,digest,key))
            c.execute('INSERT INTO material_operations VALUES(?,?,?,?,?,NULL)',(school_id,shell_id,key,digest,'PENDING'))
            c.execute('COMMIT')
            return None,True

    def finish_material(self,school_id,shell_id,key,source_id,title,sha256,filename,license,retention):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            op=c.execute('SELECT * FROM material_operations WHERE school_id=? AND shell_id=? AND op_key=?',
                (school_id,shell_id,key)).fetchone()
            if not op or op['status']!='PENDING':raise Indeterminate('Upload operation state unexpectedly changed')
            c.execute('INSERT INTO materials(source_id,shell_id,school_id,title,sha256,original_name,license,retention) VALUES(?,?,?,?,?,?,?,?)',
                (source_id,shell_id,school_id,title,sha256,filename,license,retention))
            c.execute("UPDATE material_operations SET status='COMMITTED',source_id=? WHERE school_id=? AND shell_id=? AND op_key=?",(source_id,school_id,shell_id,key))
            c.execute('COMMIT')

    def quarantine_material(self,school_id,shell_id,key):
        with self.connect() as c:
            c.execute("UPDATE material_operations SET status='QUARANTINED' WHERE school_id=? AND shell_id=? AND op_key=? AND status='PENDING'",(school_id,shell_id,key))
