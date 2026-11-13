"""Deterministic, bounded, secret-free Stage 1 Chromium observability helpers.

No network, browser or storage interaction at import. No raw URL, exception
message, user data, cookies, credentials, bodies or PDF may enter evidence.
"""
from __future__ import annotations
from urllib.parse import urlsplit
import re

STAGES = (
    'S1B-STARTUP','S1B-NAVIGATION','S1B-LOGIN-FORM','S1B-LOGIN-POST',
    'S1B-SESSION','S1B-SHELL','S1B-UPLOAD','S1B-WORKER',
    'S1B-SEARCH','S1B-DOWNLOAD','S1B-ARCHIVE','S1B-LOGOUT',
)
_METHODS = frozenset(('GET','POST','HEAD','DELETE','OPTIONS','PUT','PATCH'))


class BrowserContractError(RuntimeError):
    pass


def safe_path(url: str) -> str:
    """Whitelist endpoint templates; never persist untrusted route components."""
    try:
        path=urlsplit(url).path
    except (TypeError,ValueError):
        return '/other'
    if path in ('/auth/login','/auth/me','/auth/logout','/admin',
                '/health','/assets/app.js','/assets/style.css',
                '/vault/v1/shells'):
        return path
    if path.startswith('/vault/v1/shells/'):
        pieces=path.split('/')
        # ['', vault, v1, shells, opaque-id, ...]
        if len(pieces)==5 and pieces[4]:
            return '/vault/v1/shells/{shell}'
        if len(pieces)==6 and pieces[5] in ('materials','search','archive'):
            return '/vault/v1/shells/{shell}/'+pieces[5]
        if len(pieces)==8 and pieces[5]=='materials' and pieces[6] and pieces[7]=='download':
            return '/vault/v1/shells/{shell}/materials/{source}/download'
    return '/other'


def same_origin(url: str, allowed_origin: str) -> bool:
    try:
        got=urlsplit(url)
        allowed=urlsplit(allowed_origin)
        return bool(got.scheme in ('https','http')
                    and got.scheme==allowed.scheme
                    and got.hostname==allowed.hostname
                    and got.port==allowed.port
                    and got.username is None and got.password is None
                    and allowed.username is None and allowed.password is None)
    except (ValueError,TypeError):
        return False



def valid_admin_login_redirect(status: int, location: str) -> bool:
    """HTML Admin login must produce exactly the Gateway's relative 303 target.

    Do not accept a 200 API JSON response as a browser login, redirects to
    external origins, query-bearing URLs or unexpected relative destinations.
    """
    return type(status) is int and status == 303 and location == '/admin'


def http_category(path: str,status: int) -> str:
    if status==401:
        return 'LOGIN_AUTH_401' if path=='/auth/login' else 'HTTP_401'
    if status==403:
        return 'LOGIN_CSRF_403' if path=='/auth/login' else 'HTTP_403'
    if 500<=status<=599:
        return 'HTTP_5XX'
    if 400<=status<=499:
        return 'HTTP_4XX'
    if 300<=status<=399:
        return 'HTTP_REDIRECT'
    return 'HTTP_OK' if 200<=status<=299 else 'HTTP_UNEXPECTED'


def classify_failure(label: str) -> str:
    """Only classify; NEVER record label or exception.__str__ in evidence."""
    value=str(label).lower()
    if 'browser_executable_missing' in value or ('executable' in value and 'exist' in value):
        return 'BROWSER_BINARY_MISSING'
    if any(term in value for term in ('cert_authority','cert_common_name',
                                      'cert_date_invalid','ssl','tls','certificate')):
        return 'TLS_CERTIFICATE'
    if 'csrf' in value:
        return 'CSRF'
    if 'cookie' in value:
        return 'COOKIE'
    if 'pageerror' in value or 'javascript' in value:
        return 'JAVASCRIPT_FAILURE'
    if 'requestfailed' in value or 'net::' in value:
        return 'REQUEST_FAILURE'
    if 'timeout' in value:
        return 'SELECTOR_TIMEOUT'
    return 'BROWSER_CONTRACT_OR_RUNTIME'


def worker_status(materials: list, expected_hash: str, expected_title: str) -> str:
    """Disambiguate no-match, malformed, failed and ready Native Worker states."""
    if not isinstance(materials,list):
        raise BrowserContractError('Worker list contract invalid')
    matches=[m for m in materials if isinstance(m,dict)
             and m.get('sha256')==expected_hash and m.get('title')==expected_title]
    if len(matches)>1:
        raise BrowserContractError('Duplicate owned synthetic Source material')
    if not matches:
        return 'PENDING'
    material=matches[0]
    if not isinstance(material.get('source_id'),str) or not material['source_id'].startswith('source:'):
        raise BrowserContractError('Native Source identity missing')
    state=material.get('state')
    if state=='READY':
        return 'READY'
    if state=='FAILED':
        return 'FAILED'
    if state in ('PROCESSING','PENDING','SUBMITTED_NATIVE_PROCESSING','UNKNOWN'):
        return 'PENDING'
    raise BrowserContractError('Unverifiable Native Worker status')


class Events:
    """Evidence only stores bounded stage IDs, redacted paths and status codes."""
    def __init__(self,max_events: int=96):
        if not 1<=max_events<=256:
            raise ValueError('Invalid event bound')
        self.max_events=max_events
        self.entries=[]
        self.current='S1B-STARTUP'

    def _append(self,row: dict):
        self.entries.append(row)
        if len(self.entries)>self.max_events:
            del self.entries[:-self.max_events]

    def stage(self,stage_id: str):
        if stage_id not in STAGES:
            raise BrowserContractError('Unrecognised probe stage')
        self.current=stage_id
        self._append({'stage':stage_id,'event':'STAGE'})

    def http(self,method: str,url: str,status: int):
        if method not in _METHODS or type(status) is not int or not 100<=status<=599:
            raise BrowserContractError('Unsafe HTTP observability event')
        path=safe_path(url)
        self._append({'stage':self.current,'event':'HTTP','method':method,
                      'path':path,'status':status,'class':http_category(path,status)})

    def failure(self,source: str,label: str,url: str|None=None):
        if source not in ('requestfailed','pageerror','navigation','browser'):
            raise BrowserContractError('Unsupported browser failure source')
        row={'stage':self.current,'event':source,'class':classify_failure(label)}
        if url is not None:
            row['path']=safe_path(url)
        self._append(row)
