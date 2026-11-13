#!/usr/bin/env python3
"""Generate born-digital SYNTHETIC WP09 test PDF fixtures.

IMPLEMENTED_UNTESTED; not executed during code-only sprint.
No real school/student materials, no AI providers or external downloads.
Extended-Han requires an operator-supplied appropriately licensed TTF
which *actually contains* U+20000. Missing glyph FAILS, never silent tofu.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from fontTools.ttLib import TTFont as InspectFont

ENGLISH=("SUNRISE_SYNTHETIC_ENGLISH_2026",
         "This document contains only artificial mathematics examples.",
         "Fractions: one half plus one quarter equals three quarters.")
TRADITIONAL=("繁體中文數學教材：分數乘法與比例測試",
             "合成教材、非真實學校、非學生個人資料。",
             "SUNRISE_SYNTHETIC_CJK_2026")
EXTENDED=("擴充漢字測試："+chr(0x20000),
          "SUNRISE_SYNTHETIC_EXTENDED_HAN_2026")
MAX_SIZE=8*1024*1024


def supports(font_path,characters):
    if not font_path.is_file() or font_path.is_symlink() or font_path.stat().st_size>30<<20:
        raise ValueError('Operator-provided font missing, symlinked or unbounded')
    font=InspectFont(str(font_path),lazy=True)
    try:
        codepoints=set()
        for cmap in font['cmap'].tables:
            if cmap.isUnicode():codepoints.update(cmap.cmap)
        missing={ord(ch) for line in characters for ch in line if not ch.isspace()}-codepoints
        if missing:
            raise ValueError('Extended-Han font is missing required glyphs; no fallback to blank PDF')
    finally:
        font.close()


def write_pdf(path,lines,font='Helvetica',size=13):
    buffer=io.BytesIO()
    output=canvas.Canvas(buffer,pagesize=(595,842),pageCompression=0)
    output.setTitle('Sunrise Synthetic Stage1 Acceptance Fixture')
    output.setAuthor('Sunrise synthetic test generator')
    output.setFont(font,size)
    y=785
    for line in lines:
        output.drawString(42,y,line)
        y-=31
    output.showPage();output.save()
    raw=buffer.getvalue()
    if not raw.startswith(b'%PDF-') or len(raw)>MAX_SIZE:
        raise ValueError('Generated PDF malformed or above Gateway fixture size budget')
    path.write_bytes(raw)
    return {'filename':path.name,'bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest(),
            'text_markers':list(lines)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out-dir',required=True,type=Path)
    p.add_argument('--extended-han-font-ttf',required=True,type=Path)
    p.add_argument('--font-license-reference',required=True)
    args=p.parse_args()
    if args.out_dir.exists() or not args.out_dir.is_absolute():
        p.error('Synthetic fixture output must be a new absolute directory')
    if len(args.font_license_reference.strip())<8:
        p.error('Operator must record a valid source/licence reference for embedded font')
    supports(args.extended_han_font_ttf,EXTENDED)
    args.out_dir.mkdir(parents=True)
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    pdfmetrics.registerFont(TTFont('SunriseExtHan',str(args.extended_han_font_ttf)))
    assets=[
        write_pdf(args.out_dir/'synthetic-english.pdf',ENGLISH),
        write_pdf(args.out_dir/'synthetic-traditional-chinese.pdf',TRADITIONAL,'STSong-Light'),
        write_pdf(args.out_dir/'synthetic-extended-han.pdf',EXTENDED,'SunriseExtHan')
    ]
    manifest={'classification':'SYNTHETIC_FIXTURES_NOT_ACCEPTANCE',
              'created_utc':datetime.now(timezone.utc).isoformat(),
              'schools':['synthetic-school-a','synthetic-school-b'],
              'actors':['synthetic-admin','synthetic-service-a','synthetic-service-b'],
              'fixture_font_sha256':hashlib.sha256(args.extended_han_font_ttf.read_bytes()).hexdigest(),
              'font_license_reference':args.font_license_reference,
              'pdfs':assets,'negative_cases':[
                  'same_key_different_payload','different_key_same_scope',
                  'foreign_school_source','wrong_service_jwt_scope',
                  'search_overflow_no_vector','failed_worker_retry',
                  'wrong_restore_key','corrupt_backup','missing_original',
                  'foreign_graph_edge','stale_session_csrf']}
    (args.out_dir/'fixture-manifest.json').write_text(
        json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'classification':manifest['classification'],
                      'files':[x['filename'] for x in assets]},ensure_ascii=False))


if __name__=='__main__':main()
