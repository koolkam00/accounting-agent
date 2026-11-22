"""PDF text extraction with pypdf (pinned options for reproducibility)."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfExtraction:
    pages: list[str]
    ocr_required: bool
    page_count: int


def extract_pdf_text(
    source: bytes | str | Path, *, max_pages: int | None = None, max_chars: int | None = None
) -> PdfExtraction:
    """Extract per-page text. Flag OCR_REQUIRED for image-only PDFs."""
    if isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    else:
        data = source

    reader = PdfReader(BytesIO(data), strict=False)
    if max_pages is not None and (reader.is_encrypted or not 0 < len(reader.pages) <= max_pages):
        raise ValueError(f"Upload an unencrypted PDF with 1 to {max_pages} pages.")
    pages: list[str] = []
    any_text = False
    char_count = 0
    for page in reader.pages:
        # Pin extraction options for stability across pypdf versions.
        text = page.extract_text(extraction_mode="plain") or ""
        char_count += len(text)
        if max_chars is not None and char_count > max_chars:
            raise ValueError("The invoice has too much text for this pilot.")
        if text.strip():
            any_text = True
        pages.append(text)

    ocr_required = (len(pages) > 0) and (not any_text)
    return PdfExtraction(pages=pages, ocr_required=ocr_required, page_count=len(pages))
