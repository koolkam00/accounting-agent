#!/usr/bin/env python3
"""Every QR resolves to the right survey for the right office.

  python3 tests/test_links.py dry-run/zero dry-run/standard

For each dry-run folder: check the link tool's import file against the links list (same paths, same
destinations, no office names in titles or tags); decode every QR on the printed cards (kit/qr-check.txt is made by
make_kit.py from the card PDF itself) and every QR PNG made by make_links.py, follow each short
link through a local server that serves the drop's redirects file (the same lines a link tool or
Cloudflare Pages would serve), and check the landing address:
  - it is the campaign's own survey form (the form id in campaigns.survey_prefill_template),
  - its pre-filled card code is <campaign_id>.<office_id> for the card's office,
  - utm_medium is qr for the card link and post for the post link,
  - no back-half contains the company name.
"""
import csv
import glob
import http.client
import http.server
import json
import os
import subprocess
import sys
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tracker as TR  # noqa: E402

DECODE = r"""
const jsQR = require(process.argv[2] + '/jsqr'); const { PNG } = require(process.argv[2] + '/pngjs'); const fs = require('fs');
for (const f of process.argv.slice(3)) { const png = PNG.sync.read(fs.readFileSync(f));
  const r = jsQR(new Uint8ClampedArray(png.data), png.width, png.height); console.log(f + '\t' + (r ? r.data : 'NO DECODE')); }
"""


def serve(redirects):
    table = {}
    for line in open(redirects, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        src, dst, code = line.split()
        table[src] = (dst, int(code))

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in table:
                dst, code = table[self.path]
                self.send_response(code)
                self.send_header("Location", dst)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def resolve(srv, short_url):
    path = urllib.parse.urlparse(short_url).path
    c = http.client.HTTPConnection("127.0.0.1", srv.server_port, timeout=5)
    c.request("GET", path)
    r = c.getresponse()
    return r.status, r.getheader("Location")


def check_folder(folder):
    fails, n = [], 0
    trk = glob.glob(os.path.join(folder, "SAMPLE-tracker-*-final.xlsx"))[0]
    tr = TR.Tracker(trk)
    for red in glob.glob(os.path.join(folder, "links", "redirects-*.txt")):
        drop = os.path.basename(red)[len("redirects-"):-4]
        rows = list(csv.DictReader(open(os.path.join(folder, "links", "links-%s.csv" % drop), encoding="utf-8")))
        srv = serve(red)
        # 0. The Short.io import file (what the founder uploads) says exactly what the redirects say, and gives the
        #    link tool no office or company name (titles and tags carry IDs only).
        imp = {r["path"]: r for r in csv.DictReader(open(os.path.join(folder, "links", "shortio-import-%s.csv" % drop), encoding="utf-8"))}
        if set(imp) != {r["slug"] for r in rows}:
            fails.append("%s: import file paths differ from the links list" % drop)
        for r in rows:
            i = imp.get(r["slug"])
            if i and i["original_url"] != r["destination_url"]:
                fails.append("import %s points at %s, links list says %s" % (r["slug"], i["original_url"], r["destination_url"]))
            if i and (TR._s(r["company"]).lower() in (i["title"] + i["tags"]).lower()):
                fails.append("import %s names the office in title or tags" % r["slug"])
        # 1. QR images made by make_links.py
        pngs = sorted(glob.glob(os.path.join(folder, "links", "qr", "*.png")))
        js = os.path.join(folder, "links", "_decode.js")
        open(js, "w").write(DECODE)
        out = subprocess.run(["node", js, os.path.join(ROOT, "_work", "node", "node_modules")] + pngs, capture_output=True, text=True).stdout
        os.remove(js)
        decoded = {os.path.basename(l.split("\t")[0])[:-4]: l.split("\t")[1] for l in out.strip().splitlines()}
        # 2. QR codes on the printed cards (decoded from the card PDF by make_kit.py)
        printed = {}
        qc = os.path.join(folder, "kit", "qr-check.txt")
        for line in open(qc, encoding="utf-8"):
            parts = line.split()
            printed[(parts[3], parts[4])] = (parts[0], parts[8], parts[10])
        for r in rows:
            n += 1
            cid, oid, kind = r["campaign_id"], r["office_id"], r["link_type"]
            if tr.company_name and tr.company_name.lower().replace(" ", "") in r["slug"].lower().replace("-", ""):
                fails.append("company name in %s" % r["slug"])
            if kind == "qr":
                if decoded.get(r["slug"]) != r["short_url"]:
                    fails.append("QR png %s decodes to %s" % (r["slug"], decoded.get(r["slug"])))
                p = printed.get((oid, cid))
                if not p or p[0] != "OK" or p[1] != r["short_url"] or p[2] != r["short_url"]:
                    fails.append("printed card %s %s: %s" % (oid, cid, p))
            status, loc = resolve(srv, r["short_url"])
            if status != 302 or not loc:
                fails.append("%s does not redirect (%s)" % (r["short_url"], status))
                continue
            u = urllib.parse.urlparse(loc)
            q = urllib.parse.parse_qs(u.query)
            tpl = TR._s(tr.campaigns[cid]["survey_prefill_template"])
            form = urllib.parse.urlparse(tpl).path
            entry = [k for k in urllib.parse.parse_qs(urllib.parse.urlparse(tpl).query) if k.startswith("entry.")][0]
            if u.path != form:
                fails.append("%s lands on %s, not campaign %s's form %s" % (r["short_url"], u.path, cid, form))
            if q.get(entry) != ["%s.%s" % (cid, oid)]:
                fails.append("%s pre-fills %s, want %s.%s" % (r["short_url"], q.get(entry), cid, oid))
            if q.get("utm_medium") != [kind]:
                fails.append("%s utm_medium %s" % (r["short_url"], q.get("utm_medium")))
        srv.shutdown()
    return n, fails


def main(argv):
    total, bad = 0, []
    for folder in argv[1:]:
        n, f = check_folder(os.path.join(ROOT, folder) if not os.path.isabs(folder) else folder)
        total += n
        bad += f
        print("%s: %d links checked, %d failures" % (folder, n, len(f)))
    for b in bad[:30]:
        print("  FAIL " + b)
    print("PASS test_links" if not bad else "FAIL test_links")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
