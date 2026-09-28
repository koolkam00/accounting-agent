"""Document text extraction for QoE evidence: pypdf text layer + canonical whitespace.

Quotes are verified against this canonical page text, so extraction options are
pinned and normalization is deterministic.
"""

from __future__ import annotations

import re
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

_SPACE_RUN = re.compile(r"[ \t]+")


def canonicalize_page_text(page_text: str) -> str:
    """NFC, unified newlines, collapsed spaces, at most one blank line in a row."""
    text = unicodedata.normalize("NFC", page_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    blank_pending = False
    for line in text.split("\n"):
        collapsed = _SPACE_RUN.sub(" ", line).rstrip()
        if collapsed == "":
            if out:
                blank_pending = True
            continue
        if blank_pending:
            out.append("")
            blank_pending = False
        out.append(collapsed)
    return "\n".join(out)


def extract_pdf_pages(source: bytes | str | Path) -> list[str]:
    """Raw per-page text from the PDF text layer (empty string for image-only pages)."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source
    reader = PdfReader(BytesIO(data), strict=False)
    # Plain mode is pinned so page text (and therefore quote verification) is stable.
    return [page.extract_text(extraction_mode="plain") or "" for page in reader.pages]
