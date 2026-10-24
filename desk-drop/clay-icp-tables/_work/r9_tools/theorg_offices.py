"""Review round 1 (R1-07, R1-08): office contact candidates from The Org, for offices whose contacts were
never researched (new top-110 after the square-footage cap) and top-50 offices that lack a backup.

For each row: find the company's The Org page (slug checked against the company's web domain), read the
positions it lists and the members of its people, HR, operations, office, executive and admin teams, keep
positions whose title touches office, workplace, facilities, people, HR, executive assistant, chief of
staff or operations, then open each kept position page (name, current role, attached office, location
string, last update, any LinkedIn URL The Org lists; LinkedIn itself is never opened). Home-city strings
are read only to judge a New York base and are not stored beyond 'New York area' or 'outside New York'.
Writes _work/r9_theorg_candidates.csv for a human choice of primary and backup. Pages: _work/fetch/r9/.
Run: python3 -I clay-icp-tables/_work/r9_tools/theorg_offices.py <row_id> [...]   (or --auto)
"""
import csv, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(W, 'r9_theorg_candidates.csv')
ROLE = re.compile(r"\boffice\b|workplace|facilit|\bpeople\b|human resources|\bhr\b|talent|culture|"
                  r"employee experience|executive assistant|\bea\b|assistant to|chief of staff|\boperations\b|"
                  r"\badmin|receptionist|front desk|hospitality|events? (?:manager|coordinator)|community", re.I)
SKIP = re.compile(r"revenue operations|sales operations|marketing operations|security operations|"
                  r"clinical operations|network operations|engineering|engineer|developer|data operations|"
                  r"trading operations|ad operations|product operations|finance operations|billing|"
                  r"customer|fleet|warehouse|supply|logistic|it operations|devops|sec ?ops", re.I)
TEAM = re.compile(r"people|human|hr\b|talent|culture|operations|office|workplace|admin|executive|g&a|"
                  r"general and admin|facilities|chief of staff", re.I)
NY = re.compile(r"new york|nyc|manhattan|brooklyn|jersey city|hoboken", re.I)


def nd(h):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or '', re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ').replace('+', ' and ')
    s = re.sub(r'\(.*?\)', ' ', s)
    return re.sub(r"[^a-z0-9]+", '-', s).strip('-')


def dom(u):
    m = re.match(r'https?://(?:www\.)?([^/]+)', (u or '').strip().lower())
    return m.group(1) if m else ''


def find_org(name, website):
    d = dom(website)
    stem = d.split('.')[0] if d else ''
    base = re.sub(r'\s*\(.*?\)', '', name).strip()
    cands = []
    for c in [slugify(base), slugify(re.sub(r'^the\s+', '', base, flags=re.I)), stem, slugify(base) + '-inc',
              slugify(base.split(',')[0]), slugify(base) + '-1', slugify(base.replace('.', ''))]:
        if c and c not in cands:
            cands.append(c)
    for c in cands:
        code, fin, h = get('https://theorg.com/org/' + c, 'theorg_org')
        if not code.startswith('2'):
            continue
        j = nd(h)
        if not j:
            continue
        pp = j.get('props', {}).get('pageProps', {})
        comp = pp.get('initialCompany') or {}
        exts = [e.lower() for e in comp.get('extensions') or []]
        web = ((comp.get('social') or {}).get('websiteUrl') or '').lower()
        ok = bool(d) and (any(d.endswith(e) or e.endswith(d) for e in exts) or d in web or (web and dom(web) == d))
        if ok:
            return c, pp, fin
    return None, None, None


