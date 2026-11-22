"""Bookkeeper-facing descriptions of the engine's matching checks."""

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
    checks = []
    for check in report.get("control_checks", []):
        code, passed = check["code"], check["passed"]
        labels = CHECK_LABELS.get(code, ("Additional check passed", "Additional check needs review"))
        label = labels[0 if passed else 1]
        detail = check.get("detail", "")
        if code in {"PRICE", "QTY_PO", "QTY_RCV"}:
            words = {
                "inv": "invoiced unit price" if code == "PRICE" else "invoiced",
                "po": "purchase order unit price" if code == "PRICE" else "ordered",
                "received": "received", "tol": "allowed difference",
            }
            detail = re.sub(r"\b(inv|po|received|tol)=", lambda match: words[match[1]] + " ", detail)
            detail = re.sub(r"(?<=\d) (?=(?:ordered|received|purchase order unit price|allowed difference) )", ", ", detail)
            if detail.endswith(": ok"):
                detail = detail[:-4] + ": within tolerance"
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
                detail = detail[:-4] + "."
        if detail in {"", "ok", "OPEN"} or detail == label.lower() + ".":
            detail = ""
        elif code not in CHECK_LABELS:
            detail = f"{code}: {detail}"
        checks.append({"label": label, "detail": detail, "passed": passed})
    return checks
