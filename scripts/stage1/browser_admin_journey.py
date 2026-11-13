#!/usr/bin/env python3
"""Real Chromium Admin UI journey against a private synthetic A Gateway.

IMPLEMENTED_UNTESTED. The operator installs Playwright + Chromium locally.
No fake browser, mocked Gateway, public deployment or external HTTP requests.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stage1'))
from native_runtime_smoke import fixture as synthetic_chinese_pdf


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def git_id(revision):
    return subprocess.run(['git', '-C', str(ROOT), 'rev-parse', revision],
                          check=True, capture_output=True, text=True, timeout=12).stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gateway', default='http://127.0.0.1:8765')
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--source-tree', required=True)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    target = urlsplit(args.gateway)
    require(target.scheme == 'http' and target.hostname in ('127.0.0.1', 'localhost')
            and target.port and not target.username and not target.password
            and target.path in ('', '/') and not target.query and not target.fragment,
            'Browser probe may access only a loopback Gateway')
    require(os.getenv('VAULT_RUNTIME_SYNTHETIC_CONFIRM') == 'YES'
            and os.getenv('VAULT_STORE_BACKEND') == 'surreal',
            'Synthetic real SurrealDB runtime not confirmed')
    password = os.getenv('VAULT_TEST_ADMIN_PASSWORD')
    require(bool(password), 'Missing operator-supplied private synthetic Admin password')
    require((git_id('HEAD'), git_id('HEAD^{tree}')) ==
            (args.source_sha, args.source_tree), 'Browser source SHA/tree mismatch')
    require(not args.out.exists(), 'Browser evidence overwrite refused')
    report = {'at_id': 'S1-AT01-BROWSER', 'status': 'NOT_RUN',
              'source_commit': args.source_sha, 'source_tree': args.source_tree,
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'checks': {}, 'browser_engine': 'chromium',
              'classification': 'SYNTHETIC_LOCAL_BROWSER_JOURNEY_CANDIDATE'}
    try:
        from playwright.sync_api import sync_playwright
        from importlib.metadata import version as package_version
        report['playwright_package_version'] = package_version('playwright')
        raw = synthetic_chinese_pdf()
        digest = hashlib.sha256(raw).hexdigest()
        token = secrets.token_hex(8)
        subject = 'Synthetic Browser Maths'
        stream = 'ui_' + token
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            report['chromium_version'] = browser.version
            try:
                context = browser.new_context(accept_downloads=True)
                # A private UI must not cause the browser to fetch external resources.
                context.route('**/*', lambda route: route.continue_()
                              if urlsplit(route.request.url).hostname in
                              ('127.0.0.1', 'localhost') else route.abort())
                page = context.new_page()
                page.set_default_timeout(30000)
                script_errors = []
                page.on('pageerror', lambda exc: script_errors.append(type(exc).__name__))
                page.goto(args.gateway.rstrip('/') + '/auth/login', wait_until='domcontentloaded')
                page.locator('#password').fill(password)
                page.locator('#login button[type=submit]').click()
                page.wait_for_url('**/admin', timeout=30000)
                page.locator('#workspace').wait_for(state='visible', timeout=30000)
                session_response = page.request.get(args.gateway.rstrip('/') + '/auth/me')
                require(session_response.status == 200, 'Browser session is not authenticated')
                session = session_response.json()
                require(isinstance(session.get('school_id'), str)
                        and session['school_id'].startswith('synthetic-'),
                        'Browser journey is not on an isolated synthetic school')
                allowed = session.get('available_schools')
                require(isinstance(allowed, list) and session['school_id'] in allowed,
                        'Server-held browser school allowlist unavailable')
                if len(allowed) == 1:
                    require(page.locator('#switch-school').is_hidden(),
                            'Single-school browser demo still exposes selector')
                report['checks']['real_browser_login_and_server_school'] = 'PASS'
                page.locator('#year').fill('2026')
                page.locator('#grade').fill('P4')
                page.locator('#subject').fill(subject)
                page.locator('#stream').fill(stream)
                page.locator('#create-submit').click()
                page.locator('#detail').wait_for(state='visible', timeout=60000)
                shells = page.request.get(args.gateway.rstrip('/') + '/vault/v1/shells')
                require(shells.status == 200, 'Browser did not create a readable shell')
                matches = [s for s in shells.json().get('shells', [])
                           if s.get('curriculum_stream') == stream
                           and s.get('subject') == subject
                           and s.get('school_id') == session['school_id']]
                require(len(matches) == 1 and matches[0].get('notebook_id'),
                        'Browser shell create lacks unique native notebook mapping')
                shell_id = matches[0]['shell_id']
                report['checks']['real_browser_shell_create'] = 'PASS'
                page.locator('#file').set_input_files({
                    'name': 'synthetic_chinese.pdf', 'mimeType': 'application/pdf',
                    'buffer': raw})
                page.locator('#material-title').fill('Synthetic Fraction Browser ' + token)
                page.locator('#license').fill('synthetic-test-only')
                page.locator('#retention').fill('synthetic-short')
                page.locator('#upload-submit').click()
                deadline = time.monotonic() + 150
                source_id = None
                while time.monotonic() < deadline:
                    page.locator('#refresh-materials').click()
                    page.wait_for_timeout(1500)
                    materials = page.request.get(
                        args.gateway.rstrip('/') + '/vault/v1/shells/' + shell_id + '/materials')
                    if materials.status == 200:
                        found = [m for m in materials.json().get('materials', [])
                                 if m.get('title') == 'Synthetic Fraction Browser ' + token
                                 and m.get('sha256') == digest]
                        if len(found) == 1:
                            source_id = found[0]['source_id']
                            if found[0].get('state') == 'READY':
                                break
                    page.wait_for_timeout(1500)
                require(source_id is not None and found[0].get('state') == 'READY',
                        'Browser upload/real Worker did not reach READY with original SHA')
                require(page.locator('#materials').get_by_text(
                    'Synthetic Fraction Browser ' + token).is_visible(),
                    'Uploaded material not visible in browser DOM')
                report['checks']['real_browser_pdf_upload_and_worker_status'] = 'PASS'
                page.locator('#query').fill('SUNRISE_SYNTHETIC_FRACTION_2026')
                page.locator('#search-submit').click()
                page.locator('#search-results').get_by_text(
                    'Synthetic Fraction Browser ' + token).wait_for(state='visible', timeout=30000)
                report['checks']['real_browser_scoped_text_search'] = 'PASS'
                with page.expect_download(timeout=30000) as info:
                    page.locator('#materials button').first.click()
                downloaded = Path(info.value.path()).read_bytes()
                require(hashlib.sha256(downloaded).hexdigest() == digest and downloaded == raw,
                        'Browser original PDF download bytes/hash mismatch')
                report['checks']['real_browser_original_pdf_download'] = 'PASS'
                page.once('dialog', lambda dialog: dialog.accept())
                page.locator('#archive').click()
                page.locator('#archive-note').wait_for(state='visible', timeout=30000)
                shell_response = page.request.get(
                    args.gateway.rstrip('/') + '/vault/v1/shells/' + shell_id)
                require(shell_response.status == 200
                        and bool(shell_response.json().get('archived')),
                        'Browser archive did not persist')
                report['checks']['real_browser_archive'] = 'PASS'
                page.locator('#logout').click()
                page.wait_for_url('**/auth/login', timeout=30000)
                require(page.request.get(args.gateway.rstrip('/') + '/auth/me').status == 401,
                        'Browser logout did not revoke server session')
                report['checks']['real_browser_logout_revocation'] = 'PASS'
                require(not script_errors, 'Browser raised uncaught JavaScript errors')
                report['checks']['no_uncaught_browser_script_errors'] = 'PASS'
                report['school_id_sha256'] = hashlib.sha256(
                    session['school_id'].encode()).hexdigest()
                report['original_pdf_sha256'] = digest
                report['status'] = 'PASS'
            finally:
                browser.close()
    except Exception as exc:
        report['status'] = 'FAIL'
        report['error_type'] = type(exc).__name__
        raise
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
