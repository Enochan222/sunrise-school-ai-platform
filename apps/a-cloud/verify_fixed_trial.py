"""One bounded real-HTTPS check of the Owner-approved fixed-password trial."""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
import httpx

private=Path(sys.argv[1]);cfg=json.loads((private/'runtime.json').read_text());log=[]
client=httpx.Client(base_url=cfg['origin'],trust_env=False,timeout=45,follow_redirects=False)
headers={'Origin':cfg['origin']}
def check(label,response,expected):
    allowed=(expected,) if isinstance(expected,int) else expected
    log.append({'step':label,'http_status':response.status_code,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    assert response.status_code in allowed,(label,response.status_code,response.text[:160])
    return response
try:
    health=check('public_https_health',client.get('/health'),200).json()
    assert health['authentication']=='PASSWORD_ONLY_SYNTHETIC_TRIAL'
    check('anonymous_business_denied',client.get('/vault/v1/shells'),401)
    page=check('login_page',client.get('/auth/login'),200)
    assert 'data-password-only-trial' in page.text
    csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
    check('wrong_password_denied',client.post('/auth/login',headers=headers,data={'password':'wrong synthetic trial password','csrf':csrf}),(400,401))
    response=check('fixed_password_login_without_mfa',client.post('/auth/login',headers=headers,data={'password':(private/'initial-password.txt').read_text().strip(),'csrf':csrf}),200)
    assert response.json()=={'authenticated':True,'next':'/admin'}
    state=check('authenticated_session_without_mfa',client.get('/auth/me'),200).json()
    headers['X-CSRF-Token']=state['csrf_token']
    page=check('library_page_no_password_change_required',client.get('/admin'),200)
    assert '/account/password' not in page.text
    shells=check('existing_shells',client.get('/vault/v1/shells'),200).json()['shells']
    shell=next(s for s in shells if s['subject']=='數學・試用教材');root='/vault/v1/shells/'+shell['shell_id']
    materials=check('existing_notebook_materials',client.get(root+'/materials'),200).json()['materials']
    source=next(s for s in materials if s['sha256']=='c3bfbf7ef563692b7fc1be0ddc6660086e2b35e988f8d519ab88e3c48a638556')
    hits=check('chinese_scoped_search',client.post(root+'/search',headers=headers,json={'query':'分數'}),200).json()
    assert hits['total_count']==1 and hits['results'][0]['source_id']==source['source_id']
    pdf=check('original_pdf_download',client.get(root+'/materials/'+source['source_id']+'/download'),200)
    assert pdf.headers['content-type'].startswith('application/pdf')
    assert hashlib.sha256(pdf.content).hexdigest()==source['sha256']
    log.append({'step':'original_sha256','result':'PASS','sha256':source['sha256']})
    check('csrf_denied',client.post(root+'/search',headers={'Origin':cfg['origin']},json={'query':'分數'}),403)
    stale=client.cookies.get('sunrise_cloud_session')
    check('logout',client.post('/auth/logout',headers=headers),200)
    check('logged_out_denied',client.get('/vault/v1/shells'),401)
    check('stale_cookie_denied',client.get('/vault/v1/shells',headers={'Cookie':'sunrise_cloud_session='+stale}),(401,403))
    access=private/'trial-access.txt'
    access.write_text('Sunrise Cloud 合成試用\n網址：https://sunrise-stage1-trial.vercel.app\n固定密碼：'+(private/'initial-password.txt').read_text().strip()+'\n毋須 MFA，毋須首次改密碼。\n登入後選「數學・試用教材」，可搜尋「分數」及下載原始 PDF。\n只用合成資料；此檔含登入密碼，請勿公開。\n');access.chmod(0o600)
finally:
    (private.parent/'fixed-password-live.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
