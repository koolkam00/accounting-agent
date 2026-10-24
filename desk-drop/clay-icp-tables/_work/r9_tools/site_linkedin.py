"""R1-07(a): the company LinkedIn page each office's own website links to (LinkedIn itself is never opened).
Reads clay-icp-tables/_work/stage1_offices.csv; writes _work/linkedin_company_r9.csv.
Run: python3 -I clay-icp-tables/_work/r9_tools/site_linkedin.py"""
import csv, html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = list(csv.DictReader(open(os.path.join(W, 'stage1_offices.csv'), encoding='utf-8')))
PAT = re.compile(r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/(company|school|showcase)/([A-Za-z0-9_%.\-]+)', re.I)
out = []
for k, r in enumerate(rows, 1):
    if r['org_type'] != 'company':
        continue
    site = r['website'] if r['website'].startswith('http') else ''
    rec = dict(row_id=r['row_id'], company=r['company'], website=site, http='', linkedin_company_url='',
               candidates='', source_url='', opened='2026-10-24')
    if site:
        code, fin, h = get(site, 'site')
        rec['http'] = code
        hs = html.unescape(h)
        c = []
        for m in PAT.finditer(hs):
            slug = m.group(2).rstrip('/.').split('?')[0]
            u = f'https://www.linkedin.com/{m.group(1).lower()}/{slug}'
            if u not in c:
                c.append(u)
        rec['candidates'] = ';'.join(c[:5])
        if len(c) >= 1:
            rec['linkedin_company_url'] = c[0]
            rec['source_url'] = fin or site
    out.append(rec)
    print(k, r['row_id'], r['company'], rec['http'], rec['linkedin_company_url'], flush=True)
with open(os.path.join(W, 'linkedin_company_r9.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)
print('done', sum(1 for x in out if x['linkedin_company_url']), 'of', len(out))
