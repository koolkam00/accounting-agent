#!/usr/bin/env python3
"""Re-query every Whole Foods store_selector link in brands.csv against the store-scoped
catalog (the same public endpoint the researchers used), one request at a time.

Spot check round 5 found a brand listed at NoMad on 2026-10-23 and absent on 2026-10-24,
so store catalogs move day to day. Output: _work/wfm_recheck_2026-10-24.csv, read by
build_brands.py: a store_selector link not found today becomes `unverified` with a note.
"""
import csv
import json
import os
import re
import subprocess
import time
import unicodedata
import urllib.parse

import pandas as pd

import common as C

STORES = {"Whole Foods Market Union Square": "10162", "Whole Foods Market NoMad": "10773",
          "Whole Foods Market Chelsea": "10131", "Whole Foods Market Manhattan West": "10713"}
OUT = os.path.join(C.WORK, "wfm_recheck_2026-10-24.csv")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ").replace("+", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    stop = {"the", "co", "company", "foods", "food", "snacks", "inc", "llc", "and", "brand", "brands", "new",
            "york", "chocolate", "chocolates", "homemade", "market", "candy"}
    return [w for w in s.split() if w not in stop and len(w) > 1]


def brand_match(ours, theirs):
    """Strict: one name's distinctive words are all in the other's ('Firehook' in 'Firehook Baked
    Crackers'), or the words run together match ('SuperSeedz' = 'Super Seedz'). A single shared
    word is not enough ('Vermont Nut Free' is not 'Vermont Creamery')."""
    a, b = set(norm(ours)), set(norm(theirs))
    if not a or not b:
        return False
    return a <= b or b <= a or "".join(norm(ours)) == "".join(norm(theirs))


def queries(ev, brand):
    qs = []
    for m in re.finditer(r"wholefoodsmarket\.com/(?:api/)?search\?text=([^&\s)]+)", ev or ""):
        q = urllib.parse.unquote(m.group(1)).strip()
        if q and q not in qs:
            qs.append(q)
    if not qs:
        qs = [" ".join(norm(brand)) or brand]
    return qs[:2]


def main():
    b = pd.read_csv(os.path.join(C.A_DIR, "brands.csv"), dtype=str, keep_default_na=False)
    links = pd.read_csv(os.path.join(C.WORK, "brand_store_links.csv"), dtype=str, keep_default_na=False)
    wl = links[(links.grade == "store_selector") & (links.store.str.startswith("Whole Foods"))]
    rows = []
    for (rid, brand), g in wl.groupby(["row_id", "brand"]):
        r = b[b.row_id == rid].iloc[0]
        qs = queries(r.retailer_evidence_urls, brand)
        for store in sorted(set(g.store)):
            code = next((v for k, v in STORES.items() if store.startswith(k)), None)
            if not code:
                continue
            found, names, used = False, [], ""
            for q in qs:
                u = ("https://www.wholefoodsmarket.com/api/search?text=" + urllib.parse.quote(q) +
                     f"&store={code}&limit=60&offset=0")
                res = subprocess.run(["curl", "-sS", "-m", "30", "-A", "Mozilla/5.0", u], capture_output=True, text=True)
                time.sleep(0.6)
                try:
                    d = json.loads(res.stdout)
                    hits = [x for x in d.get("results", []) if brand_match(brand, x.get("brand", ""))]
                except Exception:
                    hits = None
                used = u
                if hits is None:
                    names = ["request failed"]
                    continue
                if hits:
                    found, names = True, [f"{x['brand']}: {x['name']}" for x in hits[:3]]
                    break
            rows.append(dict(row_id=rid, brand=brand, store=store, store_code=code, query_url=used,
                             found_2026_10_24="Y" if found else ("unknown" if names == ["request failed"] else "N"),
                             matched=" | ".join(names)))
            print(brand, "|", store, "|", rows[-1]["found_2026_10_24"], "|", rows[-1]["matched"][:80], flush=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "links re-checked;", sum(1 for x in rows if x["found_2026_10_24"] == "N"), "not found")


