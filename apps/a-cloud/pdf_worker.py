"""Bounded text-only use of the pinned ON/content-core PDF parser dependency.

Reviewed upstream: content-core2.2.1/processors/document/pdf.py. Keep originals
unchanged. OCR, URL extraction, AI and external requests are not enabled.
"""
import json
import resource
import sys
import unicodedata

import pdfplumber


def extract(path):
    resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)
    texts = []
    size = 0
    with pdfplumber.open(path) as document:
        if not 1 <= len(document.pages) <= 100:
            raise ValueError("PDF page limit")
        for page in document.pages:
            text = unicodedata.normalize("NFKC", page.extract_text() or "")
            text = "".join(c for c in text if unicodedata.category(c)[0] != "C" or c in "\n\t")
            size += len(text.encode("utf-8"))
            if size > 1024 * 1024 - 200:
                raise ValueError("PDF text limit")
            texts.append(text)
    text = "\n\n".join(texts).strip()
    if not text:
        raise ValueError("PDF has no readable text; OCR is not enabled")
    return text


if __name__ == "__main__":
    try:
        print(json.dumps({"text": extract(sys.argv[1])}, ensure_ascii=False))
    except Exception:
        # Never echo file content, private paths or parser internals.
        print(json.dumps({"error": "Unreadable or unsupported text PDF"}))
        sys.exit(2)
