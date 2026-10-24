#!/usr/bin/env python3
"""Office summaries keep each person's answer private (legal pack file 13, D9 and D10).

  python3 tests/test_office_summary.py

From the standard dry run's final tracker (summaries written to a temporary folder):
  1. with the threshold as shipped (config office_summary_min_answers = 3), no summary quotes the SAMPLE name the
     survey comments contain ("Priya"), and every comment it quotes is word for word apart from [name removed];
  2. with the threshold set to 9 (as if the config cell said 9), every office-brand block with fewer than 9 answers shows the count only (no
     rating, no would-buy split, no comment), and no rating or would-buy split is drawn from fewer than 9 people.
"""
import glob
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_report as MR  # noqa: E402
import tracker as TR  # noqa: E402


def summaries(path, out, min_n=None):
    tr = TR.Tracker(path)
    if min_n is not None:
        tr.config["office_summary_min_answers"] = min_n   # as if the config cell said so
    MR.office_summaries(tr, "SAMPLE-DRP-002", out)
    return {os.path.basename(p): open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(out, "office-summary-*.md"))}, tr


def main():
    fails = []
    src = os.path.join(ROOT, "dry-run", "standard", "SAMPLE-tracker-standard-final.xlsx")
    tmp = tempfile.mkdtemp(prefix="ops_os_")
    s1, tr = summaries(src, os.path.join(tmp, "a"))
    comments = set()
    for cid in tr.campaigns:
        comments |= {x["comment"].strip() for x in (tr.response_rows(cid) or []) if x["comment"].strip()}
    if not any("Priya" in c for c in comments):
        fails.append("the SAMPLE survey no longer contains a name to test with")
    for fn, txt in s1.items():
        if "Priya" in txt:
            fails.append("%s quotes a name" % fn)
        for q in re.findall(r'^  "(.*)"$', txt, flags=re.M):
            if not MR.verbatim(q, list(comments)):
                fails.append("%s: %r is not word for word apart from [name removed]" % (fn, q))
    s2, _ = summaries(src, os.path.join(tmp, "b"), min_n=9)
    blocks = 0
    for fn, txt in s2.items():
        for block in txt.split("\n\n"):
            m = re.search(r"- (\d+) answers from your team", block)
            if not m:
                continue
            blocks += 1
            n = int(m.group(1))
            hidden = "Fewer than 9 answers" in block
            if n < 9 and (not hidden or "Average rating" in block or "Would buy" in block or 'word for word' in block):
                fails.append("%s: a block with %d answers is broken down" % (fn, n))
            if n >= 9 and hidden:
                fails.append("%s: a block with %d answers is hidden" % (fn, n))
            r = re.search(r"from (\d+) ratings", block)
            if r and int(r.group(1)) < 9:
                fails.append("%s: a rating from %s people is shown" % (fn, r.group(1)))
            if r is None and "Would buy" in block:
                fails.append("%s: a would-buy split without enough ratings" % fn)
    print("%d summaries, %d office-brand blocks checked at threshold 9" % (len(s2), blocks))
    for f in fails:
        print("  FAIL " + f)
    print("PASS test_office_summary" if not fails else "FAIL test_office_summary")
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
