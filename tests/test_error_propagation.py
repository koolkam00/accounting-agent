"""Failures must surface: as raised domain errors or as explicit exception codes."""

import json

import pytest
from sqlalchemy import text

from app.adapters.local_erp import LocalERPAdapter
from app.audit import AuditLog
from app.database import ProcessedDocumentRow, init_db
from app.errors import (
    AuditPersistenceError,
    ERPPersistenceError,
    LLMExtractionError,
    PdfExtractionError,
    PolicyConfigError,
)
from app.llm_client import MockLLMClient
from app.matching import match_invoice
from app.pdf_text import extract_pdf_text
from app.pipeline import load_policy
from app.schemas import (
    ExtractedInvoice,
    InvoiceLineItem,
    PolicyConfig,
    PurchaseOrder,
    POLine,
    Receipt,
    ReceiptLine,
    WorkflowDecision,
    WorkflowResult,
)
from app.validation import validate_invoice
from tests.test_matching import _fixture


POLICY = PolicyConfig()


def test_corrupt_pdf_raises():
    with pytest.raises(PdfExtractionError):
        extract_pdf_text(b"not a pdf at all")


def test_unreadable_fixture_raises(tmp_path):
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    (case_dir / "expected.json").write_text("{not json", encoding="utf-8")
    llm = MockLLMClient(fixture_root=tmp_path)
    with pytest.raises(LLMExtractionError):
        llm.extract_invoice("Invoice Total: 1.00", case_id="case_001")


def test_off_schema_extraction_raises(tmp_path):
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    (case_dir / "expected.json").write_text(
        json.dumps({"extraction": {"line_items": "not-a-list"}}), encoding="utf-8"
    )
    llm = MockLLMClient(fixture_root=tmp_path)
    with pytest.raises(LLMExtractionError):
        llm.extract_invoice("Invoice Total: 1.00", case_id="case_001")


def test_bad_policy_file_raises(tmp_path):
    bad = tmp_path / "policy.yaml"
    bad.write_text("invoice_total_tolerance: [1, 2]\n", encoding="utf-8")
    with pytest.raises(PolicyConfigError):
        load_policy(bad)

    missing = tmp_path / "nope.yaml"
    with pytest.raises(PolicyConfigError):
        load_policy(missing)


def test_unparseable_tax_is_reported_not_fabricated():
    inv, po, receipts, vendor = _fixture()
    inv = inv.model_copy(update={"tax": "eight dollars"})
    decision, exc, checks = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert "TAX_UNPARSEABLE" in exc
    assert "NONZERO_TAX_REVIEW" not in exc
    assert any(c.code == "TAX" and not c.passed for c in checks)


def test_unparseable_invoice_line_is_reported():
    inv, po, receipts, vendor = _fixture()
    bad_line = inv.line_items[0].model_copy(update={"quantity": "two"})
    inv = inv.model_copy(update={"line_items": [bad_line]})
    decision, exc, _ = match_invoice(inv, po, receipts, vendor, POLICY, False)
    assert decision == WorkflowDecision.HUMAN_REVIEW
    assert "LINE_ITEM_PARSE_ERROR" in exc


def test_corrupt_erp_receipt_data_raises():
    inv, po, receipts, vendor = _fixture()
    receipts = [
        Receipt(
            receipt_id="R1",
            po_id="PO1",
            lines=[ReceiptLine(sku="S1", quantity_received="lots")],
        )
    ]
    with pytest.raises(ERPPersistenceError):
        match_invoice(inv, po, receipts, vendor, POLICY, False)


def test_corrupt_erp_po_data_raises():
    inv, po, receipts, vendor = _fixture()
    po = PurchaseOrder(
        po_id="PO1",
        vendor_id="V1",
        vendor_name="Acme",
        currency="USD",
        status="OPEN",
        lines=[
            POLine(
                line_number=1,
                sku="S1",
                description="X",
                quantity="2",
                unit_price="ten dollars",
                gl_account="5000",
            )
        ],
    )
    with pytest.raises(ERPPersistenceError):
        match_invoice(inv, po, receipts, vendor, POLICY, False)


def _invoice_missing_totals() -> ExtractedInvoice:
    return ExtractedInvoice(
        vendor_name="Acme",
        vendor_id="V1",
        invoice_number="I1",
        invoice_date="2026-01-01",
        po_number="PO1",
        currency="USD",
        line_items=[
            InvoiceLineItem(
                line_number=1,
                sku="S1",
                description="X",
                quantity="2",
                unit_price="10.00",
                line_total="20.00",
            )
        ],
        subtotal=None,
        tax="0.00",
        freight="0.00",
        invoice_total="20.00",
    )


def test_unverifiable_arithmetic_is_not_reported_as_passing():
    _, checks, _ = validate_invoice(_invoice_missing_totals(), "", POLICY)
    math_checks = [c for c in checks if c.code == "INVOICE_MATH"]
    assert math_checks and not math_checks[0].passed
    assert "Not verified" in (math_checks[0].detail or "")


def test_normalization_failure_is_reported():
    inv = _invoice_missing_totals().model_copy(update={"subtotal": "20.00", "tax": "n/a"})
    exc, checks, normalized = validate_invoice(inv, "", POLICY)
    assert "DECIMAL_NORMALIZATION_FAILED" in exc
    assert normalized is not None
    assert any(c.code == "DECIMAL_NORMALIZATION" and not c.passed for c in checks)


def _session_factory(tmp_path):
    return init_db(f"sqlite:///{tmp_path / 'erp.db'}")


def test_corrupt_cached_result_raises(tmp_path):
    sf = _session_factory(tmp_path)
    erp = LocalERPAdapter(sf)
    with sf() as session:
        session.add(
            ProcessedDocumentRow(
                idempotency_key="k1",
                vendor_id="V1",
                invoice_number="I1",
                result_json="{}",
            )
        )
        session.commit()
    with pytest.raises(ERPPersistenceError):
        erp.get_previous_result("k1")


def test_attach_source_document_rejects_malformed_calls(tmp_path):
    erp = LocalERPAdapter(_session_factory(tmp_path))
    with pytest.raises(ERPPersistenceError):
        erp.attach_source_document("", b"pdf", "a.pdf")
    with pytest.raises(ERPPersistenceError):
        erp.attach_source_document("D1", b"", "a.pdf")
    with pytest.raises(ERPPersistenceError):
        erp.attach_source_document("D1", b"pdf", "")


def test_audit_persistence_failure_propagates(tmp_path):
    sf = _session_factory(tmp_path)
    with sf() as session:
        session.execute(text("DROP TABLE audit_events"))
        session.commit()
    audit = AuditLog(sf)
    with pytest.raises(AuditPersistenceError):
        audit.emit("STATE", {"state": "INGEST"}, case_id="case_001")


def test_workflow_result_roundtrip_is_still_readable(tmp_path):
    sf = _session_factory(tmp_path)
    erp = LocalERPAdapter(sf)
    result = WorkflowResult(
        case_id="case_001",
        decision=WorkflowDecision.HUMAN_REVIEW,
        exception_codes=["PO_NOT_FOUND"],
    )
    erp.record_processed("k2", "V1", "I1", result)
    cached = erp.get_previous_result("k2")
    assert cached is not None
    assert cached.exception_codes == ["PO_NOT_FOUND"]
