"""Spot check round 10: square footage for passed offices whose B row records none, read from the row's own
address or second source when it is a leasing article (curl GET, generic User-Agent; pages under
_work/fetch/r9/space/). Writes _work/space_r9.csv with the figure, the sentence it comes from and the URL.
Run: python3 -I clay-icp-tables/_work/r9_tools/space_scan.py"""
import csv, html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get
import pandas as pd
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
o = pd.read_csv(os.path.join(W, 'stage1_offices.csv'), dtype=str, keep_default_na=False)
p = o[(o.gate_result == 'pass') & (o.leased_sf_mentioned == '') & (o.org_type == 'company')]
NEWS = re.compile(r'commercialobserver|nyrej|rebusinessonline|connectcre|therealdeal|bisnow|crainsnewyork|globest|mannpublications|fnp|costar', re.I)
SF = re.compile(r'(\d{1,3}(?:,\d{3})+|\d{4,6})[- ](?:square[- ]f(?:oo|ee)t|rentable square feet|sf|s/f)\b|(\d{1,3}(?:\.\d)?)K[- ]?SF', re.I)
def text(h):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", t)))
rows = []
for r in p.itertuples():
    for u in (r.address_source_url, r.second_source_url):
        if not u or not NEWS.search(u):
            continue
        code, fin, h = get(u, 'space')
        if not code.startswith('2'):
            continue
        t = text(h)
        name = re.sub(r"\s*\(.*\)", "", r.company)
        key = [w for w in re.findall(r"[A-Za-z0-9.]+", name) if len(w) > 2][:1]
        best = None
        for m in SF.finditer(t):
            v = int(m.group(1).replace(',', '')) if m.group(1) else int(float(m.group(2)) * 1000)
            ctx = t[max(0, m.start() - 220):m.end() + 120]
            if key and re.search(re.escape(key[0]), ctx, re.I) and 1500 <= v <= 400000:
                best = (v, ctx)
                break
        if best:
            rows.append(dict(row_id=r.row_id, company=r.company, leased_sf=best[0], source_url=u,
                             quote=best[1].strip(), opened='2026-10-24'))
            print(r.row_id, r.company, best[0], u[:80])
            break
with open(os.path.join(W, 'space_r9.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['row_id', 'company', 'leased_sf', 'source_url', 'quote', 'opened'])
    w.writeheader(); w.writerows(rows)
print(len(rows), 'of', len(p))
