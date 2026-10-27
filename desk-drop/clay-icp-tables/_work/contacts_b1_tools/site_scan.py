import csv, os, re, sys, json
from urllib.parse import urljoin, urlparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get, text, raw
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = list(csv.DictReader(open(os.path.join(W, 'top60_brands.csv'))))
only = set(sys.argv[1:])
PAT = re.compile(r'(about|team|story|founder|people|who-we-are|meet|press|news|our-)', re.I)
KW = re.compile(r'(marketing|\bCMO\b|brand manager|head of brand|director of brand|growth|co-?founder|founder|\bCEO\b|president|partnership)', re.I)
out = {}
for x in rows:
    if only and x['rank'] not in only:
        continue
    home = x['website'].rstrip('/') + '/'
    st, p = get(home, 'site')
    host = urlparse(home).netloc.replace('www.', '')
    links = set()
    for m in re.finditer(r'href="([^"#]+)"', raw(p)):
        u = urljoin(home, m.group(1))
        pu = urlparse(u)
        if pu.netloc.replace('www.', '') == host and PAT.search(pu.path) and not re.search(r'/(products|collections|blogs/[^/]+/tagged|cart|account)', pu.path):
            links.add(u.split('?')[0])
    links = sorted(links, key=len)[:8]
    hits = []
    for u in [home] + links:
        st2, p2 = get(u, 'site') if u != home else (st, p)
        t = text(p2)
        for m in KW.finditer(t):
            hits.append((u, t[max(0, m.start()-120): m.end()+120]))
    out[x['rank']] = dict(company=x['company'], home_status=st.split()[0], links=links, hits=hits[:60])
    print(x['rank'], x['company'], st.split()[0], len(links), len(hits), flush=True)
json.dump(out, open(os.path.join(W, 'fetch', 'contacts_b1', 'site_scan.json'), 'w'), indent=1, ensure_ascii=False)
