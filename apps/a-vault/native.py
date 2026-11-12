"""Private allowlisted Open Notebook v1.15.1 HTTP adapter.

Search is activated ONLY when a locally patched native server explicitly confirms its
fixed no-vector behavior. Files are size-bounded *during* download, not afterwards.
This adapter is not itself proof of live Open Notebook or SurrealDB functionality.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
import httpx

NOTEBOOK_RE = re.compile(r"notebook:[A-Za-z0-9_-]{1,128}\Z")
SOURCE_RE = re.compile(r"source:[A-Za-z0-9_-]{1,128}\Z")
TEXT_PATCH_MARKER = "sunrise-a-text-only-no-vector-v1"
MAX_ORIGINAL_BYTES = 25 * 1024 * 1024


class NativeUnavailable(Exception):
    pass


class NativeOwnershipError(Exception):
    pass


def checked_id(value: str, kind: str) -> str:
    rule = {"notebook": NOTEBOOK_RE, "source": SOURCE_RE}[kind]
    if not isinstance(value, str) or not rule.fullmatch(value):
        raise NativeOwnershipError(f"Invalid native {kind} record ID")
    return value


class Native:
    def __init__(self, base_url, secret, transport=None):
        self.base = base_url.rstrip("/")
        self.secret = secret
        self.transport = transport

    def _client(self):
        return httpx.AsyncClient(base_url=self.base, timeout=httpx.Timeout(20),
                                 transport=self.transport, trust_env=False,
                                 headers={"Authorization": f"Bearer {self.secret}",
                                          "Accept": "application/json"},
                                 follow_redirects=False)

    async def _request(self, method, path, **kwargs):
        async with self._client() as client:
            try:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                raise NativeUnavailable("Native Open Notebook request unavailable or rejected") from exc

    async def create_notebook(self, name):
        r = await self._request("POST", "/api/notebooks", json={
            "name": name, "description": "Sunrise A synthetic private notebook"})
        try:
            data = r.json()
            return checked_id(data["id"], "notebook")
        except (ValueError, KeyError, TypeError, NativeOwnershipError) as exc:
            raise NativeUnavailable("Native notebook creation receipt malformed") from exc

    async def upload_pdf(self, nb_id, data, filename, title):
        checked_id(nb_id, "notebook")
        fields = {"type": "upload", "notebooks": json.dumps([nb_id]),
                  "title": title, "embed": "false", "transformations": "[]",
                  "delete_source": "false", "async_processing": "true"}
        r = await self._request("POST", "/api/sources", data=fields,
                                files={"file": (filename, data, "application/pdf")})
        try:
            payload = r.json()
            checked_id(payload["id"], "source")
            return payload
        except (ValueError, KeyError, TypeError, NativeOwnershipError) as exc:
            raise NativeUnavailable("Native source creation receipt malformed") from exc

    async def source(self, source_id):
        checked_id(source_id, "source")
        try:
            payload = (await self._request("GET", f"/api/sources/{source_id}")).json()
        except ValueError as exc:
            raise NativeUnavailable("Native source readback response invalid") from exc
        if not isinstance(payload, dict):
            raise NativeUnavailable("Native source readback has invalid shape")
        return payload

    async def ensure_owned(self, source_id, notebook_id):
        checked_id(notebook_id, "notebook")
        source = await self.source(source_id)
        linked = source.get("notebooks")
        if source.get("id") != source_id or not isinstance(linked, list) or linked != [notebook_id]:
            raise NativeOwnershipError("Native source lacks one exact expected notebook owner")
        return source

    async def original(self, source_id, expected_sha):
        checked_id(source_id, "source")
        if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise NativeOwnershipError("Invalid immutable hash receipt")
        received = bytearray()
        async with self._client() as client:
            try:
                async with client.stream("GET", f"/api/sources/{source_id}/download") as r:
                    r.raise_for_status()
                    length = r.headers.get("content-length")
                    if length is not None and (not length.isdigit() or int(length) > MAX_ORIGINAL_BYTES):
                        raise NativeOwnershipError("Native original exceeds allowed size")
                    async for chunk in r.aiter_bytes(chunk_size=64 * 1024):
                        if len(received) + len(chunk) > MAX_ORIGINAL_BYTES:
                            raise NativeOwnershipError("Native original exceeds allowed size")
                        received.extend(chunk)
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                raise NativeUnavailable("Native original download unavailable") from exc
        result = bytes(received)
        if not hmac.compare_digest(hashlib.sha256(result).hexdigest(), expected_sha):
            raise NativeOwnershipError("Native original bytes disagree with immutable hash")
        return result

    async def search(self, nb_id, term, limit=20):
        # All searches must prove native has the A-only non-vector patch.
        checked_id(nb_id, "notebook")
        if not isinstance(term, str) or not term.strip() or not 1 <= limit <= 50:
            raise NativeUnavailable("Invalid scoped text search request")
        try:
            proof = (await self._request("GET", "/api/sunrise-patch-status")).json()
        except ValueError as exc:
            raise NativeUnavailable("Native patch attestation malformed") from exc
        if not isinstance(proof, dict) or proof.get("marker") != TEXT_PATCH_MARKER or proof.get("text_only") is not True:
            raise NativeUnavailable("Native text-only guard not confirmed; search fails closed")
        try:
            data = (await self._request("POST", "/api/search", json={
                "query": term, "type": "text", "limit": limit,
                "notebook_ids": [nb_id], "search_sources": True,
                "search_notes": False})).json()
        except ValueError as exc:
            raise NativeUnavailable("Native text search response invalid") from exc
        if not isinstance(data, dict) or data.get("search_type") != "text" or not isinstance(data.get("results"), list):
            raise NativeUnavailable("Native text search response invalid")
        if len(data["results"]) > limit:
            raise NativeUnavailable("Native text search returned too many results")
        # Never allow arbitrary native snippets to escape; Gateway performs per-hit
        # school, shell, local source mapping and native reference readbacks.
        return data["results"]
