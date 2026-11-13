#!/usr/bin/env python3
"""WP08 bounded A+Native SurrealDB inventory, read-only. IMPLEMENTED_UNTESTED.

Runs on verified private host or inside an isolated Open Notebook utility
container (without starting the Native API/Worker) using websockets v2 RPC.
Only emits row counts and deterministic digests. No original content, tokens,
passwords or student data are emitted. Synthetic records only.
"""
import hashlib
import json
import os
import re
import sys
from websockets.sync.client import connect

A_TABLES=('content_shell','vault_operation','vault_scope_claim','source_owner',
          'vault_session','vault_audit')
ON_TABLES=('notebook','source','reference','command','source_embedding')
TABLE_ID=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
MAX_ROWS=10000


def rpc(ws,sequence,method,args):
    ws.send(json.dumps({'id':sequence,'method':method,'params':args},separators=(',',':')))
    response=json.loads(ws.recv(timeout=15))
    if response.get('id')!=sequence or response.get('error'):
        raise RuntimeError('Private DB RPC failed at '+method)
    return response['result']


def survey(namespace,database,tables):
    url=os.environ.get('SURREAL_URL','ws://surrealdb:8000/rpc')
    if url!='ws://surrealdb:8000/rpc':
        raise RuntimeError('Read-only inventory requires isolated private network')
    if not all(re.fullmatch(r'[A-Za-z0-9_-]{1,100}',x) for x in (namespace,database)):
        raise ValueError('Wrong SurrealDB namespace/database')
    with connect(url,subprotocols=['json'],open_timeout=10,max_size=8*1024*1024) as ws:
        rpc(ws,1,'signin',[{'user':os.environ['SURREAL_USER'],'pass':os.environ['SURREAL_PASSWORD']}])
        rpc(ws,2,'use',[namespace,database])
        info=rpc(ws,3,'query',['INFO FOR DB;',{}])
        if not isinstance(info,list) or len(info)!=1 or info[0].get('status')!='OK':
            raise RuntimeError('Cannot attest DB tables')
        schemas=info[0]['result'].get('tables')
        if not isinstance(schemas,dict) or not set(tables).issubset(schemas):
            raise RuntimeError('Missing required A/ON DB tables: fail closed')
        records={}
        for number,table in enumerate(tables,start=4):
            if not TABLE_ID.fullmatch(table):raise ValueError('Invalid table name')
            output=rpc(ws,number,'query',[f'SELECT * FROM {table} LIMIT {MAX_ROWS+1};',{}])
            if not isinstance(output,list) or len(output)!=1 or output[0].get('status')!='OK':
                raise RuntimeError('Cannot read DB table '+table)
            rows=output[0]['result']
            if not isinstance(rows,list) or len(rows)>MAX_ROWS:
                raise RuntimeError('Unbounded/malformed synthetic table '+table)
            canonical=sorted(json.dumps(row,sort_keys=True,ensure_ascii=False,
                           separators=(',',':')) for row in rows)
            digest=hashlib.sha256(('\n'.join(canonical)).encode('utf-8')).hexdigest()
            records[table]={'count':len(rows),'canonical_sha256':digest}
        return {'namespace':namespace,'database':database,'tables':records}


def main():
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        raise SystemExit(69)
    a=survey(os.environ['VAULT_SURREAL_NAMESPACE'],
             os.environ['VAULT_SURREAL_DATABASE'],A_TABLES)
    on=survey(os.environ['ON_GRAPH_NAMESPACE'],os.environ['ON_GRAPH_DATABASE'],ON_TABLES)
    print(json.dumps({'classification':'DB_INVENTORY_ONLY_NOT_ACCEPTANCE',
                      'a_journal':a,'native':on},sort_keys=True))


if __name__=='__main__':main()
