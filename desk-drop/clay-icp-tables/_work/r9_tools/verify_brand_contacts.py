"""Review round 1: re-open the stage-1 contact source of every brand that entered the top 60 after the claims scan
(and the next ten), and check the name and title appear on the page. Prints one line per person.
Run: python3 -I clay-icp-tables/_work/r9_tools/verify_brand_contacts.py"""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get
import pandas as pd
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
b = pd.read_csv(os.path.join(W, '..', 'brands.csv'), dtype=str, keep_default_na=False)
s1 = pd.read_csv(os.path.join(W, 'stage1_brands.csv'), dtype=str, keep_default_na=False).set_index('row_id')
t = b[(b.gate_result == 'pass') & (b['rank'].apply(lambda x: x != '' and int(x) <= 75)) & (b.contacts_researched == 'stage 1 only')]
def text(h):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", t)))
for r in t.itertuples():
    x = s1.loc[r.row_id]
    for pre in ('', 'backup_'):
        name = x[pre + 'contact_name_as_found']; url = x[pre + 'contact_profile_url']; title = x[pre + 'title']
        if not name or not url.startswith('http'):
            continue
        code, fin, h = get(url, 'brand_verify')
        tx = text(h)
        parts = [p for p in re.split(r"\s+", name) if len(p) > 1]
        hit = all(re.search(re.escape(p), tx, re.I) for p in parts)
        m = re.search(re.escape(parts[-1]), tx, re.I) if parts else None
        ctx = tx[max(0, m.start() - 120):m.end() + 120] if m else ''
        print(f"{r.rank}|{r.row_id}|{r.company}|{pre or 'primary'}|{name}|{title}|{code}|{'FOUND' if hit else 'NOT FOUND'}|{url}|{ctx}")
