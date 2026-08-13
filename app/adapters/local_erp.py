"""Local SQLite ERP adapter with explicit ORDER BY."""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.base import ERPAdapter
from app.database import (
    DuplicateSeedRow,
    JournalDraftRow,
    ProcessedDocumentRow,
    POLineRow,
    PurchaseOrderRow,
    ReceiptLineRow,
    ReceiptRow,
    VendorRow,
    WorkflowRunRow,
)
from app.schemas import (
    POLine,
    PurchaseOrder,
    Receipt,
    ReceiptLine,
    Vendor,
    WorkflowResult,
)


class LocalERPAdapter(ERPAdapter):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory

    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        with self._sf() as session:
            row = session.get(VendorRow, vendor_id)
            if row is None:
                return None
            return Vendor(
                vendor_id=row.vendor_id,
                vendor_name=row.vendor_name,
                active=row.active,
                ap_account=row.ap_account,
            )

    def get_vendor_by_name(self, vendor_name: str) -> Optional[Vendor]:
        with self._sf() as session:
            stmt = (
                select(VendorRow)
                .where(VendorRow.vendor_name == vendor_name)
                .order_by(VendorRow.vendor_id)
                .limit(1)
            )
            row = session.scalars(stmt).first()
            if row is None:
                return None
            return Vendor(
                vendor_id=row.vendor_id,
                vendor_name=row.vendor_name,
                active=row.active,
                ap_account=row.ap_account,
            )

    def get_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        with self._sf() as session:
            row = session.get(PurchaseOrderRow, po_id)
            if row is None:
                return None
            line_stmt = (
                select(POLineRow)
                .where(POLineRow.po_id == po_id)
                .order_by(POLineRow.line_number)
            )
            lines = [
                POLine(
                    line_number=ln.line_number,
                    sku=ln.sku,
                    description=ln.description,
                    quantity=ln.quantity,
                    unit_price=ln.unit_price,
                    gl_account=ln.gl_account,
                )
                for ln in session.scalars(line_stmt).all()
            ]
            return PurchaseOrder(
                po_id=row.po_id,
                vendor_id=row.vendor_id,
                vendor_name=row.vendor_name,
                currency=row.currency,
                status=row.status,
                lines=lines,
            )

    def get_receipts(self, po_id: str) -> list[Receipt]:
        with self._sf() as session:
            r_stmt = select(ReceiptRow).where(ReceiptRow.po_id == po_id).order_by(ReceiptRow.receipt_id)
            receipts: list[Receipt] = []
            for r in session.scalars(r_stmt).all():
                ln_stmt = (
                    select(ReceiptLineRow)
                    .where(ReceiptLineRow.receipt_id == r.receipt_id)
                    .order_by(ReceiptLineRow.id)
                )
                lines = [
                    ReceiptLine(sku=ln.sku, quantity_received=ln.quantity_received)
                    for ln in session.scalars(ln_stmt).all()
                ]
                receipts.append(Receipt(receipt_id=r.receipt_id, po_id=r.po_id, lines=lines))
            return receipts

    def check_duplicate_invoice(self, vendor_id: str, invoice_number: str) -> bool:
        with self._sf() as session:
            seed = session.scalars(
                select(DuplicateSeedRow)
                .where(
                    DuplicateSeedRow.vendor_id == vendor_id,
                    DuplicateSeedRow.invoice_number == invoice_number,
                )
                .order_by(DuplicateSeedRow.id)
                .limit(1)
            ).first()
            if seed is not None:
                return True
            existing = session.scalars(
                select(ProcessedDocumentRow)
                .where(
                    ProcessedDocumentRow.vendor_id == vendor_id,
                    ProcessedDocumentRow.invoice_number == invoice_number,
                )
                .order_by(ProcessedDocumentRow.id)
                .limit(1)
            ).first()
            return existing is not None

    def create_draft_bill(self, result: WorkflowResult) -> str:
        draft_id = f"DRAFT-{result.idempotency_key[:12].upper()}" if result.idempotency_key else "DRAFT-UNKNOWN"
        with self._sf() as session:
            run = WorkflowRunRow(
                case_id=result.case_id,
                idempotency_key=result.idempotency_key or "",
                decision=result.decision.value,
                exception_codes=json.dumps(result.exception_codes),
                pipeline_state=result.pipeline_state.value,
                mode="create_draft",
            )
            session.add(run)
            session.flush()
            session.add(
                JournalDraftRow(
                    workflow_run_id=run.id,
                    draft_bill_id=draft_id,
                    payload_json=result.proposed_journal.model_dump_json() if result.proposed_journal else "{}",
                )
            )
            session.commit()
        return draft_id

    def attach_source_document(self, draft_bill_id: str, pdf_bytes: bytes, filename: str) -> None:
        # Local adapter: no-op persistence of attachment metadata (bytes not stored to keep DB light)
        _ = (draft_bill_id, len(pdf_bytes), filename)
        return None

    def get_previous_result(self, idempotency_key: str) -> Optional[WorkflowResult]:
        with self._sf() as session:
            row = session.scalars(
                select(ProcessedDocumentRow)
                .where(ProcessedDocumentRow.idempotency_key == idempotency_key)
                .order_by(ProcessedDocumentRow.id)
                .limit(1)
            ).first()
            if row is None:
                return None
            return WorkflowResult.model_validate_json(row.result_json)

    def record_processed(
        self,
        idempotency_key: str,
        vendor_id: str,
        invoice_number: str,
        result: WorkflowResult,
    ) -> None:
        with self._sf() as session:
            existing = session.scalars(
                select(ProcessedDocumentRow)
                .where(ProcessedDocumentRow.idempotency_key == idempotency_key)
                .order_by(ProcessedDocumentRow.id)
                .limit(1)
            ).first()
            if existing is not None:
                return
            session.add(
                ProcessedDocumentRow(
                    idempotency_key=idempotency_key,
                    vendor_id=vendor_id,
                    invoice_number=invoice_number,
                    result_json=result.model_dump_json(),
                )
            )
            session.commit()

    def seed_duplicate(self, vendor_id: str, invoice_number: str) -> None:
        with self._sf() as session:
            existing = session.scalars(
                select(DuplicateSeedRow)
                .where(
                    DuplicateSeedRow.vendor_id == vendor_id,
                    DuplicateSeedRow.invoice_number == invoice_number,
                )
                .order_by(DuplicateSeedRow.id)
                .limit(1)
            ).first()
            if existing is None:
                session.add(DuplicateSeedRow(vendor_id=vendor_id, invoice_number=invoice_number))
                session.commit()
