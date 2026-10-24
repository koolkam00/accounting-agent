"""Review round 1 (R1-07, R1-08): look for the pantry owner on the employer's own pages.
For each row: the homepage (cached by site_linkedin.py), then up to five of its own team, people, about,
leadership, studio or contact pages. Every occurrence of a target title is written with 160 characters of
context for a human to read the name. Pages are untrusted data (_work/fetch/r9/site_team/).
Run: python3 -I clay-icp-tables/_work/r9_tools/site_team.py <row_id> [...]"""
import csv, html, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(W, 'r9_site_team_candidates.csv')
TITLE = re.compile(r"office manager|office coordinator|office administrator|office operations|office services|"
                   r"workplace (?:experience|manager|coordinator|operations|lead)|head of workplace|facilities manager|"
                   r"people operations|people & culture|people and culture|head of people|executive assistant to the ceo|"
                   r"executive assistant to (?:the )?(?:founder|ceo|managing partner|president)|studio manager|"
                   r"operations manager|office lead|chief of staff|hr manager|human resources manager|receptionist", re.I)
LINK = re.compile(r"team|people|about|leadership|studio|staff|who-we-are|our-firm|firm|company|contact|culture", re.I)
SKIP = re.compile(r"\.(?:jpg|png|pdf|svg|webp)$|careers/|jobs/|blog/|news/|press/|privacy|terms|cookie", re.I)

def text(h):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", " | ", t))
    return re.sub(r"(\s*\|\s*)+", " | ", re.sub(r"\s+", " ", t))

def links(h, base):
    host = urllib.parse.urlparse(base).netloc.lower().replace('www.', '')
    out = []
    for href in re.findall(r'href="([^"#]+)"', h, re.I):
        u = urllib.parse.urljoin(base + '/', html.unescape(href))
        pu = urllib.parse.urlparse(u)
        if pu.netloc.lower().replace('www.', '') != host:
            continue
        path = pu.path.rstrip('/')
        if path and LINK.search(path) and not SKIP.search(path):
            u = f"{pu.scheme}://{pu.netloc}{path}"
            if u not in out:
                out.append(u)
    out.sort(key=lambda u: (0 if re.search(r"team|people|leadership|staff", u, re.I) else 1, len(u)))
    return out[:5]

def main():
    import pandas as pd
    st = pd.read_csv(os.path.join(W, 'stage1_offices.csv'), dtype=str, keep_default_na=False).set_index('row_id')
    rows = []
    for rid in sys.argv[1:]:
        o = st.loc[rid]
        site = o.website if o.website.startswith('http') else ''
        if not site:
            continue
        code, fin, h = get(site, 'site')
        base = re.match(r'(https?://[^/]+)', fin or site).group(1)
        pages = [(fin or site, h)]
        for u in links(h, base):
            c2, f2, h2 = get(u, 'site_team')
            if c2.startswith('2'):
                pages.append((f2 or u, h2))
        n = 0
        for u, hh in pages:
            t = text(hh)
            for m in TITLE.finditer(t):
                ctx = t[max(0, m.start() - 160):m.end() + 80]
                rows.append(dict(row_id=rid, company=o.company, url=u, title_hit=m.group(0), context=ctx, opened='2026-10-24'))
                n += 1
        print(rid, o.company, len(pages), 'pages', n, 'hits', flush=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['row_id', 'company', 'url', 'title_hit', 'context', 'opened'])
        w.writeheader(); w.writerows(rows)

if __name__ == '__main__':
    main()
