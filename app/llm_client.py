"""OpenAI-compatible LLM client (vLLM) + MockLLMClient for local tests."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from app.errors import LLMExtractionError
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


def is_qwen3_dense(model_name: str) -> bool:
    """True for Qwen3 dense checkpoints, not Qwen3.5 / 3.6 GDN."""
    n = (model_name or "").lower()
    if "qwen3.5" in n or "qwen3.6" in n or "gdn" in n:
        return False
    return "qwen3" in n


def is_gpt_oss(model_name: str) -> bool:
    n = (model_name or "").lower().replace("_", "-")
    return "gpt-oss" in n or "gptoss" in n


def build_chat_extra_body(model_name: str, reasoning_effort: str = "low") -> dict[str, Any]:
    """Model-specific Chat Completions extra_body for current OpenAI+vLLM.

    gpt-oss / Harmony: top-level ``reasoning_effort``. vLLM's Harmony path
    ignores ``chat_template_kwargs.reasoning_effort`` (issues #23015, #41902).
    Qwen3 dense: ``chat_template_kwargs.enable_thinking=false``.
    The two are mutually exclusive for a given MODEL_NAME.
    """
    extra: dict[str, Any] = {}
    if is_qwen3_dense(model_name):
        extra["chat_template_kwargs"] = {"enable_thinking": False}
    if is_gpt_oss(model_name):
        extra["reasoning_effort"] = reasoning_effort
    return extra


class LLMClient(ABC):
    @abstractmethod
    def extract_invoice(
        self,
        canonical_text: str,
        *,
        case_id: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ExtractedInvoice:
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
            data = _read_fixture_json(expected_path)
            case_id = data.get("case_id") or case_dir.name
            self._expected_by_case[case_id] = data

    def extract_invoice(
        self,
        canonical_text: str,
        *,
        case_id: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ExtractedInvoice:
        _ = temperature  # sampling is a live-client concern; mock is deterministic
        if case_id and case_id in self._expected_by_case:
            exp = self._expected_by_case[case_id]
            extraction = exp.get("extraction") or exp.get("extracted_invoice")
            if extraction:
                return _validate_extraction(extraction, source=f"registered fixture {case_id}")
        # Try locate fixture by scanning known roots
        if case_id and self.fixture_root:
            candidates = [
                self.fixture_root / split / case_id / "expected.json"
                for split in ("development", "holdout")
            ]
            candidates.extend(
                self.fixture_root / "difficulty" / diff / case_id / "expected.json"
                for diff in ("easy", "medium", "hard")
            )
            # fixture_root may already be a pack directory
            candidates.append(self.fixture_root / case_id / "expected.json")
            candidates.append(self.fixture_root / "expected.json")
            for path in candidates:
                if path.exists():
                    data = _read_fixture_json(path)
                    extraction = data.get("extraction") or data.get("extracted_invoice")
                    if extraction:
                        return _validate_extraction(extraction, source=str(path))
        return parse_synthetic_invoice_text(canonical_text)


class VLLMLLMClient(LLMClient):
    """OpenAI-compatible client targeting pinned vLLM server."""

    def __init__(self, temperature: Optional[float] = None) -> None:
        from openai import OpenAI

        s = get_settings()
        self.settings = s
        self._temperature_override = temperature
        self.client = OpenAI(base_url=s.vllm_base_url, api_key=s.vllm_api_key, timeout=1200.0)
        self.prompt = s.prompt_path.read_text(encoding="utf-8")

    def extract_invoice(
        self,
        canonical_text: str,
        *,
        case_id: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ExtractedInvoice:
        _ = case_id
        s = self.settings
        if temperature is not None:
            temp = temperature
        elif self._temperature_override is not None:
            temp = self._temperature_override
        else:
            temp = s.temperature
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": f"Invoice text:\n\n{canonical_text}"},
        ]
        extra_body = build_chat_extra_body(s.model_name, s.reasoning_effort)
        kwargs: dict[str, Any] = {
            "model": s.model_name,
            "messages": messages,
            "temperature": temp,
            "top_p": s.top_p,
            "seed": s.seed,
            "n": 1,
            "response_format": {
                "type": "json_schema",
                "json_schema": INVOICE_JSON_SCHEMA,
            },
        }
        if extra_body:
            kwargs["extra_body"] = extra_body
        resp = self.client.chat.completions.create(**kwargs)
        # Hash / parse the final channel only. Never use reasoning_content / traces.
        if not resp.choices:
            raise LLMExtractionError(f"Model {s.model_name} returned no choices")
        choice = resp.choices[0]
        finish_reason = choice.finish_reason
        content = choice.message.content
        if not content or not content.strip():
            raise LLMExtractionError(
                f"Model {s.model_name} returned empty final-channel content "
                f"(finish_reason={finish_reason!r})"
            )
        if finish_reason == "length":
            raise LLMExtractionError(
                f"Model {s.model_name} response truncated by max tokens; "
                f"partial content ({len(content)} chars) is not a complete extraction"
            )
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMExtractionError(
                f"Model {s.model_name} returned non-JSON content "
                f"(finish_reason={finish_reason!r}): {exc}; content starts with "
                f"{content[:200]!r}"
            ) from exc
        return _validate_extraction(data, source=f"model {s.model_name}")


def _read_fixture_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LLMExtractionError(f"Unreadable fixture {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMExtractionError(f"Fixture {path} is a {type(data).__name__}, expected an object")
    return data


def _validate_extraction(data: Any, *, source: str) -> ExtractedInvoice:
    try:
        return ExtractedInvoice.model_validate(data)
    except ValidationError as exc:
        raise LLMExtractionError(
            f"Extraction from {source} does not match ExtractedInvoice: {exc}"
        ) from exc


def parse_synthetic_invoice_text(text: str) -> ExtractedInvoice:
    """Deterministic parser for synthetic ReportLab invoices (labeled or messy layouts)."""

    distractor_inv = "INV-000000"
    distractor_po = "PO-9999"
    vendors = [
        "Northwind Office Supply LLC",
        "Cedar Ridge Industrial Parts",
        "Blue Harbor Packaging Co",
        "Summit Ridge Labware Inc",
        "Pinecrest Facilities Goods",
    ]
    sku_desc = {
        "SKU-1001": "Copy Paper Case",
        "SKU-1002": "Toner Cartridge Black",
        "SKU-1003": "Safety Gloves Box",
        "SKU-1004": "Packing Tape Roll",
        "SKU-1005": "Widget Assembly A",
        "SKU-1006": "Widget Assembly B",
        "SKU-1007": "Label Stock Pack",
        "SKU-1008": "Cleaning Solvent Gal",
    }

    def grab(pattern: str, default: Optional[str] = None) -> Optional[str]:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else default

    def normalize_money(raw: str) -> str:
        cleaned = re.sub(r"[$,]|USD\s*", "", raw, flags=re.IGNORECASE).strip()
        return format(Decimal(cleaned).quantize(Decimal("0.01")), "f")

    vendor_name = None
    for name in vendors:
        if name in text:
            vendor_name = name
            break
    if vendor_name is None:
        vendor_name = grab(
            r"(?:Sold by|Issuer|Bill From|From|Remitter|Vendor):\s*(.+)"
        )

    vendor_id = grab(r"(?:Supplier #|Acct|Vendor code|Internal vendor|ID|Vendor ID:)\s*(V\d+)")
    inv_candidates = [m.group(0) for m in re.finditer(r"INV-\d+", text) if m.group(0) != distractor_inv]
    invoice_number = inv_candidates[0] if inv_candidates else grab(
        r"(?:Bill No\.|Document|Inv #|Invoice|Ref|Invoice Number:)\s*(INV-\S+)"
    )
    po_candidates = [
        m.group(0)
        for m in re.finditer(r"PO-(?:MISSING-)?\d+", text)
        if m.group(0) != distractor_po
    ]
    po_number = po_candidates[0] if po_candidates else grab(
        r"(?:Customer #|Our order|PO Ref|Release|This release|PO Number:)\s*(PO-\S+)"
    )

    date_iso = grab(r"Invoice Date:\s*(\d{4}-\d{2}-\d{2})")
    if date_iso is None:
        m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if m:
            date_iso = m.group(0)
        else:
            m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
            if m:
                date_iso = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
            else:
                months = {
                    "january": "01", "february": "02", "march": "03", "april": "04",
                    "may": "05", "june": "06", "july": "07", "august": "08",
                    "september": "09", "october": "10", "november": "11", "december": "12",
                    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "jun": "06",
                    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
                }
                m = re.search(
                    r"\b([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\b|\b(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b",
                    text,
                )
                if m:
                    if m.group(1):
                        date_iso = f"{m.group(3)}-{months[m.group(1).lower()]}-{int(m.group(2)):02d}"
                    else:
                        date_iso = f"{m.group(6)}-{months[m.group(5).lower()]}-{int(m.group(4)):02d}"

    payment_terms = "Net 30" if re.search(r"Net\s*30|NET30|Due in 30", text, re.I) else grab(
        r"Payment Terms:\s*(.+)"
    )
    currency = "USD" if ("USD" in text or "$" in text or grab(r"Currency:\s*(\S+)")) else grab(
        r"Currency:\s*(\S+)", "USD"
    )

    line_items: list[InvoiceLineItem] = []
    # Legacy machine rows
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
    if not line_items:
        money_tok = r"(?:USD\s+)?\$?[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})"
        qty_tok = r"([0-9]+(?:\.[0-9]+)?(?:\s+ea)?)"
        n = 0
        for raw_line in text.splitlines():
            sku_m = re.search(r"(SKU-\d+)", raw_line)
            if not sku_m:
                continue
            sku = sku_m.group(1)
            desc = sku_desc.get(sku)
            if desc is None or desc not in raw_line:
                continue
            amounts = [normalize_money(x) for x in re.findall(money_tok, raw_line)]
            qty = None
            qm = re.search(rf"{qty_tok}", raw_line.replace(sku, " "))
            if qm:
                qty = qm.group(1).replace(" ea", "").strip()
                if "." in qty:
                    d = Decimal(qty)
                    qty = str(int(d)) if d == d.to_integral() else format(d, "f")
            if qty is None or len(amounts) < 2:
                continue
            n += 1
            unit_price, line_total = amounts[0], amounts[-1]
            if Decimal(line_total) < Decimal(unit_price) and len(amounts) >= 2:
                unit_price, line_total = amounts[-1], amounts[0]
            line_items.append(
                InvoiceLineItem(
                    line_number=n,
                    sku=sku,
                    description=desc,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                    evidence=EvidenceSpan(quote=raw_line.strip(), page=1),
                )
            )

    total_m = re.search(
        r"(?:Amount due|Invoice total|Balance due|Please pay|Total due|Invoice Total:)\s+(USD\s+)?\$?([0-9,]+\.[0-9]{2})",
        text,
        flags=re.IGNORECASE,
    )
    invoice_total = normalize_money(total_m.group(2)) if total_m else grab(r"Invoice Total:\s*([0-9.]+)")
    sub_m = re.search(
        r"(?:Merchandise|Goods|Net merchandise|Subtotal|Lines):\s*(USD\s+)?\$?([0-9,]+\.[0-9]{2})",
        text,
        flags=re.IGNORECASE,
    )
    subtotal = normalize_money(sub_m.group(2)) if sub_m else grab(r"Subtotal:\s*([0-9.]+)")
    tax_m = re.search(r"\bTax\s+(USD\s+)?\$?([0-9,]+\.[0-9]{2})", text, flags=re.IGNORECASE)
    tax = normalize_money(tax_m.group(2)) if tax_m else ("0.00" if re.search(r"tax exempt", text, re.I) else grab(r"Tax:\s*([0-9.]+)"))
    freight_m = re.search(r"\bFreight\s+(USD\s+)?\$?([0-9,]+\.[0-9]{2})", text, flags=re.IGNORECASE)
    freight = (
        normalize_money(freight_m.group(2))
        if freight_m
        else ("0.00" if re.search(r"freight prepaid", text, re.I) else grab(r"Freight:\s*([0-9.]+)"))
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
        elif field == "invoice_total" and total_m:
            evidence[field] = EvidenceSpan(quote=total_m.group(0), page=1)

    ambiguities = []
    if "AMBIGUOUS:" in text or "Letterhead: Other Corp" in text:
        ambiguities.append(
            {"field": "vendor_name", "reason": "Multiple vendor headers detected", "candidates": []}
        )

    return ExtractedInvoice(
        vendor_name=vendor_name,
        vendor_id=vendor_id,
        invoice_number=invoice_number,
        invoice_date=date_iso,
        po_number=po_number,
        currency=currency or "USD",
        line_items=line_items,
        subtotal=subtotal,
        tax=tax,
        freight=freight,
        invoice_total=invoice_total,
        payment_terms=payment_terms,
        ambiguities=ambiguities,
        evidence=evidence,
    )
