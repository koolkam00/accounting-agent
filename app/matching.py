"""Three-way match: invoice vs PO vs receipts (pure Python / Decimal)."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.schemas import (
    ControlCheck,
    ExtractedInvoice,
    PolicyConfig,
    PurchaseOrder,
    Receipt,
    Vendor,
    WorkflowDecision,
)
from app.validation import money, to_decimal


def _price_tolerance(po_unit_price: Decimal, policy: PolicyConfig) -> Decimal:
    pct = to_decimal(policy.unit_price_percentage_tolerance)
    minimum = to_decimal(policy.minimum_unit_price_tolerance)
    return max(money(po_unit_price * pct), minimum)


def match_invoice(
    invoice: ExtractedInvoice,
    po: Optional[PurchaseOrder],
    receipts: list[Receipt],
    vendor: Optional[Vendor],
    policy: PolicyConfig,
    is_duplicate: bool,
) -> tuple[WorkflowDecision, list[str], list[ControlCheck]]:
    """
    Perform three-way match checks.
    READY_FOR_DRAFT only if exception list is empty (includes tax==0 when policy requires).
    """
    exceptions: list[str] = []
    checks: list[ControlCheck] = []

    if is_duplicate:
        exceptions.append("DUPLICATE_INVOICE")
        checks.append(ControlCheck(code="DUPLICATE_INVOICE", passed=False, detail="Duplicate invoice number"))
    else:
        checks.append(ControlCheck(code="DUPLICATE_INVOICE", passed=True, detail="ok"))

    if po is None:
        exceptions.append("PO_NOT_FOUND")
        checks.append(ControlCheck(code="PO_NOT_FOUND", passed=False, detail="PO not found or not open"))
        # Still continue for other checks that don't need PO
    else:
        if po.status.upper() != "OPEN":
            exceptions.append("PO_NOT_FOUND")
            checks.append(ControlCheck(code="PO_STATUS", passed=False, detail=f"PO status={po.status}"))
        else:
            checks.append(ControlCheck(code="PO_STATUS", passed=True, detail="OPEN"))

    if vendor is None:
        # If we have PO vendor mismatch path separately; inactive/missing vendor
        if po is not None:
            exceptions.append("VENDOR_MISMATCH")
            checks.append(ControlCheck(code="VENDOR", passed=False, detail="Vendor not found"))
        else:
            checks.append(ControlCheck(code="VENDOR", passed=False, detail="Vendor unknown (no PO)"))
    else:
        if not vendor.active:
            exceptions.append("VENDOR_INACTIVE")
            checks.append(ControlCheck(code="VENDOR_ACTIVE", passed=False, detail="Vendor inactive"))
        else:
            checks.append(ControlCheck(code="VENDOR_ACTIVE", passed=True, detail="ok"))

        if po is not None:
            name_inv = (invoice.vendor_name or "").strip().lower()
            name_po = po.vendor_name.strip().lower()
            id_ok = True
            if invoice.vendor_id and invoice.vendor_id != po.vendor_id:
                id_ok = False
            if vendor.vendor_id != po.vendor_id:
                id_ok = False
            name_ok = name_inv == name_po or name_inv == vendor.vendor_name.strip().lower()
            if not (id_ok and name_ok):
                exceptions.append("VENDOR_MISMATCH")
                checks.append(
                    ControlCheck(
                        code="VENDOR_MATCH",
                        passed=False,
                        detail=f"Invoice vendor '{invoice.vendor_name}' vs PO '{po.vendor_name}'",
                    )
                )
            else:
                checks.append(ControlCheck(code="VENDOR_MATCH", passed=True, detail="ok"))

    if po is not None and invoice.currency:
        if invoice.currency.upper() != po.currency.upper() or invoice.currency.upper() != policy.currency.upper():
            exceptions.append("CURRENCY_MISMATCH")
            checks.append(
                ControlCheck(
                    code="CURRENCY",
                    passed=False,
                    detail=f"Invoice {invoice.currency} / PO {po.currency} / policy {policy.currency}",
                )
            )
        else:
            checks.append(ControlCheck(code="CURRENCY", passed=True, detail="ok"))

    # Tax review
    try:
        tax = money(to_decimal(invoice.tax or "0"))
    except Exception:
        tax = Decimal("0.01")  # force review if unparseable here
    if policy.nonzero_tax_requires_review and tax != Decimal("0.00"):
        exceptions.append("NONZERO_TAX_REVIEW")
        checks.append(ControlCheck(code="TAX", passed=False, detail=f"tax={tax}"))
    else:
        checks.append(ControlCheck(code="TAX", passed=True, detail="ok"))

    # Line-level SKU / price / qty vs PO and receipts
    if po is not None:
        po_by_sku = {ln.sku: ln for ln in po.lines}
        received: dict[str, Decimal] = {}
        for r in receipts:
            for rl in r.lines:
                received[rl.sku] = received.get(rl.sku, Decimal("0")) + to_decimal(rl.quantity_received)

        qty_tol = to_decimal(policy.quantity_tolerance)

        for li in invoice.line_items:
            if li.sku not in po_by_sku:
                exceptions.append("SKU_NOT_FOUND")
                checks.append(
                    ControlCheck(code="SKU", passed=False, detail=f"SKU {li.sku} not on PO")
                )
                continue
            po_line = po_by_sku[li.sku]
            inv_price = money(to_decimal(li.unit_price))
            po_price = money(to_decimal(po_line.unit_price))
            tol = _price_tolerance(po_price, policy)
            if abs(inv_price - po_price) > tol:
                exceptions.append("PRICE_VARIANCE")
                checks.append(
                    ControlCheck(
                        code="PRICE",
                        passed=False,
                        detail=f"{li.sku}: inv={inv_price} po={po_price} tol={tol}",
                    )
                )
            else:
                checks.append(
                    ControlCheck(code="PRICE", passed=True, detail=f"{li.sku}: within tolerance")
                )

            inv_qty = to_decimal(li.quantity)
            po_qty = to_decimal(po_line.quantity)
            if inv_qty > po_qty + qty_tol:
                exceptions.append("QUANTITY_EXCEEDS_PO")
                checks.append(
                    ControlCheck(
                        code="QTY_PO",
                        passed=False,
                        detail=f"{li.sku}: inv={inv_qty} po={po_qty}",
                    )
                )
            else:
                checks.append(ControlCheck(code="QTY_PO", passed=True, detail=f"{li.sku}: ok"))

            recv_qty = received.get(li.sku, Decimal("0"))
            if inv_qty > recv_qty + qty_tol:
                exceptions.append("QUANTITY_EXCEEDS_RECEIPT")
                checks.append(
                    ControlCheck(
                        code="QTY_RCV",
                        passed=False,
                        detail=f"{li.sku}: inv={inv_qty} received={recv_qty}",
                    )
                )
            else:
                checks.append(ControlCheck(code="QTY_RCV", passed=True, detail=f"{li.sku}: ok"))

    exceptions = sorted(set(exceptions))
    decision = (
        WorkflowDecision.READY_FOR_DRAFT
        if not exceptions
        else WorkflowDecision.HUMAN_REVIEW
    )
    return decision, exceptions, checks
