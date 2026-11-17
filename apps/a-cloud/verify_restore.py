"""Restore a real A data/blob snapshot into a fresh isolated PostgreSQL fixture.

This verifies A logical data and encryption-key recovery, not hosted Auth DR.
"""
import ast
import hashlib
import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from cloud_app import Config, BUCKET

private=Path(sys.argv[1]); dsn=sys.argv[2]
raw=json.loads((private/'runtime.json').read_text())
cfg=Config(**{k:v for k,v in raw.items() if k!='origin'},origins=(raw['origin'],))
backup=private/'backup'; data=json.loads((backup/'a-data.json').read_text())
shutil.copy2(private/'runtime.json',backup/'keys-and-configuration.json')
(backup/'keys-and-configuration.json').chmod(0o600)
manifest=[]
for source in data['sources']:
    response=httpx.get(cfg.url+'/storage/v1/object/authenticated/'+BUCKET+'/'+source['original_path'],
        headers={'apikey':cfg.service_key},timeout=30,trust_env=False)
    response.raise_for_status(); cipher=response.content
    assert hashlib.sha256(cipher).hexdigest()==source['cipher_sha256']
    original=cfg.crypto('original-v1').decrypt(cipher)
    assert hashlib.sha256(original).hexdigest()==source['sha256']
    path=backup/(source['source_id'].split(':')[1]+'.bin');path.write_bytes(cipher);path.chmod(0o600)
    manifest.append({'source_id':source['source_id'],'original_sha256':source['sha256'],'cipher_sha256':source['cipher_sha256']})

# Recovery phase reads only the saved artifacts, with no provider access.
recovered=json.loads((backup/'keys-and-configuration.json').read_text())
recovered_cfg=Config(**{k:v for k,v in recovered.items() if k!='origin'},origins=(recovered['origin'],)).validate()
data=json.loads((backup/'a-data.json').read_text())
for source in data['sources']:
    cipher=(backup/(source['source_id'].split(':')[1]+'.bin')).read_bytes()
    assert hashlib.sha256(cipher).hexdigest()==source['cipher_sha256']
    original=recovered_cfg.crypto('original-v1').decrypt(cipher)
    assert hashlib.sha256(original).hexdigest()==source['sha256']
cfg=recovered_cfg

# Reuse the explicitly simplified Auth/Storage SQL harness, not provider internals.
tree=ast.parse(Path(__file__).with_name('test_cloud.py').read_text())
fixture=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pg')
bootstrap=next(n.value.value for n in fixture.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='bootstrap' for t in n.targets))
with psycopg.connect(dsn,autocommit=True) as conn:
    database_name=conn.info.dbname
    assert conn.execute("select count(*) from information_schema.tables where table_schema in ('auth','storage','vault_private')").fetchone()[0]==0
    conn.execute(bootstrap)
    conn.execute(next((Path(__file__).parent/'supabase/migrations').glob('*.sql')).read_text())
    for admin in data['admins']:
        conn.execute('insert into auth.users(id) values(%s)',(admin['user_id'],))
    for name in ('admins','shells','sources'):
        for row in data[name]:
            columns=list(row)
            values=[Jsonb(row[k]) if isinstance(row[k],dict) else row[k] for k in columns]
            conn.execute(sql.SQL('insert into vault_private.{} ({}) values ({})').format(
                sql.Identifier(name),sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder()*len(columns))),values)
    for source in data['sources']:
        conn.execute('insert into storage.objects(bucket_id,name) values(%s,%s)',(BUCKET,source['original_path']))
    session=str(uuid4());conn.execute("insert into auth.sessions values(%s,%s,'aal2',null)",(session,cfg.admin_id))
    conn.execute("set request.jwt.claim.role='service_role'");conn.execute('set role service_role')
    scope=cfg.schools[0]
    state=conn.execute('select public.vault_open_session(%s,%s,%s)',(cfg.admin_id,session,scope)).fetchone()[0]
    for source in data['sources']:
        restored=conn.execute('select public.vault_source(%s,%s,%s,%s,%s,%s)',
            (cfg.admin_id,session,scope,state['csrf_token'],source['shell_id'],source['source_id'])).fetchone()[0]
        assert restored['sha256']==source['sha256'] and restored['notebook_id']==source['notebook_id']
        assert restored['ai_usage_allowed'] is False and restored['approved_sharing'] is False
        hits=conn.execute('select public.vault_search(%s,%s,%s,%s,%s,%s,20)',
            (cfg.admin_id,session,scope,state['csrf_token'],source['shell_id'],'fractions')).fetchone()[0]
        assert hits['total_count']>=1
report={'result':'PASS','scope':'real hosted A snapshot + encrypted original + key restored into independent local PostgreSQL; hosted Auth DR NOT_VERIFIED',
        'shells':len(data['shells']),'sources':manifest,'database':database_name}
(backup.parent.parent/'logical-restore.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
