"""Deployed synthetic Admin password negative/change/relogin verification."""
import json
import re
import secrets
import sys
import time
from pathlib import Path
import httpx
from verify_hosted import totp

private=Path(sys.argv[1]);cfg=json.loads((private/'runtime.json').read_text())
client=httpx.Client(base_url=cfg['origin'],trust_env=False,timeout=60,follow_redirects=False)
factor=json.loads((private/'test-factor.json').read_text());log=[]
headers={'Origin':cfg['origin']}
def check(label,response,expected):
    allowed=(expected,) if isinstance(expected,int) else expected
    log.append({'step':label,'status':response.status_code,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    assert response.status_code in allowed,(label,response.status_code,response.text[:200])
    return response
def password_login(password,expected=200):
    page=check('login_page',client.get('/auth/login'),200)
    csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
    return check('password_login',client.post('/auth/login',headers=headers,data={'password':password,'csrf':csrf}),expected)
def mfa():
    state=check('pending_mfa',client.get('/auth/mfa/state'),200).json()
    headers['X-CSRF-Token']=state['csrf_token']
    time.sleep(31-int(time.time())%30)
    check('mfa',client.post('/auth/mfa/verify',headers=headers,data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
    headers['X-CSRF-Token']=check('live_admin_session',client.get('/auth/me'),200).json()['csrf_token']
try:
    old=(private/'initial-password.txt').read_text().strip();password_login(old);mfa()
    check('password_change_form',client.get('/account/password'),200)
    new=secrets.token_urlsafe(32);candidate=private/('password-candidate-'+str(time.time_ns())+'.txt')
    candidate.write_text(new);candidate.chmod(0o600)
    check('wrong_current_password_denied',client.post('/account/password',headers=headers,
        data={'current_password':'invalid synthetic current password','new_password':new,'confirm_password':new}),(400,401,403))
    check('mismatched_confirmation_denied',client.post('/account/password',headers=headers,
        data={'current_password':old,'new_password':new,'confirm_password':new+'mismatch'}),422)
    check('password_change',client.post('/account/password',headers=headers,
        data={'current_password':old,'new_password':new,'confirm_password':new}),200)
    (private/'initial-password.txt').write_text(new);(private/'initial-password.txt').chmod(0o600)
    check('old_session_denied',client.get('/vault/v1/shells'),401)
    password_login(old,(400,401));password_login(new);mfa()
    check('read_after_new_password_login',client.get('/vault/v1/shells'),200)
    check('final_logout',client.post('/auth/logout',headers=headers),200)
finally:
    (private.parent/'deployed-account-smoke.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
