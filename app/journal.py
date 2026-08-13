"""Proposed journal entry generation (deterministic aggregation)."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.schemas import (
    ExtractedInvoice,
    JournalLine,
    ProposedJournal,
    PurchaseOrder,
    WorkflowDecision,
)
from app.validation import money, normalize_decimal_str, to_decimal


def propose_journal(
    invoice: ExtractedInvoice,
    po: PurchaseOrder,
    ap_account: str = "2000",
) -> tuple[ProposedJournal, list[str], WorkflowDecision]:
    """
    When called for READY_FOR_DRAFT candidates:
    Dr expense/GL accounts from PO lines (aggregated by account),
    Cr Accounts Payable.
    """
    # Allocate invoice line totals to PO GL accounts by SKU
    po_by_sku = {ln.sku: ln for ln in po.lines}
    by_account: dict[str, Decimal] = {}

    for li in invoice.line_items:
        gl = po_by_sku[li.sku].gl_account if li.sku in po_by_sku else "5999"
        by_account[gl] = by_account.get(gl, Decimal("0")) + money(to_decimal(li.line_total))

    # Include freight in first GL account if present
    freight = money(to_decimal(invoice.freight or "0"))
    if freight and by_account:
        first = sorted(by_account.keys())[0]
        by_account[first] = money(by_account[first] + freight)

    lines: list[JournalLine] = []
    debit_total = Decimal("0")
    for account in sorted(by_account.keys()):
        amt = money(by_account[account])
        if amt == 0:
            continue
        lines.append(
            JournalLine(
                account=account,
                debit=normalize_decimal_str(amt),
                credit="0.00",
                memo=f"Invoice {invoice.invoice_number} / PO {po.po_id}",
            )
        )
        debit_total += amt

    credit_total = money(to_decimal(invoice.invoice_total or "0"))
    # Prefer balancing to invoice total (subtotal+tax+freight); tax should be 0 for draft path
    lines.append(
        JournalLine(
            account=ap_account,
            debit="0.00",
            credit=normalize_decimal_str(credit_total),
            memo=f"AP {invoice.vendor_name} {invoice.invoice_number}",
        )
    )

    # Sort: debits first by account, then credits by account
    debit_lines = sorted([ln for ln in lines if to_decimal(ln.debit) > 0], key=lambda x: x.account)
    credit_lines = sorted([ln for ln in lines if to_decimal(ln.credit) > 0], key=lambda x: x.account)
    ordered = debit_lines + credit_lines

    sum_debits = money(sum((to_decimal(ln.debit) for ln in ordered), Decimal("0")))
    sum_credits = money(sum((to_decimal(ln.credit) for ln in ordered), Decimal("0")))
    balanced = sum_debits == sum_credits

    journal = ProposedJournal(
        lines=ordered,
        balanced=balanced,
        currency=invoice.currency or po.currency,
    )

    if not balanced:
        return journal, ["UNBALANCED_JOURNAL"], WorkflowDecision.HUMAN_REVIEW
    return journal, [], WorkflowDecision.READY_FOR_DRAFT
