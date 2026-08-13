"""Bounded state-machine pipeline for AP three-way match."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional

import yaml

from app.adapters.base import ERPAdapter
from app.adapters.local_erp import LocalERPAdapter
from app.audit import AuditLog
from app.canonicalize import canonicalize_document, sha256_bytes, sha256_text
from app.idempotency import compute_idempotency_key, hash_text
from app.journal import propose_journal
from app.llm_client import LLMClient, MockLLMClient
from app.matching import match_invoice
from app.pdf_text import extract_pdf_text
from app.schemas import (
    AuditManifest,
    ExtractedInvoice,
    PipelineState,
    PolicyConfig,
    WorkflowDecision,
    WorkflowResult,
)
from app.settings import REPO_ROOT, get_settings
from app.validation import validate_invoice


Mode = Literal["evaluate", "create_draft"]


def load_policy(path: Optional[Path] = None) -> PolicyConfig:
    settings = get_settings()
    p = path or settings.policy_path
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return PolicyConfig.model_validate(data)


def _receipt_snapshot(receipts) -> str:
    payload = [
        {
            "receipt_id": r.receipt_id,
            "po_id": r.po_id,
            "lines": sorted(
                [{"sku": ln.sku, "quantity_received": ln.quantity_received} for ln in r.lines],
                key=lambda x: x["sku"],
            ),
        }
        for r in sorted(receipts, key=lambda x: x.receipt_id)
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _schema_hash() -> str:
    # Stable hash of schema module version marker
    settings = get_settings()
    return hash_text(f"ExtractedInvoice:{settings.schema_version}")


def _prompt_hash() -> str:
    settings = get_settings()
    return sha256_bytes(settings.prompt_path.read_bytes())


def _policy_hash(policy_path: Path) -> str:
    return sha256_bytes(policy_path.read_bytes())


class Pipeline:
    def __init__(
        self,
        erp: ERPAdapter,
        llm: LLMClient,
        policy: Optional[PolicyConfig] = None,
        audit: Optional[AuditLog] = None,
        ap_account: Optional[str] = None,
    ) -> None:
        self.erp = erp
        self.llm = llm
        self.policy = policy or load_policy()
        self.audit = audit or AuditLog()
        self.settings = get_settings()
        self.ap_account = ap_account or self.settings.ap_account

    def run(
        self,
        pdf_bytes: bytes,
        *,
        case_id: Optional[str] = None,
        mode: Mode = "evaluate",
        preseeded_extraction: Optional[ExtractedInvoice] = None,
    ) -> WorkflowResult:
        settings = self.settings
        messages: list[str] = []
        all_exceptions: list[str] = []
        all_checks = []

        # INGEST
        self.audit.emit("STATE", {"state": PipelineState.INGEST.value}, case_id=case_id)
        pdf_hash = sha256_bytes(pdf_bytes)
        extraction_pdf = extract_pdf_text(pdf_bytes)
        canonical = canonicalize_document(
            pdf_bytes, extraction_pdf.pages, ocr_required=extraction_pdf.ocr_required
        )

        if canonical.ocr_required:
            self.audit.emit("OCR_REQUIRED", {"page_count": canonical.page_count}, case_id=case_id)
            result = WorkflowResult(
                case_id=case_id,
                decision=WorkflowDecision.HUMAN_REVIEW,
                exception_codes=["OCR_REQUIRED"],
                pipeline_state=PipelineState.INGEST,
                messages=["Image-only PDF; OCR required — never auto-approve"],
                ocr_required=True,
            )
            return result

        # EXTRACT
        self.audit.emit("STATE", {"state": PipelineState.EXTRACT.value}, case_id=case_id)
        if preseeded_extraction is not None:
            extracted = preseeded_extraction
        else:
            extracted = self.llm.extract_invoice(canonical.canonical_text, case_id=case_id)

        # VALIDATE
        self.audit.emit("STATE", {"state": PipelineState.VALIDATE.value}, case_id=case_id)
        v_exc, v_checks, normalized = validate_invoice(
            extracted, canonical.canonical_text, self.policy
        )
        all_exceptions.extend(v_exc)
        all_checks.extend(v_checks)
        invoice = normalized or extracted

        # LOOKUP
        self.audit.emit("STATE", {"state": PipelineState.LOOKUP.value}, case_id=case_id)
        po = None
        receipts = []
        vendor = None
        if invoice.po_number:
            po = self.erp.get_purchase_order(invoice.po_number)
            if po is not None:
                receipts = self.erp.get_receipts(po.po_id)
                vendor = self.erp.get_vendor(po.vendor_id)
        if vendor is None and invoice.vendor_id:
            vendor = self.erp.get_vendor(invoice.vendor_id)
        if vendor is None and invoice.vendor_name and isinstance(self.erp, LocalERPAdapter):
            vendor = self.erp.get_vendor_by_name(invoice.vendor_name)

        vendor_id_for_dup = (
            (vendor.vendor_id if vendor else None)
            or (po.vendor_id if po else None)
            or (invoice.vendor_id or "")
        )
        is_duplicate = False
        if invoice.invoice_number and vendor_id_for_dup:
            is_duplicate = self.erp.check_duplicate_invoice(vendor_id_for_dup, invoice.invoice_number)

        receipt_snap = _receipt_snapshot(receipts)
        receipt_hash = hash_text(receipt_snap)
        po_id = po.po_id if po else (invoice.po_number or "")
        idem_key = compute_idempotency_key(
            invoice_pdf_hash=pdf_hash,
            po_id=po_id,
            receipt_snapshot_hash=receipt_hash,
            prompt_hash=_prompt_hash(),
            schema_hash=_schema_hash(),
            policy_hash=_policy_hash(settings.policy_path),
            model_revision=settings.model_revision,
        )

        previous = self.erp.get_previous_result(idem_key)
        if previous is not None and mode == "create_draft":
            self.audit.emit("IDEMPOTENT_HIT", {"idempotency_key": idem_key}, case_id=case_id)
            previous.messages = list(previous.messages) + ["Returned cached idempotent result"]
            return previous

        # If validation already failed hard, still run match for complete exception set
        # MATCH
        self.audit.emit("STATE", {"state": PipelineState.MATCH.value}, case_id=case_id)
        decision, m_exc, m_checks = match_invoice(
            invoice=invoice,
            po=po,
            receipts=receipts,
            vendor=vendor,
            policy=self.policy,
            is_duplicate=is_duplicate,
        )
        all_exceptions.extend(m_exc)
        all_checks.extend(m_checks)
        all_exceptions = sorted(set(all_exceptions))

        proposed = None
        # PROPOSE_JOURNAL only when match side is clean of non-journal exceptions so far
        self.audit.emit("STATE", {"state": PipelineState.PROPOSE_JOURNAL.value}, case_id=case_id)
        if not all_exceptions and po is not None:
            proposed, j_exc, j_decision = propose_journal(invoice, po, ap_account=self.ap_account)
            all_exceptions.extend(j_exc)
            all_exceptions = sorted(set(all_exceptions))
            if j_exc:
                decision = WorkflowDecision.HUMAN_REVIEW
            else:
                decision = j_decision
        else:
            decision = WorkflowDecision.HUMAN_REVIEW

        if all_exceptions:
            decision = WorkflowDecision.HUMAN_REVIEW

        # CREATE_DRAFT_OR_REVIEW
        self.audit.emit(
            "STATE",
            {"state": PipelineState.CREATE_DRAFT_OR_REVIEW.value, "decision": decision.value},
            case_id=case_id,
        )

        draft_id = None
        result = WorkflowResult(
            case_id=case_id,
            decision=decision,
            exception_codes=all_exceptions,
            control_checks=all_checks,
            extracted_invoice=invoice,
            proposed_journal=proposed,
            idempotency_key=idem_key,
            draft_bill_id=None,
            pipeline_state=PipelineState.CREATE_DRAFT_OR_REVIEW,
            messages=messages,
            ocr_required=False,
        )

        if mode == "create_draft" and decision == WorkflowDecision.READY_FOR_DRAFT:
            draft_id = self.erp.create_draft_bill(result)
            self.erp.attach_source_document(draft_id, pdf_bytes, f"{case_id or 'invoice'}.pdf")
            result.draft_bill_id = draft_id
            self.erp.record_processed(
                idem_key,
                vendor_id_for_dup or "UNKNOWN",
                invoice.invoice_number or "UNKNOWN",
                result,
            )
        elif mode == "create_draft":
            # Still record processed for idempotency of review outcomes
            self.erp.record_processed(
                idem_key,
                vendor_id_for_dup or "UNKNOWN",
                invoice.invoice_number or "UNKNOWN",
                result,
            )

        self.audit.emit(
            "COMPLETE",
            {
                "decision": decision.value,
                "exception_codes": all_exceptions,
                "idempotency_key": idem_key,
            },
            case_id=case_id,
        )
        return result

    def build_manifest(self, result: WorkflowResult, pdf_bytes: bytes) -> AuditManifest:
        settings = self.settings
        pdf_hash = sha256_bytes(pdf_bytes)
        pages = extract_pdf_text(pdf_bytes).pages
        canon = canonicalize_document(pdf_bytes, pages)
        return AuditManifest(
            case_id=result.case_id or "",
            invoice_pdf_hash=pdf_hash,
            canonical_text_hash=canon.canonical_hash,
            prompt_hash=_prompt_hash(),
            schema_hash=_schema_hash(),
            policy_hash=_policy_hash(settings.policy_path),
            model_revision=settings.model_revision,
            idempotency_key=result.idempotency_key or "",
            decision=result.decision,
            exception_codes=result.exception_codes,
            events=self.audit.events,
        )


def run_case_dir(
    case_dir: Path,
    erp: ERPAdapter,
    llm: Optional[LLMClient] = None,
    mode: Mode = "evaluate",
) -> WorkflowResult:
    case_id = case_dir.name
    pdf_bytes = (case_dir / "invoice.pdf").read_bytes()
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
    client = llm or MockLLMClient()
    if isinstance(client, MockLLMClient):
        client.register_expected(case_id, expected)
    extraction = expected.get("extraction")
    preseeded = ExtractedInvoice.model_validate(extraction) if extraction else None
    pipe = Pipeline(erp=erp, llm=client)
    return pipe.run(pdf_bytes, case_id=case_id, mode=mode, preseeded_extraction=preseeded)
