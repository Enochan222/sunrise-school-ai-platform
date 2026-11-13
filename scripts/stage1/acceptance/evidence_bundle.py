#!/usr/bin/env python3
"""WP09 independently inspectable, *review-required* synthetic evidence bundle.

IMPLEMENTED_UNTESTED. Bundle contents are textual, sanitized derivatives:
original artifact digests are recorded but unredacted originals are never
copied. Any unrecognised credential/record format fails closed. Automatic
redaction is only defence-in-depth; Reviewer must read every exported file
before sending. No Stage 1 approval can be inferred from a signed ZIP digest.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import zipfile

SAFE_EXT={'.json','.txt','.log','.md','.csv'}
MAX_FILE=2<<20
MAX_BUNDLE=20<<20
SAFE_FILE=re.compile(r'^[A-Za-z0-9_./-]{1,220}$')
SHA40=re.compile(r'^[a-f0-9]{40}$')
JWT=re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{16,}\b')
SECRET_LINE=re.compile(r'(?im)^(?P<prefix>\s*(?:[A-Za-z_-]*password|secret|api[_-]?key|private[_-]?key|authorization|set-cookie|cookie|access[_-]?token|refresh[_-]?token|bearer)\s*[:=]\s*)(?P<secret>.+)$')
AUTH_HEADER=re.compile(r'(?im)^(Authorization|Cookie|Set-Cookie):.*$')
PRIVATE_KEY=re.compile(r'-----BEGIN [^-]*PRIVATE KEY-----')
EXCLUDED_NAMES={'id_rsa','id_ed25519','.env','.env.local','credentials.json'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checkout(repo,source_sha,tree):
    def command(what):
        return subprocess.run(['git','-C',str(repo),'rev-parse',what],check=True,
            text=True,capture_output=True,timeout=12).stdout.strip()
    if (command('HEAD'),command('HEAD^{tree}'))!=(source_sha,tree):
        raise ValueError('Actual source commit/tree differs from supplied tested SHA/tree')


def sanitize(data):
    try:text=data.decode('utf-8')
    except UnicodeError as error:raise ValueError('Evidence must be UTF-8 text') from error
    if PRIVATE_KEY.search(text) or '\0' in text:
        raise ValueError('Private key/binary evidence cannot be exported')
    secrets=[]
    for variable in ('OPEN_NOTEBOOK_PASSWORD','VAULT_NATIVE_PASSWORD','VAULT_SESSION_SECRET',
        'VAULT_ENCRYPTION_KEY','OPEN_NOTEBOOK_ENCRYPTION_KEY','VAULT_SURREAL_PASSWORD'):
        value=os.environ.get(variable)
        if value and len(value)>=8:
            secrets.append(value)
    for secret in secrets:
        text=text.replace(secret,'[REDACTED_OPERATOR_SECRET]')
    text=JWT.sub('[REDACTED_JWT]',text)
    text=AUTH_HEADER.sub('[REDACTED_HTTP_CREDENTIAL_HEADER]',text)
    text=SECRET_LINE.sub(lambda m:m.group('prefix')+'[REDACTED_SECRET]',text)
    # Parse structured JSON evidence recursively: flat log-regex-only
    # filtering would miss {"authorization":"Bearer ..."} or nested tokens.
    try:
        structured=json.loads(text)
    except json.JSONDecodeError:
        structured=None
    sensitive_key=re.compile(
        r'(?i)(?:password|secret|token|authorization|cookie|api[_-]?key|private[_-]?key|credential)')
    def scrub(node):
        if isinstance(node,dict):
            return {key:('[REDACTED_STRUCTURED_SECRET]' if sensitive_key.search(key)
                         else scrub(value))
                    for key,value in node.items()}
        if isinstance(node,list):
            return [scrub(value) for value in node]
        return node
    if structured is not None:
        text=json.dumps(scrub(structured),ensure_ascii=False,sort_keys=True,indent=2)+'\\n'
    # Fail on suspicious residual token forms that automatic redaction
    # did not safely recognize. No raw dump of hidden data.
    if (PRIVATE_KEY.search(text) or JWT.search(text) or
        re.search(r'(?i)(?:bearer|basic)\s+[A-Za-z0-9._~+/-]{18,}',text)):
        raise ValueError('Residual credential pattern in evidence')
    return text.encode('utf-8')


def collect(folder):
    root=folder.resolve(strict=True)
    if not root.is_dir() or folder.is_symlink():
        raise ValueError('Evidence input must be a real directory')
    selected=[];total=0
    for file in sorted(root.rglob('*')):
        mode=file.lstat().st_mode
        if stat.S_ISDIR(mode):continue
        if not stat.S_ISREG(mode) or file.is_symlink():
            raise ValueError('Evidence includes symlink, device or unknown file')
        relative=file.relative_to(root).as_posix()
        if (not SAFE_FILE.fullmatch(relative) or file.suffix.lower() not in SAFE_EXT
                or file.name in EXCLUDED_NAMES or '/.' in '/'+relative):
            raise ValueError('Unsafe evidence path or format')
        size=file.stat().st_size
        if size>MAX_FILE:raise ValueError('Oversized evidence')
        raw=file.read_bytes()
        clean=sanitize(raw)
        total+=len(clean)
        if total>MAX_BUNDLE:raise ValueError('Evidence bundle exceeds safe text budget')
        selected.append((relative,raw,clean))
    if not selected:raise ValueError('Empty evidence input is not reviewable')
    return selected


def create(args):
    if not SHA40.fullmatch(args.source_sha) or not SHA40.fullmatch(args.source_tree):
        raise ValueError('Full tested SHA and tree required')
    checkout(args.repo_root,args.source_sha,args.source_tree)
    files=collect(args.evidence_dir)
    record={'classification':'REDACTED_CANDIDATE_REVIEW_REQUIRED_NOT_ACCEPTANCE',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'source_commit':args.source_sha,'source_tree':args.source_tree,
            'review_status':'NEEDS_MANUAL_FILE_BY_FILE_REVIEW','owner_UAT':'NOT_RUN',
            'R01':'NOT_APPROVED','files':{}}
    for name,original,clean in files:
        record['files'][name]={'original_sha256':sha(original),
                               'exported_sha256':sha(clean),
                               'exported_size':len(clean),
                               'redaction_applied':clean!=original}
    manifest=json.dumps(record,sort_keys=True,indent=2).encode()+b'\n'
    sums=[sha(manifest)+'  MANIFEST.json']
    for name,_,clean in files:
        sums.append(sha(clean)+'  evidence/'+name)
    checksum=('\n'.join(sums)+'\n').encode()
    output=args.output.absolute()
    if output.exists() or output.is_relative_to(args.evidence_dir.resolve()):
        raise ValueError('Output ZIP must be new and outside evidence input')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.s1-evidence-',suffix='.zip',
                                     dir=output.parent,delete=False) as temp:
        scratch=Path(temp.name)
    try:
        with zipfile.ZipFile(scratch,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
            def add(name,data):
                info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
                info.external_attr=0o600<<16
                bundle.writestr(info,data)
            add('MANIFEST.json',manifest)
            add('SHA256SUMS',checksum)
            for name,_,clean in files:
                add('evidence/'+name,clean)
        os.chmod(scratch,0o600)
        scratch.replace(output)
    finally:
        scratch.unlink(missing_ok=True)
    return {'bundle_sha256':sha(output.read_bytes()),
            'file_count':len(files),'classification':record['classification']}


def verify(path):
    with zipfile.ZipFile(path,'r') as zipf:
        records=zipf.infolist()
        if len(records)<3 or len(set(x.filename for x in records))!=len(records):
            raise ValueError('Empty or duplicate evidence archive')
        if any(x.is_dir() or x.file_size>MAX_FILE for x in records):
            raise ValueError('Unknown evidence member type/size')
        for member in records:
            name=member.filename
            if (name.startswith('/') or '..' in Path(name).parts or '\\\\' in name
                    or not SAFE_FILE.fullmatch(name) or
                    ((member.external_attr>>16)&0o170000)==0o120000):
                raise ValueError('Evidence archive contains traversal/symlink/unsafe member')
        if zipf.testzip() is not None:raise ValueError('Archive CRC check failed')
        manifest=json.loads(zipf.read('MANIFEST.json'))
        if manifest.get('classification')!='REDACTED_CANDIDATE_REVIEW_REQUIRED_NOT_ACCEPTANCE':
            raise ValueError('Evidence package classification invalid')
        lines=zipf.read('SHA256SUMS').decode().splitlines()
        expectation={}
        for line in lines:
            parts=line.split('  ',1)
            if len(parts)!=2 or not re.fullmatch(r'[a-f0-9]{64}',parts[0]):
                raise ValueError('Invalid archive SHA256SUMS')
            if parts[1] in expectation:raise ValueError('Duplicate archive checksum entry')
            expectation[parts[1]]=parts[0]
        if set(expectation)!=set(zipf.namelist())-{'SHA256SUMS'}:
            raise ValueError('Archive member inventory incomplete')
        for name,digest in expectation.items():
            if sha(zipf.read(name))!=digest:raise ValueError('Evidence checksum mismatch')
        return {'classification':'ARCHIVE_INTEGRITY_VERIFIED_MANUAL_REVIEW_REQUIRED',
                'source_commit':manifest.get('source_commit'),
                'files':len(manifest['files'])}


def main():
    parser=argparse.ArgumentParser()
    action=parser.add_subparsers(dest='command',required=True)
    c=action.add_parser('create')
    c.add_argument('--repo-root',required=True,type=Path)
    c.add_argument('--source-sha',required=True)
    c.add_argument('--source-tree',required=True)
    c.add_argument('--evidence-dir',required=True,type=Path)
    c.add_argument('--output',required=True,type=Path)
    v=action.add_parser('verify')
    v.add_argument('archive',type=Path)
    args=parser.parse_args()
    outcome=create(args) if args.command=='create' else verify(args.archive)
    print(json.dumps(outcome,sort_keys=True))


if __name__=='__main__':main()
