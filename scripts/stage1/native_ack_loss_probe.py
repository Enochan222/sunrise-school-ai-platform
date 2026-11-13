"""Real TCP response suppression AFTER upstream native notebook-create commit.

The proxy relays only one authenticated create request to a pinned real native API,
reads its complete successful HTTP receipt, then closes the client connection
WITHOUT sending an acknowledgement. This is a distinct fault from a process
crash *after* Native.create_notebook returned successfully.

Only invoke on an exclusive synthetic host. Does not emulate a native DB crash.
"""
from __future__ import annotations
import asyncio
import json
import re

import httpx
from native import Native, NativeUnavailable


async def create_and_drop_ack(secret: str, marker: str,
                              native_host: str = 'http://127.0.0.1:5055') -> dict:
    if not re.fullmatch(r'sunrise-a-op-v1:[a-f0-9]{64}',marker):
        raise ValueError('Invalid native creation marker')
    state={'forwarded':0,'upstream_ack':False,'downstream_ack_sent':False}
    transport_error=[]
    async def proxy(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            # HTTPX sends Content-Length for the small JSON create body.
            raw=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),10)
            if len(raw)>16000:raise ValueError('Request headers too large')
            head=raw.decode('iso-8859-1')
            first=head.split('\r\n',1)[0]
            if not first.startswith('POST /api/notebooks HTTP/1.'):
                raise ValueError('Unexpected request routed to injection proxy')
            match=re.search(r'(?im)^Content-Length: (\d+)\r?$',head)
            if not match or int(match.group(1))>8192:
                raise ValueError('Missing or excessive POST request length')
            length=int(match.group(1))
            payload=await asyncio.wait_for(reader.readexactly(length),10)
            data=json.loads(payload)
            if not isinstance(data,dict) or data.get('description')!=marker:
                raise ValueError('Native create marker incorrect; refusing to forward')
            state['forwarded']+=1
            if state['forwarded']!=1:
                raise ValueError('Duplicate native create detected')
            # Forward the authenticated JSON request to the *real* Open Notebook.
            async with httpx.AsyncClient(timeout=25,trust_env=False,follow_redirects=False) as cli:
                response=await cli.post(native_host+'/api/notebooks',content=payload,
                    headers={'Content-Type':'application/json','Authorization':'Bearer '+secret,
                             'Accept':'application/json'})
                response.raise_for_status()
                receipt=response.json()
                if not isinstance(receipt,dict) or not re.fullmatch(
                        r'notebook:[A-Za-z0-9_-]{1,128}',str(receipt.get('id',''))):
                    raise ValueError('Upstream native create lacked valid receipt')
            state['upstream_ack']=True
            # DELIBERATE FAULT: close without writing a single HTTP response byte.
        except Exception as exc:
            transport_error.append(type(exc).__name__)
        finally:
            writer.close()
            try:await writer.wait_closed()
            except ConnectionError:pass

    server=await asyncio.start_server(proxy,'127.0.0.1',0)
    try:
        port=server.sockets[0].getsockname()[1]
        n=Native(f'http://127.0.0.1:{port}',secret)
        try:
            await n.create_notebook('SUNRISE SYNTHETIC ACK LOSS',marker)
        except NativeUnavailable:
            pass
        else:
            raise AssertionError('Client unexpectedly received Native Create acknowledgement')
        # Close the listening socket before any replay is attempted.
        server.close()
        await server.wait_closed()
    finally:
        server.close()
        await server.wait_closed()
    if transport_error or state['forwarded']!=1 or not state['upstream_ack'] or state['downstream_ack_sent']:
        raise AssertionError('Fault injection not proven: '+str({'state':state,'errors':transport_error}))
    return state
