"""Invoice field and arithmetic validation (Decimal math)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

from app.schemas import (
    ControlCheck,
    ExtractedInvoice,
    PolicyConfig,
    WorkflowDecision,
)

REQUIRED_FIELDS = [
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "po_number",
    "currency",
    "subtotal",
    "tax",
    "freight",
    "invoice_total",
]


def to_decimal(value: str | Decimal) -> Decimal:
    """Parse a money/quantity string. Rejects NaN and Infinity.

    Extracted values are model output derived from an untrusted document, so a
    non-finite Decimal must never reach a comparison (it raises mid-match) or a
    journal amount.
    """
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    if not d.is_finite():
        raise InvalidOperation(f"non-finite decimal value: {value!r}")
    return d


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_decimal_str(value: str | Decimal, places: str = "0.01") -> str:
    d = to_decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return format(d, "f")


def _evidence_ok(quote: str, canonical_text: str) -> bool:
    return quote in canonical_text


def validate_invoice(
    invoice: ExtractedInvoice,
    canonical_text: str,
    policy: PolicyConfig,
) -> tuple[list[str], list[ControlCheck], ExtractedInvoice | None]:
    """
    Validate required fields, evidence quotes, and invoice arithmetic.
    Returns (exception_codes, control_checks, normalized_invoice_or_None).
    """
    exceptions: list[str] = []
    checks: list[ControlCheck] = []

    # Required fields
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        val = getattr(invoice, field, None)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(field)
    if not invoice.line_items:
        missing.append("line_items")

    if missing:
        exceptions.append("MISSING_REQUIRED_FIELD")
        if "invoice_number" in missing or invoice.invoice_number in (None, ""):
            if "MISSING_INVOICE_NUMBER" not in exceptions:
                exceptions.append("MISSING_INVOICE_NUMBER")
        checks.append(
            ControlCheck(
                code="REQUIRED_FIELDS",
                passed=False,
                detail=f"Missing: {', '.join(sorted(missing))}",
            )
        )
    else:
        checks.append(ControlCheck(code="REQUIRED_FIELDS", passed=True, detail="ok"))

    # Ambiguities
    if invoice.ambiguities:
        exceptions.append("AMBIGUOUS_FIELD")
        checks.append(
            ControlCheck(
                code="AMBIGUOUS_FIELD",
                passed=False,
                detail="; ".join(f"{a.field}: {a.reason}" for a in invoice.ambiguities),
            )
        )
    else:
        checks.append(ControlCheck(code="AMBIGUOUS_FIELD", passed=True, detail="ok"))

    # Evidence quotes must appear exactly in canonical source
    evidence_fail = False
    for key, span in sorted(invoice.evidence.items()):
        if not _evidence_ok(span.quote, canonical_text):
            evidence_fail = True
            checks.append(
                ControlCheck(
                    code="EVIDENCE",
                    passed=False,
                    detail=f"Field {key} quote not found in canonical text",
                )
            )
    for li in invoice.line_items:
        if li.evidence is not None and not _evidence_ok(li.evidence.quote, canonical_text):
            evidence_fail = True
            checks.append(
                ControlCheck(
                    code="EVIDENCE",
                    passed=False,
                    detail=f"Line {li.line_number} evidence quote not found",
                )
            )
    if evidence_fail:
        exceptions.append("EVIDENCE_VALIDATION_FAILED")
    else:
        checks.append(ControlCheck(code="EVIDENCE", passed=True, detail="ok"))

    # Arithmetic — only if we have parseable decimals
    math_ok = True
    try:
        if invoice.line_items and invoice.subtotal is not None and invoice.invoice_total is not None:
            line_sum = Decimal("0")
            for li in invoice.line_items:
                qty = to_decimal(li.quantity)
                price = to_decimal(li.unit_price)
                expected_line = money(qty * price)
                actual_line = money(to_decimal(li.line_total))
                if abs(expected_line - actual_line) > Decimal("0.00"):
                    # allow exact match only for line; policy uses invoice_total_tolerance later
                    if abs(expected_line - actual_line) > to_decimal(policy.invoice_total_tolerance):
                        math_ok = False
                line_sum += actual_line

            subtotal = money(to_decimal(invoice.subtotal))
            tax = money(to_decimal(invoice.tax or "0"))
            freight = money(to_decimal(invoice.freight or "0"))
            total = money(to_decimal(invoice.invoice_total))
            tol = to_decimal(policy.invoice_total_tolerance)

            if abs(line_sum - subtotal) > tol:
                math_ok = False
            expected_total = money(subtotal + tax + freight)
            if abs(expected_total - total) > tol:
                math_ok = False
        elif invoice.line_items:
            # Incomplete totals — treat as math/required already covered
            pass
    except (InvalidOperation, TypeError, ValueError):
        math_ok = False

    if not math_ok:
        exceptions.append("INVOICE_MATH_ERROR")
        checks.append(ControlCheck(code="INVOICE_MATH", passed=False, detail="Arithmetic mismatch"))
    else:
        checks.append(ControlCheck(code="INVOICE_MATH", passed=True, detail="ok"))

    # Normalize decimal strings if parseable
    normalized: ExtractedInvoice | None = None
    try:
        if not missing or (invoice.line_items and invoice.invoice_total):
            norm_lines = []
            for li in invoice.line_items:
                norm_lines.append(
                    li.model_copy(
                        update={
                            "quantity": format(to_decimal(li.quantity), "f"),
                            "unit_price": normalize_decimal_str(li.unit_price),
                            "line_total": normalize_decimal_str(li.line_total),
                        }
                    )
                )
            updates: dict = {"line_items": norm_lines}
            for f in ("subtotal", "tax", "freight", "invoice_total"):
                v = getattr(invoice, f)
                if v is not None and str(v).strip() != "":
                    updates[f] = normalize_decimal_str(v)
            normalized = invoice.model_copy(update=updates)
        else:
            normalized = invoice
    except (InvalidOperation, TypeError, ValueError):
        normalized = invoice

    # Deterministic sort of exception codes
    exceptions = sorted(set(exceptions))
    return exceptions, checks, normalized


def decision_from_exceptions(exceptions: Iterable[str]) -> WorkflowDecision:
    return (
        WorkflowDecision.READY_FOR_DRAFT
        if not list(exceptions)
        else WorkflowDecision.HUMAN_REVIEW
    )
