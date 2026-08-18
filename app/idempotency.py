"""Stable idempotency key derivation."""

from __future__ import annotations

from app.hashing import sha256_text


SEPARATOR = "|"


def compute_idempotency_key(
    invoice_pdf_hash: str,
    po_id: str,
    receipt_snapshot_hash: str,
    prompt_hash: str,
    schema_hash: str,
    policy_hash: str,
    model_revision: str,
) -> str:
    """
    key = SHA256(invoice_pdf_hash + po_id + receipt_snapshot_hash +
                 prompt_hash + schema_hash + policy_hash + model_revision)
    Stable concatenation with separators.
    """
    parts = [
        invoice_pdf_hash,
        po_id,
        receipt_snapshot_hash,
        prompt_hash,
        schema_hash,
        policy_hash,
        model_revision,
    ]
    return sha256_text(SEPARATOR.join(parts))


def receipt_snapshot_hash(receipt_ids_and_payload: str) -> str:
    """Hash a deterministic snapshot string of receipts."""
    return sha256_text(receipt_ids_and_payload)
