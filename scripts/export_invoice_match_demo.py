"""Generate a static, sample-only Invoice Match demo."""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.pilot_match import build_report, read_context, sample_context, sample_pdf
from app.settings import REPO_ROOT

ROUTES = {
    "home": "index.html",
    "prepare": "checkout.html",
    "start_checkout": "result.html",
    "download": "invoice-match-report-sample.json",
    "static": "pilot.css",
}
SAMPLES = {"invoice": "sample-invoice.pdf", "context": "sample-po-and-receipts.json"}


def static_url(endpoint: str, **values: str) -> str:
    return SAMPLES[values["kind"]] if endpoint == "sample" else ROUTES[endpoint]


def export_demo(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Export into an empty directory so no unrelated files are published.")
    source = REPO_ROOT / "app"
    template = Environment(
        loader=FileSystemLoader(source / "pilot_templates"), autoescape=select_autoescape()
    ).get_template("pilot.html")
    pdf, context = sample_pdf(), sample_context()
    report = build_report(pdf, read_context(context), demo=True)
    for screen, endpoint in (("home", "home"), ("checkout", "prepare"), ("result", "start_checkout")):
        html = template.render(
            url_for=static_url, mode="demo", public_demo=True, static_demo=True,
            screen=screen, session={}, report_id="sample", report=report,
            invoice=report["extracted_invoice"],
        )
        (output / ROUTES[endpoint]).write_text(html, encoding="utf-8")
    (output / SAMPLES["invoice"]).write_bytes(pdf)
    (output / SAMPLES["context"]).write_bytes(context)
    (output / ROUTES["download"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / ROUTES["static"]).write_bytes((source / "pilot_static" / ROUTES["static"]).read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    export_demo(parser.parse_args().output)
