"""Bookkeeper-facing descriptions of the engine's matching checks."""

from decimal import Decimal
import re


CHECK_LABELS = {
    "REQUIRED_FIELDS": ("Required invoice information is present", "Required invoice information is missing"),
    "AMBIGUOUS_FIELD": ("Invoice information is unambiguous", "Invoice information needs clarification"),
    "EVIDENCE": ("Extracted information is supported by the invoice", "Extracted information could not be verified against the invoice"),
    "INVOICE_MATH": ("Invoice amounts add up", "Invoice amounts do not add up"),
    "DUPLICATE_INVOICE": ("Invoice is not a duplicate", "This invoice number has already been used"),
    "PO_NOT_FOUND": ("Purchase order found", "Purchase order could not be found"),
    "PO_STATUS": ("Purchase order is open", "Purchase order is not open"),
    "VENDOR": ("Vendor found", "Vendor could not be identified"),
    "VENDOR_ACTIVE": ("Vendor is active", "Vendor is inactive"),
    "VENDOR_MATCH": ("Invoice vendor matches the purchase order", "Invoice vendor does not match the purchase order"),
    "CURRENCY": ("Invoice and purchase order use the required currency", "Invoice or purchase order currency does not match the required currency"),
    "TAX": ("Tax meets the review policy", "Nonzero invoice tax requires review"),
    "SKU": ("Item is on the purchase order", "Invoice item is not on the purchase order"),
    "PRICE": ("Unit price is within tolerance", "Invoice unit price is outside the purchase order tolerance"),
    "QTY_PO": ("Quantity within purchase order", "Invoiced quantity exceeds the purchase order"),
    "QTY_RCV": ("Quantity within received amount", "Invoiced quantity exceeds the amount received"),
}


def present_checks(report, context=None):
    invoice = report.get("extracted_invoice") or {}
    po = context.purchase_order if context else None
    po_lines = {line.sku: line for line in po.lines} if po else {}
    invoice_lines = {line["sku"]: line for line in invoice.get("line_items", [])}
    received = {}
    for receipt in context.receipts if context else []:
        for line in receipt.lines:
            received[line.sku] = received.get(line.sku, Decimal(0)) + Decimal(line.quantity_received)
    checks = []
    for check in report.get("control_checks", []):
        code, passed = check["code"], check["passed"]
        labels = CHECK_LABELS.get(code, ("Additional check passed", "Additional check needs review"))
        label = labels[0 if passed else 1]
        detail = check.get("detail", "")
        if code in {"PRICE", "QTY_PO", "QTY_RCV"}:
            sku = detail.split(": ", 1)[0]
            line, ordered = invoice_lines.get(sku), po_lines.get(sku)
            if line and ordered:
                if code == "PRICE":
                    detail = f"{sku}: invoiced unit price {line['unit_price']}, purchase order unit price {ordered.unit_price} {po.currency}"
                    if " tol=" in check.get("detail", ""):
                        detail += f"; allowed difference {check['detail'].rsplit(' tol=', 1)[1]} {po.currency}"
                elif code == "QTY_PO":
                    detail = f"{sku}: invoiced {line['quantity']}, ordered {ordered.quantity}"
                else:
                    detail = f"{sku}: invoiced {line['quantity']}, received {received.get(sku, Decimal(0))}"
        elif code == "PO_STATUS" and po:
            detail = f"Purchase order {po.po_id} is {po.status.lower()}."
        elif code == "VENDOR_MATCH" and po:
            detail = f"Invoice vendor: {invoice.get('vendor_name') or 'not identified'}; purchase order vendor: {po.vendor_name}."
        elif code == "CURRENCY" and po:
            detail = f"Invoice currency: {invoice.get('currency') or 'not identified'}; purchase order currency: {po.currency}; required currency: USD."
        elif code == "TAX":
            detail = f"Invoice tax: {invoice.get('tax') or 'not identified'} {invoice.get('currency') or ''}."
        if not context:
            detail = re.sub(r"\binv=", "invoiced ", detail)
            detail = re.sub(r"\bpo=", "purchase order ", detail)
            detail = re.sub(r"\breceived=", "received ", detail)
            detail = re.sub(r"\btol=", "allowed difference ", detail)
            detail = detail.replace("PO status=", "Purchase order status: ")
            if detail.endswith(": ok"):
                detail = detail[:-2] + label.lower() + "."
        if detail in {"", "ok", "OPEN"}:
            detail = label + "."
        elif code not in CHECK_LABELS:
            detail = f"{code}: {detail}"
        checks.append({"label": label, "detail": detail, "passed": passed})
    return checks
