"""Parse a cached The Org company page (untrusted data) and list positions.
Usage: python3 -I theorg_parse.py <file.html> [keyword ...]"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import _read

def walk(o, out):
    if isinstance(o, dict):
        if 'fullName' in o:
            out.append(o)
        for v in o.values():
            walk(v, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, out)

def positions(path):
    h = _read(path)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return None, []
    d = json.loads(m.group(1))
    out = []
    walk(d, out)
    seen = {}
    for p in out:
        key = (p.get('fullName'), p.get('role') or p.get('title'))
        if key not in seen:
            seen[key] = p
    comp = d.get('props', {}).get('pageProps', {}).get('initialCompany', {}) or {}
    return comp, list(seen.values())

if __name__ == '__main__':
    comp, ps = positions(sys.argv[1])
    kws = [k.lower() for k in sys.argv[2:]]
    if comp:
        print('COMPANY', comp.get('name'), comp.get('slug'), comp.get('extensions'), (comp.get('locationV2') or {}).get('locationString'))
    for p in ps:
        role = p.get('role') or p.get('title') or ''
        line = f"{p.get('fullName')} | {role} | {p.get('slug','')}"
        if not kws or any(k in role.lower() for k in kws):
            print(line)
