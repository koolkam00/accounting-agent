#!/usr/bin/env python3
"""Load all fixture PO/receipt/vendor data into SQLite deterministically."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.adapters.local_erp import LocalERPAdapter
from app.database import (
    DuplicateSeedRow,
    POLineRow,
    PurchaseOrderRow,
    ReceiptLineRow,
    ReceiptRow,
    VendorRow,
    init_db,
    reset_db,
)
from app.settings import get_settings


VENDORS = [
    {"vendor_id": "V001", "vendor_name": "Northwind Office Supply LLC", "active": True, "ap_account": "2000"},
    {"vendor_id": "V002", "vendor_name": "Cedar Ridge Industrial Parts", "active": True, "ap_account": "2000"},
    {"vendor_id": "V003", "vendor_name": "Blue Harbor Packaging Co", "active": True, "ap_account": "2000"},
    {"vendor_id": "V004", "vendor_name": "Summit Ridge Labware Inc", "active": True, "ap_account": "2000"},
    {"vendor_id": "V005", "vendor_name": "Pinecrest Facilities Goods", "active": True, "ap_account": "2000"},
]


def iter_case_dirs() -> list[Path]:
    roots = [
        REPO / "tests" / "fixtures" / "development",
        REPO / "tests" / "fixtures" / "holdout",
    ]
    cases: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        cases.extend(sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("case_")))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    settings = get_settings()
    db_url = args.database_url or settings.database_url
    sf = reset_db(db_url) if args.reset else init_db(db_url)

    with sf() as session:
        for v in sorted(VENDORS, key=lambda x: x["vendor_id"]):
            if session.get(VendorRow, v["vendor_id"]) is None:
                session.add(VendorRow(**v))
        session.commit()

        for case_dir in iter_case_dirs():
            po = json.loads((case_dir / "po.json").read_text(encoding="utf-8"))
            receipt = json.loads((case_dir / "receipt.json").read_text(encoding="utf-8"))
            expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

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
                for ln in sorted(po["lines"], key=lambda x: x["line_number"]):
                    session.add(
                        POLineRow(
                            po_id=po["po_id"],
                            line_number=ln["line_number"],
                            sku=ln["sku"],
                            description=ln["description"],
                            quantity=ln["quantity"],
                            unit_price=ln["unit_price"],
                            gl_account=ln["gl_account"],
                        )
                    )

            if session.get(ReceiptRow, receipt["receipt_id"]) is None:
                session.add(ReceiptRow(receipt_id=receipt["receipt_id"], po_id=receipt["po_id"]))
                session.flush()
                for ln in receipt["lines"]:
                    session.add(
                        ReceiptLineRow(
                            receipt_id=receipt["receipt_id"],
                            sku=ln["sku"],
                            quantity_received=ln["quantity_received"],
                        )
                    )

            already = expected.get("already_processed")
            if already:
                exists = session.query(DuplicateSeedRow).filter_by(
                    vendor_id=already["vendor_id"],
                    invoice_number=already["invoice_number"],
                ).first()
                if exists is None:
                    session.add(
                        DuplicateSeedRow(
                            vendor_id=already["vendor_id"],
                            invoice_number=already["invoice_number"],
                        )
                    )
            session.commit()

    print(f"Initialized database at {db_url}")
    print(f"Loaded {len(iter_case_dirs())} cases")


if __name__ == "__main__":
    main()
