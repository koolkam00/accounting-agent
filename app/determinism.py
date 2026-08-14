"""Determinism analysis helpers: field disagreement, match-field equality, classification.

These helpers operate purely on ExtractedInvoice JSON payloads and per-repeat
metadata (hashes, decisions). They do not call the LLM or ERP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


# -------- Flatteners

FlatMap = Dict[str, Any]


def _sorted_or_none(seq: Iterable[Any] | None) -> list[Any] | None:
    if not seq:
        return None
    return sorted(seq)


def flatten_extract_for_disagreement(extract: Dict[str, Any]) -> FlatMap:
    """Return a flat mapping of human fields for pairwise disagreement metrics.

    Includes header-level fields and aggregate equality for line-items and evidence.
    """
    inv = extract or {}
    lines = inv.get("line_items") or []
    # Build maps by SKU for stable comparison (matcher aligns by SKU)
    by_sku: Dict[str, Dict[str, Any]] = {}
    for li in lines:
        sku = li.get("sku")
        if not sku:
            continue
        by_sku[sku] = {
            "quantity": li.get("quantity"),
            "unit_price": li.get("unit_price"),
            "line_total": li.get("line_total"),
            "description": li.get("description"),
        }
    line_skus = _sorted_or_none(by_sku.keys())
    qty_map = {k: v.get("quantity") for k, v in sorted(by_sku.items())}
    price_map = {k: v.get("unit_price") for k, v in sorted(by_sku.items())}
    total_map = {k: v.get("line_total") for k, v in sorted(by_sku.items())}
    desc_map = {k: v.get("description") for k, v in sorted(by_sku.items())}

    ev = inv.get("evidence") or {}
    # stable list of (field, page, quote) for coarse disagreement
    evidence_quotes = [
        (field, str(span.get("page")), str(span.get("quote")))
        for field, span in sorted(ev.items())
    ]

    return {
        # Header-level
        "vendor_name": inv.get("vendor_name"),
        "vendor_id": inv.get("vendor_id"),
        "invoice_number": inv.get("invoice_number"),
        "invoice_date": inv.get("invoice_date"),
        "po_number": inv.get("po_number"),
        "currency": inv.get("currency"),
        "subtotal": inv.get("subtotal"),
        "tax": inv.get("tax"),
        "freight": inv.get("freight"),
        "invoice_total": inv.get("invoice_total"),
        "payment_terms": inv.get("payment_terms"),
        # Lines (aggregated equality checks)
        "line_skus": line_skus,
        "line_qty_map": qty_map,
        "line_unit_price_map": price_map,
        "line_total_map": total_map,
        "line_description_map": desc_map,
        # Evidence
        "evidence_quotes": evidence_quotes,
    }


def flatten_extract_for_match_fields(extract: Dict[str, Any]) -> FlatMap:
    """Return only the fields the matcher consults from the extraction.

    Reflects app/matching.py and config/policy.yaml usage.
    - Vendor identity by id/name
    - PO number
    - Currency
    - Invoice number (for duplicate checks)
    - Line items by SKU: quantity, unit_price, line_total
    - Totals relevant to policy checks: tax, invoice_total
    """
    inv = extract or {}
    lines = inv.get("line_items") or []
    by_sku: Dict[str, Dict[str, Any]] = {}
    for li in lines:
        sku = li.get("sku")
        if not sku:
            continue
        by_sku[sku] = {
            "quantity": li.get("quantity"),
            "unit_price": li.get("unit_price"),
            "line_total": li.get("line_total"),
        }
    qty_map = {k: v.get("quantity") for k, v in sorted(by_sku.items())}
    price_map = {k: v.get("unit_price") for k, v in sorted(by_sku.items())}
    total_map = {k: v.get("line_total") for k, v in sorted(by_sku.items())}
    return {
        "vendor_name": inv.get("vendor_name"),
        "vendor_id": inv.get("vendor_id"),
        "invoice_number": inv.get("invoice_number"),
        "po_number": inv.get("po_number"),
        "currency": inv.get("currency"),
        "tax": inv.get("tax"),
        "invoice_total": inv.get("invoice_total"),
        "line_qty_map": qty_map,
        "line_unit_price_map": price_map,
        "line_total_map": total_map,
    }


# -------- Pairwise metrics


def _pairwise_iter(items: List[Any]) -> Iterable[Tuple[int, int]]:
    n = len(items)
    for i in range(n):
        for j in range(i + 1, n):
            yield i, j


def compute_pairwise_field_disagreements(extracts: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute field-level pairwise disagreement rates for a set of extractions."""
    if not extracts or len(extracts) == 1:
        # No pairs -> zero disagreement
        return {k: 0.0 for k in flatten_extract_for_disagreement(extracts[0] if extracts else {}).keys()}
    flats = [flatten_extract_for_disagreement(e) for e in extracts]
    keys = sorted(flats[0].keys())
    disagree_count: Dict[str, int] = {k: 0 for k in keys}
    total_pairs = 0
    for i, j in _pairwise_iter(flats):
        total_pairs += 1
        a = flats[i]
        b = flats[j]
        for k in keys:
            if a.get(k) != b.get(k):
                disagree_count[k] += 1
    if total_pairs == 0:
        return {k: 0.0 for k in keys}
    return {k: disagree_count[k] / total_pairs for k in keys}


