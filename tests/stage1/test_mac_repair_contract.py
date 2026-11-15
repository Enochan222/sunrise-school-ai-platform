"""Synthetic regression for the Mac source-repair candidate."""
import importlib.util
from pathlib import Path
import sys
import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from config import Settings
from vault_app import build_app
import browser_admin_journey as browser
spec=importlib.util.spec_from_file_location('verify_native',ROOT/'scripts/stage1/restore/verify_native.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)

def test_browser_json_response_contract():
 assert browser.valid_json_login(200,'application/json; charset=utf-8',{'authenticated':True})
 for status,content,body in [(303,'application/json',{'authenticated':True}),(200,'text/html',{'authenticated':True}),(200,'application/json',{'authenticated':False}),(200,'application/json',{}),(True,'application/json',{'authenticated':True})]:
  assert not browser.valid_json_login(status,content,body)

def test_login_policy_and_foreign_origin_rejected(tmp_path):
 cfg=Settings(admin_hash=PasswordHasher().hash('synthetic-password'),session_secret='s'*60,encryption_key='e'*60,school_id='synthetic-a',actor_id='synthetic-admin',sqlite_file=str(tmp_path/'data.sqlite'),native_url='http://127.0.0.1:5055',native_password='synthetic-native-password',store_backend='synthetic_sqlite')
 with TestClient(build_app(cfg,native=object())) as c:
  assert c.get('/auth/login').headers['referrer-policy']=='same-origin'
  for origin in ('null','https://foreign.invalid'):
   assert c.post('/auth/login',headers={'Origin':origin},data={'password':'synthetic-password','csrf':'invalid'}).status_code==403

def test_native_identity_exact_match_and_fail_closed():
 e={'SURREAL_NAMESPACE':'on_ns','SURREAL_DATABASE':'on_db','VAULT_EXPECTED_ON_NAMESPACE':'on_ns','VAULT_EXPECTED_ON_DATABASE':'on_db'}
 assert verify.validated_on_identity(e)==('on_ns','on_db')
 for key in e:
  bad=dict(e);bad.pop(key)
  with pytest.raises(RuntimeError):verify.validated_on_identity(bad)
 for key in e:
  bad=dict(e);bad[key]='forged'
  with pytest.raises(RuntimeError):verify.validated_on_identity(bad)
