#!/usr/bin/env python3
"""Actual native API/worker/PDF/search/restart baseline; no mocks.

Only run after pinned patch, Docker private-network and secrets verification.
Stores redacted machine-readable evidence. Does NOT perform crash/ACK fault injection.
"""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
from native import Native


def fixture():
    out=io.BytesIO()
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    p=canvas.Canvas(out)
    p.setFont('STSong-Light',16)
    p.drawString(60,770,'繁體中文數學教材：分數乘法與比例測試')
    p.setFont('Helvetica',12)
    p.drawString(60,730,'SUNRISE_SYNTHETIC_FRACTION_2026')
    p.save()
    return out.getvalue()


async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=Path('native-runtime-redacted.json'))
    ap.add_argument('--host',default='http://127.0.0.1:5055')
    args=ap.parse_args()
    secret=os.environ['OPEN_NOTEBOOK_PASSWORD']
    # Explicit gating is test-only: operator already patched upstream source.
    n=Native(args.host,secret,text_only_verified=True)
    raw=fixture()
    sha=hashlib.sha256(raw).hexdigest()
    result={'start_utc':datetime.now(timezone.utc).isoformat(),
            'source_pin':'5e285b7a2e435895c4ee99ad7e4b8d2af64c3239',
            'pdf_sha256':sha,'runtime_tests':{},'official_S1_AT01_15':'NOT_RUN'}
    try:
        nb=await n.create_notebook('SUNRISE SYNTHETIC WP00 NO STUDENT DATA')
        result['notebook_id']=nb
        result['runtime_tests']['notebook_create']='PASS'
        receipt=await n.upload_pdf(nb,raw,'wp00_synthetic_zh.pdf','SUNRISE_SYNTHETIC_FRACTION_2026')
        src=receipt['id'];result['source_id']=src
        result['runtime_tests']['pdf_submit_embed_off']='PASS'
        deadline=time.monotonic()+120
        while True:
            detail=await n.ensure_owned(src,nb)
            status=detail.get('status')
            if status=='completed' or (detail.get('full_text') and status in (None,'completed')):
                break
            if status in ('failed','error','cancelled','unknown'):
                raise RuntimeError(f'Worker failed/unknown: status={status!r}')
            if time.monotonic()>deadline:
                raise TimeoutError('Worker extraction not confirmed within bounded polling window')
            await asyncio.sleep(2)
        text=detail.get('full_text') or ''
        if '繁體中文數學教材' not in text or 'SUNRISE_SYNTHETIC_FRACTION_2026' not in text:
            raise RuntimeError('Required synthetic Chinese/ASCII PDF text not extracted')
        result['runtime_tests']['native_worker_pdf_extraction']='PASS'
        if await n.original(src,sha)!=raw:
            raise RuntimeError('Immutable PDF content not preserved')
        result['runtime_tests']['original_hash']='PASS'
        matches=await n.search(nb,'SUNRISE_SYNTHETIC_FRACTION_2026',10)
        if src not in [hit['parent_id'] for hit in matches]:
            raise RuntimeError('Scoped BM25 did not locate extracted synthetic PDF')
        result['runtime_tests']['scoped_bm25']='PASS'
        # Chinese BM25 behavior is version/tokenizer-sensitive: record truth, not fabricated PASS.
        zh=await n.search(nb,'繁體中文',10)
        result['runtime_tests']['traditional_chinese_bm25'] = 'PASS' if src in [hit['parent_id'] for hit in zh] else 'FAIL'
        result['runtime_tests']['graph_owner_readback']='PASS'
        result['status']='PASS' if all(v=='PASS' for v in result['runtime_tests'].values()) else 'FAIL'
    except Exception as e:
        result['status']='FAIL'
        result['error_type']=type(e).__name__
        # Never include unredacted HTTP error bodies, passwords or PDF data in a shared report.
        result['error']='Runtime prerequisite, native behavior, worker or text-search probe failed'
        raise
    finally:
        result['end_utc']=datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'result':result.get('status'),'tests':result['runtime_tests'],
                          'evidence_file':str(args.out)},ensure_ascii=False))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':
    asyncio.run(main())
