#!/usr/bin/env python3
"""Scan every brand that passed the gates for health-claim wording on its own pages.

History. Spot check round 7 found a top-60 brand whose homepage made a structure/function claim, so the
first version of this scan read every passed brand's homepage. Review round 1 (R1-01) then found eight
top-60 brands whose product pages, About or FAQ pages made explicit claims the homepage did not show
("Reishi supports a calm mood", "xylitol to fight cavities", "helps support gut health"). CONTRACTS
section 4: structure or function wording is an explicit health claim and is excluded.

What it reads now, per passed brand (curl GET, generic User-Agent, one request at a time, no personal
identifier, every page cached gzipped under _work/fetch/claims_scan/):
  1. the homepage;
  2. Shopify's public catalog, <site>/products.json?limit=250 (titles, descriptions and tags of every
     product), when the site is a Shopify store;
  3. up to six of the brand's own About, Our story, FAQ, Mission, Benefits, Ingredients or Science pages
     linked from the homepage, plus /pages/about and /pages/faq (Shopify) or /about and /faq (other sites).
Every candidate phrase is written with its page and context to _work/claims_scan_v2_2026-10-24.csv,
in three classes: 'claim' (structure or function, or disease wording), 'ingredient' (functional
ingredients that need a founder look even without a claim) and 'nutrient' (nutrient-content wording,
which CONTRACTS allows with founder review). A human verdict per brand goes into
_work/claims_verdicts_2026-10-24.csv; an 'exclude' verdict becomes a sourced row in
_work/stage3_corrections.csv. The scan itself changes nothing.
    python3 -B clay-icp-tables/_build/scan_claims.py            # all passed brands
    python3 -B clay-icp-tables/_build/scan_claims.py AB-070      # one brand
"""
import gzip
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

import pandas as pd

import common as C

OUT = os.path.join(C.WORK, "claims_scan_v2_2026-10-24.csv")
CACHE = os.path.join(C.WORK, "fetch", "claims_scan")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

VERB = (r"(?:supports?|support for|supporting|improves?|improving|promotes?|promoting|boosts?|boosting|aids?|"
        r"enhances?|strengthens?|regulates?|balances?|balancing|stabiliz\w+|reduces?|relieves?|fights?|"
        r"protects?|nourish(?:es)?|fuels? your|keeps? you|helps?(?: to)? (?:support|improve|regulate|reduce|boost|"
        r"balance|promote|ease|fight|protect|keep|calm|relieve|maintain))")
TARGET = (r"(?:gut|immune|immunity|digest\w*|brain|focus|metabolism|heart|mood|calm|sleep|stress|anxiety|"
          r"inflammation|blood sugar|glucose|cholesterol|cognitive|cognition|memory|hydration|recovery|skin|liver|"
          r"detox\w*|cavities|enamel|teeth|joints?|bones?|muscles?|hormones?|bloat\w*|gas|indigestion|"
          r"energy levels|sharp|alert\w*|libido|weight|appetite)")
