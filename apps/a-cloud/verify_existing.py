"""Read-only verification of the existing browser-uploaded Chinese fixture."""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
import httpx
from verify_hosted import totp

private=Path(sys.argv[1]);cfg=json.loads((private/'runtime.json').read_text())
factor=json.loads((private/'test-factor.json').read_text());log=[]
client=httpx.Client(base_url=cfg['origin'],trust_env=False,timeout=60,follow_redirects=False)
headers={'Origin':cfg['origin']}
def check(label,response,status):
    log.append({'step':label,'status':response.status_code,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    assert response.status_code==status,(label,response.status_code,response.text[:200])
    return response
try:
    page=check('login_page',client.get('/auth/login'),200)
    csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
    check('password_login',client.post('/auth/login',headers=headers,data={'password':(private/'initial-password.txt').read_text().strip(),'csrf':csrf}),200)
    state=check('pending_mfa',client.get('/auth/mfa/state'),200).json();headers['X-CSRF-Token']=state['csrf_token']
    check('mfa',client.post('/auth/mfa/verify',headers=headers,data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
    state=check('session',client.get('/auth/me'),200).json();headers['X-CSRF-Token']=state['csrf_token']
    shells=check('existing_shells',client.get('/vault/v1/shells'),200).json()['shells']
    shell=next(s for s in shells if s['subject']=='數學・試用教材');root='/vault/v1/shells/'+shell['shell_id']
    materials=check('existing_browser_material',client.get(root+'/materials'),200).json()['materials']
    source=next(s for s in materials if s['sha256']=='c3bfbf7ef563692b7fc1be0ddc6660086e2b35e988f8d519ab88e3c48a638556')
    hits=check('existing_chinese_search',client.post(root+'/search',headers=headers,json={'query':'分數'}),200).json()
    assert hits['total_count']==1 and hits['results'][0]['source_id']==source['source_id']
    response=check('existing_original_download',client.get(root+'/materials/'+source['source_id']+'/download'),200)
    assert hashlib.sha256(response.content).hexdigest()==source['sha256']
    log.append({'step':'original_sha256','result':'PASS','sha256':source['sha256'],'shell_id':shell['shell_id'],'source_id':source['source_id']})
    check('empty_scope_query_denied',client.post(root+'/search',headers=headers,json={'query':' '}),422)
    other=next(s for s in shells if s['shell_id']!=shell['shell_id'])
    check('cross_shell_download_denied',client.get('/vault/v1/shells/'+other['shell_id']+'/materials/'+source['source_id']+'/download'),404)
    check('final_logout',client.post('/auth/logout',headers=headers),200)
finally:
    (private.parent/'deployed-existing-content.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
