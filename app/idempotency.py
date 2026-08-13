"""Stable idempotency key derivation."""

from __future__ import annotations

import hashlib


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
    material = SEPARATOR.join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def receipt_snapshot_hash(receipt_ids_and_payload: str) -> str:
    """Hash a deterministic snapshot string of receipts."""
    return hash_text(receipt_ids_and_payload)
