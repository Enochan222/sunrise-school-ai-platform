#!/usr/bin/env python3
"""Read-only per-physical-engine SurrealDB inventory for cold/isolated restore.

IMPLEMENTED_UNTESTED. Exactly ONE root engine is reachable from the
short-lived, network-scoped verifier. A and ON inventories are collected from
different Docker networks and independent root credentials, never one query.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from websockets.sync.client import connect

A_TABLES=('content_shell','vault_operation','vault_scope_claim','source_owner',
          'vault_session','vault_audit')
ON_TABLES=('notebook','source','reference','command','source_embedding')
MAX_ROWS=10000
IDENT=re.compile(r'^[A-Za-z_][A-Za-z0-9_]{1,63}$')


def require(condition,why):
    if not condition:raise RuntimeError(why)


def rpc(ws,number,method,args):
    ws.send(json.dumps({'id':number,'method':method,'params':args},separators=(',',':')))
    response=json.loads(ws.recv(timeout=20))
    require(response.get('id')==number and not response.get('error'),
            'Physical DB RPC authentication/query failed')
    return response.get('result')


def survey(role):
    require(role in ('a','on'),'Invalid physical DB role')
    prefix='A_SURREAL_' if role=='a' else 'ON_SURREAL_'
    user=os.getenv(prefix+'USER')
    password=os.getenv(prefix+'PASSWORD')
    ns=os.getenv('A_SURREAL_NAMESPACE' if role=='a' else 'ON_GRAPH_NAMESPACE')
    db=os.getenv('A_SURREAL_DATABASE' if role=='a' else 'ON_GRAPH_DATABASE')
    expected_url='ws://'+('a_db' if role=='a' else 'on_db')+':8000/rpc'
    require(all(isinstance(v,str) and v for v in (user,password,ns,db)),
            'Physical engine private credentials/namespace absent')
    require(IDENT.fullmatch(ns) and IDENT.fullmatch(db),
            'Physical engine namespace/database unsafe')
    url=os.getenv('SURREAL_URL')
    require(url==expected_url,'Inventory target not the verified physical engine')
    tables=A_TABLES if role=='a' else ON_TABLES
    with connect(url,subprotocols=['json'],open_timeout=10,max_size=8*1024*1024) as ws:
        rpc(ws,1,'signin',[{'user':user,'pass':password}])
        rpc(ws,2,'use',[ns,db])
        info=rpc(ws,3,'query',['INFO FOR DB;',{}])
        require(isinstance(info,list) and len(info)==1
                and info[0].get('status')=='OK','Cannot inspect physical DB')
        schemas=info[0]['result'].get('tables')
        require(isinstance(schemas,dict) and set(tables).issubset(schemas),
                'Missing required A or ON DB tables')
        records={}
        for i,table in enumerate(tables,start=4):
            result=rpc(ws,i,'query',[f'SELECT * FROM {table} LIMIT {MAX_ROWS+1};',{}])
            require(isinstance(result,list) and len(result)==1
                    and result[0].get('status')=='OK',
                    'Physical DB table read failed')
            rows=result[0]['result']
            require(isinstance(rows,list) and len(rows)<=MAX_ROWS,
                    'Unbounded/malformed physical engine table')
            canonical=sorted(json.dumps(row,sort_keys=True,ensure_ascii=False,
                               separators=(',',':')) for row in rows)
            records[table]={'count':len(rows),'canonical_sha256':hashlib.sha256(
                '\n'.join(canonical).encode('utf-8')).hexdigest()}
        return {'role':role,'namespace':ns,'database':db,'tables':records}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--role',choices=('a','on'),required=True)
    args=p.parse_args()
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')=='YES',
            'Dual physical inventory synthetic authorization missing')
    result=survey(args.role)
    print(json.dumps({'classification':'PHYSICAL_DB_INVENTORY_ONLY_NOT_ACCEPTANCE',
                      'physical_db':result},sort_keys=True))


if __name__=='__main__':main()
