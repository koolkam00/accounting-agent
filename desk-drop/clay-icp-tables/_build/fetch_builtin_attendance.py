#!/usr/bin/env python3
"""Free attendance enrichment, run only on office rows that passed the hard gates.

For each passed company row whose own sources (B's columns) include a Built In company
URL, open that company's Built In "offices" page once (curl GET, generic User-Agent,
1.5 s apart, cached in _work/fetch/builtin/) and read: the workplace type Built In shows
(OnSite / Hybrid / Remote), "Typical time on-site", and the tags on the recently posted
jobs ("In-Office", "Hybrid", "Remote"). Writes _work/attendance_builtin.csv.

Built In profiles are employer-edited and undated, so the signal carries the date opened.
No URL is guessed: rows without a Built In URL in their sources stay "unknown".
"""
import csv
import html
import os
import re
import subprocess
import time

import pandas as pd

import common as C

CACHE = os.path.join(C.WORK, "fetch", "builtin")
os.makedirs(CACHE, exist_ok=True)


def bi_url(r):
    for col in ("hq_source_url", "headcount_source_url", "address_source_url", "second_source_url",
                "headcount_second_source_url"):
        u = r.get(col, "") or ""
        m = re.match(r"https?://(?:www\.)?(builtin[a-z]*\.com)/company/([^/?#]+)", u)
        if m:
            return f"https://www.{m.group(1)}/company/{m.group(2)}/offices", m.group(2)
    return None, None


