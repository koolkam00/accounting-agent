"""OpenAI-compatible LLM client (vLLM) + MockLLMClient for local tests."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from app.schemas import ExtractedInvoice, InvoiceLineItem, EvidenceSpan
from app.settings import get_settings


INVOICE_JSON_SCHEMA: dict[str, Any] = {
    "name": "extracted_invoice",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "vendor_name": {"type": ["string", "null"]},
            "vendor_id": {"type": ["string", "null"]},
            "invoice_number": {"type": ["string", "null"]},
            "invoice_date": {"type": ["string", "null"]},
            "po_number": {"type": ["string", "null"]},
            "currency": {"type": ["string", "null"]},
            "subtotal": {"type": ["string", "null"]},
            "tax": {"type": ["string", "null"]},
            "freight": {"type": ["string", "null"]},
            "invoice_total": {"type": ["string", "null"]},
            "payment_terms": {"type": ["string", "null"]},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "line_number": {"type": "integer"},
                        "sku": {"type": "string"},
                        "description": {"type": "string"},
                        "quantity": {"type": "string"},
                        "unit_price": {"type": "string"},
                        "line_total": {"type": "string"},
                    },
                    "required": [
                        "line_number",
                        "sku",
                        "description",
                        "quantity",
                        "unit_price",
                        "line_total",
                    ],
                },
            },
            "ambiguities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field": {"type": "string"},
                        "reason": {"type": "string"},
                        "candidates": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["field", "reason", "candidates"],
                },
            },
            "evidence": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "quote": {"type": "string"},
                        "page": {"type": "integer"},
                    },
                    "required": ["quote", "page"],
                },
            },
        },
        "required": [
            "vendor_name",
            "vendor_id",
            "invoice_number",
            "invoice_date",
            "po_number",
            "currency",
            "subtotal",
            "tax",
            "freight",
            "invoice_total",
            "payment_terms",
            "line_items",
            "ambiguities",
            "evidence",
        ],
    },
}


class LLMClient(ABC):
    @abstractmethod
    def extract_invoice(self, canonical_text: str, *, case_id: Optional[str] = None) -> ExtractedInvoice:
        ...


class MockLLMClient(LLMClient):
    """
    Returns fixture expected extraction JSON when case_id / fixture path is known.
    Falls back to a deterministic regex parser for synthetic ReportLab invoices.
    """

    def __init__(self, fixture_root: Optional[Path] = None) -> None:
        settings_ignored = get_settings()  # ensure dotenv loaded
        _ = settings_ignored
        self.fixture_root = fixture_root
        self._expected_by_case: dict[str, dict[str, Any]] = {}

    def register_expected(self, case_id: str, expected: dict[str, Any]) -> None:
        self._expected_by_case[case_id] = expected

    def load_fixture_expected(self, case_dir: Path) -> None:
        expected_path = case_dir / "expected.json"
        if expected_path.exists():
            data = json.loads(expected_path.read_text(encoding="utf-8"))
            case_id = data.get("case_id") or case_dir.name
            self._expected_by_case[case_id] = data

    def extract_invoice(self, canonical_text: str, *, case_id: Optional[str] = None) -> ExtractedInvoice:
        if case_id and case_id in self._expected_by_case:
            exp = self._expected_by_case[case_id]
            extraction = exp.get("extraction") or exp.get("extracted_invoice")
            if extraction:
                return ExtractedInvoice.model_validate(extraction)
        # Try locate fixture by scanning known roots
        if case_id and self.fixture_root:
            for split in ("development", "holdout"):
                path = self.fixture_root / split / case_id / "expected.json"
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    extraction = data.get("extraction") or data.get("extracted_invoice")
                    if extraction:
                        return ExtractedInvoice.model_validate(extraction)
        return parse_synthetic_invoice_text(canonical_text)


class VLLMLLMClient(LLMClient):
    """OpenAI-compatible client targeting pinned vLLM server."""

    def __init__(self) -> None:
        from openai import OpenAI

        s = get_settings()
        self.settings = s
        self.client = OpenAI(base_url=s.vllm_base_url, api_key=s.vllm_api_key, timeout=1200.0)
        self.prompt = s.prompt_path.read_text(encoding="utf-8")

    def extract_invoice(self, canonical_text: str, *, case_id: Optional[str] = None) -> ExtractedInvoice:
        _ = case_id
        s = self.settings
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": f"Invoice text:\n\n{canonical_text}"},
        ]
        resp = self.client.chat.completions.create(
            model=s.model_name,
            messages=messages,
            temperature=s.temperature,
            top_p=s.top_p,
            seed=s.seed,
            n=1,
            response_format={
                "type": "json_schema",
                "json_schema": INVOICE_JSON_SCHEMA,
            },
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        return ExtractedInvoice.model_validate(data)


def parse_synthetic_invoice_text(text: str) -> ExtractedInvoice:
    """Deterministic parser for our ReportLab synthetic invoices."""

    def grab(pattern: str, default: Optional[str] = None) -> Optional[str]:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else default

    vendor_name = grab(r"Vendor:\s*(.+)")
    vendor_id = grab(r"Vendor ID:\s*(\S+)")
    invoice_number = grab(r"Invoice Number:\s*(\S+)")
    invoice_date = grab(r"Invoice Date:\s*(\S+)")
    po_number = grab(r"PO Number:\s*(\S+)")
    currency = grab(r"Currency:\s*(\S+)", "USD")
    payment_terms = grab(r"Payment Terms:\s*(.+)")
    subtotal = grab(r"Subtotal:\s*([0-9.]+)")
    tax = grab(r"Tax:\s*([0-9.]+)")
    freight = grab(r"Freight:\s*([0-9.]+)")
    invoice_total = grab(r"Invoice Total:\s*([0-9.]+)")

    line_items: list[InvoiceLineItem] = []
    # LINE|<n>|<sku>|<desc>|<qty>|<price>|<total>
    for m in re.finditer(
        r"LINE\|(\d+)\|([^|]+)\|([^|]+)\|([0-9.]+)\|([0-9.]+)\|([0-9.]+)",
        text,
    ):
        line_items.append(
            InvoiceLineItem(
                line_number=int(m.group(1)),
                sku=m.group(2).strip(),
                description=m.group(3).strip(),
                quantity=m.group(4).strip(),
                unit_price=m.group(5).strip(),
                line_total=m.group(6).strip(),
                evidence=EvidenceSpan(quote=m.group(0), page=1),
            )
        )

    evidence: dict[str, EvidenceSpan] = {}
    for field, val in [
        ("vendor_name", vendor_name),
        ("invoice_number", invoice_number),
        ("po_number", po_number),
        ("invoice_total", invoice_total),
    ]:
        if val and val in text:
            evidence[field] = EvidenceSpan(quote=val, page=1)

    ambiguities = []
    if "AMBIGUOUS:" in text:
        ambiguities.append(
            {"field": "vendor_name", "reason": "Marked ambiguous in source", "candidates": []}
        )

    return ExtractedInvoice(
        vendor_name=vendor_name,
        vendor_id=vendor_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        po_number=po_number,
        currency=currency,
        line_items=line_items,
        subtotal=subtotal,
        tax=tax,
        freight=freight,
        invoice_total=invoice_total,
        payment_terms=payment_terms,
        ambiguities=ambiguities,
        evidence=evidence,
    )
