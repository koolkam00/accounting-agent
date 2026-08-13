"""Strict Pydantic v2 schemas for the AP three-way-match agent."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowDecision(str, Enum):
    READY_FOR_DRAFT = "READY_FOR_DRAFT"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class PipelineState(str, Enum):
    INGEST = "INGEST"
    EXTRACT = "EXTRACT"
    VALIDATE = "VALIDATE"
    LOOKUP = "LOOKUP"
    MATCH = "MATCH"
    PROPOSE_JOURNAL = "PROPOSE_JOURNAL"
    CREATE_DRAFT_OR_REVIEW = "CREATE_DRAFT_OR_REVIEW"


class EvidenceSpan(StrictModel):
    quote: str
    page: int = Field(ge=1)


class InvoiceLineItem(StrictModel):
    line_number: int = Field(ge=1)
    sku: str
    description: str
    quantity: str  # normalized decimal string
    unit_price: str
    line_total: str
    evidence: Optional[EvidenceSpan] = None


class Ambiguity(StrictModel):
    field: str
    reason: str
    candidates: list[str] = Field(default_factory=list)


class ExtractedInvoice(StrictModel):
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None  # ISO YYYY-MM-DD
    po_number: Optional[str] = None
    currency: Optional[str] = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    subtotal: Optional[str] = None
    tax: Optional[str] = None
    freight: Optional[str] = None
    invoice_total: Optional[str] = None
    payment_terms: Optional[str] = None
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    evidence: dict[str, EvidenceSpan] = Field(default_factory=dict)


class ControlCheck(StrictModel):
    code: str
    passed: bool
    detail: str = ""


class JournalLine(StrictModel):
    account: str
    debit: str  # decimal string
    credit: str
    memo: str = ""


class ProposedJournal(StrictModel):
    lines: list[JournalLine]
    balanced: bool
    currency: str = "USD"


class WorkflowResult(StrictModel):
    case_id: Optional[str] = None
    decision: WorkflowDecision
    exception_codes: list[str] = Field(default_factory=list)
    control_checks: list[ControlCheck] = Field(default_factory=list)
    extracted_invoice: Optional[ExtractedInvoice] = None
    proposed_journal: Optional[ProposedJournal] = None
    idempotency_key: Optional[str] = None
    draft_bill_id: Optional[str] = None
    pipeline_state: PipelineState = PipelineState.CREATE_DRAFT_OR_REVIEW
    messages: list[str] = Field(default_factory=list)
    ocr_required: bool = False


class AuditManifest(StrictModel):
    case_id: str
    invoice_pdf_hash: str
    canonical_text_hash: str
    prompt_hash: str
    schema_hash: str
    policy_hash: str
    model_revision: str
    idempotency_key: str
    decision: WorkflowDecision
    exception_codes: list[str] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)


# ERP / fixture models

class POLine(StrictModel):
    line_number: int
    sku: str
    description: str
    quantity: str
    unit_price: str
    gl_account: str


class PurchaseOrder(StrictModel):
    po_id: str
    vendor_id: str
    vendor_name: str
    currency: str
    status: str  # OPEN / CLOSED
    lines: list[POLine]


class ReceiptLine(StrictModel):
    sku: str
    quantity_received: str


class Receipt(StrictModel):
    receipt_id: str
    po_id: str
    lines: list[ReceiptLine]


class Vendor(StrictModel):
    vendor_id: str
    vendor_name: str
    active: bool = True
    ap_account: Optional[str] = None


class PolicyConfig(StrictModel):
    currency: str = "USD"
    unit_price_percentage_tolerance: str = "0.005"
    minimum_unit_price_tolerance: str = "0.01"
    quantity_tolerance: str = "0"
    invoice_total_tolerance: str = "0.01"
    nonzero_tax_requires_review: bool = True
    missing_field_action: str = "HUMAN_REVIEW"
    ambiguous_field_action: str = "HUMAN_REVIEW"


EXCEPTION_CODES = [
    "MISSING_INVOICE_NUMBER",
    "PO_NOT_FOUND",
    "VENDOR_MISMATCH",
    "DUPLICATE_INVOICE",
    "CURRENCY_MISMATCH",
    "INVOICE_MATH_ERROR",
    "SKU_NOT_FOUND",
    "PRICE_VARIANCE",
    "QUANTITY_EXCEEDS_PO",
    "QUANTITY_EXCEEDS_RECEIPT",
    "NONZERO_TAX_REVIEW",
    "EVIDENCE_VALIDATION_FAILED",
    "OCR_REQUIRED",
    "MISSING_REQUIRED_FIELD",
    "AMBIGUOUS_FIELD",
    "UNBALANCED_JOURNAL",
    "VENDOR_INACTIVE",
]
