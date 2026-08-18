from app.idempotency import (
    compute_idempotency_key,
    hash_bytes,
    hash_text,
    receipt_snapshot_hash,
)


def test_hash_helpers_and_receipt_alias():
    assert hash_bytes(b"invoice") == hash_text("invoice")
    assert receipt_snapshot_hash("R1:1") == hash_text("R1:1")
    assert hash_bytes(b"invoice") != hash_bytes(b"other")


def test_idempotency_key_changes_for_each_input():
    base = {
        "invoice_pdf_hash": "pdf",
        "po_id": "po",
        "receipt_snapshot_hash": "receipts",
        "prompt_hash": "prompt",
        "schema_hash": "schema",
        "policy_hash": "policy",
        "model_revision": "model",
    }
    original = compute_idempotency_key(**base)
    assert compute_idempotency_key(**base) == original
    for field in base:
        changed = dict(base, **{field: base[field] + "-changed"})
        assert compute_idempotency_key(**changed) != original
