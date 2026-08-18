"""Streamlit UI for AP three-way match — local MockLLM path."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None  # type: ignore

from app.adapters.local_erp import LocalERPAdapter
from app.audit import AuditLog
from app.database import init_db
from app.fixtures import FIXTURE_ROOT, SPLITS, case_dirs, split_root
from app.hashing import sha256_bytes
from app.jsonio import read_json
from app.llm_client import MockLLMClient
from app.pipeline import Pipeline, load_policy, run_case_dir
from app.schemas import ExtractedInvoice, WorkflowDecision, WorkflowResult
from app.settings import get_settings


def _list_cases() -> list[tuple[str, str]]:
    return [(split, d.name) for split in SPLITS for d in case_dirs(split_root(split))]


def _case_dir(split: str, case_id: str) -> Path:
    return split_root(split) / case_id


def _load_fixture_json(path: Path) -> dict[str, Any]:
    return read_json(path)


def _ensure_session() -> None:
    if "sf" not in st.session_state:
        settings = get_settings()
        st.session_state.sf = init_db(settings.database_url)
    if "erp" not in st.session_state:
        st.session_state.erp = LocalERPAdapter(st.session_state.sf)
    if "llm" not in st.session_state:
        st.session_state.llm = MockLLMClient(fixture_root=FIXTURE_ROOT)
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_manifest" not in st.session_state:
        st.session_state.last_manifest = None
    if "last_pdf_bytes" not in st.session_state:
        st.session_state.last_pdf_bytes = None
    if "draft_history" not in st.session_state:
        st.session_state.draft_history = []
    if "audit_events" not in st.session_state:
        st.session_state.audit_events = []


def _env_metadata() -> dict[str, Any]:
    settings = get_settings()
    commit = "unknown"
    try:
        import subprocess

        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(REPO_ROOT),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        pass
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "source_commit": commit,
        "model_name": settings.model_name,
        "model_revision": settings.model_revision,
        "schema_version": settings.schema_version,
        "prompt_version": settings.prompt_version,
        "database_url": settings.database_url,
        "llm_mode": "MockLLMClient (local)",
        "gpu_run": False,
    }


def _render_extracted(inv: Optional[ExtractedInvoice]) -> None:
    if inv is None:
        st.warning("No extraction available.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Vendor", inv.vendor_name or "—")
    c2.metric("Invoice #", inv.invoice_number or "—")
    c3.metric("PO #", inv.po_number or "—")
    c4, c5, c6 = st.columns(3)
    c4.write(f"**Date:** {inv.invoice_date or '—'}")
    c5.write(f"**Currency:** {inv.currency or '—'}")
    c6.write(f"**Total:** {inv.invoice_total or '—'}")
    st.write(
        f"Subtotal `{inv.subtotal}` · Tax `{inv.tax}` · Freight `{inv.freight}` · Terms `{inv.payment_terms}`"
    )
    if inv.line_items:
        st.dataframe(
            [
                {
                    "line": ln.line_number,
                    "sku": ln.sku,
                    "description": ln.description,
                    "qty": ln.quantity,
                    "unit_price": ln.unit_price,
                    "line_total": ln.line_total,
                }
                for ln in inv.line_items
            ],
            use_container_width=True,
        )
    if inv.ambiguities:
        st.subheader("Ambiguities")
        for a in inv.ambiguities:
            st.error(f"{a.field}: {a.reason} candidates={a.candidates}")


def _render_evidence(inv: Optional[ExtractedInvoice]) -> None:
    if inv is None:
        return
    rows = []
    for field, span in (inv.evidence or {}).items():
        rows.append({"field": field, "page": span.page, "quote": span.quote})
    for ln in inv.line_items or []:
        if ln.evidence:
            rows.append(
                {
                    "field": f"line_{ln.line_number}",
                    "page": ln.evidence.page,
                    "quote": ln.evidence.quote,
                }
            )
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No evidence quotes on extraction.")


def _render_controls(result: WorkflowResult) -> None:
    if not result.control_checks:
        st.info("No control checks recorded.")
        return
    st.dataframe(
        [
            {
                "code": c.code,
                "passed": c.passed,
                "detail": c.detail,
            }
            for c in result.control_checks
        ],
        use_container_width=True,
    )


def _render_journal(result: WorkflowResult) -> None:
    j = result.proposed_journal
    if j is None:
        st.info("No proposed journal (HUMAN_REVIEW or incomplete match).")
        return
    bal = "✅ balanced" if j.balanced else "❌ UNBALANCED"
    st.write(f"**Currency:** {j.currency} · **Status:** {bal}")
    st.dataframe(
        [
            {
                "account": ln.account,
                "debit": ln.debit,
                "credit": ln.credit,
                "memo": ln.memo,
            }
            for ln in j.lines
        ],
        use_container_width=True,
    )


def _run_fixture_workflow(
    split: str,
    case_id: str,
    mode: str,
) -> tuple[WorkflowResult, Any, bytes]:
    case_dir = _case_dir(split, case_id)
    pdf_bytes = (case_dir / "invoice.pdf").read_bytes()
    audit = AuditLog(session_factory=st.session_state.sf)
    erp = st.session_state.erp
    llm = st.session_state.llm
    settings = get_settings()
    expected = _load_fixture_json(case_dir / "expected.json")
    if isinstance(llm, MockLLMClient):
        llm.register_expected(case_id, expected)
    extraction = expected.get("extraction")
    preseeded = ExtractedInvoice.model_validate(extraction) if extraction else None
    pipe = Pipeline(erp=erp, llm=llm, policy=load_policy(), audit=audit)
    result = pipe.run(
        pdf_bytes,
        case_id=case_id,
        mode=mode,  # type: ignore[arg-type]
        preseeded_extraction=preseeded,
    )
    manifest = pipe.build_manifest(result, pdf_bytes)
    st.session_state.audit_events = list(audit.events)
    return result, manifest, pdf_bytes


def _run_upload_workflow(
    pdf_bytes: bytes,
    case_id: str,
    mode: str,
    po_id: Optional[str],
) -> tuple[WorkflowResult, Any, bytes]:
    """Upload path: MockLLM falls back to deterministic PDF parser when no fixture."""
    audit = AuditLog(session_factory=st.session_state.sf)
    erp = st.session_state.erp
    llm = st.session_state.llm
    pipe = Pipeline(erp=erp, llm=llm, policy=load_policy(), audit=audit)
    # Hint PO via temporary expected registration is not used; parser extracts from PDF text.
    result = pipe.run(pdf_bytes, case_id=case_id, mode=mode)  # type: ignore[arg-type]
    # If user selected a PO and extraction missed it, surface note
    if po_id and result.extracted_invoice and not result.extracted_invoice.po_number:
        result.messages = list(result.messages) + [
            f"Selected PO {po_id} was not present on invoice; match used extracted PO only."
        ]
    manifest = pipe.build_manifest(result, pdf_bytes)
    st.session_state.audit_events = list(audit.events)
    return result, manifest, pdf_bytes


def _list_pos_receipts() -> tuple[list[str], dict[str, list[str]]]:
    erp: LocalERPAdapter = st.session_state.erp
    # Discover from fixture po.json files for selector convenience
    po_ids: list[str] = []
    receipts_by_po: dict[str, list[str]] = {}
    for split, case_id in _list_cases():
        po_path = _case_dir(split, case_id) / "po.json"
        rc_path = _case_dir(split, case_id) / "receipt.json"
        if po_path.exists():
            po = _load_fixture_json(po_path)
            pid = po.get("po_id")
            if pid and pid not in po_ids:
                po_ids.append(pid)
                receipts_by_po[pid] = []
            if pid and rc_path.exists():
                rc = _load_fixture_json(rc_path)
                # receipt.json may be object or list
                items = rc if isinstance(rc, list) else [rc]
                for item in items:
                    rid = item.get("receipt_id")
                    if rid and rid not in receipts_by_po[pid]:
                        receipts_by_po[pid].append(rid)
    # Also verify live ERP has them
    live = []
    for pid in po_ids:
        if erp.get_purchase_order(pid) is not None:
            live.append(pid)
    return live or po_ids, receipts_by_po


def main() -> None:
    if st is None:
        print("streamlit not installed; cannot launch UI")
        return

    st.set_page_config(page_title="AP Three-Way Match", layout="wide")
    st.title("Accounts Payable — Three-Way Match")
    st.caption(
        "Local non-GPU demo using MockLLMClient. Decision space: READY_FOR_DRAFT | HUMAN_REVIEW. "
        "Zero GPU spend in this environment."
    )
    _ensure_session()

    with st.sidebar:
        st.header("Environment")
        env = _env_metadata()
        st.json(env)
        st.header("Mode")
        mode = st.radio(
            "Workflow mode",
            options=["evaluate", "create_draft"],
            index=0,
            help="create_draft persists an idempotent draft when READY_FOR_DRAFT",
        )
        if st.button("Reset session ERP cache note"):
            st.info("Database persists on disk; restart process or change DATABASE_URL to fully reset.")

    tab_fixture, tab_upload = st.tabs(["Select fixture case", "Upload invoice PDF"])

    selected_po = None
    selected_receipt = None
    pdf_bytes: Optional[bytes] = None
    case_id = "upload"
    split = "custom"
    run_clicked = False

    with tab_fixture:
        cases = _list_cases()
        labels = [f"{s}/{c}" for s, c in cases]
        choice = st.selectbox("Invoice / case", options=labels, index=0 if labels else None)
        if choice:
            split, case_id = choice.split("/", 1)
            case_path = _case_dir(split, case_id)
            expected = _load_fixture_json(case_path / "expected.json")
            po = _load_fixture_json(case_path / "po.json")
            receipt = _load_fixture_json(case_path / "receipt.json")
            st.write(
                f"**Scenario:** `{expected.get('scenario')}` · "
                f"**Expected decision:** `{expected.get('decision')}` · "
                f"**Expected exceptions:** `{expected.get('exception_codes')}`"
            )
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Purchase order")
                st.json(po)
                selected_po = po.get("po_id")
            with c2:
                st.subheader("Receipt")
                st.json(receipt)
                if isinstance(receipt, list):
                    selected_receipt = receipt[0].get("receipt_id") if receipt else None
                else:
                    selected_receipt = receipt.get("receipt_id")
            st.write(f"Selected PO `{selected_po}` · Receipt `{selected_receipt}` (loaded from ERP DB seed)")
            run_clicked = st.button("Run workflow (fixture)", type="primary", key="run_fixture")
            if run_clicked:
                with st.spinner("Running pipeline…"):
                    result, manifest, pdf_bytes = _run_fixture_workflow(split, case_id, mode)
                    st.session_state.last_result = result
                    st.session_state.last_manifest = manifest
                    st.session_state.last_pdf_bytes = pdf_bytes
                    st.session_state.draft_history.append(
                        {
                            "case_id": case_id,
                            "mode": mode,
                            "decision": result.decision.value,
                            "draft_bill_id": result.draft_bill_id,
                            "idempotency_key": result.idempotency_key,
                            "messages": list(result.messages),
                        }
                    )

    with tab_upload:
        uploaded = st.file_uploader("Upload invoice PDF", type=["pdf"])
        po_ids, receipts_by_po = _list_pos_receipts()
        selected_po_u = st.selectbox("Select PO", options=["(none)"] + po_ids)
        r_opts = receipts_by_po.get(selected_po_u, []) if selected_po_u != "(none)" else []
        selected_receipt_u = st.selectbox(
            "Select receipt",
            options=["(auto from PO)"] + r_opts,
        )
        upload_case_id = st.text_input("Case / document id", value="upload_001")
        run_upload = st.button("Run workflow (upload)", type="primary", key="run_upload")
        if run_upload and uploaded is not None:
            pdf_bytes = uploaded.read()
            with st.spinner("Running pipeline on upload…"):
                result, manifest, pdf_bytes = _run_upload_workflow(
                    pdf_bytes,
                    upload_case_id,
                    mode,
                    None if selected_po_u == "(none)" else selected_po_u,
                )
                st.session_state.last_result = result
                st.session_state.last_manifest = manifest
                st.session_state.last_pdf_bytes = pdf_bytes
                st.session_state.draft_history.append(
                    {
                        "case_id": upload_case_id,
                        "mode": mode,
                        "decision": result.decision.value,
                        "draft_bill_id": result.draft_bill_id,
                        "idempotency_key": result.idempotency_key,
                        "messages": list(result.messages),
                        "selected_po": selected_po_u,
                        "selected_receipt": selected_receipt_u,
                    }
                )
        elif run_upload:
            st.error("Please upload a PDF first.")

    result: Optional[WorkflowResult] = st.session_state.last_result
    manifest = st.session_state.last_manifest

    st.divider()
    st.header("Workflow result")
    if result is None:
        st.info("Run a workflow to see results.")
        return

    decision = result.decision.value
    color = "green" if decision == WorkflowDecision.READY_FOR_DRAFT.value else "orange"
    st.markdown(f"### Decision: :{color}[{decision}]")
    cols = st.columns(4)
    cols[0].metric("Case", result.case_id or "—")
    cols[1].metric("Draft bill id", result.draft_bill_id or "—")
    cols[2].metric("OCR required", str(result.ocr_required))
    cols[3].metric("Pipeline state", result.pipeline_state.value)

    st.subheader("Exception codes")
    if result.exception_codes:
        st.error(", ".join(result.exception_codes))
    else:
        st.success("None")

    t1, t2, t3, t4, t5 = st.tabs(
        [
            "Extracted fields",
            "Evidence quotes",
            "Matching controls",
            "Proposed journal",
            "Audit / hashes",
        ]
    )
    with t1:
        _render_extracted(result.extracted_invoice)
    with t2:
        _render_evidence(result.extracted_invoice)
    with t3:
        _render_controls(result)
    with t4:
        _render_journal(result)
    with t5:
        if manifest is not None:
            st.json(manifest.model_dump())
        else:
            st.write("No manifest.")
        if st.session_state.last_pdf_bytes:
            st.write(f"PDF SHA-256: `{sha256_bytes(st.session_state.last_pdf_bytes)}`")
        st.subheader("Audit events")
        st.json(st.session_state.audit_events)
        st.subheader("Messages")
        for m in result.messages:
            st.write(f"- {m}")

    st.subheader("Idempotent draft history (this session)")
    if st.session_state.draft_history:
        st.dataframe(st.session_state.draft_history, use_container_width=True)
        # Highlight re-run: same idempotency key / same draft id
        keys = [h.get("draft_bill_id") for h in st.session_state.draft_history if h.get("draft_bill_id")]
        if len(keys) >= 2 and keys[-1] == keys[-2]:
            st.success(
                f"Re-run returned the same draft id `{keys[-1]}` — no duplicate draft created "
                "(idempotency hit)."
            )
        elif any("cached idempotent" in " ".join(h.get("messages") or []).lower() for h in st.session_state.draft_history):
            st.success("Cached idempotent result returned — no duplicate draft.")
    else:
        st.caption("No draft runs yet. Switch mode to create_draft and re-run to demonstrate idempotency.")

    st.caption(
        "Tip: set mode to `create_draft`, run a READY_FOR_DRAFT case twice — second run should show "
        "the same draft_bill_id / idempotent cache message."
    )


if __name__ == "__main__":
    main()
