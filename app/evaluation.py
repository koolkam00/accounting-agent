"""Shared scoring helpers for the accuracy and determinism evaluations."""

from __future__ import annotations

import os
from typing import Any, Optional

FIELD_KEYS = (
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
)

LINE_ITEM_KEYS = ("line_number", "sku", "description", "quantity", "unit_price", "line_total")


def field_exact_match(got: Optional[dict[str, Any]], gold: Optional[dict[str, Any]]) -> bool:
    """True when every header field and line item matches the gold extraction."""
    if not got or not gold:
        return False
    for key in FIELD_KEYS:
        if (got.get(key) or None) != (gold.get(key) or None):
            return False
    got_lines = got.get("line_items") or []
    gold_lines = gold.get("line_items") or []
    if len(got_lines) != len(gold_lines):
        return False
    for got_line, gold_line in zip(got_lines, gold_lines):
        for key in LINE_ITEM_KEYS:
            if got_line.get(key) != gold_line.get(key):
                return False
    return True


def invariance_label(negative_control: bool) -> str:
    """Report label for the server's batch-invariance setting."""
    if negative_control:
        return "off"
    return "on" if os.getenv("VLLM_BATCH_INVARIANT", "1") == "1" else "off"
