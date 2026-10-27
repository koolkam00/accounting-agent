#!/usr/bin/env python3
"""Spot-check helper: open a URL (curl GET, generic User-Agent), save it under
_work/fetch/spotcheck/<round>/, and print short snippets around each search term.

    python3 -B peek.py r1 "<url>" "term one" "term two" ...

Never used for sec.gov (it demands a contact email) or LinkedIn (not opened).
"""
import hashlib
import html
import os
import re
import subprocess
import sys

import common as C

rnd, url, terms = sys.argv[1], sys.argv[2], sys.argv[3:]
if "sec.gov" in url or "linkedin.com" in url:
    print("SKIPPED (policy):", url)
    sys.exit(0)
d = os.path.join(C.WORK, "fetch", "spotcheck", rnd)
os.makedirs(d, exist_ok=True)
path = os.path.join(d, hashlib.md5(url.encode()).hexdigest()[:12] + ".html")
if not (os.path.exists(path) and os.path.getsize(path) > 500):
    r = subprocess.run(["curl", "-sS", "-L", "-m", "40", "-A", "Mozilla/5.0", "-o", path, "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    code = r.stdout.strip() or r.stderr.strip()[:80]
else:
    code = "cache"
h = open(path, encoding="utf-8", errors="ignore").read() if os.path.exists(path) else ""
t = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
raw = t
t = html.unescape(re.sub(r"<[^>]+>", " ", t))
t = re.sub(r"\s+", " ", t)
print(f"[{code}] {len(h)} bytes {url}")
for term in terms:
    ms = [m for m in re.finditer(re.escape(term), t, re.I)]
    if not ms:
        # JSON payloads keep text in scripts: search the raw page too
        ms2 = [m for m in re.finditer(re.escape(term), h, re.I)]
        if ms2:
            m = ms2[0]
            print(f"  ~ '{term}' (raw x{len(ms2)}): ...{h[max(0, m.start()-120):m.end()+120]}...")
        else:
            print(f"  - '{term}': not found")
        continue
    m = ms[0]
    print(f"  + '{term}' (x{len(ms)}): ...{t[max(0, m.start()-150):m.end()+150]}...")
