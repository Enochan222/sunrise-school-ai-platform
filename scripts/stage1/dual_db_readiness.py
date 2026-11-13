#!/usr/bin/env python3
"""Dual physical SurrealDB v2.3.10 RPC auth/readiness and ON VIEWER smoke.

IMPLEMENTED_UNTESTED. Executes only in an operator-approved *new* synthetic
project, on dynamic loopback WS endpoints. No passwords or raw query results
are printed or saved. Root is never accepted in place of the scoped VIEWER.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from urllib.parse import urlsplit
from websockets.sync.client import connect

IDENT=re.compile(r'^[A-Za-z_][A-Za-z0-9_]{1,63}$')


def require(condition,msg):
    if not condition:
        raise RuntimeError(msg)


def validate_endpoint(url):
    u=urlsplit(url)
    if (u.scheme!='ws' or u.hostname!='127.0.0.1' or not u.port
            or u.path!='/rpc' or u.query or u.fragment
            or u.username or u.password):
        raise ValueError('SurrealDB RPC must use measured dynamic loopback endpoint')
    return url


class Client:
    def __init__(self,url):
        self.ws=connect(validate_endpoint(url),subprotocols=['json'],
                        open_timeout=8,close_timeout=3)
        self.counter=0

    def close(self):
        self.ws.close()

    def call(self,method,params):
        self.counter+=1
        self.ws.send(json.dumps({'id':self.counter,'method':method,'params':params},
                                separators=(',',':')))
        reply=json.loads(self.ws.recv(timeout=12))
        require(reply.get('id')==self.counter and not reply.get('error'),
                'Authenticated database RPC call rejected')
        return reply.get('result')

    def query(self,sql):
        blocks=self.call('query',[sql,{}])
        require(isinstance(blocks,list) and len(blocks)==1
                and isinstance(blocks[0],dict),
                'Malformed SurrealDB query envelope')
        return blocks[0]


def db_root(url,user,password,ns,db):
    c=Client(url)
    try:
        c.call('signin',[{'user':user,'pass':password}])
        c.call('use',[ns,db])
        response=c.query('INFO FOR DB;')
        require(response.get('status')=='OK' and isinstance(response.get('result'),dict),
                'Authenticated engine database not ready')
    except Exception:
        c.close()
        raise
    return c


def test_viewer(url,username,password,ns,db):
    c=Client(url)
    try:
        c.call('signin',[{'NS':ns,'DB':db,'user':username,'pass':password}])
        c.call('use',[ns,db])
        read=c.query('SELECT * FROM reference LIMIT 1;')
        require(read.get('status')=='OK',
                'Graph database VIEWER cannot SELECT from ON graph')
        # This is an authorization check, NEVER a real write by the viewer.
        denied=c.query('CREATE sunrise_s1_forbidden_probe SET synthetic=true;')
        require(denied.get('status')!='OK','Graph VIEWER unexpectedly has WRITE role')
    finally:
        c.close()


def provision_viewer(root,username,password):
    require(IDENT.fullmatch(username) is not None,'Unsafe ON viewer username')
    require(len(password)>=24 and "'" not in password and '\\' not in password,
            'Graph VIEWER secret unsafe for SurrealQL v2 CREATE USER syntax')
    # Fresh isolated ON database only; no existing user is modified.
    existing=root.query('INFO FOR DB;')
    require(existing.get('status')=='OK','Cannot inspect ON DB users')
    users=existing['result'].get('users')
    require(isinstance(users,dict) and username not in users,
            'Viewer already exists; never reset or replace existing credentials')
    result=root.query(
        "DEFINE USER "+username+" ON DATABASE PASSWORD '"+password+"' ROLES VIEWER;")
    require(result.get('status')=='OK','Native DB-only VIEWER provisioning failed')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--a-url',required=True)
    p.add_argument('--on-url',required=True)
    p.add_argument('--provision-new-viewer',action='store_true')
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or (
            os.getenv('VAULT_EXCLUSIVE_SYNTHETIC_PROJECT')!='YES'):
        p.error('Exclusive new synthetic runtime required')
    require(validate_endpoint(args.a_url)!=validate_endpoint(args.on_url),
            'A Journal and ON Graph may not share physical endpoint')
    names=('A_SURREAL_USER','A_SURREAL_PASSWORD','A_SURREAL_NAMESPACE',
           'A_SURREAL_DATABASE','ON_SURREAL_USER','ON_SURREAL_PASSWORD',
           'ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE','ON_GRAPH_VIEWER_USER',
           'ON_GRAPH_VIEWER_PASSWORD')
    require(all(os.getenv(n) for n in names),'Explicit dual DB credentials/identity required')
    require(os.environ['A_SURREAL_PASSWORD']!=os.environ['ON_SURREAL_PASSWORD']
            and os.environ['ON_GRAPH_VIEWER_PASSWORD'] not in (
                os.environ['A_SURREAL_PASSWORD'],os.environ['ON_SURREAL_PASSWORD']),
            'Independent A/ON/Viewer trust domains required')
    for key in ('A_SURREAL_NAMESPACE','A_SURREAL_DATABASE',
                'ON_GRAPH_NAMESPACE','ON_GRAPH_DATABASE'):
        require(IDENT.fullmatch(os.environ[key]) is not None,
                'Unsafe namespace/database identity')
    a=db_root(args.a_url,os.environ['A_SURREAL_USER'],
              os.environ['A_SURREAL_PASSWORD'],
              os.environ['A_SURREAL_NAMESPACE'],os.environ['A_SURREAL_DATABASE'])
    try:
        on=db_root(args.on_url,os.environ['ON_SURREAL_USER'],
                   os.environ['ON_SURREAL_PASSWORD'],
                   os.environ['ON_GRAPH_NAMESPACE'],os.environ['ON_GRAPH_DATABASE'])
        try:
            if args.provision_new_viewer:
                provision_viewer(on,os.environ['ON_GRAPH_VIEWER_USER'],
                                 os.environ['ON_GRAPH_VIEWER_PASSWORD'])
            test_viewer(args.on_url,os.environ['ON_GRAPH_VIEWER_USER'],
                        os.environ['ON_GRAPH_VIEWER_PASSWORD'],
                        os.environ['ON_GRAPH_NAMESPACE'],os.environ['ON_GRAPH_DATABASE'])
            # Root password from one physical engine cannot sign into the other.
            negative=Client(args.on_url)
            try:
                try:
                    negative.call('signin',[{'user':os.environ['A_SURREAL_USER'],
                                            'pass':os.environ['A_SURREAL_PASSWORD']}])
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError('A root credentials accepted by ON physical engine')
            finally:
                negative.close()
        finally:
            on.close()
    finally:
        a.close()
    print(json.dumps({'dual_physical_engines':'RPC_READY',
                      'root_secrets_separate':True,'graph_viewer_read_only':'PASS',
                      'cross_engine_root_denied':True,'source_status':'IMPLEMENTED_UNTESTED',
                      'formal_acceptance':'NOT_RUN'},sort_keys=True))


if __name__=='__main__':
    main()
