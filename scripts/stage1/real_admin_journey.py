#!/usr/bin/env python3
"""Real HTTPS-independent LOOPBACK-only synthetic A Admin user journey probe.

Requires running private Gateway + pinned ON + actual SurrealDB + Worker.
Only a diagnostic for a controlled local host; NOT a release/UAT approval.
No mocks, SQLite mode, fake native hit results, or external model API.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
from html.parser import HTMLParser
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import httpx

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native
from native_runtime_smoke import fixture as synthetic_chinese_pdf
from wp01_network_boundary_probe import verify_manifest


def utc():return datetime.now(timezone.utc).isoformat()


class LoginParser(HTMLParser):
    csrf=None
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if tag=='input' and data.get('name')=='csrf':self.csrf=data.get('value')


def login(client,password):
    page=client.get('/auth/login')
    if page.status_code!=200:raise AssertionError('Login page not available')
    form=LoginParser();form.feed(page.text)
    if not form.csrf:raise AssertionError('Login form CSRF field absent')
    auth=client.post('/auth/login',data={'csrf':form.csrf,'password':password})
    if auth.status_code!=200:raise AssertionError('Controlled Admin login rejected')
    csrf=auth.json()['csrf_token']
    if len(csrf)<12:raise AssertionError('Invalid session CSRF token')
    return {'X-CSRF-Token':csrf}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--gateway',required=True)
    p.add_argument('--ca-file',required=True,type=Path)
    p.add_argument('--runtime-identity',required=True,type=Path)
    p.add_argument('--context',required=True)
    p.add_argument('--project',required=True)
    p.add_argument('--source-sha',required=True)
    p.add_argument('--source-tree',required=True)
    p.add_argument('--native-url',required=True)
    p.add_argument('--out',type=Path,default=Path('wp03-owner-journey-redacted.json'))
    args=p.parse_args()
    target=urlsplit(args.gateway)
    if (target.scheme!='https' or target.hostname not in ('127.0.0.1','localhost')
            or not target.port or target.username or target.password
            or target.path not in ('','/') or target.query or target.fragment):
        raise ValueError('Only authenticated, verified loopback HTTPS A Gateway permitted')
    if not args.ca_file.is_file() or args.ca_file.is_symlink():
        raise ValueError('Private trusted Gateway TLS CA missing')
    identity,_,_=verify_manifest(args.runtime_identity,args.context,
                                  args.project,args.source_sha,args.source_tree)
    gateway=identity['gateway']
    if (args.gateway.rstrip('/')!=gateway.get('origin') or
            hashlib.sha256(args.ca_file.read_bytes()).hexdigest()!=gateway.get('tls_ca_sha256')):
        raise ValueError('Native Admin diagnostic Gateway TLS identity changed')
    native_port=identity['services']['native']['published_ports'][0]['host_port']
    if args.native_url!='http://127.0.0.1:'+str(native_port):
        raise ValueError('Native diagnostic endpoint not from inspected Docker container')
    if (subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],
                       capture_output=True,text=True,check=True,timeout=12).stdout.strip()!=args.source_sha
            or subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD^{tree}'],
                       capture_output=True,text=True,check=True,timeout=12).stdout.strip()!=args.source_tree):
        raise ValueError('HTTP diagnostic revision not fixed Source SHA/tree')
    if os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')!='YES' or os.getenv('VAULT_STORE_BACKEND')!='surreal':
        print('RUNTIME_NOT_RUN: real A SurrealDB + synthetic runtime confirmation missing',file=sys.stderr)
        raise SystemExit(69)
    for key in ('VAULT_ADMIN_PASSWORD','OPEN_NOTEBOOK_PASSWORD'):
        if not os.getenv(key):
            print('RUNTIME_NOT_RUN: private operator secret missing',file=sys.stderr)
            raise SystemExit(69)
    token=secrets.token_hex(6)
    evidence={'start_utc':utc(),'probe':'A_ADMIN_NATIVE_SURREAL_WORKER_HTTPS_LOOPBACK',
              'source_commit':args.source_sha,'source_tree':args.source_tree,
              'stage':'LOCAL_SYNTHETIC_DEMO_NOT_RELEASE_READY',
              'formal_s1_at01_15':'NOT_RUN','results':{}}
    raw=synthetic_chinese_pdf()
    digest=hashlib.sha256(raw).hexdigest()
    evidence['pdf_sha256']=digest
    try:
        with httpx.Client(base_url=args.gateway,trust_env=False,timeout=25,
                          follow_redirects=False,verify=str(args.ca_file)) as c:
            assert c.get('/vault/v1/shells').status_code==401
            h=login(c,os.environ['VAULT_ADMIN_PASSWORD'])
            assert c.get('/admin').status_code==200
            who=c.get('/auth/me').json()
            assert who.get('school_id') and who.get('actor_id')
            evidence['results']['admin_login_and_private_session']='PASS'
            body={'academic_year':'2026','grade':'P4','subject':'Synthetic mathematics',
                  'curriculum_stream':'wp03_'+token}
            route='/vault/v1/shells';key='synthetic_shell_'+token
            a=c.post(route,headers={**h,'Idempotency-Key':key},json=body)
            assert a.status_code==201,'Failed to create durable native shell'
            shell=a.json();sid=shell['shell_id'];nb=shell['notebook_id']
            assert nb.startswith('notebook:')
            repeat=c.post(route,headers={**h,'Idempotency-Key':key},json=body)
            assert repeat.status_code==200 and repeat.json()['notebook_id']==nb
            wrong=c.post(route,headers={**h,'Idempotency-Key':key},json={**body,'grade':'P5'})
            assert wrong.status_code==409
            assert c.get(f'/vault/v1/shells/{sid}').json()['notebook_id']==nb
            evidence['results']['surreal_durable_native_notebook_unique']='PASS'
            evidence['results']['same_key_replay_and_body_conflict']='PASS'
            assert c.get('/vault/v1/shells/nonexistent-synthetic-shell').status_code==404
            pdf_route=f'/vault/v1/shells/{sid}/materials'
            files={'file':('synthetic_chinese.pdf',raw,'application/pdf')}
            metadata={'title':'SYNTHETIC FRACTION 2026','license':'synthetic-test-only','retention':'synthetic-short'}
            ukey='synthetic_upload_'+token
            upload=c.post(pdf_route,headers={**h,'Idempotency-Key':ukey},data=metadata,files=files)
            assert upload.status_code==201,'Native Source upload rejected'
            receipt=upload.json();source=receipt['source_id']
            assert receipt['sha256']==digest and source.startswith('source:')
            evidence['results']['native_pdf_upload_original_sha']='PASS'
            native=Native(args.native_url,os.environ['OPEN_NOTEBOOK_PASSWORD'],text_only_verified=True)
            deadline=time.monotonic()+120
            while True:
                detail=asyncio.run(native.ensure_owned(source,nb))
                plain=detail.get('full_text') or ''
                if 'SUNRISE_SYNTHETIC_FRACTION_2026' in plain:break
                if detail.get('status') in ('failed','error','cancelled','unknown'):
                    raise AssertionError('Native Worker did not extract synthetic PDF')
                if time.monotonic()>deadline:raise TimeoutError('Native Worker extraction incomplete')
                time.sleep(2)
            evidence['results']['worker_extracted_synthetic_pdf']='PASS'
            text=c.post(f'/vault/v1/shells/{sid}/search',json={'query':'SUNRISE_SYNTHETIC_FRACTION_2026'},headers=h)
            assert text.status_code==200 and any(hit['source_id']==source for hit in text.json()['results'])
            evidence['results']['server_scoped_text_only_search']='PASS'
            download=c.get(f'/vault/v1/shells/{sid}/materials/{source}/download')
            assert download.status_code==200 and hashlib.sha256(download.content).hexdigest()==digest
            assert download.content==raw
            evidence['results']['original_pdf_hash_and_authorization']='PASS'
            listed=c.get(pdf_route)
            assert listed.status_code==200 and len(listed.json()['materials'])==1
            assert listed.json()['materials'][0]['source_id']==source
            archived=c.post(f'/vault/v1/shells/{sid}/archive',headers=h)
            assert archived.status_code==200 and archived.json()['archived']
            rejected=c.post(pdf_route,headers={**h,'Idempotency-Key':'after_archive_'+token},data=metadata,files=files)
            assert rejected.status_code==409
            evidence['results']['archive_non_destructive']='PASS'
            assert c.post('/auth/logout',headers=h).status_code==200
            assert c.get(f'/vault/v1/shells/{sid}').status_code==401
            evidence['results']['logout_session_revocation']='PASS'
            evidence['results']['gateway_restart_persistence']='NOT_RUN'
            evidence['results']['school_b_separate_gateway_negative']='NOT_RUN'
            evidence['results']['independent_backup_restore']='NOT_RUN'
            evidence['result']='PARTIAL_PASSED_WITH_UNRUN_GATES'
    except Exception as exc:
        evidence['result']='FAIL';evidence['error_type']=type(exc).__name__
        evidence['error']='Real synthetic journey prerequisite or invariant failed; see private host logs'
        raise
    finally:
        evidence['end_utc']=utc()
        args.out.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'result':evidence.get('result'),'checks':evidence['results'],
                          'evidence':str(args.out)},ensure_ascii=False))
    if evidence['result']!='PARTIAL_PASSED_WITH_UNRUN_GATES':raise SystemExit(1)

if __name__=='__main__':main()
