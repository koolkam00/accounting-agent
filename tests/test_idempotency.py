from app.idempotency import compute_idempotency_key


def test_key_stable():
    kwargs = dict(
        invoice_pdf_hash="a" * 64,
        po_id="PO-1",
        receipt_snapshot_hash="b" * 64,
        prompt_hash="c" * 64,
        schema_hash="d" * 64,
        policy_hash="e" * 64,
        model_revision="b968826d9c46dd6066d109eabc6255188de91218",
    )
    k1 = compute_idempotency_key(**kwargs)
    k2 = compute_idempotency_key(**kwargs)
    assert k1 == k2
    assert len(k1) == 64


def test_key_changes_with_inputs():
    base = dict(
        invoice_pdf_hash="a" * 64,
        po_id="PO-1",
        receipt_snapshot_hash="b" * 64,
        prompt_hash="c" * 64,
        schema_hash="d" * 64,
        policy_hash="e" * 64,
        model_revision="rev1",
    )
    k1 = compute_idempotency_key(**base)
    base2 = dict(base, po_id="PO-2")
    k2 = compute_idempotency_key(**base2)
    assert k1 != k2
