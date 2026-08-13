"""ERP adapter protocol / base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.schemas import PurchaseOrder, Receipt, Vendor, WorkflowResult


class ERPAdapter(ABC):
    @abstractmethod
    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        ...

    @abstractmethod
    def get_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        ...

    @abstractmethod
    def get_receipts(self, po_id: str) -> list[Receipt]:
        ...

    @abstractmethod
    def check_duplicate_invoice(self, vendor_id: str, invoice_number: str) -> bool:
        ...

    @abstractmethod
    def create_draft_bill(self, result: WorkflowResult) -> str:
        ...

    @abstractmethod
    def attach_source_document(self, draft_bill_id: str, pdf_bytes: bytes, filename: str) -> None:
        ...

    @abstractmethod
    def get_previous_result(self, idempotency_key: str) -> Optional[WorkflowResult]:
        ...

    @abstractmethod
    def record_processed(self, idempotency_key: str, vendor_id: str, invoice_number: str, result: WorkflowResult) -> None:
        ...
