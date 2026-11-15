#!/usr/bin/env python3
"""Real SurrealDB v2.3.10 WRONG-INDEX fail-start probe, never a mock PASS.

An exclusively allocated synthetic DB with a randomized name is intentionally
configured with a same-name/wrong-order UNIQUE index. Migration MUST fail closed.
Does not modify the intended A runtime database or any Work checkout.
"""
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from surreal_store import RPC,SurrealConfig,SurrealStore,SurrealUnavailable


def run():
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or os.getenv('VAULT_EXCLUSIVE_SCHEMA_PROBE')!='YES':
        print('RUNTIME_NOT_RUN: exclusive isolated schema test DB not authorized',file=sys.stderr)
        raise SystemExit(69)
    keys=('VAULT_SURREAL_WS_URL','VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
          'VAULT_SURREAL_NAMESPACE')
    if not all(os.getenv(k) for k in keys):
        print('RUNTIME_NOT_RUN: dedicated private Surreal credentials missing',file=sys.stderr)
        raise SystemExit(69)
    db='wp03_wrong_index_'+secrets.token_hex(6)
    config=SurrealConfig(os.environ[keys[0]],os.environ[keys[1]],os.environ[keys[2]],
                        os.environ[keys[3]],db)
    evidence={'utc':datetime.now(timezone.utc).isoformat(),'database':db,
              'case':'UNIQUE_NAME_MATCH_BUT_WRONG_FIELD_ORDER','result':'NOT_RUN'}
    try:
        client=RPC(config)
        client.query('DEFINE TABLE content_shell SCHEMALESS; '
                     'DEFINE INDEX shell_scope_unique ON content_shell '
                     'FIELDS grade, academic_year, school_id, subject, curriculum_stream UNIQUE;')
        try:
            SurrealStore(config,'synthetic-actor')
        except SurrealUnavailable:
            evidence['result']='PASS'
        else:
            evidence['result']='FAIL'
            raise AssertionError('A journal accepted a misordered UNIQUE index')
    except Exception as exc:
        if evidence['result']!='FAIL':evidence['result']='FAIL'
        evidence['error_type']=type(exc).__name__
        raise
    finally:
        evidence['end_utc']=datetime.now(timezone.utc).isoformat()
        out=Path(os.getenv('VAULT_SCHEMA_EVIDENCE','wp03-schema-drift-redacted.json'))
        out.write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps({'case':evidence['case'],'result':evidence['result'],'evidence':str(out)}))
    return 0


if __name__=='__main__':raise SystemExit(run())
