"""Strict read-only ON Graph VIEWER RPC on separately attested physical server.

Never send A Journal root or ON root credentials to this connection.
Use database-scoped SurrealDB v2 signin (NS/DB), not root signin.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from websockets.sync.client import connect

SHA64=re.compile(r'^[a-f0-9]{64}$')


class GraphViewerDenied(RuntimeError):
    pass


def require(condition):
    if not condition:raise GraphViewerDenied(
        'Native Graph read-only role must be independently authorized and verified')


def attest_viewer(identity_path,url,username,password,ns,db,a_ws_url,a_user,a_password):
    path=Path(identity_path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=1<<20)
    identity=json.loads(path.read_bytes())
    services=identity.get('services',{})
    require(identity.get('type')=='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED')
    require(set(services)=={'a_db','on_db','native'})
    require(services['a_db'].get('container_id')!=services['on_db'].get('container_id'))
    require(services['a_db'].get('network_id')!=services['on_db'].get('network_id'))
    require(services['a_db'].get('persistent_volume')!=services['on_db'].get('persistent_volume'))
    require(identity.get('dual_rpc',{}).get('authenticated') is True)
    require(identity['dual_rpc'].get('on_viewer_read_only') is True)
    require(identity['dual_rpc'].get('on_url')==url and
            identity['dual_rpc'].get('a_url')==a_ws_url)
    require(identity.get('on_namespace')==ns and identity.get('on_database')==db)
    require(identity.get('surreal_namespace') and identity.get('surreal_database'))
    require(hashlib.sha256(username.encode()).hexdigest()==
            identity['dual_rpc'].get('on_viewer_user_sha256'))
    require(username!=a_user and password!=a_password)
    require(isinstance(password,str) and len(password)>=24)
    uri=urlsplit(url)
    require(uri.scheme=='ws' and uri.hostname=='127.0.0.1' and uri.port
            and uri.path=='/rpc' and not uri.username and not uri.password
            and not uri.query and not uri.fragment)
    return identity


class ViewerRPC:
    def __init__(self,url,username,password,ns,db):
        self.url=url
        self.username=username
        self.password=password
        self.ns=ns
        self.db=db

    def query(self,sql,params=None):
        # No mutation, multiple statements, administration, dynamic SQL or
        # client-supplied ability to redefine a DB. One SELECT only.
        if (not isinstance(sql,str) or
                not re.match(r'^\s*SELECT\s',sql,re.IGNORECASE)
                or sql.count(';')>1
                or ';' in sql.rstrip().rstrip(';') or
                len(sql)>6000):
            raise GraphViewerDenied('ON Graph Viewer only permits one bounded SELECT')
        counter=0
        with connect(self.url,subprotocols=['json'],open_timeout=8,
                     close_timeout=3,max_size=4*1024*1024) as ws:
            def rpc(method,arguments):
                nonlocal counter
                counter+=1
                ws.send(json.dumps({'id':counter,'method':method,'params':arguments},
                                   separators=(',',':')))
                response=json.loads(ws.recv(timeout=15))
                require(response.get('id')==counter and not response.get('error'))
                return response.get('result')
            rpc('signin',[{'NS':self.ns,'DB':self.db,
                           'user':self.username,'pass':self.password}])
            rpc('use',[self.ns,self.db])
            result=rpc('query',[sql,params or {}])
            require(isinstance(result,list) and len(result)==1
                    and result[0].get('status')=='OK')
            return [item['result'] for item in result]
