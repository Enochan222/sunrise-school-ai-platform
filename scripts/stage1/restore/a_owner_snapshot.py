"""Read A SourceOwner/Shell rows ONLY inside isolated A physical private network.

Output goes to a private pipe to the Native ON verifier, never to GitHub,
logs, public endpoints or durable user-facing evidence.
"""
from __future__ import annotations
import json
import os
from websockets.sync.client import connect


def require(condition):
    if not condition:raise RuntimeError('A private SourceOwner snapshot unavailable')


def rpc(ws,i,method,args):
    ws.send(json.dumps({'id':i,'method':method,'params':args},separators=(',',':')))
    reply=json.loads(ws.recv(timeout=15))
    require(reply.get('id')==i and not reply.get('error'))
    return reply['result']


def main():
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')=='YES')
    keys=('A_SURREAL_USER','A_SURREAL_PASSWORD','A_SURREAL_NAMESPACE',
          'A_SURREAL_DATABASE')
    require(all(os.environ.get(k) for k in keys))
    require(os.environ.get('SURREAL_URL')=='ws://a_db:8000/rpc')
    with connect('ws://a_db:8000/rpc',subprotocols=['json'],
                 open_timeout=10,max_size=4*1024*1024) as ws:
        rpc(ws,1,'signin',[{'user':os.environ['A_SURREAL_USER'],
                            'pass':os.environ['A_SURREAL_PASSWORD']}])
        rpc(ws,2,'use',[os.environ['A_SURREAL_NAMESPACE'],
                        os.environ['A_SURREAL_DATABASE']])
        rows={}
        for index,table in enumerate(('source_owner','content_shell'),start=3):
            results=rpc(ws,index,'query',[f'SELECT * FROM {table} LIMIT 10001;',{}])
            require(isinstance(results,list) and len(results)==1
                    and results[0].get('status')=='OK'
                    and isinstance(results[0].get('result'),list)
                    and len(results[0]['result'])<=10000)
            rows[table]=results[0]['result']
    print(json.dumps({'classification':'PRIVATE_A_OWNER_SNAPSHOT_NOT_ACCEPTANCE',
                      'source_owner':rows['source_owner'],
                      'content_shell':rows['content_shell']},
                     separators=(',',':'),sort_keys=True))


if __name__=='__main__':
    main()
