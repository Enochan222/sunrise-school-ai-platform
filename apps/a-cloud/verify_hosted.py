"""Real provider smoke via A HTTP application. Private config/password stay outside Git."""
import base64
import hashlib
import hmac
import io
import json
import re
import struct
import sys
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from reportlab.pdfgen.canvas import Canvas
from cloud_app import Config, build_app, COOKIE

def totp(secret):
    key=base64.b32decode(secret+'='*((8-len(secret)%8)%8))
    raw=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest()
    offset=raw[-1]&15
    return str((struct.unpack('>I',raw[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)

def main():
    private=Path(sys.argv[1]); runtime=json.loads((private/'runtime.json').read_text())
    cfg=Config(**{k:v for k,v in runtime.items() if k!='origin'},origins=(runtime['origin'],))
    deployed=len(sys.argv)>2 and sys.argv[2]=='--deployed'
    client=(httpx.Client(base_url=runtime['origin'],trust_env=False,timeout=60,follow_redirects=False)
        if deployed else TestClient(build_app(cfg),base_url=runtime['origin']))
    log=[]
    def check(label,response,status):
        log.append({'step':label,'http_status':response.status_code,'expected':status,
                    'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        assert response.status_code==status, (label,response.status_code,response.text[:200])
        return response
    try:
        check('unauthenticated_shells',client.get('/vault/v1/shells'),401)
        page=check('login_page',client.get('/auth/login'),200)
        csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
        headers={'Origin':runtime['origin']}
        check('real_password_login',client.post('/auth/login',headers=headers,
            data={'password':(private/'initial-password.txt').read_text().strip(),'csrf':csrf}),200)
        state=check('real_pending_mfa',client.get('/auth/mfa/state'),200).json()
        headers['X-CSRF-Token']=state['csrf_token']
        factor_path=private/'test-factor.json'
        if state['factor_id']:
            factor=json.loads(factor_path.read_text())
            assert factor['factor_id']==state['factor_id']
        else:
            factor=check('real_totp_enrollment',client.post('/auth/mfa/enroll',headers=headers),200).json()
            factor_path.write_text(json.dumps(factor));factor_path.chmod(0o600)
        check('real_totp_verification',client.post('/auth/mfa/verify',headers=headers,
            data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
        state=check('real_admin_session',client.get('/auth/me'),200).json()
        headers['X-CSRF-Token']=state['csrf_token']
        check('shell_visibility',client.get('/vault/v1/shells'),200)
        run=hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:16]
        shell=check('create_synthetic_shell_notebook',client.post('/vault/v1/shells',headers={**headers,'Idempotency-Key':'hosted-'+run},
            json={'academic_year':'2026-2027','grade':'S1','subject':'Cloud smoke '+run,'curriculum_stream':'synthetic'}),201).json()
        root='/vault/v1/shells/'+shell['shell_id']
        output=io.BytesIO(); pdf=Canvas(output);pdf.drawString(72,750,'Sunrise synthetic fractions hosted verification '+run);pdf.save()
        content=output.getvalue(); digest=hashlib.sha256(content).hexdigest()
        source=check('upload_real_encrypted_original',client.post(root+'/materials',headers={**headers,'Idempotency-Key':'pdf-'+run},
            files={'file':('synthetic.pdf',content,'application/pdf')},data={'title':'Synthetic trial PDF','license':'Owner synthetic fixture','retention':'trial evidence'}),201).json()
        assert source['state']=='READY' and source['sha256']==digest
        check('existing_notebook_materials',client.get(root+'/materials'),200)
        hits=check('scoped_search',client.post(root+'/search',headers=headers,json={'query':'fractions'}),200).json()
        assert hits['total_count']==1
        downloaded=check('original_pdf_download',client.get(root+'/materials/'+source['source_id']+'/download'),200)
        assert hashlib.sha256(downloaded.content).hexdigest()==digest
        log.append({'step':'original_sha256','result':'PASS','sha256':digest,'source_id':source['source_id'],'shell_id':shell['shell_id']})
        check('csrf_negative',client.post(root+'/search',headers={'Origin':runtime['origin']},json={'query':'fractions'}),403)
        stale_cookie=client.cookies.get(COOKIE)
        check('logout',client.post('/auth/logout',headers=headers),200)
        check('logged_out_denied',client.get('/vault/v1/shells'),401)
        replay=client.get('/vault/v1/shells',headers={'Cookie':COOKIE+'='+stale_cookie})
        log.append({'step':'revoked_cookie_replay','http_status':replay.status_code,'result':'PASS' if replay.status_code in (401,403) else 'FAIL'})
        assert replay.status_code in (401,403)
        page=check('login_again_page',client.get('/auth/login'),200)
        csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
        check('password_login_again',client.post('/auth/login',headers={'Origin':runtime['origin']},data={'password':(private/'initial-password.txt').read_text().strip(),'csrf':csrf}),200)
        pending_status=client.get('/vault/v1/shells').status_code
        log.append({'step':'mfa_still_required_after_relogin','http_status':pending_status,'result':'PASS' if pending_status in (401,403) else 'FAIL'})
        assert pending_status in (401,403)
        state=check('mfa_state_again',client.get('/auth/mfa/state'),200).json()
        headers['X-CSRF-Token']=state['csrf_token']
        # A provider rejects replay of a code used in the same TOTP interval.
        delay=31-int(time.time())%30
        time.sleep(delay)
        check('mfa_login_again',client.post('/auth/mfa/verify',headers=headers,
            data={'factor_id':factor['factor_id'],'code':totp(factor['secret'])}),200)
        state=check('session_again',client.get('/auth/me'),200).json()
        headers['X-CSRF-Token']=state['csrf_token']
        check('existing_shell_after_relogin',client.get(root),200)
        check('final_logout',client.post('/auth/logout',headers=headers),200)
    finally:
        (private.parent/('deployed-smoke.json' if deployed else 'hosted-provider-smoke.json')).write_text(json.dumps(log,indent=2))
        print(json.dumps(log,indent=2))

if __name__=='__main__':main()