def fetch(url, slug):
    path = os.path.join(CACHE, f"{slug}_offices.html")
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return path, "cache"
    r = subprocess.run(["curl", "-sS", "-L", "-m", "40", "-A", "Mozilla/5.0", "-o", path, "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    time.sleep(1.5)
    return path, r.stdout.strip()


def parse(path):
    h = open(path, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\s+", " ", t)
    wt = None
    m = re.search(r"(OnSite Workplace|Hybrid Workspace|Remote Workspace|Remote Workplace|Hybrid Workplace|OnSite Workspace)", t)
    if m:
        wt = m.group(1)
    days = None
    m2 = re.search(r"Typical time on-site: ([^.]*?)(?: U\.S\.| Recently| International| Office Locations|$)", t)
    if m2:
        days = m2.group(1).strip()[:60]
    jobs = re.findall(r"(?:Ago|Today|Yesterday) Saved (In-Office|Hybrid|Remote|In-Office or Remote|Remote or Hybrid)", t)
    desc = ""
    m3 = re.search(r"(?:OnSite Workplace|Hybrid Workplace|Remote Workplace)(.*?)Typical time on-site", t)
    if m3:
        desc = m3.group(1).replace("Employees work from physical offices.", "").replace(
            "Employees engage in a combination of remote and on-site work.", "").strip()
    return wt, days, jobs, desc


WORDNUM = {"two": 2, "three": 3, "four": 4, "five": 5}


def days_from_desc(desc):
    """The employer's own policy sentence overrides the 'typical time' box when they disagree
    (spot check round 1: Radar says Monday-Thursday, PlayPlay 3 days, 1stDibs 'Flex First')."""
    d = desc.lower()
    if re.search(r"monday\s*(?:-|–|to|through)\s*thursday", d):
        return 4, "policy text: Monday to Thursday in office"
    if re.search(r"monday\s*(?:-|–|to|through)\s*wednesday", d):
        return 3, "policy text: Monday to Wednesday in office"
    N = r"(\d|two|three|four|five)"
    m = re.search(N + r"\s*(?:-|–|to)\s*" + N + r"[- ]days?\b", d)
    if m:
        a, b2 = [int(x) if x.isdigit() else WORDNUM[x] for x in m.groups()]
        return min(a, b2), f"policy text: {a} to {b2} days in person (lower figure used)"
    m = re.search(N + r"[- ]days? (?:a week |per week )?(?:at|in) (?:the )?office|" + N +
                  r"[- ]days? (?:a week |per week )?in[- ](?:office|person)|" + N + r" in-office days|hybrid " + N +
                  r" days|" + N + r"-days in the office", d)
    if m:
        w = next(x for x in m.groups() if x)
        n = int(w) if w.isdigit() else WORDNUM[w]
        return n, f"policy text: {n} days in the office"
    if re.search(r"twice a week", d):
        return 2, "policy text: twice a week"
    if re.search(r"tuesdays?,? wednesdays?,? and thursdays?", d):
        return 3, "policy text: Tuesday, Wednesday and Thursday in office"
    if re.search(r"flex first|teams to set the parameters", d):
        return 0, "policy text: teams set their own in-office days"
    return None, ""


def key_of(wt, days, jobs):
    d = (days or "").lower()
    n = re.search(r"(\d)", d)
    if wt and "onsite" in wt.lower().replace("-", ""):
        return "in-office-5" if (not n or n.group(1) == "5") else ("hybrid-4" if n.group(1) == "4" else "hybrid-3")
    if wt and "remote" in wt.lower():
        return "remote"
    if wt and "hybrid" in wt.lower():
        if n:
            k = int(n.group(1))
            return {5: "in-office-5", 4: "hybrid-4", 3: "hybrid-3"}.get(k, "hybrid-2-or-less")
        return "hybrid-unspecified"
    if jobs:
        if all(j == "In-Office" for j in jobs):
            return "in-office-5"
        if all(j == "Remote" for j in jobs):
            return "remote"
        return "hybrid-unspecified"
    return None


def main():
    offices = pd.read_csv(os.path.join(C.A_DIR, "offices.csv"), dtype=str, keep_default_na=False)
    passed = set(offices[(offices.gate_result == "pass") & (offices.org_type == "company")].b_id)
    raw = pd.concat([pd.read_csv(os.path.join(C.B_DIR, f), dtype=str, keep_default_na=False)
                     for f in ("companies.csv", "near_miss.csv")])
    rows = []
    for r in raw.to_dict("records"):
        if r["company_id"] not in passed:
            continue
        url, slug = bi_url(r)
        if not url:
            continue
        path, code = fetch(url, slug)
        wt = days = None
        jobs = []
        desc = ""
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            wt, days, jobs, desc = parse(path)
        k = key_of(wt, days, jobs)
        n, why = days_from_desc(desc)
        tue = "Y" if ((re.search(r"tuesday", desc, re.I) and not re.search(r"remote(?:ly)? (?:on )?tuesday", desc, re.I))
                      or re.search(r"monday\s*(?:-|–|to|through)\s*(?:wednesday|thursday)", desc, re.I)) else "N"
        if n is not None and k not in (None, "remote"):
            k2 = {5: "in-office-5", 4: "hybrid-4", 3: "hybrid-3", 0: "hybrid-unspecified"}.get(n, "hybrid-2-or-less")
            if k2 != k:
                days = f"{days} (box) but {why}"
                k = k2
        jt = {}
        for j in jobs:
            jt[j] = jt.get(j, 0) + 1
        text = "; ".join(x for x in [
            f"Built In workplace type: {wt}" if wt else "",
            f"typical time on-site: {days}" if days else "",
            ("recent job tags: " + ", ".join(f"{v} {k2}" for k2, v in jt.items())) if jt else ""] if x)
        rows.append(dict(company_id=r["company_id"], company=r["company_name"], url=url, http=code,
                         opened=C.TODAY, workplace_type=wt or "", typical_onsite=days or "",
                         job_tags=";".join(f"{k2}={v}" for k2, v in jt.items()), tuesday_named=tue,
                         policy_text=desc[:300],
                         attendance_key=k or "", attendance_text=text or "page opened; no attendance text found"))
        print(r["company_name"], code, k, text[:100], flush=True)
    with open(os.path.join(C.WORK, "attendance_builtin.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