CLAIM_PATS = [
    re.compile(VERB + r"\s+(?:your |a |healthy |natural |a healthy |the |overall |optimal )?(?:body'?s? )?"
               r"(?:\w+ ){0,2}?" + TARGET, re.I),
    re.compile(r"\bsupport(?:s|ing)?\b[^.!?]{0,40}\b(?:calm|mood|focus|energy|digest\w*|immun\w*|gut)\b", re.I),
    re.compile(r"gut[- ]health(?:y)?|immune support|immunity[- ]boost\w*|anti-inflammatory|stress[- ]reliev\w*|"
               r"blood sugar|bloating|improves? athletic|post-workout recovery|steady focus|no[- ]crash|"
               r"keeps? you sharp|fights? cavities|protects? (?:your )?enamel|detoxif\w*|mental clarity|"
               r"brain health|heart health|immune health|digestive health|hormone balanc\w*|balancing hormones|"
               r"(?:lowers?|reduces?) (?:cholesterol|blood pressure|inflammation)|weight loss", re.I),
    re.compile(r"not been evaluated by the (?:food and drug administration|fda)|"
               r"not intended to diagnose|supplement facts", re.I),
    re.compile(r"\b(?:diabetes|diabetic|glp-1|ibs|crohn'?s|dialysis|cancer|arthritis|alzheimer'?s|adhd)\b", re.I),
]
INGREDIENT_PAT = re.compile(r"adaptogen\w*|ashwagandha|reishi|lion.?s mane|cordyceps|chaga|l-theanine|theanine|"
                            r"valerian|l-tryptophan|tryptophan|nootropic\w*|rhodiola|ginseng|maca\b|kava|"
                            r"melatonin|\bcbd\b|\bthc\b|hemp extract|kratom|mushroom extract|functional mushroom\w*|"
                            r"probiotic\w*|prebiotic\w*|electrolyte\w*|collagen", re.I)
NUTRIENT_PAT = re.compile(r"\b\d+\s?g (?:of )?(?:protein|fiber|sugar)\b|\blow sugar\b|\bzero sugar\b|"
                          r"\bno added sugar\b|\bhigh[- ]protein\b|\bhigh[- ]fiber\b", re.I)
LINK_WORDS = re.compile(r"about|story|faq|mission|benefit|ingredient|science|why-|our-|learn|wellness|health", re.I)
SKIP_LINK = re.compile(r"cart|account|login|policy|policies|terms|privacy|shipping|refund|wholesale|blog/tagged|"
                       r"\.(?:jpg|png|pdf|svg)$", re.I)


def text(h):
    t = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def get(url):
    """Cached GET. Returns (http code or 'cache', body)."""
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest()[:12] + ".html.gz")
    meta = p + ".meta"
    if os.path.exists(p):
        code = open(meta).read().split()[0] if os.path.exists(meta) else "cache"
        return code, gzip.open(p, "rt", encoding="utf-8", errors="ignore").read()
    tmp = p[:-3]
    r = subprocess.run(["curl", "-sS", "-L", "-m", "30", "--max-filesize", "15000000", "-A", UA, "-o", tmp,
                        "-w", "%{http_code} %{url_effective}", url], capture_output=True, text=True)
    time.sleep(0.3)
    h = open(tmp, encoding="utf-8", errors="ignore").read() if os.path.exists(tmp) else ""
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(h)
    if os.path.exists(tmp):
        os.remove(tmp)
    code = (r.stdout or "ERR").strip() or "ERR"
    open(meta, "w").write(code + "\n" + url + "\n" + C.TODAY + "\n")
    return code.split()[0], h


def base_of(u):
    m = re.match(r"(https?://[^/]+)", u.strip())
    return m.group(1) if m else ""


def links(home_html, base):
    host = urllib.parse.urlparse(base).netloc.lower().replace("www.", "")
    out = []
    for href in re.findall(r'href="([^"#]+)"', home_html, re.I):
        u = urllib.parse.urljoin(base + "/", html.unescape(href))
        pu = urllib.parse.urlparse(u)
        if pu.netloc.lower().replace("www.", "") != host or pu.scheme not in ("http", "https"):
            continue
        path = pu.path.rstrip("/")
        if not path or SKIP_LINK.search(path) or "/products/" in path or "/collections/" in path:
            continue
        if LINK_WORDS.search(path):
            u = f"{pu.scheme}://{pu.netloc}{path}"
            if u not in out:
                out.append(u)
    out.sort(key=lambda u: (0 if re.search(r"about|faq|story", u, re.I) else 1, len(u)))
    return out[:6]


def scan_text(t, url, hits):
    for cls, pats in (("claim", CLAIM_PATS), ("ingredient", [INGREDIENT_PAT]), ("nutrient", [NUTRIENT_PAT])):
        for pat in pats:
            for m in pat.finditer(t):
                ph = m.group(0).lower().strip()
                key = (cls, ph)
                if key in hits:
                    continue
                hits[key] = dict(cls=cls, phrase=ph, url=url,
                                 context="..." + t[max(0, m.start() - 140):m.end() + 100].strip() + "...")


