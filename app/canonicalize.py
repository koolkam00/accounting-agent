"""Deterministic text canonicalization for invoice PDF text."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass


PAGE_SEP_TEMPLATE = "\n\n--- PAGE {n} ---\n\n"
_SPACE_RUN = re.compile(r"[ \t]+")


def canonicalize_page_text(page_text: str) -> str:
    """Normalize a single page: NFC, newlines, whitespace policy."""
    text = unicodedata.normalize("NFC", page_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    out_lines: list[str] = []
    blank_pending = False
    for line in lines:
        collapsed = _SPACE_RUN.sub(" ", line).rstrip()
        if collapsed == "":
            if out_lines:  # preserve as single blank line
                blank_pending = True
            continue
        if blank_pending:
            out_lines.append("")
            blank_pending = False
        out_lines.append(collapsed)
    return "\n".join(out_lines)


def join_pages(pages: list[str]) -> str:
    """Join page texts with stable page separators. Page numbers are 1-based."""
    parts: list[str] = []
    for i, page in enumerate(pages, start=1):
        if i > 1:
            parts.append(PAGE_SEP_TEMPLATE.format(n=i))
        parts.append(canonicalize_page_text(page))
    return "".join(parts) if parts else ""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanonicalDocument:
    original_hash: str
    canonical_text: str
    canonical_hash: str
    page_count: int
    ocr_required: bool


def canonicalize_document(
    original_bytes: bytes,
    pages: list[str],
    ocr_required: bool = False,
) -> CanonicalDocument:
    canonical_text = join_pages(pages)
    return CanonicalDocument(
        original_hash=sha256_bytes(original_bytes),
        canonical_text=canonical_text,
        canonical_hash=sha256_text(canonical_text),
        page_count=len(pages),
        ocr_required=ocr_required,
    )
