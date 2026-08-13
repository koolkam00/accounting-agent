"""SQLAlchemy models and engine helpers (SQLite)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VendorRow(Base):
    __tablename__ = "vendors"
    vendor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(256), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    ap_account: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class PurchaseOrderRow(Base):
    __tablename__ = "purchase_orders"
    po_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(64), ForeignKey("vendors.vendor_id"))
    vendor_name: Mapped[str] = mapped_column(String(256), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    lines: Mapped[list["POLineRow"]] = relationship(back_populates="po", order_by="POLineRow.line_number")


class POLineRow(Base):
    __tablename__ = "po_lines"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    po_id: Mapped[str] = mapped_column(String(64), ForeignKey("purchase_orders.po_id"))
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    quantity: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_price: Mapped[str] = mapped_column(String(64), nullable=False)
    gl_account: Mapped[str] = mapped_column(String(64), nullable=False)
    po: Mapped[PurchaseOrderRow] = relationship(back_populates="lines")


class ReceiptRow(Base):
    __tablename__ = "receipts"
    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    po_id: Mapped[str] = mapped_column(String(64), ForeignKey("purchase_orders.po_id"))
    lines: Mapped[list["ReceiptLineRow"]] = relationship(
        back_populates="receipt", order_by="ReceiptLineRow.id"
    )


class ReceiptLineRow(Base):
    __tablename__ = "receipt_lines"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[str] = mapped_column(String(64), ForeignKey("receipts.receipt_id"))
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_received: Mapped[str] = mapped_column(String(64), nullable=False)
    receipt: Mapped[ReceiptRow] = relationship(back_populates="lines")


class WorkflowRunRow(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    exception_codes: Mapped[str] = mapped_column(Text, default="[]")
    pipeline_state: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ExtractedInvoiceRow(Base):
    __tablename__ = "extracted_invoices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class ControlCheckRow(Base):
    __tablename__ = "control_checks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")


class JournalDraftRow(Base):
    __tablename__ = "journal_drafts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    draft_bill_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class ProcessedDocumentRow(Base):
    __tablename__ = "processed_documents"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_idempotency_key"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DuplicateSeedRow(Base):
    """Tracks invoices already processed (for duplicate detection fixtures)."""
    __tablename__ = "duplicate_seeds"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vendor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    __table_args__ = (UniqueConstraint("vendor_id", "invoice_number", name="uq_vendor_invoice"),)


def make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, connect_args=connect_args, future=True)

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def init_db(database_url: str) -> sessionmaker[Session]:
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def reset_db(database_url: str) -> sessionmaker[Session]:
    engine = make_engine(database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