def products_text(body, base):
    """Shopify catalog -> list of (url, text)."""
    try:
        d = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(d, dict) or "products" not in d:
        return None
    out = []
    for p in d["products"]:
        t = " ".join([p.get("title", ""), text(p.get("body_html") or ""),
                      " ".join(p.get("tags", []) if isinstance(p.get("tags"), list) else [str(p.get("tags", ""))])])
        out.append((f"{base}/products/{p.get('handle', '')}", t))
    return out


def scan_brand(r):
    url = r.website if r.website.startswith("http") else ""
    row = dict(row_id=r.row_id, brand=r.company, rank=r.rank, website=url, shopify="", products=0, pages=0,
               pages_ok=0, claim_hits=0, ingredient_hits=0, nutrient_hits=0, claims="", ingredients="",
               nutrients="", evidence="", opened=C.TODAY)
    if not url:
        row["evidence"] = "no website"
        return row, []
    base = base_of(url)
    hits = {}
    code, home = get(url)
    row["pages"] += 1
    row["pages_ok"] += 1 if code.startswith("2") or code == "cache" else 0
    if home:
        scan_text(text(home), url, hits)
    pcode, pbody = get(base + "/products.json?limit=250")
    row["pages"] += 1
    prods = products_text(pbody, base) if pcode.startswith("2") or pcode == "cache" else None
    if prods is not None:
        row["shopify"] = "Y"
        row["products"] = len(prods)
        row["pages_ok"] += 1
        for pu, pt in prods:
            scan_text(pt, pu, hits)
    else:
        row["shopify"] = "N"
    extra = links(home or "", base)
    defaults = ["/pages/about", "/pages/faq"] if row["shopify"] == "Y" else ["/about", "/faq"]
    for d in defaults:
        u = base + d
        if not any(x.rstrip("/").lower() == u.lower() for x in extra):
            extra.append(u)
    for u in extra[:8]:
        c2, h2 = get(u)
        row["pages"] += 1
        if (c2.startswith("2") or c2 == "cache") and h2:
            row["pages_ok"] += 1
            scan_text(text(h2), u, hits)
    hl = list(hits.values())
    for cls in ("claim", "ingredient", "nutrient"):
        sel = [h for h in hl if h["cls"] == cls]
        row[f"{cls}_hits"] = len(sel)
        row[f"{cls}s"] = "; ".join(f"{h['phrase']} @ {h['url']}" for h in sel[:12])
    row["evidence"] = " || ".join(h["context"] for h in hl if h["cls"] == "claim")[:3000]
    return row, hl


def main():
    b = pd.read_csv(os.path.join(C.WORK, "stage1_brands.csv"), dtype=str, keep_default_na=False)
    b = b[b.gate_result == "pass"]
    only = set(sys.argv[1:])
    if only:
        b = b[b.row_id.isin(only)]
    rows, detail = [], []
    for k, r in enumerate(b.itertuples(), 1):
        row, hl = scan_brand(r)
        rows.append(row)
        for h in hl:
            detail.append(dict(row_id=r.row_id, brand=r.company, rank=r.rank, **h))
        print(k, r.row_id, r.company, row["shopify"], row["pages_ok"], "/", row["pages"],
              "claims", row["claim_hits"], "ingr", row["ingredient_hits"], flush=True)
    if not only:
        pd.DataFrame(rows).to_csv(OUT, index=False)
        pd.DataFrame(detail).to_csv(OUT.replace(".csv", "_hits.csv"), index=False)
        print("wrote", OUT)
    else:
        for d in detail:
            print(d["cls"], "|", d["phrase"], "|", d["url"], "|", d["context"][:300])


if __name__ == "__main__":
    main()
