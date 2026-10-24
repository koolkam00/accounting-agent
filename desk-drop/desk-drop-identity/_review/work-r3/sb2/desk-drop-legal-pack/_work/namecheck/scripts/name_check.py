#!/usr/bin/env python3
"""Rerun the name-check log's automatable rows for any candidate name.

Usage (from the desk-drop/ folder):
    python3 desk-drop-legal-pack/_work/namecheck/scripts/name_check.py "Desk Drop" [outdir]

It prints a markdown summary and saves raw responses under outdir
(default: desk-drop-legal-pack/_work/namecheck/runs/<slug>-<UTC timestamp>/).

What it runs (read-only lookups, the same ones logged in 01-name-check-log.md):
  1. RDAP for <name>.com, <name>nyc.com, <name-with-hyphen>.com, <name>.net (Verisign)
     and <name>.nyc, <name>nyc.nyc (rdap.nic.nyc). 404 = no registry record.
  2. NY Department of State open data (data.ny.gov): active entities (n9v6-gdp6),
     all current and past entity names (ekwr-p59j), last-30-days filings (k4vb-judh).
  3. USPTO trademark search through headless Chromium (needs node + playwright):
     the phrase, the one-word spelling, both words in any order, and a wildcard.
What it cannot run: the Department of State web search (bot protection), the
.co lookup (no public RDAP server reachable), registrar prices, common-law use.
Those stay "founder to run". A search result never clears a name.
"""
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent


def curl(url, out, headers=None):
    cmd = ["curl", "-sS", "-L", "--max-time", "40", "-o", str(out), "-w", "%{http_code}", url]
    for h in headers or []:
        cmd[1:1] = ["-H", h]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # network trouble is reported, never hidden
        return f"error: {e}"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    name = sys.argv[1].strip()
    words = re.findall(r"[a-z0-9]+", name.lower())
    one = "".join(words)
    hyph = "-".join(words)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "runs" / f"{one}-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows = [f"# Name check run: {name} ({stamp})", "", "| Check | Query | Result | Raw file |", "| --- | --- | --- | --- |"]

    # 1. RDAP
    targets = [(f"{one}.com", "https://rdap.verisign.com/com/v1/domain/"),
               (f"{one}nyc.com", "https://rdap.verisign.com/com/v1/domain/"),
               (f"{one}.net", "https://rdap.verisign.com/net/v1/domain/"),
               (f"{one}.nyc", "https://rdap.nic.nyc/domain/"),
               (f"{one}nyc.nyc", "https://rdap.nic.nyc/domain/")]
    if hyph != one:
        targets.insert(2, (f"{hyph}.com", "https://rdap.verisign.com/com/v1/domain/"))
    for dom, base in targets:
        f = out / f"rdap_{dom}.json"
        code = curl(base + dom, f)
        detail = ""
        if code == "200":
            try:
                j = json.loads(f.read_text())
                ev = {e.get("eventAction"): e.get("eventDate") for e in j.get("events", [])}
                detail = f"registered {ev.get('registration', '?')}, expires {ev.get('expiration', '?')}"
            except Exception:
                detail = "registered (could not parse dates)"
        elif code == "404":
            detail = "no registry record (not proof it can be bought)"
        rows.append(f"| RDAP | {dom} | HTTP {code} {detail} | {f.name} |")

    # 2. NY DOS open data
    like_terms = {name.upper(), one.upper(), hyph.upper()}
    for ds, field, label in [("n9v6-gdp6", "current_entity_name", "Active entities"),
                             ("ekwr-p59j", "corp_name", "All entity names, current and past"),
                             ("k4vb-judh", "corp_name", "Filings, last 30 days")]:
        for term in sorted(like_terms):
            where = f"upper({field}) like '%{term}%'"
            url = f"https://data.ny.gov/resource/{ds}.json?" + urllib.parse.urlencode({"$where": where, "$limit": "200"})
            f = out / f"nydos_{ds}_{re.sub(r'[^A-Z0-9-]+', '_', term)}.json"
            code = curl(url, f)
            try:
                n = len(json.loads(f.read_text()))
            except Exception:
                n = "?"
            rows.append(f"| NY DOS open data: {label} | contains `{term}` | HTTP {code}, {n} rows | {f.name} |")
        if len(words) > 1:
            where = " AND ".join(f"upper({field}) like '%{w.upper()}%'" for w in words)
            url = f"https://data.ny.gov/resource/{ds}.json?" + urllib.parse.urlencode({"$where": where, "$limit": "200"})
            f = out / f"nydos_{ds}_allwords.json"
            code = curl(url, f)
            try:
                got = json.loads(f.read_text())
                names = "; ".join(sorted({r.get(field, "") for r in got}))[:300]
                n = len(got)
            except Exception:
                n, names = "?", ""
            rows.append(f"| NY DOS open data: {label} | all words | HTTP {code}, {n} rows {names} | {f.name} |")

    # 3. USPTO via headless Chromium
    node_path = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=node_path)
    qfile = out / "uspto_queries.json"
    queries = {
        "phrase_WM": {"query": {"match_phrase": {"WM": " ".join(words)}}},
        "oneword_WM": {"query": {"match": {"WM": one}}},
        "wildcard_WM": {"query": {"wildcard": {"WM": {"value": f"*{one}*"}}}},
        "wildcard_PM": {"query": {"wildcard": {"PM": {"value": f"*{one}*"}}}},
    }
    if len(words) > 1:
        queries["allwords_WM"] = {"query": {"bool": {"must": [{"match": {"WM": w}} for w in words]}}}
        queries["allwords_PM"] = {"query": {"bool": {"must": [{"match": {"PM": w}} for w in words]}}}
    qfile.write_text(json.dumps(queries))
    try:
        r = subprocess.run(["node", str(HERE / "tmsearch3.js"), str(out), str(qfile), "uspto_results.json"],
                           capture_output=True, text=True, timeout=240, env=env)
        res = json.loads((out / "uspto_results.json").read_text())
        for qn, v in res.items():
            try:
                j = json.loads(v["body"])
                hits = j["hits"]["hits"]
                live = [h for h in hits if h["source"].get("alive")]
                top = "; ".join(f"{h['source'].get('wordmark')} {h['id']} {'LIVE' if h['source'].get('alive') else 'dead'}" for h in hits[:6])
                rows.append(f"| USPTO | {qn} | total {j['hits']['totalValue']}, live in first 100: {len(live)}. {top} | uspto_results.json |")
            except Exception:
                rows.append(f"| USPTO | {qn} | HTTP {v.get('status')}, could not parse | uspto_results.json |")
    except Exception as e:
        rows.append(f"| USPTO | all | not run here ({e}); founder to run at https://tmsearch.uspto.gov | |")

    rows += ["", "Not run by this script, founder to run: NY Department of State web search "
             "(https://apps.dos.ny.gov/publicInquiry/), .co and other domains at a registrar, "
             "and a web and social search for businesses already using the name."]
    text = "\n".join(rows)
    (out / "summary.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
