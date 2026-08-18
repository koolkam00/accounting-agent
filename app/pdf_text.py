"""PDF text extraction with pypdf (pinned options for reproducibility)."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.errors import PdfExtractionError


@dataclass(frozen=True)
class PdfExtraction:
    pages: list[str]
    ocr_required: bool
    page_count: int


def extract_pdf_text(source: bytes | str | Path) -> PdfExtraction:
    """Extract per-page text. Flag OCR_REQUIRED for image-only PDFs."""
    if isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    else:
        data = source

    try:
        reader = PdfReader(BytesIO(data), strict=False)
        page_count = len(reader.pages)
    except (PyPdfError, OSError, ValueError) as exc:
        raise PdfExtractionError(
            f"Unreadable PDF ({len(data)} bytes): {type(exc).__name__}: {exc}"
        ) from exc

    pages: list[str] = []
    any_text = False
    for index, page in enumerate(reader.pages, start=1):
        # Pin extraction options for stability across pypdf versions.
        try:
            text = page.extract_text(extraction_mode="plain") or ""
        except (PyPdfError, OSError, ValueError, KeyError) as exc:
            raise PdfExtractionError(
                f"Text extraction failed on page {index} of {page_count}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        if text.strip():
            any_text = True
        pages.append(text)

    ocr_required = (len(pages) > 0) and (not any_text)
    return PdfExtraction(pages=pages, ocr_required=ocr_required, page_count=len(pages))
