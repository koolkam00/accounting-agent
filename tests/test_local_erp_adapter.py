from __future__ import annotations

from sqlalchemy import select

from app.adapters.local_erp import LocalERPAdapter
from app.database import (
    DuplicateSeedRow,
    JournalDraftRow,
    POLineRow,
    ProcessedDocumentRow,
    PurchaseOrderRow,
    ReceiptLineRow,
    ReceiptRow,
    VendorRow,
    init_db,
)
from app.schemas import (
    ControlCheck,
    PipelineState,
    ProposedJournal,
    WorkflowDecision,
    WorkflowResult,
)


def _db(tmp_path):
    return init_db(f"sqlite:///{tmp_path / 'erp.db'}")


def _result(key="abc123"):
    return WorkflowResult(
        case_id="case-1",
        decision=WorkflowDecision.READY_FOR_DRAFT,
        exception_codes=[],
        control_checks=[ControlCheck(code="OK", passed=True)],
        idempotency_key=key,
        pipeline_state=PipelineState.CREATE_DRAFT_OR_REVIEW,
        proposed_journal=ProposedJournal(lines=[], balanced=True),
    )


def test_vendor_and_purchase_order_misses_and_hits(tmp_path):
    sf = _db(tmp_path)
    with sf() as session:
        session.add_all([
            VendorRow(vendor_id="V1", vendor_name="Acme", active=True, ap_account="2000"),
            VendorRow(vendor_id="V2", vendor_name="Acme", active=False, ap_account=None),
        ])
        session.commit()
        session.add_all(
            [
                PurchaseOrderRow(
                    po_id="PO-1", vendor_id="V1", vendor_name="Acme", currency="USD", status="OPEN"
                ),
                POLineRow(
                    po_id="PO-1", line_number=2, sku="B", description="B", quantity="2", unit_price="2.00", gl_account="5200"
                ),
                POLineRow(
                    po_id="PO-1", line_number=1, sku="A", description="A", quantity="1", unit_price="1.00", gl_account="5100"
                ),
            ]
        )
        session.commit()
    erp = LocalERPAdapter(sf)

    assert erp.get_vendor("missing") is None
    assert erp.get_vendor("V1").ap_account == "2000"
    assert erp.get_vendor_by_name("Acme").vendor_id == "V1"
    assert erp.get_vendor_by_name("missing") is None
    assert erp.get_purchase_order("missing") is None
    po = erp.get_purchase_order("PO-1")
    assert [line.line_number for line in po.lines] == [1, 2]


def test_receipts_are_ordered_and_duplicate_sources_are_checked(tmp_path):
    sf = _db(tmp_path)
    with sf() as session:
        session.add(VendorRow(vendor_id="V1", vendor_name="Acme", active=True, ap_account="2000"))
        session.commit()
        session.add(
            PurchaseOrderRow(
                po_id="PO-1", vendor_id="V1", vendor_name="Acme", currency="USD", status="OPEN"
            )
        )
        session.commit()
        session.add_all(
            [
                ReceiptRow(receipt_id="R-2", po_id="PO-1"),
                ReceiptRow(receipt_id="R-1", po_id="PO-1"),
                ReceiptLineRow(receipt_id="R-2", sku="B", quantity_received="2"),
                ReceiptLineRow(receipt_id="R-1", sku="A", quantity_received="1"),
            ]
        )
        session.commit()
    erp = LocalERPAdapter(sf)
    assert [receipt.receipt_id for receipt in erp.get_receipts("PO-1")] == ["R-1", "R-2"]

    assert not erp.check_duplicate_invoice("V1", "INV-1")
    erp.seed_duplicate("V1", "INV-1")
    erp.seed_duplicate("V1", "INV-1")
    assert erp.check_duplicate_invoice("V1", "INV-1")
    with sf() as session:
        assert session.scalar(select(DuplicateSeedRow).where(DuplicateSeedRow.vendor_id == "V1")) is not None

    erp.record_processed("key-1", "V2", "INV-2", _result("key-1"))
    erp.record_processed("key-1", "V2", "INV-2", _result("key-1"))
    assert erp.check_duplicate_invoice("V2", "INV-2")
    with sf() as session:
        assert len(session.scalars(select(ProcessedDocumentRow)).all()) == 1


def test_previous_result_draft_ids_and_attachment(tmp_path):
    sf = _db(tmp_path)
    erp = LocalERPAdapter(sf)
    result = _result("abcdef1234567890")
    assert erp.get_previous_result("missing") is None
    erp.record_processed("abcdef1234567890", "V1", "INV-1", result)
    assert erp.get_previous_result("abcdef1234567890").case_id == "case-1"

    assert erp.create_draft_bill(result) == "DRAFT-ABCDEF123456"
    assert erp.create_draft_bill(_result("")) == "DRAFT-UNKNOWN"
    erp.attach_source_document("DRAFT-ABCDEF123456", b"pdf", "invoice.pdf")
    with sf() as session:
        assert len(session.scalars(select(JournalDraftRow)).all()) == 2
