#!/usr/bin/env python3
"""Exact source/runtime binding for executed Stage 1 synthetic cases.

This is not a runtime test or authority to return PASS. The caller must
perform real assertions and re-attest before publishing an executed PASS.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

_SHA40=re.compile(r'[0-9a-f]{40}\Z')
_SHA64=re.compile(r'[0-9a-f]{64}\Z')
_TYPE='SUNRISE_S1_A_DUAL_DB_RUNTIME_IDENTITY_UNREVIEWED'


def _git(root: Path, arg: str) -> str:
    return subprocess.run(['git','-C',str(root),'rev-parse',arg],
                          check=True,capture_output=True,text=True,
                          timeout=12).stdout.strip()


def inspect(root: Path, path: Path, source_sha: str, source_tree: str) -> str:
    """Validate immutable external runtime evidence; return SHA256 of raw JSON."""
    root=root.resolve(strict=True)
    if (not _SHA40.fullmatch(source_sha or '')
            or not _SHA40.fullmatch(source_tree or '')
            or _git(root,'HEAD')!=source_sha
            or _git(root,'HEAD^{tree}')!=source_tree):
        raise RuntimeError('Executed case Git SHA/tree mismatch')
    if (not isinstance(path,Path) or path.is_symlink()
            or not path.is_file() or path.resolve().is_relative_to(root)
            or not 0<path.stat().st_size<=4*1024*1024):
        raise RuntimeError('External immutable runtime JSON absent/unsafe')
    data=path.read_bytes()
    if not data or len(data)>4*1024*1024:
        raise RuntimeError('Runtime identity JSON changed or exceeded limit')
    doc=json.loads(data)
    if (not isinstance(doc,dict) or doc.get('type')!=_TYPE
            or doc.get('source_commit')!=source_sha
            or doc.get('source_tree')!=source_tree
            or set(doc.get('services',{}))!={'a_db','on_db','native'}
            or doc.get('gateway',{}).get('tls_verified') is not True):
        raise RuntimeError('Wrong runtime identity source/physical services/TLS')
    for service in ('a_db','on_db','native'):
        entry=doc['services'][service]
        if (not isinstance(entry,dict) or entry.get('status')!='running'
                or not re.fullmatch(r'sha256:[0-9a-f]{64}',
                                    str(entry.get('image_id','')))
                or not isinstance(entry.get('container_id'),str)
                or not re.fullmatch(r'[0-9a-f]{64}',entry['container_id'])):
            raise RuntimeError('Incomplete live-container identity')
    return hashlib.sha256(data).hexdigest()


def guard(root: Path, path: Path, source_sha: str, source_tree: str, expected_sha256: str) -> None:
    """Reopen source and runtime evidence after real case side effects."""
    if not _SHA64.fullmatch(expected_sha256 or ''):
        raise RuntimeError('Missing initial provenance digest')
    if inspect(root,path,source_sha,source_tree)!=expected_sha256:
        raise RuntimeError('Runtime identity changed across executed case')


def load_live_services(context: str, project: str) -> dict:
    """Re-inspect the actual three-service Docker relay identity, not a saved URL."""
    from runtime_identity import load_containers
    return load_containers(context, project)


def resolve_native_endpoint(root: Path, path: Path, source_sha: str,
                            source_tree: str, expected_sha256: str) -> str:
    """Fail closed before ANY Native POST if saved identity differs from live Docker."""
    if not _SHA64.fullmatch(expected_sha256 or ''):
        raise RuntimeError('AT06 missing runtime provenance hash')
    if inspect(root, path, source_sha, source_tree) != expected_sha256:
        raise RuntimeError('AT06 stale runtime identity hash or Git source')
    record = json.loads(path.read_bytes())
    context, project = record.get('context'), record.get('project')
    if (not isinstance(context,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',context)
            or not isinstance(project,str)
            or not re.fullmatch(r'sunrise-s1-[a-z0-9-]{8,40}',project)):
        raise RuntimeError('AT06 invalid Docker context or exclusive project')
    saved = record.get('services')
    if not isinstance(saved,dict) or set(saved) != {'a_db','on_db','native'}:
        raise RuntimeError('AT06 missing exact physical services')
    live = load_live_services(context,project)
    if not isinstance(live,dict) or set(live) != set(saved):
        raise RuntimeError('AT06 live Docker service set mismatch')
    for role in ('a_db','on_db','native'):
        for field in ('container_id','image_id','network_id','persistent_volume',
                      'host_relay','published_ports'):
            if saved[role].get(field) != live[role].get(field):
                raise RuntimeError('AT06 saved/live Docker relay identity changed: '+role+'/'+field)
    mappings = live['native']['published_ports']
    if (not isinstance(mappings,list) or len(mappings)!=1
            or mappings[0].get('container_port')!='5055/tcp'
            or mappings[0].get('host_ip')!='127.0.0.1'
            or type(mappings[0].get('host_port')) is not int
            or not 1024 <= mappings[0]['host_port'] <= 65535):
        raise RuntimeError('AT06 native relay has no unique private loopback endpoint')
    if (live['native']['host_relay'].get('port') != mappings[0]['host_port']):
        raise RuntimeError('AT06 relay port differs from live published port')
    return 'http://127.0.0.1:'+str(mappings[0]['host_port'])
