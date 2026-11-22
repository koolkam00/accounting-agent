import json
import re

import pytest

from app.pilot_match import sample_context, sample_pdf
from scripts.export_invoice_match_demo import export_demo


def test_static_demo_builds_a_self_contained_sample_flow(tmp_path):
    export_demo(tmp_path)
    home = (tmp_path / "index.html").read_text()
    checkout = (tmp_path / "checkout.html").read_text()
    result = (tmp_path / "result.html").read_text()
    assert 'href="checkout.html">Use sample documents' in home
    assert 'href="result.html">Simulate payment' in checkout
    assert "No card details, real charge or Stripe connection." in checkout
    assert "Simulated payment confirmed" in result
    assert "Documents match." in result
    for html in (home, checkout, result):
        assert "<form" not in html and "<script" not in html
        assert 'type="file"' not in html
        for url in re.findall(r'href="([^"]+)"', html):
            assert "/" not in url and (tmp_path / url).is_file()
    assert (tmp_path / "sample-invoice.pdf").read_bytes() == sample_pdf()
    assert (tmp_path / "sample-po-and-receipts.json").read_bytes() == sample_context()
    report = json.loads((tmp_path / "invoice-match-report-sample.json").read_text())
    assert report["demo"] is True and report["decision"] == "READY_FOR_DRAFT"
    assert set(p.suffix for p in tmp_path.iterdir()) == {".html", ".css", ".pdf", ".json"}


def test_static_demo_export_rejects_nonempty_directory(tmp_path):
    (tmp_path / "unrelated.txt").touch()
    with pytest.raises(ValueError, match="empty directory"):
        export_demo(tmp_path)
