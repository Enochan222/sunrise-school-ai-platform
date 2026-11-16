"""Private v1.15.1 Open Notebook adapter. No raw native interface is exposed to clients.

The search endpoint requires an independently verified *patched* native runtime:
upstream v1.15.1 otherwise silently falls back from text to vector search.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import time
from urllib.parse import urlsplit

import httpx

_LOG = logging.getLogger(__name__)


class NativeUnavailable(Exception):
    """Native API failed: do not interpret this as an empty search result."""


class NativeOwnershipError(Exception):
    """Native source identity or exclusive notebook edge cannot be established."""


RECORD_RE = re.compile(r"^(notebook|source):[A-Za-z0-9_-]{1,128}$", re.ASCII)
MAX_NATIVE_DOWNLOAD = 25 * 1024 * 1024


def checked_id(value: str, expected_table: str) -> str:
    if not isinstance(value, str) or not RECORD_RE.fullmatch(value) or not value.startswith(expected_table + ':'):
        raise NativeOwnershipError(f'Invalid {expected_table} record id')
    return value


class Native:
    def __init__(self, base_url: str, secret: str, transport=None, *, text_only_verified=False,
                 max_download_bytes=MAX_NATIVE_DOWNLOAD):
        parsed = urlsplit(base_url)
        if (parsed.scheme != 'http' or not parsed.hostname or parsed.username or parsed.password
                or parsed.path.rstrip('/') or parsed.query or parsed.fragment):
            raise ValueError('Native URL must be an internal HTTP origin with no credentials or path')
        if not secret or len(secret) < 16:
            raise ValueError('Native password must be a strong configured secret')
        if not (1 <= max_download_bytes <= MAX_NATIVE_DOWNLOAD):
            raise ValueError('Native download limit must be in 1..25MiB')
        self.base = base_url.rstrip('/')
        self.secret = secret
        self.transport = transport
        self.text_only_verified = bool(text_only_verified)
        self.max_download_bytes = max_download_bytes

    def _client(self):
        return httpx.AsyncClient(base_url=self.base, timeout=httpx.Timeout(25, connect=5),
                                 transport=self.transport, trust_env=False,
                                 follow_redirects=False,
                                 headers={'Authorization': f'Bearer {self.secret}', 'Accept': 'application/json'})

    @staticmethod
    def _checked_response(r: httpx.Response) -> None:
        if 300 <= r.status_code < 400:
            raise NativeUnavailable('Native redirects are not permitted')
        r.raise_for_status()

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        started = time.monotonic()
        # Only a fixed route category may appear in diagnostic logs. Source IDs,
        # query terms, credentials and request/response payloads stay private.
        endpoint = ('search' if path == '/api/search' else
                    'patch_attestation' if path == '/api/sunrise-patch-status' else
                    'source' if path.startswith('/api/sources/') else 'other')
        async with self._client() as client:
            try:
                r = await client.request(method, path, **kwargs)
                self._checked_response(r)
                return r
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                _LOG.warning('Native request unavailable endpoint=%s elapsed_ms=%.1f error_type=%s',
                             endpoint, (time.monotonic()-started)*1000, type(e).__name__)
                raise NativeUnavailable('Native Open Notebook request unavailable or rejected') from e

    async def create_notebook(self, name: str, marker: str | None = None) -> str:
        if marker is not None and (not isinstance(marker,str) or
                not re.fullmatch(r'sunrise-a-op-v1:[a-f0-9]{64}',marker)):
            raise NativeOwnershipError('Invalid reserved Notebook creation marker')
        description = marker if marker is not None else 'Sunrise A synthetic private notebook'
        r = await self._request('POST', '/api/notebooks',
                                json={'name': name, 'description': description})
        try:
            data = r.json()
            if not isinstance(data, dict):
                raise ValueError()
            return checked_id(data['id'], 'notebook')
        except (ValueError, TypeError, KeyError, NativeOwnershipError) as e:
            raise NativeUnavailable('Native notebook receipt invalid') from e

    async def find_notebooks_by_marker(self, marker: str) -> list[str]:
        # Marker is an operation identity, NOT a title-based heuristic.
        if not isinstance(marker,str) or not re.fullmatch(r'sunrise-a-op-v1:[a-f0-9]{64}',marker):
            raise NativeOwnershipError('Invalid native creation marker')
        response=await self._request('GET','/api/notebooks')
        try:
            notebooks=response.json()
            if not isinstance(notebooks,list) or len(notebooks)>10000:
                raise ValueError('Unbounded or invalid notebook readback')
            candidates=[]
            for n in notebooks:
                if not isinstance(n,dict):
                    raise ValueError('Invalid notebook list entry')
                if n.get('description') == marker:
                    candidates.append(checked_id(n.get('id'),'notebook'))
            if len(candidates)!=len(set(candidates)) or len(candidates)>1:
                raise NativeOwnershipError('Duplicate native notebook creation marker')
            for nb in candidates:
                readback=(await self._request('GET',f'/api/notebooks/{nb}')).json()
                if (not isinstance(readback,dict) or readback.get('id')!=nb or
                        readback.get('description')!=marker):
                    raise NativeOwnershipError('Native Notebook marker readback mismatch')
            return candidates
        except (ValueError,TypeError,KeyError) as e:
            raise NativeUnavailable('Malformed native Notebook marker readback') from e

    async def upload_pdf(self, nb_id: str, data: bytes, filename: str, title: str) -> dict:
        checked_id(nb_id, 'notebook')
        if not isinstance(data, bytes) or not data.startswith(b'%PDF-'):
            raise ValueError('Synthetic PDF must have a PDF signature')
        if not filename or '/' in filename or '\\' in filename or not filename.lower().endswith('.pdf'):
            raise ValueError('Invalid upload filename')
        fields = {'type': 'upload', 'notebooks': json.dumps([nb_id]), 'title': title,
                  'embed': 'false', 'transformations': '[]', 'delete_source': 'false',
                  'async_processing': 'true'}
        r = await self._request('POST', '/api/sources', data=fields,
                                files={'file': (filename, data, 'application/pdf')})
        try:
            receipt = r.json()
            if not isinstance(receipt, dict):
                raise ValueError()
            checked_id(receipt['id'], 'source')
            return receipt
        except (ValueError, TypeError, KeyError, NativeOwnershipError) as e:
            raise NativeUnavailable('Native source receipt invalid') from e

    async def source(self, source_id: str) -> dict:
        checked_id(source_id, 'source')
        r = await self._request('GET', f'/api/sources/{source_id}')
        try:
            src = r.json()
            if not isinstance(src, dict) or src.get('id') != source_id:
                raise NativeOwnershipError('Native source identity mismatched')
            return src
        except ValueError as e:
            raise NativeUnavailable('Native source JSON invalid') from e

    async def ensure_owned(self, source_id: str, notebook_id: str) -> dict:
        checked_id(notebook_id, 'notebook')
        src = await self.source(source_id)
        # Never accept multi-notebook relationships, missing graph info, or a string instead of a list.
        if src.get('notebooks') != [notebook_id]:
            raise NativeOwnershipError('Native source does not have exactly one expected notebook owner')
        return src

    @staticmethod
    def processing_state(source: dict) -> str:
        """Conservative read-only Native worker status for an already-owned source.

        This does not mutate or enqueue native jobs, infer readiness from the
        upload receipt, or expose upstream command internals to the browser.
        Native SourceResponse on pinned v1.15.1 supplies status and full_text.
        """
        if not isinstance(source, dict):
            raise NativeUnavailable('Malformed native source status')
        status=source.get('status')
        if status=='completed':
            full_text=source.get('full_text')
            return 'READY' if isinstance(full_text,str) and full_text.strip() else 'UNKNOWN'
        if status in ('queued','running'):
            return 'PROCESSING'
        if status=='failed':
            return 'FAILED'
        return 'UNKNOWN'

    async def retry_failed_owned_source(self, source_id: str, notebook_id: str,
                                        expected_sha: str, *, operator_authorized=False) -> dict:
        """Private operator-only failed-job retry, NEVER a browser/API route.

        Requires the full pinned all-or-nothing Sunrise Native patch attestation.
        Native retry independently enforces status=='failed' and embed=False;
        any race/ACK loss must be reconciled manually, never blindly retried.
        """
        if not operator_authorized or not self.text_only_verified:
            raise NativeUnavailable('Unapproved native retry; disabled by default')
        checked_id(source_id,'source')
        checked_id(notebook_id,'notebook')
        proof=(await self._request('GET','/api/sunrise-patch-status')).json()
        if (not isinstance(proof,dict) or
                proof.get('marker')!='sunrise-a-text-only-no-vector-v1' or
                proof.get('text_only') is not True):
            raise NativeUnavailable('Pinned A-only native patch provenance not verified')
        before=await self.ensure_owned(source_id,notebook_id)
        if before.get('status')!='failed' or not before.get('command_id'):
            raise NativeUnavailable('Native job not proven failed; retry forbidden')
        # Immutable source bytes are compared before any destructive/queuing action.
        await self.original(source_id,expected_sha)
        try:
            receipt=(await self._request('POST',f'/api/sources/{source_id}/retry')).json()
        except (ValueError,TypeError) as e:
            raise NativeUnavailable('Native retry receipt unreadable; reconcile manually') from e
        if (not isinstance(receipt,dict) or receipt.get('id')!=source_id or
                receipt.get('status')!='queued' or
                not isinstance(receipt.get('command_id'),str) or
                receipt['command_id']==before['command_id']):
            raise NativeUnavailable('Native retry outcome uncertain; no automatic replay')
        after=await self.ensure_owned(source_id,notebook_id)
        await self.original(source_id,expected_sha)
        if after.get('command_id')!=receipt['command_id']:
            raise NativeUnavailable('Retry command identity not durable/consistent')
        return {'source_id':source_id,'notebook_id':notebook_id,
                'new_command_id':receipt['command_id'],'state':'RETRY_SUBMITTED_NOT_COMPLETED'}

    async def original(self, source_id: str, expected_sha: str) -> bytes:
        """Verify bounded native body BEFORE passing any byte to Gateway client.

        The Gateway must already have authenticated and checked Shell/Source/Native owner.
        HTTPX streaming avoids unbounded buffering on oversized/chunked payloads.
        """
        checked_id(source_id, 'source')
        if not isinstance(expected_sha, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_sha):
            raise NativeOwnershipError('Invalid original SHA-256 receipt')
        chunks = []
        size = 0
        digest = hashlib.sha256()
        async with self._client() as client:
            try:
                async with client.stream('GET', f'/api/sources/{source_id}/download') as r:
                    self._checked_response(r)
                    length = r.headers.get('content-length')
                    if length is not None:
                        try:
                            declared = int(length)
                        except (ValueError, TypeError) as e:
                            raise NativeOwnershipError('Invalid native content-length') from e
                        if declared < 0 or declared > self.max_download_bytes:
                            raise NativeOwnershipError('Native original exceeds permitted size')
                    async for chunk in r.aiter_bytes(chunk_size=65536):
                        size += len(chunk)
                        if size > self.max_download_bytes:
                            raise NativeOwnershipError('Native original exceeds permitted size')
                        digest.update(chunk)
                        chunks.append(chunk)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                raise NativeUnavailable('Native original download failed') from e
        if not hmac.compare_digest(digest.hexdigest(), expected_sha):
            raise NativeOwnershipError('Native original hash does not match immutable receipt')
        return b''.join(chunks)

    async def search(self, nb_id: str, term: str, limit: int = 20) -> list[dict]:
        """Scoped BM25 only. Must not activate on unpatched pinned native source."""
        checked_id(nb_id, 'notebook')
        if not self.text_only_verified:
            raise NativeUnavailable('Pinned native text fallback is not verified to be vector-free')
        # An environment flag alone is NOT sufficient attestation. The patched
        # native service must prove its A-only no-vector implementation on each search.
        try:
            proof = (await self._request('GET', '/api/sunrise-patch-status')).json()
        except (ValueError, TypeError) as e:
            raise NativeUnavailable('Native patch proof malformed') from e
        if not isinstance(proof, dict) or proof.get('marker') != 'sunrise-a-text-only-no-vector-v1' or proof.get('text_only') is not True:
            raise NativeUnavailable('Pinned native no-vector patch not confirmed')
        if not isinstance(term, str) or not term.strip() or not 1 <= limit <= 50:
            raise ValueError('Invalid scoped text-search input')
        r = await self._request('POST', '/api/search',
                                json={'query': term, 'type': 'text', 'limit': limit,
                                      'notebook_ids': [nb_id], 'search_sources': True,
                                      'search_notes': False})
        try:
            payload = r.json()
            if not isinstance(payload, dict) or payload.get('search_type') != 'text':
                raise ValueError()
            results = payload['results']
            if not isinstance(results, list) or len(results) > limit:
                raise ValueError()
            for hit in results:
                if not isinstance(hit, dict):
                    raise ValueError()
                checked_id(hit.get('parent_id'), 'source')
            return results
        except (ValueError, KeyError, NativeOwnershipError, TypeError) as e:
            raise NativeUnavailable('Native text-search receipt invalid') from e
