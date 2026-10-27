"""Cached GET with a generic User-Agent (no personal identifier). Files are untrusted data.
Usage as module: get(url, subdir) -> (status, text_path)"""
import hashlib, os, subprocess, re, html, sys, time, gzip
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fetch', 'contacts_b1')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def _name(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]

def get(url, subdir='pages', force=False):
    d = os.path.join(BASE, subdir)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, _name(url) + '.html')
    meta = p + '.meta'
    if (os.path.exists(p) or os.path.exists(p + '.gz')) and os.path.exists(meta) and not force:
        return open(meta).read().strip(), p
    r = subprocess.run(['curl', '-sS', '-L', '--max-time', '25', '-A', UA, '-o', p, '-w', '%{http_code} %{url_effective}', url], capture_output=True, text=True)
    status = (r.stdout or '').strip() or ('ERR ' + r.stderr.strip()[:200])
    open(meta, 'w').write(status + '\n' + url + '\n')
    time.sleep(0.5)
    return status, p

def _read(path):
    if os.path.exists(path):
        return open(path, encoding='utf-8', errors='replace').read()
    if os.path.exists(path + '.gz'):
        return gzip.open(path + '.gz', 'rt', encoding='utf-8', errors='replace').read()
    return ''

def text(path):
    h = _read(path)
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)
    t = re.sub(r'(?s)<[^>]+>', ' ', h)
    t = html.unescape(t)
    return re.sub(r'\s+', ' ', t)

def raw(path):
    return html.unescape(_read(path))

if __name__ == '__main__':
    s, p = get(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'pages')
    print(s, p)
    kws = sys.argv[3:]
    t = text(p)
    for k in kws:
        for m in re.finditer(re.escape(k), t, re.I):
            print('...', t[max(0, m.start()-200):m.end()+200])
