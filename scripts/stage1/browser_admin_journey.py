#!/usr/bin/env python3
"""Real Chromium A-only Admin journey, secret-free stage-scoped diagnostic.

IMPLEMENTED_UNTESTED. Requires separately fixed synthetic local Gateway,
real Native Worker, Playwright and Chromium. NEVER a synthetic UI mock PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from native_runtime_smoke import fixture as synthetic_chinese_pdf
from wp01_network_boundary_probe import verify_manifest
from runtime_identity import tls_gateway_identity
from browser_observability import (
    Events,BrowserContractError,STAGES,same_origin,safe_path,
    worker_status,http_category,classify_failure
)


def require(condition,reason):
    if not condition:
        raise BrowserContractError(reason)


def git_id(revision):
    return subprocess.run(['git','-C',str(ROOT),'rev-parse',revision],
        check=True,capture_output=True,text=True,timeout=12).stdout.strip()


def safe_http(response,expected,events,report,method,url):
    status=response.status
    events.http(method,url,status)
    if status!=expected:
        report['error_category']=http_category(safe_path(url),status)
        raise BrowserContractError('Unexpected authenticated HTTP status; inspect redacted events')
    return response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gateway',required=True)
    parser.add_argument('--gateway-ca-file',required=True,type=Path)
    parser.add_argument('--runtime-identity',required=True,type=Path)
    parser.add_argument('--context',required=True)
    parser.add_argument('--project',required=True)
    parser.add_argument('--source-sha',required=True)
    parser.add_argument('--source-tree',required=True)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    target=urlsplit(args.gateway)
    require(target.scheme=='https'
        and target.hostname in ('127.0.0.1','localhost') and target.port
        and not target.username and not target.password
        and target.path in ('','/') and not target.query and not target.fragment,
        'Only an explicit private loopback Gateway is permitted')
    origin=args.gateway.rstrip('/')
    identity,_,runtime_sha=verify_manifest(args.runtime_identity,args.context,
        args.project,args.source_sha,args.source_tree)
    gateway=identity['gateway']
    ca=args.gateway_ca_file
    require(ca.is_file() and not ca.is_symlink() and ca.stat().st_size<=1<<20,
            'Browser private TLS root is missing/unsafe')
    require(origin==gateway.get('origin') and
            hashlib.sha256(ca.read_bytes()).hexdigest()==gateway.get('tls_ca_sha256'),
            'Browser Gateway origin or TLS CA differs from attested service')
    actual=tls_gateway_identity(origin,ca)
    require(all(actual.get(k)==gateway.get(k) for k in (
        'instance_id','tls_peer_sha256','tls_ca_sha256','origin')),
        'Browser preflight TLS peer or A Gateway process changed')
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM')=='YES'
        and os.getenv('VAULT_STORE_BACKEND')=='surreal',
        'Real synthetic SurrealDB runtime not confirmed')
    password=os.getenv('VAULT_TEST_ADMIN_PASSWORD')
    require(bool(password),'Private operator synthetic Admin secret missing')
    require((git_id('HEAD'),git_id('HEAD^{tree}'))==(args.source_sha,args.source_tree),
        'Git source SHA/tree mismatch')
    require(not args.out.exists(),'Browser evidence overwrite refused')
    trace=Events()
    report={'at_id':'S1-AT01-BROWSER','status':'NOT_RUN',
        'source_commit':args.source_sha,'source_tree':args.source_tree,
        'browser_engine':'chromium','source_classification':'IMPLEMENTED_UNTESTED',
        'classification':'SYNTHETIC_LOCAL_BROWSER_JOURNEY_CANDIDATE',
        'started_utc':datetime.now(timezone.utc).isoformat(),
        'checks':{},'gateway_scheme':target.scheme,
        'runtime_identity_sha256':runtime_sha,
        'gateway_tls_peer_sha256':gateway['tls_peer_sha256']}
    try:
        trace.stage('S1B-STARTUP')
        from playwright.sync_api import sync_playwright
        report['playwright_package_version']=package_version('playwright')
        raw=synthetic_chinese_pdf()
        digest=hashlib.sha256(raw).hexdigest()
        token=secrets.token_hex(8)
        subject='Synthetic Browser Maths'
        stream='ui_'+token
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            report['chromium_version']=browser.version
            try:
                # Default TLS verification stays enabled, no ignore_https_errors.
                context=browser.new_context(accept_downloads=True,ignore_https_errors=False)
                external_attempts=[]
                def route_guard(route):
                    requested=route.request.url
                    if not same_origin(requested,origin):
                        external_attempts.append(safe_path(requested))
                        trace.failure('requestfailed','requestfailed',requested)
                        route.abort()
                    else:
                        route.continue_()
                context.route('**/*',route_guard)
                page=context.new_page()
                page.set_default_timeout(30000)
                script_errors=[]
                failed_requests=[]
                def on_page_error(error):
                    script_errors.append('JAVASCRIPT_FAILURE')
                    trace.failure('pageerror','pageerror')
                def on_request_failed(request):
                    # Playwright failure text can contain untrusted paths/headers:
                    # use it for classification only; never place it in evidence.
                    category=classify_failure(str(request.failure or 'requestfailed'))
                    failed_requests.append(category)
                    trace.failure('requestfailed',str(request.failure or 'requestfailed'),request.url)
                def on_response(response):
                    trace.http(response.request.method,response.url,response.status)
                page.on('pageerror',on_page_error)
                page.on('requestfailed',on_request_failed)
                page.on('response',on_response)
                page.on('framenavigated',lambda frame: trace._append({
                    'stage':trace.current,'event':'NAVIGATION','path':safe_path(frame.url),
                    'same_origin':same_origin(frame.url,origin)})
                    if frame==page.main_frame else None)
                trace.stage('S1B-NAVIGATION')
                landing=page.goto(origin+'/auth/login',wait_until='domcontentloaded')
                require(landing is not None,'Browser Navigation had no HTTP response')
                safe_http(landing,200,trace,report,'GET',origin+'/auth/login')
                require(same_origin(page.url,origin),
                    'Browser navigated outside the verified Gateway')
                trace.stage('S1B-LOGIN-FORM')
                page.locator('#login input[name=csrf]').wait_for(state='attached')
                csrf_present=page.locator('#login input[name=csrf]').input_value()
                require(bool(csrf_present) and csrf_present!='__SUNRISE_LOGIN_CSRF__',
                    'Browser login form CSRF unavailable')
                page.locator('#password').fill(password)
                trace.stage('S1B-LOGIN-POST')
                with page.expect_response(lambda r: safe_path(r.url)=='/auth/login'
                        and r.request.method=='POST',timeout=30000) as login_receipt:
                    page.locator('#login button[type=submit]').click()
                login_response=login_receipt.value
                safe_http(login_response,200,trace,report,'POST',login_response.url)
                page.wait_for_url('**/admin',timeout=30000)
                require(same_origin(page.url,origin),'Admin browser redirected outside Gateway')
                page.locator('#workspace').wait_for(state='visible',timeout=30000)
                trace.stage('S1B-SESSION')
                session_response=page.request.get(origin+'/auth/me')
                safe_http(session_response,200,trace,report,'GET',origin+'/auth/me')
                session=session_response.json()
                require(isinstance(session.get('school_id'),str)
                        and session['school_id'].startswith('synthetic-'),
                        'Browser session not restricted to synthetic school')
                allowed=session.get('available_schools')
                require(isinstance(allowed,list) and session['school_id'] in allowed,
                        'Browser school allowlist not proven server-held')
                if len(allowed)==1:
                    require(page.locator('#switch-school').is_hidden(),
                        'Single school Admin UI unexpectedly exposes School selector')
                report['checks']['real_browser_login_and_server_school']='PASS'
                trace.stage('S1B-SHELL')
                for selector,value in (('#year','2026'),('#grade','P4'),
                                       ('#subject',subject),('#stream',stream)):
                    page.locator(selector).fill(value)
                page.locator('#create-submit').click()
                page.locator('#detail').wait_for(state='visible',timeout=60000)
                shells=page.request.get(origin+'/vault/v1/shells')
                safe_http(shells,200,trace,report,'GET',origin+'/vault/v1/shells')
                matches=[item for item in shells.json().get('shells',[])
                         if item.get('curriculum_stream')==stream
                         and item.get('subject')==subject
                         and item.get('school_id')==session['school_id']]
                require(len(matches)==1 and matches[0].get('notebook_id'),
                        'Real Browser Shell creation/Notebook mapping not unique')
                shell_id=matches[0]['shell_id']
                report['checks']['real_browser_shell_create']='PASS'
                trace.stage('S1B-UPLOAD')
                title='Synthetic Fraction Browser '+token
                page.locator('#file').set_input_files({
                    'name':'synthetic_chinese.pdf','mimeType':'application/pdf','buffer':raw})
                page.locator('#material-title').fill(title)
                page.locator('#license').fill('synthetic-test-only')
                page.locator('#retention').fill('synthetic-short')
                page.locator('#upload-submit').click()
                # Browser UI mutator must finish first. No false-positive if
                # Native material already exists from a previous action.
                page.locator('#upload-receipt').wait_for(state='visible',timeout=60000)
                trace.stage('S1B-WORKER')
                deadline=time.monotonic()+150
                source_id=None
                latest_state='PENDING'
                material_route=origin+'/vault/v1/shells/'+shell_id+'/materials'
                while time.monotonic()<deadline:
                    page.locator('#refresh-materials').click()
                    page.wait_for_timeout(1250)
                    materials=page.request.get(material_route)
                    safe_http(materials,200,trace,report,'GET',material_route)
                    material_list=materials.json().get('materials')
                    latest_state=worker_status(material_list,digest,title)
                    if latest_state=='FAILED':
                        report['error_category']='NATIVE_WORKER_FAILED'
                        raise BrowserContractError('Real Native Worker returned FAILED')
                    if latest_state=='READY':
                        found=[m for m in material_list
                               if m.get('sha256')==digest and m.get('title')==title]
                        source_id=found[0]['source_id']
                        break
                    page.wait_for_timeout(1250)
                require(latest_state=='READY' and source_id is not None,
                        'Real Native Worker did not reach READY within finite deadline')
                page.locator('#materials').get_by_text(title).wait_for(
                    state='visible',timeout=30000)
                report['checks']['real_browser_pdf_upload_and_worker_status']='PASS'
                trace.stage('S1B-SEARCH')
                page.locator('#query').fill('SUNRISE_SYNTHETIC_FRACTION_2026')
                page.locator('#search-submit').click()
                page.locator('#search-results').get_by_text(title).wait_for(
                    state='visible',timeout=30000)
                report['checks']['real_browser_scoped_text_search']='PASS'
                trace.stage('S1B-DOWNLOAD')
                with page.expect_download(timeout=30000) as info:
                    page.locator('#materials button').first.click()
                downloaded=Path(info.value.path()).read_bytes()
                require(hashlib.sha256(downloaded).hexdigest()==digest and downloaded==raw,
                        'Browser original PDF download bytes or original hash mismatch')
                report['checks']['real_browser_original_pdf_download']='PASS'
                trace.stage('S1B-ARCHIVE')
                page.once('dialog',lambda dialog:dialog.accept())
                page.locator('#archive').click()
                page.locator('#archive-note').wait_for(state='visible',timeout=30000)
                shell_url=origin+'/vault/v1/shells/'+shell_id
                shell=page.request.get(shell_url)
                safe_http(shell,200,trace,report,'GET',shell_url)
                require(bool(shell.json().get('archived')),
                        'Real Browser Archive did not persist')
                report['checks']['real_browser_archive']='PASS'
                trace.stage('S1B-LOGOUT')
                page.locator('#logout').click()
                page.wait_for_url('**/auth/login',timeout=30000)
                revoke=page.request.get(origin+'/auth/me')
                safe_http(revoke,401,trace,report,'GET',origin+'/auth/me')
                report['checks']['real_browser_logout_revocation']='PASS'
                require(not script_errors,'Browser raised uncaught JavaScript errors')
                require(not failed_requests and not external_attempts,
                        'Browser network request failed or left pinned origin')
                report['checks']['no_uncaught_browser_script_errors']='PASS'
                report['school_id_sha256']=hashlib.sha256(
                    session['school_id'].encode()).hexdigest()
                report['original_pdf_sha256']=digest
                report['status']='PASS'
            finally:
                browser.close()
    except Exception as error:
        report['status']='FAIL'
        report['error_type']=type(error).__name__
        if 'error_category' not in report:
            report['error_category']=classify_failure(str(error))
        trace.failure('browser',str(error))
        # Never re-raise raw Playwright exceptions: they may include
        # untrusted URLs, selectors, cookies, or request diagnostics.
    finally:
        report['failure_stage']=trace.current if report['status']=='FAIL' else None
        report['stage_ids']=list(STAGES)
        report['redacted_events']=trace.entries
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'at_id':report['at_id'],'status':report['status'],
            'failure_stage':report['failure_stage'],
            'error_category':report.get('error_category'),
            'evidence':str(args.out)},sort_keys=True))
    raise SystemExit(0 if report['status']=='PASS' else 1)


if __name__=='__main__':
    main()
