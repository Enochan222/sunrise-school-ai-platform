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
from pathlib import Path
from urllib.parse import urlsplit
import httpx


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
    authorized_materials(client,args.shell_a)
    values={name:os.getenv(name) for name in (
        'VAULT_TEST_SERVICE_A','VAULT_TEST_SERVICE_WRONG_SCOPE','VAULT_TEST_SERVICE_FOREIGN_SCHOOL')}
    if any(not x for x in values.values()):
        raise RuntimeError('Independent signed positive/negative service JWT fixtures required')
    urls='/vault/v1/shells/'+args.shell_a+'/materials'
    # The Admin client above holds a valid session cookie. Reusing it for JWT
    # checks would not prove token-only authorization (or rejection): a valid
    # Admin cookie could independently grant access to the same endpoint.
    # Use a fresh cookie-free HTTP client for every Service JWT probe.
    with httpx.Client(base_url=args.gateway,timeout=35,follow_redirects=False,
                      trust_env=False,verify=True) as service_client:
        allowed=service_client.get(
            urls,headers={'Authorization':'Bearer '+values['VAULT_TEST_SERVICE_A']})
        expect(allowed.status_code==200,'Valid scoped Service JWT materials read denied')
        for key in ('VAULT_TEST_SERVICE_WRONG_SCOPE','VAULT_TEST_SERVICE_FOREIGN_SCHOOL'):
            bad=service_client.get(urls,headers={'Authorization':'Bearer '+values[key]})
            expect(bad.status_code in (401,403,404),'Service token bypassed scope/school')
    return session


def case_15(client,args,session):
    session=change_school(client,session,args.school_a) if session['school_id']!=args.school_a else session
    expect(client.get('/vault/v1/shells/'+args.shell_a).status_code==200,'School A shell missing')
    for path in (f'/vault/v1/shells/{args.shell_b}',
                 f'/vault/v1/shells/{args.shell_b}/materials',
                 f'/vault/v1/shells/{args.shell_b}/materials/{args.source_b}/download'):
        expect(client.get(path).status_code==404,'B identity leaked in A context')
    # Client forged header must not change active school.
    forged=client.get('/auth/me',headers={'X-School-ID':args.school_b})
    expect(forged.status_code==200 and forged.json()['school_id']==args.school_a,
           'Client-controlled header changed trusted school context')
    stale=session['csrf_token']
    session=change_school(client,session,args.school_b)
    old_csrf=client.post('/auth/school',headers={'X-CSRF-Token':stale},
                         json={'school_id':args.school_a})
    expect(old_csrf.status_code==403,'Rotated CSRF accepted after school switch')
    expect(client.get('/vault/v1/shells/'+args.shell_b).status_code==200,'B shell unreadable')
    expect(client.get('/vault/v1/shells/'+args.shell_a).status_code==404,'A shell leaked after switch')
    return session


CASES={'S1-AT03':case_03,'S1-AT10':case_10,'S1-AT14':case_14,'S1-AT15':case_15}


def main():
    p=argparse.ArgumentParser()
    for arg in ('school-a','school-b','shell-a','shell-b','source-a','source-b','query-a'):
        p.add_argument('--'+arg,required=True)
    p.add_argument('--gateway',required=True)
    p.add_argument('--at-id',required=True,choices=CASES)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES':
        p.error('Exclusive synthetic test environment confirmation required')
    gateway=urlsplit(args.gateway)
    if not (gateway.scheme=='https' or gateway.scheme=='http' and
            gateway.hostname in ('127.0.0.1','localhost','::1')):
        p.error('Only certificate-verified HTTPS or private local loopback allowed')
    for value in (args.school_a,args.school_b):
        if not value.startswith('synthetic-'):p.error('Only synthetic schools permitted')
    report={'at_id':args.at_id,'status':'NOT_RUN',
        'started_utc':datetime.now(timezone.utc).isoformat(),
        'classification':'REAL_HTTP_AT_CANDIDATE_NOT_REVIEWED'}
    try:
        with httpx.Client(base_url=args.gateway,timeout=35,follow_redirects=False,
                          trust_env=False,verify=True) as client:
            session=authenticate(client)
            CASES[args.at_id](client,args,session)
        report['status']='PASS'
    except Exception as exc:
        report['status']='FAIL'
        report['error_type']=type(exc).__name__
        raise
    finally:
        report['end_utc']=datetime.now(timezone.utc).isoformat()
        if args.out.exists():raise RuntimeError('Evidence overwrite forbidden')
        args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