def match_fields_all_equal(extracts: List[Dict[str, Any]]) -> bool:
    """True iff all pairwise comparisons match on the fields used by matcher."""
    if not extracts:
        return True
    flats = [flatten_extract_for_match_fields(e) for e in extracts]
    for i, j in _pairwise_iter(flats):
        if flats[i] != flats[j]:
            return False
    return True


@dataclass
class CaseClassification:
    case_id: str
    unique_hashes: int
    decision_equal: bool
    match_fields_equal: bool
    classification: str  # "stable" | "cosmetic" | "material" | "unknown"


def classify_case_records(case_id: str, recs: List[Dict[str, Any]]) -> CaseClassification:
    """Classify one case across repeats into stable/cosmetic/material."""
    # Consider only successful repetitions with an extraction and decision
    good = [r for r in recs if r.get("ok") and r.get("hash") and r.get("extraction") is not None]
    if not good:
        return CaseClassification(
            case_id=case_id,
            unique_hashes=0,
            decision_equal=False,
            match_fields_equal=False,
            classification="unknown",
        )
    hashes = sorted({r["hash"] for r in good})
    decs = sorted({r.get("decision") for r in good})
    decision_equal = len(decs) <= 1
    extracts = [r["extraction"] for r in good]
    m_equal = match_fields_all_equal(extracts)
    if len(hashes) <= 1:
        classification = "stable"
    else:
        classification = "cosmetic" if (decision_equal and m_equal) else "material"
    return CaseClassification(
        case_id=case_id,
        unique_hashes=len(hashes),
        decision_equal=decision_equal,
        match_fields_equal=m_equal,
        classification=classification,
    )


def aggregate_field_disagreements(by_case_extracts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
    """Aggregate field-level disagreement rates across cases (weighted by pairs)."""
    total_disagree: Dict[str, int] = {}
    total_pairs: Dict[str, int] = {}
    for extracts in by_case_extracts.values():
        flats = [flatten_extract_for_disagreement(e) for e in extracts] if extracts else []
        if len(flats) <= 1:
            # Zero pairs for this case; just ensure keys exist
            if flats:
                for k in flats[0].keys():
                    total_disagree.setdefault(k, 0)
                    total_pairs.setdefault(k, 0)
            continue
        keys = sorted(flats[0].keys())
        for k in keys:
            total_disagree.setdefault(k, 0)
            total_pairs.setdefault(k, 0)
        for i, j in _pairwise_iter(flats):
            a = flats[i]
            b = flats[j]
            for k in keys:
                total_pairs[k] += 1
                if a.get(k) != b.get(k):
                    total_disagree[k] += 1
    # Compute rates
    rates: Dict[str, float] = {}
    for k in sorted(total_pairs.keys()):
        denom = total_pairs[k]
        rates[k] = (total_disagree[k] / denom) if denom else 0.0
    return rates

