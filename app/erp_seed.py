"""Seed the local SQLite ERP from fixture case directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.database import (
    DuplicateSeedRow,
    POLineRow,
    PurchaseOrderRow,
    ReceiptLineRow,
    ReceiptRow,
    VendorRow,
)
from app.fixtures import load_expected
from app.jsonio import read_json

VENDOR_SEEDS: list[dict[str, Any]] = [
    {"vendor_id": "V001", "vendor_name": "Northwind Office Supply LLC", "active": True, "ap_account": "2000"},
    {"vendor_id": "V002", "vendor_name": "Cedar Ridge Industrial Parts", "active": True, "ap_account": "2000"},
    {"vendor_id": "V003", "vendor_name": "Blue Harbor Packaging Co", "active": True, "ap_account": "2000"},
    {"vendor_id": "V004", "vendor_name": "Summit Ridge Labware Inc", "active": True, "ap_account": "2000"},
    {"vendor_id": "V005", "vendor_name": "Pinecrest Facilities Goods", "active": True, "ap_account": "2000"},
    {"vendor_id": "V006", "vendor_name": "Harbor Closed Supply LLC", "active": False, "ap_account": "2000"},
]


def seed_vendors(session: Session) -> None:
    for vendor in sorted(VENDOR_SEEDS, key=lambda v: v["vendor_id"]):
        if session.get(VendorRow, vendor["vendor_id"]) is None:
            session.add(VendorRow(**vendor))
    session.commit()


def seed_case(session: Session, case_dir: Path) -> None:
    """Insert PO, receipt, and duplicate seed rows for one case (idempotent)."""
    po = read_json(case_dir / "po.json")
    receipt = read_json(case_dir / "receipt.json")
    expected = load_expected(case_dir)

    if session.get(PurchaseOrderRow, po["po_id"]) is None:
        session.add(
            PurchaseOrderRow(
                po_id=po["po_id"],
                vendor_id=po["vendor_id"],
                vendor_name=po["vendor_name"],
                currency=po["currency"],
                status=po["status"],
            )
        )
        session.flush()
        for line in sorted(po["lines"], key=lambda x: x["line_number"]):
            session.add(
                POLineRow(
                    po_id=po["po_id"],
                    line_number=line["line_number"],
                    sku=line["sku"],
                    description=line["description"],
                    quantity=line["quantity"],
                    unit_price=line["unit_price"],
                    gl_account=line["gl_account"],
                )
            )

    if session.get(ReceiptRow, receipt["receipt_id"]) is None:
        session.add(ReceiptRow(receipt_id=receipt["receipt_id"], po_id=receipt["po_id"]))
        session.flush()
        for line in receipt["lines"]:
            session.add(
                ReceiptLineRow(
                    receipt_id=receipt["receipt_id"],
                    sku=line["sku"],
                    quantity_received=line["quantity_received"],
                )
            )

    already = expected.get("already_processed")
    if already:
        exists = (
            session.query(DuplicateSeedRow)
            .filter_by(
                vendor_id=already["vendor_id"],
                invoice_number=already["invoice_number"],
            )
            .first()
        )
        if exists is None:
            session.add(
                DuplicateSeedRow(
                    vendor_id=already["vendor_id"],
                    invoice_number=already["invoice_number"],
                )
            )


def seed_fixture_cases(
    session_factory: sessionmaker[Session],
    case_dirs: list[Path],
) -> None:
    """Load vendors plus every provided case into the database."""
    with session_factory() as session:
        seed_vendors(session)
        for case_dir in case_dirs:
            seed_case(session, case_dir)
            session.commit()
