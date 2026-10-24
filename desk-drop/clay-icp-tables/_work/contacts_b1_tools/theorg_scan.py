import csv, os, re, sys, unicodedata, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get
from theorg_parse import positions
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = list(csv.DictReader(open(os.path.join(W, 'top60_brands.csv'))))
def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ').replace('+', ' and ')
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r"[^a-z0-9]+", '-', s).strip('-')
    return s
res = []
for x in rows:
    name = x['company']; dom = re.sub(r'^https?://(www\.)?', '', x['website']).split('/')[0].lower()
    stem = dom.split('.')[0]
    cands = []
    for c in [slugify(name), slugify(re.sub(r'^the\s+', '', name, flags=re.I)), stem, slugify(name) + '-inc', slugify(name.split('(')[0])]:
        if c and c not in cands:
            cands.append(c)
    hit = None
    for c in cands:
        st, p = get('https://theorg.com/org/' + c, 'theorg')
        code = st.split()[0]
        if code == '200':
            comp, ps = positions(p)
            exts = [e.lower() for e in (comp or {}).get('extensions', []) or []]
            web = ((comp or {}).get('social') or {}).get('websiteUrl') or ''
            match = any(dom.endswith(e) or e.endswith(dom) for e in exts) or (dom in web.lower())
            hit = dict(rank=x['rank'], company=name, slug=c, match=match, exts=';'.join(exts), web=web, n=len(ps), file=p)
            if match:
                break
    if hit:
        res.append(hit)
        print(x['rank'], name, hit['slug'], hit['match'], hit['exts'], hit['n'], flush=True)
    else:
        print(x['rank'], name, 'no org page', flush=True)
json.dump(res, open(os.path.join(W, 'fetch', 'contacts_b1', 'theorg_hits.json'), 'w'), indent=1)
