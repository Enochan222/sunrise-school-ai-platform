"""Verify private Owner recovery activation without emailing or exposing tokens."""
import json
import re
import secrets
import sys
import time
from pathlib import Path
import httpx
from verify_hosted import totp

private=Path(sys.argv[1]);cfg=json.loads((private/'runtime.json').read_text());log=[]
client=httpx.Client(base_url=cfg['origin'],trust_env=False,timeout=60,follow_redirects=False)
headers={'Origin':cfg['origin']}
def check(label,response,expected):
    allowed=(expected,) if isinstance(expected,int) else expected
    log.append({'step':label,'status':response.status_code,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    assert response.status_code in allowed,(label,response.status_code)
    return response
def activation_csrf():
    check('activation_page',client.get('/auth/activate'),200)
    headers['X-CSRF-Token']=check('activation_csrf',client.get('/auth/activation-csrf'),200).json()['csrf_token']
try:
    activation_csrf();new=secrets.token_urlsafe(32)
    candidate=private/('activation-password-candidate-'+str(time.time_ns())+'.txt');candidate.write_text(new);candidate.chmod(0o600)
    check('invalid_activation_denied',client.post('/auth/activate',headers=headers,data={'activation_code':'f'*64,'new_password':new,'confirm_password':new}),(400,401,403))
    response=httpx.post(cfg['url']+'/auth/v1/admin/generate_link',headers={'apikey':cfg['service_key']},
        json={'type':'recovery','email':cfg['admin_email'],'redirect_to':cfg['origin']+'/auth/activate'},trust_env=False,timeout=30)
    check('generate_private_recovery_no_email',response,200)
    result=response.json();token=result.get('hashed_token') or result.get('properties',{}).get('hashed_token');assert token
    token_file=private/('used-activation-'+str(time.time_ns())+'.json');token_file.write_text(json.dumps({'token_hash':token}));token_file.chmod(0o600)
    check('valid_owner_activation',client.post('/auth/activate',headers=headers,data={'activation_code':token}),200)
    check('activation_requires_mfa',client.get('/vault/v1/shells'),401)
    check('password_reset_before_mfa_denied',client.get('/account/recovery-password'),401)
    state=check('activation_pending_session',client.get('/auth/mfa/state'),200).json();headers['X-CSRF-Token']=state['csrf_token']
    factor=json.loads((private/'test-factor.json').read_text())
    time.sleep(31-int(time.time())%30)
    response=check('recovery_mfa',client.post('/auth/mfa/verify',headers=headers,data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
    assert response.json()['next']=='/account/recovery-password'
    check('password_reset_after_mfa_page',client.get('/account/recovery-password'),200)
    headers['X-CSRF-Token']=check('recovered_admin_session',client.get('/auth/me'),200).json()['csrf_token']
    check('owner_recovery_password_change',client.post('/account/recovery-password',headers=headers,data={'new_password':new,'confirm_password':new}),200)
    (private/'initial-password.txt').write_text(new);(private/'initial-password.txt').chmod(0o600)
    check('recovery_session_logged_out',client.get('/vault/v1/shells'),401)
    activation_csrf()
    check('used_activation_cannot_replay',client.post('/auth/activate',headers=headers,data={'activation_code':token,'new_password':new,'confirm_password':new}),(400,401,403))
    page=check('new_password_login_page',client.get('/auth/login'),200)
    csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
    check('recovered_new_password_login',client.post('/auth/login',headers={'Origin':cfg['origin']},data={'password':new,'csrf':csrf}),200)
    state=check('normal_pending_mfa',client.get('/auth/mfa/state'),200).json();headers['X-CSRF-Token']=state['csrf_token']
    time.sleep(31-int(time.time())%30)
    response=check('normal_mfa_after_recovery',client.post('/auth/mfa/verify',headers=headers,data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
    assert response.json()['next']=='/admin'
    check('normal_session_cannot_reset_without_recovery',client.get('/account/recovery-password'),403)
    check('read_after_recovery_and_login',client.get('/vault/v1/shells'),200)
    headers['X-CSRF-Token']=check('normal_admin_session',client.get('/auth/me'),200).json()['csrf_token']
    check('final_logout',client.post('/auth/logout',headers=headers),200)
finally:
    (private.parent/'deployed-activation-smoke.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
