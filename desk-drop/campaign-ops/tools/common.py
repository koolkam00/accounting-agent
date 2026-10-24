"""Shared helpers for the generators: paths, the name, HTML page shell, rendering."""
import datetime as dt
import html
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESK = os.path.dirname(ROOT)
IDENTITY = os.path.join(DESK, "desk-drop-identity")
sys.path.insert(0, HERE)

E = html.escape


def fmt_date(d, style="%a %Y-%m-%d"):
    if d in (None, ""):
        return ""
    if isinstance(d, str):
        d = dt.date.fromisoformat(d[:10])
    return d.strftime(style)


def fmt_time(t):
    if t in (None, ""):
        return ""
    if isinstance(t, dt.datetime):
        t = t.time()
    return t.strftime("%H:%M")


def is_sample(*vals):
    return any(str(v).startswith("SAMPLE") for v in vals if v not in (None, ""))


def tokens_href(from_dir):
    return os.path.relpath(os.path.join(IDENTITY, "tokens", "tokens.css"), from_dir)


def fonts_href(from_dir):
    p = os.path.join(IDENTITY, "fonts", "fonts.css")
    return os.path.relpath(p, from_dir) if os.path.exists(p) else ""


BASE_CSS = """
:root { --ink:#16181d; --muted:#5b616e; --rule:#d5d8de; --hi:#fff3bf; --bad:#b42318; --ok:#1a7f37; --paper:#ffffff; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font: 10.5pt/1.35 "Atkinson Hyperlegible Next", "Atkinson Hyperlegible", Arial, sans-serif; }
.page { max-width: 7.7in; margin: 0 auto; padding: 0.1in 0; }
h1 { font: 800 18pt/1.1 "Bricolage Grotesque", Arial, sans-serif; margin: 0 0 4pt; }
h2 { font: 800 12pt/1.2 "Bricolage Grotesque", Arial, sans-serif; margin: 12pt 0 4pt; }
h3 { font-size: 10.5pt; margin: 8pt 0 2pt; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid var(--rule); padding: 3pt 4pt; text-align: left; vertical-align: top; }
th { font-size: 8.5pt; text-transform: none; color: var(--muted); border-bottom: 2px solid var(--ink); }
.muted { color: var(--muted); }
.small { font-size: 8.5pt; }
.box { display:inline-block; min-width: 0.55in; border-bottom: 1px solid var(--ink); height: 14pt; }
.chk { display:inline-block; width: 10pt; height: 10pt; border: 1px solid var(--ink); margin-right: 4pt; vertical-align: -1pt; }
.sample { background:#b42318; color:#fff; font-weight:700; padding:4pt 8pt; margin-bottom:8pt; letter-spacing:.02em; }
.warn { color: var(--bad); font-weight: 700; }
.hi { background: var(--hi); }
.stop { page-break-inside: avoid; border-top: 2px solid var(--ink); padding: 6pt 0 4pt; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap: 4pt 14pt; }
@media screen and (max-width: 600px) { .page { padding: 0 16px; } .grid { grid-template-columns: 1fr; } table { font-size: 9pt; } }
@page { size: Letter; margin: 0.45in; }
"""


def page(title, body, out_dir, sample=False, extra_css=""):
    fonts = fonts_href(out_dir)
    links = '<link rel="stylesheet" href="%s">' % E(fonts) if fonts else ""
    banner = '<div class="sample">SAMPLE. Test data only: illustrative placeholders, not results. Never send or print for use.</div>' if sample else ""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>%s</title>%s<style>%s%s</style></head><body><div class=\"page\">%s%s</div></body></html>") % (
        E(title), links, BASE_CSS, extra_css, banner, body)


def render(html_path, pdf_path=None, png_path=None, landscape=False, width=None):
    cmd = ["node", os.path.join(HERE, "render_html.js"), html_path]
    cmd.append(pdf_path or "-")
    if png_path:
        cmd += ["--png", png_path]
    if landscape:
        cmd.append("--landscape")
    if width:
        cmd += ["--width", str(width)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "errors": [r.stderr[-500:]]}


TEXT_BANNER = "SAMPLE. Test data only: illustrative placeholders, not results. Never send or print for use."


def write(path, text):
    """Write a generated file. A text draft (.md, .txt) built on SAMPLE rows starts with the SAMPLE banner line
    (CONTRACTS section 2; review round 1, R1-10). Every SAMPLE ID and text starts with SAMPLE, so a draft that holds
    the word SAMPLE was built on sample data; a real draft never does."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith((".md", ".txt")) and "SAMPLE" in text and not text.startswith(TEXT_BANNER):
        text = TEXT_BANNER + "\n\n" + text
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def brand_name():
    """BRAND_NAME from desk-drop-identity/brand.json: the name the printed pieces (cards, labels, report) carry."""
    return json.load(open(os.path.join(IDENTITY, "brand.json"), encoding="utf-8"))["BRAND_NAME"]


def require_same_name(tr):
    """A rename must reach both places the same day: the tracker's company_name (config!B2), which the text documents
    print, and desk-drop-identity/brand.json, which the printed pieces print. Refuse (exit 2) while they differ, so a
    kit can never carry two names (review round 1, R1-04)."""
    want = brand_name()
    if (tr.company_name or "").strip() != want.strip():
        print("REFUSED: the name differs. The tracker's company_name (config!B2) says %r; desk-drop-identity/brand.json "
              "(BRAND_NAME) says %r. Change config!B2 and brand.json together (README, Rename), then run this again." % (tr.company_name, want))
        sys.exit(2)