def positions_of(pp):
    out = {}
    def walk(o):
        if isinstance(o, dict):
            if o.get('fullName') and o.get('slug') and (o.get('role') or o.get('title')):
                out.setdefault(o['slug'], dict(name=o['fullName'], role=o.get('role') or o.get('title'),
                                               updated=(o.get('lastUpdate') or '')[:10]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(pp)
    return out


def person(org, slug):
    url = f'https://theorg.com/org/{org}/person/{slug}'
    code, fin, h = get(url, 'theorg_person')
    j = nd(h)
    if not j:
        return dict(url=url, http=code)
    pos = j['props']['pageProps'].get('initialPosition') or {}
    s = json.dumps(pos)
    li = ''
    mm = re.search(r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/[^"\\\s]+', s)
    if mm:
        li = mm.group(0).replace('http://', 'https://')
    loc = (pos.get('locationV2') or {}).get('locationString') or ''
    offices = '; '.join(filter(None, [(o.get('name') or '') + (' (' + ((o.get('locationV2') or {}).get('locationString') or '') + ')' if (o.get('locationV2') or {}).get('locationString') else '') for o in pos.get('offices') or []]))
    tl = [(r.get('role'), r.get('current'), (r.get('startDate') or {}).get('year')) for r in pos.get('roleTimeline') or []]
    cr = pos.get('currentRole')
    role = cr if isinstance(cr, str) else ((cr or {}).get('role') or (cr or {}).get('title') or '')
    return dict(url=url, http=code, name=pos.get('fullName') or '', role=role or pos.get('role') or '',
                updated=(pos.get('updatedAt') or '')[:10], loc_ny=('Y' if NY.search(loc) else ('N' if loc else '')),
                offices=offices, office_ny=('Y' if NY.search(offices) else ('N' if offices else '')), linkedin=li,
                timeline=json.dumps(tl)[:300])


def main():
    import pandas as pd
    st = pd.read_csv(os.path.join(W, 'stage1_offices.csv'), dtype=str, keep_default_na=False).set_index('row_id')
    ids = sys.argv[1:]
    rows = []
    done = set()
    if os.path.exists(OUT):
        for r in csv.DictReader(open(OUT, encoding='utf-8')):
            rows.append(r)
            done.add(r['row_id'])
    for rid in ids:
        if rid in done:
            continue
        o = st.loc[rid]
        org, pp, fin = find_org(o.company, o.website)
        if not org:
            rows.append(dict(row_id=rid, company=o.company, org='', role_found='', name='', role='', url='',
                             http='', updated='', loc_ny='', offices='', office_ny='', linkedin='', timeline='',
                             company_linkedin='', note='no The Org page matching the company domain'))
            print(rid, o.company, 'no org', flush=True)
            continue
        comp = pp.get('initialCompany') or {}
        cli = ((comp.get('social') or {}).get('linkedInUrl') or '')
        pos = positions_of(pp)
        for t in pp.get('initialTeams') or []:
            if TEAM.search(t.get('name') or '') and t.get('slug'):
                code, f2, h2 = get(f'https://theorg.com/org/{org}/teams/{t["slug"]}', 'theorg_team')
                j2 = nd(h2)
                if j2:
                    pos.update({k: v for k, v in positions_of(j2.get('props', {}).get('pageProps', {})).items() if k not in pos})
        keep = [(s, p) for s, p in pos.items() if ROLE.search(p['role'] or '') and not SKIP.search(p['role'] or '')]
        print(rid, o.company, org, len(pos), 'positions', len(keep), 'kept', flush=True)
        if not keep:
            rows.append(dict(row_id=rid, company=o.company, org=org, role_found='', name='', role='', url='',
                             http='', updated='', loc_ny='', offices='', office_ny='', linkedin='', timeline='',
                             company_linkedin=cli, note=f'{len(pos)} positions listed; none in the office, people or EA family'))
        for s, p in keep[:10]:
            d = person(org, s)
            rows.append(dict(row_id=rid, company=o.company, org=org, role_found=p['role'], name=d.get('name', p['name']),
                             role=d.get('role', ''), url=d['url'], http=d.get('http', ''), updated=d.get('updated', ''),
                             loc_ny=d.get('loc_ny', ''), offices=d.get('offices', ''), office_ny=d.get('office_ny', ''),
                             linkedin=d.get('linkedin', ''), timeline=d.get('timeline', ''), company_linkedin=cli, note=''))
        with open(OUT, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


if __name__ == '__main__':
    main()
