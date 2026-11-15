#!/usr/bin/env python3
"""AT07 real Admin audit + independent signed synthetic-only data attestation.

IMPLEMENTED_UNTESTED. This *never* infers absence of real student data from
synthetic-looking labels. A separate Owner/Reviewer must audit all isolated
Native/A volumes and sign claims bound to the exact runtime identity.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

import httpx
from itsdangerous import URLSafeTimedSerializer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from surreal_store import RPC,SurrealConfig,_record,_digest


class CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csrf=None

    def handle_starttag(self,tag,attrs):
        if tag=='input':
            data=dict(attrs)
            if data.get('name')=='csrf':
                self.csrf=data.get('value')


def require(value,why):
    if not value:
        raise RuntimeError(why)


def read_limited(path,limit=32768):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=limit,
            'Missing, symlinked or oversized independent audit evidence')
    return json.loads(path.read_text(encoding='utf-8'))


def verify_independent_data_audit(args):
    """Cryptographically validate separate human-reviewed full volume evidence."""
    identity_bytes=args.runtime_identity.read_bytes()
    require(len(identity_bytes)<=1<<20 and not args.runtime_identity.is_symlink(),
            'Runtime identity path is unbounded or symlinked')
    identity=json.loads(identity_bytes)
    require(identity.get('source_commit')==args.source_sha
            and identity.get('source_tree')==args.source_tree
            and identity.get('context')==args.context
            and identity.get('project')==args.project,
            'Independent audit cannot bind to different runtime project/revision')
    envelope=read_limited(args.owner_attestation)
    payload=envelope.get('payload')
    require(isinstance(payload,dict) and set(envelope)=={'payload','signature_ed25519'},
            'Independent signed audit payload missing')
    expected={'type':'S1_SYNTHETIC_DATA_INDEPENDENT_REVIEW_V1',
              'source_commit':args.source_sha,'source_tree':args.source_tree,
              'runtime_identity_sha256':hashlib.sha256(identity_bytes).hexdigest(),
              'context':args.context,'project':args.project,
              'scope':'FULL_ISOLATED_A_AND_NATIVE_DATABASES_AND_ORIGINAL_FILES',
              'reviewed_synthetic_only':True,'real_student_data_present':False,
              'reviewer_role':'OWNER_OR_INDEPENDENT_REVIEWER'}
    if any(payload.get(k)!=v for k,v in expected.items()):
        raise RuntimeError('Independent Owner/Reviewer data-scope attestation is incomplete')
    date=payload.get('reviewed_utc')
    require(isinstance(date,str) and date.endswith('Z')
            and len(date) in range(20,40),'Independent audit time absent')
    key_text=os.environ.get('VAULT_OWNER_AUDIT_PUBKEY_BASE64')
    require(bool(key_text),'Pinned independent Owner audit verification key missing')
    key=base64.b64decode(key_text,validate=True)
    signature=base64.b64decode(envelope['signature_ed25519'],validate=True)
    require(len(key)==32 and len(signature)==64,'Independent audit key/signature malformed')
    serialized=json.dumps(payload,sort_keys=True,separators=(',',':')).encode('utf-8')
    Ed25519PublicKey.from_public_bytes(key).verify(signature,serialized)
    return {'identity_sha256':expected['runtime_identity_sha256'],
            'attestation_sha256':hashlib.sha256(
                args.owner_attestation.read_bytes()).hexdigest(),
            'signature_verified':True,'full_volume_scope_signed_by_independent_reviewer':True}


def open_a_rpc():
    required=('VAULT_SURREAL_USER','VAULT_SURREAL_PASSWORD',
              'VAULT_SURREAL_NAMESPACE','VAULT_SURREAL_DATABASE')
    require(all(os.getenv(key) for key in required),
            'Private A DB credentials/namespace unavailable for independent Admin audit')
    return RPC(SurrealConfig(
        os.getenv('VAULT_SURREAL_WS_URL','ws://127.0.0.1:8000/rpc'),
        os.environ['VAULT_SURREAL_USER'],os.environ['VAULT_SURREAL_PASSWORD'],
        os.environ['VAULT_SURREAL_NAMESPACE'],os.environ['VAULT_SURREAL_DATABASE']))


def read_a_record(rpc,rid):
    result=rpc.query('SELECT * FROM type::record($rid);',{'rid':rid})
    require(isinstance(result,list) and result
            and isinstance(result[-1],list),'A audit database returned no readable record set')
    rows=result[-1]
    require(len(rows)<=1,'Duplicate A audit record identity')
    return rows[0] if rows else None


def verify_audit_row(rpc,rid,kind,actor,session_hash,school=None,previous=None):
    row=read_a_record(rpc,rid)
    require(isinstance(row,dict) and row.get('kind')==kind
            and row.get('actor_id')==actor
            and row.get('session_hash')==session_hash,
            'Admin audit record not durable under exact session/actor identity')
    if school is not None:
        require(row.get('school_id',row.get('active_school'))==school,
                'Admin audit school identity mismatch')
    if previous is not None:
        require(row.get('previous_school')==previous,
                'Admin school-switch previous identity mismatch')


def admin_login_switch_logout_audit(args):
    """Use real HTTPS Gateway, signed cookie and live SurrealDB audit readback."""
    url=urlsplit(args.gateway)
    require(url.scheme=='https' and url.hostname
            and not url.username and not url.password and url.path in ('','/')
            and not url.query and not url.fragment,
            'AT07 Admin audit requires verified HTTPS Gateway')
    password=os.environ.get('VAULT_TEST_ADMIN_PASSWORD')
    secret=os.environ.get('VAULT_SESSION_SECRET')
    actor=os.environ.get('VAULT_ACTOR_ID')
    require(password and secret and actor,'Private synthetic Admin credentials unavailable')
    identity=read_limited(args.runtime_identity,limit=1<<20)
    trusted=identity.get('gateway',{})
    ca=args.gateway_ca_file
    require(ca.is_file() and not ca.is_symlink() and ca.stat().st_size<=1<<20
            and hashlib.sha256(ca.read_bytes()).hexdigest()==trusted.get('tls_ca_sha256')
            and trusted.get('tls_verified') is True
            and trusted.get('origin')==args.gateway.rstrip('/'),
            'AT07 Admin HTTPS origin/CA is not same attested Gateway')
    rpc=open_a_rpc()
    with httpx.Client(base_url=args.gateway,verify=str(ca),trust_env=False,
                      timeout=15,follow_redirects=False) as client:
        page=client.get('/auth/login')
        require(page.status_code==200,'Actual private Admin login page unavailable')
        csrf=CSRFParser();csrf.feed(page.text)
        require(csrf.csrf,'Admin login form lacked CSRF')
        response=client.post('/auth/login',
            data={'password':password,'csrf':csrf.csrf},
            headers={'Accept':'application/json'})
        require(response.status_code==200
                and response.json().get('authenticated') is True,
                'Real synthetic Admin login failed')
        session_cookies=[h for h in response.headers.get_list('set-cookie')
                         if h.startswith('sunrise_a_sid=')]
        require(len(session_cookies)==1
                and 'secure' in session_cookies[0].lower()
                and 'httponly' in session_cookies[0].lower()
                and 'samesite=strict' in session_cookies[0].lower(),
                'HTTPS Admin login did not set Secure HttpOnly SameSite=Strict session cookie')
        signed_sid=client.cookies.get('sunrise_a_sid')
        require(bool(signed_sid),'Authenticated browser session cookie absent')
        sid=URLSafeTimedSerializer(secret,salt='sunrise-a-session').loads(
            signed_sid,max_age=3600)
        session_hash=_digest(sid)
        live=client.get('/auth/me')
        require(live.status_code==200,'Admin session not readable')
        principal=live.json()
        active=principal.get('school_id')
        schools=principal.get('available_schools')
        require(isinstance(active,str) and active.startswith('synthetic-')
                and isinstance(schools,list) and active in schools
                and len(schools)>=2
                and all(isinstance(s,str) and s.startswith('synthetic-')
                        for s in schools),
                'Two trusted synthetic schools required for Admin switch audit')
        verify_audit_row(rpc,_record('vault_audit','admin_login',sid),
                         'admin_login',actor,session_hash,school=active)
        other=next(s for s in schools if s!=active)
        switched=client.post('/auth/school',json={'school_id':other},
                             headers={'X-CSRF-Token':principal['csrf_token']})
        require(switched.status_code==200,'Trusted Admin school switch denied')
        rotated=switched.json()
        require(rotated.get('school_id')==other and
                rotated.get('csrf_token')!=principal['csrf_token'],
                'Server-held school switch/CSRF not rotated')
        verify_audit_row(rpc,_record('vault_audit','admin_school_switch',sid,
                                    other,rotated['csrf_token']),
                         'admin_school_switch',actor,session_hash,
                         school=other,previous=active)
        logout=client.post('/auth/logout',
                           headers={'X-CSRF-Token':rotated['csrf_token']})
        require(logout.status_code==200 and logout.json().get('logged_out') is True,
                'Admin logout did not complete')
        verify_audit_row(rpc,_record('vault_audit','admin_logout',sid),
                         'admin_logout',actor,session_hash,school=other)
        require(read_a_record(rpc,_record('vault_session',sid)) is None,
                'Logout left an active server session in private A DB')
        require(client.get('/auth/me').status_code==401,
                'Logout left a usable authenticated browser session')
    return {'admin_login_audit':'PASS','trusted_school_switch_audit':'PASS',
            'admin_logout_audit':'PASS','session_revocation':'PASS',
            'synthetic_two_school_probed':True}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gateway',required=True)
    parser.add_argument('--gateway-ca-file',required=True,type=Path)
    parser.add_argument('--runtime-identity',required=True,type=Path)
    parser.add_argument('--owner-attestation',required=True,type=Path)
    for name in ('context','project','source-sha','source-tree'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')=='YES'
            and os.getenv('VAULT_OBSERVER_ISOLATED_CONFIRM')=='YES',
            'AT07 isolated synthetic observer not confirmed')
    require(not args.out.exists(),'Admin audit evidence overwrite refused')
    result={'at_id':'S1-AT07-AUDIT','status':'NOT_RUN',
            'source_commit':args.source_sha,'source_tree':args.source_tree,
            'start_utc':datetime.now(timezone.utc).isoformat()}
    try:
        result['signed_data_scope']=verify_independent_data_audit(args)
        result['real_admin_session_audit']=admin_login_switch_logout_audit(args)
        result['status']='PASS'
    except Exception as error:
        result['status']='FAIL'
        result['error_type']=type(error).__name__
        raise
    finally:
        result['finished_utc']=datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
