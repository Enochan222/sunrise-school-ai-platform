#!/usr/bin/env python3
"""WP09 S1-AT03/10/14/15 HTTPS/loopback real A Gateway negative/positive cases.

IMPLEMENTED_UNTESTED. Needs two already-created synthetic Shells and Sources
with positive searchable text. No mock, Native direct query, or destructive
Archive action. Never print passwords, cookies, bearer tokens or PDF bytes.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
import stat
import time
from cryptography.hazmat.primitives import serialization
from make_synthetic_service_jwt import build_tokens
import httpx
import jwt

# The trusted repository root, independent of the current working directory.
ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wp01_network_boundary_probe import verify_manifest
from runtime_identity import tls_gateway_identity
from acceptance.evidence_inventory import verify_clean_source


class CSRF(HTMLParser):
    value=None
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if tag=='input' and data.get('name')=='csrf':self.value=data.get('value')


def expect(condition,what):
    if not condition:raise AssertionError(what)


def authenticate(client):
    page=client.get('/auth/login')
    expect(page.status_code==200,'Auth login form HTTP status')
    parser=CSRF();parser.feed(page.text)
    expect(bool(parser.value),'Login CSRF missing')
    password=os.environ.get('VAULT_TEST_ADMIN_PASSWORD')
    if not password:raise RuntimeError('Private synthetic admin password missing')
    response=client.post('/auth/login',data={'password':password,'csrf':parser.value},
                         headers={'Accept':'application/json'})
    expect(response.status_code==200 and response.json().get('authenticated') is True,'Login denied')
    me=client.get('/auth/me')
    expect(me.status_code==200,'Session not active')
    return me.json()


def change_school(client,session,school):
    response=client.post('/auth/school',json={'school_id':school},
        headers={'X-CSRF-Token':session['csrf_token']})
    expect(response.status_code==200,'Trusted School switch denied')
    updated=client.get('/auth/me')
    expect(updated.status_code==200,'Rotated session unreadable')
    result=updated.json()
    expect(result['school_id']==school and
           result['csrf_token']!=session['csrf_token'],'School/CSRF did not rotate')
    return result


def authorized_materials(client,shell):
    result=client.get('/vault/v1/shells/'+shell+'/materials')
    expect(result.status_code==200,'Owned materials list rejected')
    data=result.json().get('materials')
    expect(isinstance(data,list),'Owned materials not a list')
    for material in data:
        expect(isinstance(material.get('source_id'),str),'Missing source id')
        expect(isinstance(material.get('sha256'),str) and len(material['sha256'])==64,'Original hash missing')
        expect(material.get('version')==1,'Immutable initial version missing')
    return data


def case_03(client,args,session):
    session=change_school(client,session,args.school_a) if session['school_id']!=args.school_a else session
    materials=authorized_materials(client,args.shell_a)
    expect(any(x['source_id']==args.source_a for x in materials),'A source not in A shell')
    result=client.post('/vault/v1/shells/'+args.shell_a+'/search',
        headers={'X-CSRF-Token':session['csrf_token']},json={'query':args.query_a})
    expect(result.status_code==200,'Scoped text search rejected')
    body=result.json()
    expect(body.get('search_type')=='text' and isinstance(body.get('results'),list),'Wrong search type')
    hits=[r['source_id'] for r in body['results']]
    expect(args.source_a in hits,'A searchable synthetic positive not found')
    expect(args.source_b not in hits,'CROSS-SCHOOL LEAK in A Search')
    return session


def case_10(client,args,session):
    session=change_school(client,session,args.school_a) if session['school_id']!=args.school_a else session
    for path in (f'/vault/v1/shells/{args.shell_a}/materials/{args.source_b}/download',
                 f'/vault/v1/shells/{args.shell_b}/materials/{args.source_b}/download',
                 '/api/sources/'+args.source_b,'/api/sources/'+args.source_b+'/download',
                 '/api/preview/'+args.source_b,'/api/events','/api/stream'):
        response=client.get(path)
        expect(response.status_code in (401,403,404),'Foreign Source/preview/SSE produced HTTP access')
        expect(not response.content.startswith(b'%PDF-'),'Foreign original bytes leaked')
    return session


def case_14(client,args,session):
    session=change_school(client,session,args.school_a) if session['school_id']!=args.school_a else session
    # Both schools must actually be provisioned by the authoritative Gateway.
    # Otherwise an unknown-school rejection does not exercise school IDOR.
    allowed=session.get('available_schools')
    expect(isinstance(allowed,list) and args.school_a in allowed and
           args.school_b in allowed and args.school_a!=args.school_b,
           'AT14 requires both synthetic schools independently provisioned')
    expected=authorized_materials(client,args.shell_a)
    by_id={m['source_id']:m for m in expected}
    expect(args.source_a in by_id and args.source_b not in by_id,
           'Admin source ownership baseline invalid')
    positive='VAULT_TEST_SERVICE_A'
    negatives=('VAULT_TEST_SERVICE_WRONG_SCOPE',
               'VAULT_TEST_SERVICE_FOREIGN_SCHOOL',
               'VAULT_TEST_SERVICE_EXPIRED',
               'VAULT_TEST_SERVICE_WRONG_AUDIENCE',
               'VAULT_TEST_SERVICE_INVALID_SIGNATURE',
               'VAULT_TEST_SERVICE_NOT_YET_VALID',
               'VAULT_TEST_SERVICE_MISSING_CLAIMS')
    # Re-sign only at actual AT14 execution. A full 15-case campaign may take
    # longer than the required max 300-second JWT lifetime.
    private_path=os.getenv('VAULT_AT14_SIGNING_KEY_FILE')
    issuer=os.getenv('VAULT_AT14_ISSUER')
    audience=os.getenv('VAULT_AT14_AUDIENCE')
    if not private_path or not issuer or not audience:
        raise RuntimeError('AT14 synthetic RSA private key path/issuer/audience absent')
    key_file=Path(private_path)
    if (key_file.is_symlink() or not key_file.is_file()
            or key_file.resolve().is_relative_to(ROOT)
            or not 0<key_file.stat().st_size<=8192
            or stat.S_IMODE(key_file.stat().st_mode)!=0o600):
        raise RuntimeError('AT14 private fixture key missing/unsafe/in source tree')
    signing_key=serialization.load_pem_private_key(key_file.read_bytes(),password=None)
    values=build_tokens(signing_key,issuer,audience,args.school_a,args.school_b,
                        int(time.time()))
    expect(set(values)=={positive,*negatives},
           'AT14 missing exact complete token-claim matrix')
    url='/vault/v1/shells/'+args.shell_a+'/materials'
    # The Admin cookie MUST NOT participate in any Service JWT assertion.
    # Strict Gateway CA remains enabled and no redirects may be followed.
    with httpx.Client(base_url=args.gateway,timeout=35,follow_redirects=False,
                      trust_env=False,verify=str(args.gateway_ca_file)) as service_client:
        allowed=service_client.get(url,headers={'Authorization':'Bearer '+values[positive]})
    expect(allowed.status_code==200,'Valid scoped Service JWT materials read denied')
    rows=allowed.json().get('materials')
    expect(isinstance(rows,list),'JWT returned invalid Materials schema')
    owned={m.get('source_id'):m for m in rows if isinstance(m,dict)}
    expect(len(owned)==len(rows) and set(owned)==set(by_id),
           'JWT response omitted/duplicated/leaked source ownership')
    for source_id,baseline in by_id.items():
        actual=owned[source_id]
        expect(actual.get('version')==baseline.get('version')
               and actual.get('sha256')==baseline.get('sha256')
               and isinstance(actual.get('sha256'),str)
               and re.fullmatch(r'[0-9a-f]{64}',actual['sha256']) is not None,
               'JWT source version/SHA differs from owned Admin baseline')
    for key in negatives:
        # A negative is meaningful only if it is rejected for the intended
        # claim, not because the entire fixture set aged out during a slow run.
        claims=jwt.decode(values[key],options={'verify_signature':False,
            'verify_exp':False,'verify_nbf':False,'verify_aud':False})
        current=int(time.time())
        expect(claims.get('iss')==issuer and claims.get('sub')=='synthetic-at14-service',
               'AT14 invalid negative token baseline issuer/subject')
        if key=='VAULT_TEST_SERVICE_EXPIRED':
            expect(claims.get('exp',current)>=0 and claims['exp']<current-15,
                   'AT14 expired token is not demonstrably expired')
        else:
            expect(type(claims.get('exp')) is int and claims['exp']>current+15,
                   'AT14 negative token expired before intended claim test')
        if key=='VAULT_TEST_SERVICE_NOT_YET_VALID':
            expect(claims.get('nbf',0)>current+15,
                   'AT14 future not-before reached before negative request')
        else:
            expect(claims.get('nbf',current+1)<=current,
                   'AT14 other negative accidentally future-dated')
        expect((claims.get('aud')!=audience)==(key=='VAULT_TEST_SERVICE_WRONG_AUDIENCE'),
               'AT14 wrong-audience negative confounded')
        expect((claims.get('school_id')!=args.school_a)==
               (key=='VAULT_TEST_SERVICE_FOREIGN_SCHOOL'),
               'AT14 foreign-school negative confounded')
        expect((claims.get('scope')!='vault.materials.read')==
               (key=='VAULT_TEST_SERVICE_WRONG_SCOPE'),
               'AT14 wrong-scope negative confounded')
        expect(('jti' not in claims)==(key=='VAULT_TEST_SERVICE_MISSING_CLAIMS'),
               'AT14 missing-claim negative confounded')
        with httpx.Client(base_url=args.gateway,timeout=35,follow_redirects=False,
                          trust_env=False,verify=str(args.gateway_ca_file)) as bad_client:
            denied=bad_client.get(url,headers={'Authorization':'Bearer '+values[key]})
        expect(denied.status_code in (401,403,404),
               'Service JWT negative bypassed expected rejection: '+key)
    return session


def case_15(client,args,session):
    """Real same-Gateway two-school IDOR and session-switch negatives."""
    checks={}
    session=change_school(client,session,args.school_a) if session['school_id']!=args.school_a else session
    expect(client.get('/vault/v1/shells/'+args.shell_a).status_code==200,'School A shell missing')
    checks['school_a_access']='PASS'
    negatives=((f'/vault/v1/shells/{args.shell_b}', 'school_a_denies_school_b_shell'),
               (f'/vault/v1/shells/{args.shell_b}/materials', 'school_a_denies_school_b_materials'),
               (f'/vault/v1/shells/{args.shell_b}/materials/{args.source_b}/download',
                'school_a_denies_school_b_original_download'))
    for path,key in negatives:
        expect(client.get(path).status_code==404,'B identity leaked in A context')
        checks[key]='PASS'
    forged=client.get('/auth/me',headers={'X-School-ID':args.school_b})
    expect(forged.status_code==200 and forged.json()['school_id']==args.school_a,
           'Client-controlled header changed trusted school context')
    checks['forged_school_header_denied']='PASS'
    stale=session['csrf_token']
    session=change_school(client,session,args.school_b)
    old_csrf=client.post('/auth/school',headers={'X-CSRF-Token':stale},
                         json={'school_id':args.school_a})
    expect(old_csrf.status_code==403,'Rotated CSRF accepted after school switch')
    checks['csrf_rotated_on_switch']='PASS'
    expect(client.get('/vault/v1/shells/'+args.shell_b).status_code==200,'B shell unreadable')
    checks['school_b_access']='PASS'
    expect(client.get('/vault/v1/shells/'+args.shell_a).status_code==404,'A shell leaked after switch')
    checks['school_b_denies_school_a_shell']='PASS'
    return checks


CASES={'S1-AT03':case_03,'S1-AT10':case_10,'S1-AT14':case_14,'S1-AT15':case_15}


def main():
    p=argparse.ArgumentParser()
    for arg in ('school-a','school-b','shell-a','shell-b','source-a','source-b','query-a'):
        p.add_argument('--'+arg,required=True)
    p.add_argument('--gateway',required=True)
    p.add_argument('--gateway-ca-file',required=True,type=Path)
    p.add_argument('--runtime-identity',required=True,type=Path)
    for field in ('context','project','source-sha','source-tree'):
        p.add_argument('--'+field,required=True)
    p.add_argument('--at-id',required=True,choices=CASES)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Exclusive synthetic test environment confirmation required')
    gateway=urlsplit(args.gateway)
    if not (gateway.scheme=='https' and gateway.hostname in ('127.0.0.1','localhost')
            and gateway.port and gateway.path in ('','/') and not gateway.query
            and not gateway.fragment and not gateway.username and not gateway.password):
        p.error('Formal HTTP AT requires exactly one loopback HTTPS Gateway origin')
    verify_clean_source(Path(__file__).resolve().parents[3],args.source_sha,args.source_tree,output=args.out)
    identity,_,identity_sha=verify_manifest(args.runtime_identity,args.context,
        args.project,args.source_sha,args.source_tree)
    trusted=identity.get('gateway',{})
    ca=args.gateway_ca_file
    if (not ca.is_file() or ca.is_symlink() or ca.stat().st_size>1<<20
            or hashlib.sha256(ca.read_bytes()).hexdigest()!=trusted.get('tls_ca_sha256')
            or trusted.get('origin')!=args.gateway.rstrip('/')):
        p.error('HTTP AT Gateway TLS CA/origin does not match runtime identity')
    actual_gateway=tls_gateway_identity(args.gateway,ca)
    if (actual_gateway.get('tls_peer_sha256')!=trusted.get('tls_peer_sha256')
            or actual_gateway.get('instance_id')!=trusted.get('instance_id')
            or actual_gateway.get('origin')!=trusted.get('origin')):
        p.error('Actual TLS peer / Gateway process has changed since attestation')
    for value in (args.school_a,args.school_b):
        if not value.startswith('synthetic-'):p.error('Only synthetic schools permitted')
    report={'at_id':args.at_id,'status':'NOT_RUN',
        'started_utc':datetime.now(timezone.utc).isoformat(),
        'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED',
        'source_commit':args.source_sha,'source_tree':args.source_tree,
        'gateway_tls_peer_sha256':trusted.get('tls_peer_sha256'),
        'runtime_identity_sha256':identity_sha}
    try:
        with httpx.Client(base_url=args.gateway,timeout=35,follow_redirects=False,
                          trust_env=False,verify=str(args.gateway_ca_file)) as client:
            session=authenticate(client)
            checks=CASES[args.at_id](client,args,session)
            if args.at_id=='S1-AT15':
                report['checks']=checks
        verify_clean_source(Path(__file__).resolve().parents[3],args.source_sha,args.source_tree,output=args.out)
        report['status']='PASS'
    except Exception as exc:
        report['status']='FAIL'
        report['error_type']=type(exc).__name__
        raise
    finally:
        report['end_utc']=datetime.now(timezone.utc).isoformat()
        if args.out.exists():raise RuntimeError('Evidence overwrite forbidden')
        with args.out.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
