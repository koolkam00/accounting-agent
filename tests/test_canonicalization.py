from app.canonicalize import canonicalize_page_text, join_pages, sha256_text, canonicalize_document


def test_nfc_and_newlines():
    text = "cafe\u0301\r\nnext"
    out = canonicalize_page_text(text)
    assert "\r" not in out
    assert "é" in out or "café" in out  # NFC composed or equivalent


def test_whitespace_policy():
    raw = "a   b\t\tc  \n\n\nfoo  "
    out = canonicalize_page_text(raw)
    assert out == "a b c\n\nfoo"


def test_page_separators_stable():
    joined = join_pages(["page one", "page two"])
    assert "\n\n--- PAGE 2 ---\n\n" in joined
    assert joined.startswith("page one")


def test_hashes_stable():
    pages = ["Hello", "World"]
    doc1 = canonicalize_document(b"%PDF-fake", pages)
    doc2 = canonicalize_document(b"%PDF-fake", pages)
    assert doc1.canonical_hash == doc2.canonical_hash == sha256_text(doc1.canonical_text)
    assert doc1.original_hash == doc2.original_hash
