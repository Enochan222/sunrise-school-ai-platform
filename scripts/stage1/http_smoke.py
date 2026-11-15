"""Real loopback Uvicorn process smoke (NOT native runtime acceptance)."""
import base64,hashlib,io,os,re,secrets,signal,subprocess,sys,tempfile,time
from pathlib import Path
import httpx
from argon2 import PasswordHasher

root=Path(__file__).resolve().parents[2]
env=dict(os.environ)
with tempfile.TemporaryDirectory() as td:
    env.update(VAULT_ADMIN_PASSWORD_HASH=PasswordHasher().hash('synthetic-http-only'),
        VAULT_SESSION_SECRET=secrets.token_urlsafe(48),VAULT_ENCRYPTION_KEY=secrets.token_urlsafe(48),
        VAULT_SCHOOL_ID='synthetic-school',VAULT_ACTOR_ID='synthetic-admin',
        VAULT_SQLITE_FILE=str(Path(td)/'journal.sqlite3'),
        VAULT_NATIVE_URL='http://127.0.0.1:8001',VAULT_NATIVE_PASSWORD='synthetic-native-no-provider',
        VAULT_COOKIE_SECURE='false',VAULT_STORE_BACKEND='synthetic_sqlite')
    p=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--host','127.0.0.1','--port','18765','--no-access-log'],
        cwd=root/'apps'/'a-vault',env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        client=httpx.Client(base_url='http://127.0.0.1:18765',trust_env=False)
        for _ in range(100):
            try:
                r=client.get('/health',timeout=.4)
                if r.status_code==200:break
            except (httpx.RequestError,httpx.TimeoutException):pass
            time.sleep(.08)
        else:raise AssertionError('gateway did not listen on loopback')
        assert r.json()['gateway']=='running'
        assert client.get('/vault/v1/shells').status_code==401
        page=client.get('/auth/login')
        csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
        login=client.post('/auth/login',data={'password':'synthetic-http-only','csrf':csrf})
        assert login.status_code==200,login.text
        token=login.json()['csrf_token']
        assert client.get('/admin').status_code==200
        assert client.get('/vault/v1/shells').json()=={'shells':[]}
        # Native API isn't running: create must FAIL CLOSED, not synthesize a notebook.
        bad=client.post('/vault/v1/shells',headers={'Idempotency-Key':'synthetic-http-create','X-CSRF-Token':token},json={
            'academic_year':'2026','grade':'P4','subject':'Math','curriculum_stream':'HK'})
        assert bad.status_code==503,bad.text
        assert client.get('/vault/v1/shells').json()['shells']==[]
        assert client.post('/auth/logout',headers={'X-CSRF-Token':token}).status_code==200
        assert client.get('/admin').status_code==401
        print('HTTP_LOOPBACK_SMOKE PASS (Uvicorn PID='+str(p.pid)+', native/DB/worker NOT_RUN)')
    finally:
        p.terminate()
        try:out,err=p.communicate(timeout=4)
        except subprocess.TimeoutExpired:p.kill();out,err=p.communicate()
        print('UVICORN_EXIT',p.returncode)
        if p.returncode not in (0,-15):print(err.decode(errors='replace')[-1600:])
