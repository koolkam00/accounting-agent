"""Open The Org position pages and summarise (untrusted data).
Usage: python3 theorg_person.py org/slug [org/slug ...]"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get, _read

def summary(org, slug):
    url = f'https://theorg.com/org/{org}/person/{slug}'
    st, p = get(url, 'theorg_person')
    h = _read(p)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return dict(url=url, http=st.split()[0], error='no data')
    d = json.loads(m.group(1))
    pos = d['props']['pageProps'].get('initialPosition') or {}
    tl = [(r.get('role'), r.get('current'), (r.get('startDate') or {}).get('year')) for r in pos.get('roleTimeline') or []]
    social = pos.get('social') or {}
    s = json.dumps(pos)
    li = ''
    mm = re.search(r'https?://(?:[a-z]+\.)?linkedin\.com/in/[^"\\\s]+', s)
    if mm:
        li = mm.group(0)
    return dict(url=url, http=st.split()[0], name=pos.get('fullName'), role=pos.get('role'), updated=(pos.get('updatedAt') or '')[:10],
                timeline=tl, location=(pos.get('locationV2') or {}).get('locationString'),
                offices=[o.get('name') for o in pos.get('offices') or []], linkedin=li,
                company=(pos.get('company') or {}).get('name'))

if __name__ == '__main__':
    for a in sys.argv[1:]:
        org, slug = a.split('/')
        print(json.dumps(summary(org, slug), ensure_ascii=False))
