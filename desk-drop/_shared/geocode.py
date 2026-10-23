#!/usr/bin/env python3
"""Geocode a New York City street address, cached and rate limited.

Usage:
    python3 _shared/geocode.py "200 Fifth Avenue, New York, NY 10010"
    python3 _shared/geocode.py --batch addresses.txt   # one address per line, prints CSV

Primary source: NYC Planning Labs GeoSearch (geosearch.planninglabs.nyc), built on
the city's own address database (PAD). It returns the tax lot (BBL), which
identifies a building, so use `bbl` to deduplicate buildings. Fallback:
OpenStreetMap Nominatim, bounded to Manhattan below 60th Street. It is
rate limited to one request per second across the whole project.

Output is JSON: {"query", "lat", "lon", "label", "bbl", "match", "confidence",
"source"}. A miss prints lat and lon as null. Never invent coordinates for a miss.
Pass the street address only ("200 Fifth Avenue"); a business name in front of
it is stripped automatically.
"""
import fcntl
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "geocode_cache.json")
LOCK = os.path.join(HERE, ".geocode.lock")
STAMP = os.path.join(HERE, ".geocode.last")
UA = "desk-drop-cluster-research/0.1 (founder research)"
NOMINATIM_INTERVAL = 1.1
GEOSEARCH_INTERVAL = 0.25


def _load():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _get(url, interval):
    try:
        last = float(open(STAMP).read().strip())
    except (FileNotFoundError, ValueError):
        last = 0.0
    wait = interval - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    finally:
        open(STAMP, "w").write(str(time.time()))


def _street_only(address):
    m = re.search(r"\d", address)
    return address[m.start():] if m and m.start() > 0 else address


def _geosearch(address):
    text = _street_only(address)
    if "manhattan" not in text.lower():
        text = re.sub(r",?\s*New York,?\s*NY.*$", "", text, flags=re.I) + ", Manhattan"
    d = _get("https://geosearch.planninglabs.nyc/v2/search?" +
             urllib.parse.urlencode({"text": text, "size": 1}), GEOSEARCH_INTERVAL)
    feats = d.get("features") or []
    if not feats:
        return None
    f = feats[0]
    p = f.get("properties", {})
    pad = (p.get("addendum") or {}).get("pad") or {}
    lon, lat = f["geometry"]["coordinates"]
    return {"lat": lat, "lon": lon, "label": p.get("label"), "bbl": pad.get("bbl"),
            "match": p.get("match_type"), "confidence": p.get("confidence"),
            "source": "nyc-geosearch"}


def _nominatim(address):
    q = urllib.parse.urlencode({"q": _street_only(address), "format": "json", "limit": 1,
                                "countrycodes": "us", "viewbox": "-74.03,40.775,-73.955,40.695",
                                "bounded": 1})
    hits = _get(f"https://nominatim.openstreetmap.org/search?{q}", NOMINATIM_INTERVAL)
    if not hits:
        return None
    h = hits[0]
    return {"lat": float(h["lat"]), "lon": float(h["lon"]), "label": h.get("display_name"),
            "bbl": None, "match": h.get("osm_type"), "confidence": None, "source": "nominatim"}


def geocode(address):
    key = " ".join(address.lower().split())
    with open(LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cache = _load()
        if key in cache:
            return cache[key]
        result = {"query": address, "lat": None, "lon": None, "label": None, "bbl": None,
                  "match": None, "confidence": None, "source": None}
        errors = []
        for fn in (_geosearch, _nominatim):
            try:
                hit = fn(address)
            except Exception as e:  # network or policy failure: record, try the next source
                errors.append(f"{fn.__name__}: {e}")
                continue
            if hit:
                result.update(hit)
                break
        if errors and result["lat"] is None:
            result["error"] = "; ".join(errors)
            return result  # do not cache failures
        cache[key] = result
        tmp = CACHE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cache, f, indent=1, sort_keys=True)
        os.replace(tmp, CACHE)
        return result


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--batch":
        import csv
        w = csv.writer(sys.stdout)
        w.writerow(["query", "lat", "lon", "label", "bbl", "match", "confidence", "source"])
        for line in open(sys.argv[2]):
            a = line.strip()
            if a:
                r = geocode(a)
                w.writerow([a, r["lat"], r["lon"], r["label"], r["bbl"], r["match"],
                            r["confidence"], r["source"]])
    elif len(sys.argv) == 2:
        print(json.dumps(geocode(sys.argv[1])))
    else:
        print(__doc__)
        sys.exit(2)