def fixup():
    """Re-query only the links whose recorded hits fail the strict match (raw JSON cached)."""
    r = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    cache = os.path.join(C.WORK, "fetch", "wfm_recheck")
    os.makedirs(cache, exist_ok=True)
    changed = 0
    for i, x in r.iterrows():
        if x.found_2026_10_24 != "Y":
            continue
        hits = [h.split(": ")[0] for h in x.matched.split(" | ") if h]
        if any(brand_match(x.brand, h) for h in hits):
            continue
        res = subprocess.run(["curl", "-sS", "-m", "30", "-A", "Mozilla/5.0", x.query_url], capture_output=True, text=True)
        time.sleep(0.6)
        open(os.path.join(cache, f"{x.row_id}_{x.store_code}.json"), "w").write(res.stdout)
        try:
            d = json.loads(res.stdout)
            good = [y for y in d.get("results", []) if brand_match(x.brand, y.get("brand", ""))]
        except Exception:
            continue
        r.at[i, "found_2026_10_24"] = "Y" if good else "N"
        r.at[i, "matched"] = " | ".join(f"{y['brand']}: {y['name']}" for y in good[:3]) if good else \
            "strict re-match: no result carries this brand (first pass matched another brand)"
        changed += 1
        print(x.brand, x.store, r.at[i, "found_2026_10_24"], r.at[i, "matched"][:80])
    r.to_csv(OUT, index=False)
    print("re-matched", changed)


def aliases(brand):
    """The brand name plus any name in parentheses ('formerly Pipcorn', 'Candy Deluxe')."""
    out = [re.sub(r"\(.*?\)", "", brand).strip()]
    for m in re.findall(r"\(([^)]*)\)", brand):
        out.append(re.sub(r"^(formerly|aka|also|by)\s+", "", m.strip(), flags=re.I))
    return [a for a in out if a]


def retry_not_found():
    """Second pass for links not found: query by each brand alias as well, match on any alias."""
    r = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    cache = os.path.join(C.WORK, "fetch", "wfm_recheck")
    os.makedirs(cache, exist_ok=True)
    for i, x in r.iterrows():
        if x.found_2026_10_24 != "N":
            continue
        names = aliases(x.brand)
        qs = []
        for a in names + [" ".join(norm(a)) for a in names]:
            if a and a not in qs:
                qs.append(a)
        good = []
        for q in qs:
            u = ("https://www.wholefoodsmarket.com/api/search?text=" + urllib.parse.quote(q) +
                 f"&store={x.store_code}&limit=60&offset=0")
            res = subprocess.run(["curl", "-sS", "-m", "30", "-A", "Mozilla/5.0", u], capture_output=True, text=True)
            time.sleep(0.6)
            open(os.path.join(cache, f"{x.row_id}_{x.store_code}_{len(good)}.json"), "w").write(res.stdout)
            try:
                d = json.loads(res.stdout)
            except Exception:
                continue
            good = [y for y in d.get("results", []) if any(brand_match(a, y.get("brand", "")) for a in names)]
            if good:
                r.at[i, "query_url"] = u
                break
        if good:
            r.at[i, "found_2026_10_24"] = "Y"
            r.at[i, "matched"] = " | ".join(f"{y['brand']}: {y['name']}" for y in good[:3])
        else:
            r.at[i, "matched"] = "not in the store catalog on 2026-10-24 (queried by the research term and by brand name)"
        print(x.brand, x.store, r.at[i, "found_2026_10_24"], r.at[i, "matched"][:90])
    r.to_csv(OUT, index=False)


if __name__ == "__main__":
    import sys
    if "--retry" in sys.argv:
        retry_not_found()
        sys.exit(0)
    fixup() if "--fixup" in sys.argv else main()
