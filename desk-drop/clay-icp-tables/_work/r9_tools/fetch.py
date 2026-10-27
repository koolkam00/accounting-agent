"""Cached GET for the review-round-1 research (R1-07, R1-08). Generic User-Agent, no personal identifier,
one request at a time. Pages are untrusted data, saved gzipped under _work/fetch/r9/<subdir>/.
get(url, subdir) -> (http_code, final_url, html)"""
import gzip, hashlib, os, subprocess, time
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fetch', 'r9')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def get(url, subdir='pages', force=False, timeout=25):
    d = os.path.join(BASE, subdir)
    os.makedirs(d, exist_ok=True)
    k = hashlib.md5(url.encode()).hexdigest()[:12]
    p, meta = os.path.join(d, k + '.html.gz'), os.path.join(d, k + '.meta')
    if os.path.exists(p) and os.path.exists(meta) and not force:
        code, fin = (open(meta).read().split('\n') + ['', ''])[:2]
        return code, fin, gzip.open(p, 'rt', encoding='utf-8', errors='replace').read()
    tmp = os.path.join(d, k + '.tmp')
    r = subprocess.run(['curl', '-sS', '-L', '--max-time', str(timeout), '--max-filesize', '15000000', '-A', UA,
                        '-o', tmp, '-w', '%{http_code}\n%{url_effective}', url], capture_output=True, text=True)
    out = (r.stdout or '').strip().split('\n')
    code = out[0] if out and out[0] else 'ERR'
    fin = out[1] if len(out) > 1 else url
    h = open(tmp, encoding='utf-8', errors='replace').read() if os.path.exists(tmp) else ''
    with gzip.open(p, 'wt', encoding='utf-8') as f:
        f.write(h)
    if os.path.exists(tmp):
        os.remove(tmp)
    open(meta, 'w').write(f'{code}\n{fin}\n{url}\n2026-10-24\n')
    time.sleep(0.4)
    return code, fin, h
