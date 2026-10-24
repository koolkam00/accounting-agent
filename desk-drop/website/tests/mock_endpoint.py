#!/usr/bin/env python3
"""Local stand-in for the Google Apps Script web app (apps-script/Code.gs), for tests only.

Same contract as Code.gs, and the same field rules: it reads the SCHEMA JSON straight out of
Code.gs, so the two cannot drift apart.

  POST /exec   form fields as application/x-www-form-urlencoded (plus form, form_version,
               submission_id, hp_url). Answers like Apps Script does: a 302 redirect to a
               one-time URL, which returns the JSON result. Accepted submissions append ONE row
               to <out>/office_intake.csv or <out>/brand_intake.csv (header = CONTRACTS 6.3
               columns, in order) and ONE line to <out>/notifications.log.
  GET  /exec   health check.
  GET  /count  analytics stub in GoatCounter's /count format: logs the query to
               <out>/analytics.log as one JSON line and returns a 1x1 GIF.

Run:  python3 tests/mock_endpoint.py --port 8787 --out tests/out/mock
"""
import argparse
import csv
import json
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_GS = os.path.join(os.path.dirname(HERE), "apps-script", "Code.gs")
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")
NOTIFY_TO = "founder@example.test"
RATE_LIMIT_PER_10_MIN = 30


def load_schema():
    src = open(CODE_GS, encoding="utf-8").read()
    m = re.search(r"/\*SCHEMA-JSON-START\*/(.*?)/\*SCHEMA-JSON-END\*/", src, re.S)
    if not m:
        sys.exit("SCHEMA markers not found in Code.gs")
    return json.loads(m.group(1))


SCHEMA = load_schema()
LOCK = threading.Lock()
SEEN = {}          # submission_id -> time
RATE = {}          # 10-minute bucket -> count
RESULTS = {}       # one-time redirect id -> JSON body

CTRL = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")


def clean(v, multiline):
    v = CTRL.sub("", str(v or "").replace("\r\n", "\n").replace("\r", "\n"))
    if multiline:
        v = "\n".join(line.rstrip() for line in v.replace("\t", " ").split("\n"))
        return re.sub(r"\n{3,}", "\n\n", v).strip()
    return re.sub(r"\s+", " ", v).strip()


def matches(row, when):
    return all(row.get(k) == v for k, v in when.items())


def validate(defn, params, multi):
    row, errors = {}, {}
    for name, spec in defn["fields"].items():
        if spec.get("type") == "list":
            vals = multi.get(name) or [params.get(name, "")]
            raw = ";".join(vals) if len(vals) > 1 else vals[0]
        else:
            raw = params.get(name, "")
        row[name] = clean(raw, bool(spec.get("multiline")))
    for d in defn.get("derived", []):
        if matches(row, d["when"]):
            row[d["target"]] = re.sub(r"\{(\w+)\}", lambda m: row.get(m.group(1), ""), d["template"])
    for name, spec in defn["fields"].items():
        v = row[name]
        needed = spec.get("required") is True or (spec.get("required_if") and matches(row, spec["required_if"]))
        if v == "":
            if needed:
                errors[name] = "required"
            continue
        t = spec.get("type")
        if t == "list":
            picked = [s.strip() for s in v.split(";") if s.strip()]
            if any(s not in spec["enum"] for s in picked):
                errors[name] = "invalid"
                continue
            row[name] = ";".join(s for s in spec["enum"] if s in picked)
            if row[name] == "" and needed:
                errors[name] = "required"
            continue
        if spec.get("enum") and v not in spec["enum"]:
            errors[name] = "invalid"
            continue
        if t == "int":
            digits = re.sub(r"[,\s]", "", v)
            if not re.fullmatch(r"\d{1,6}", digits):
                errors[name] = "invalid"
                continue
            n = int(digits)
            if n < spec["min_value"] or n > spec["max_value"]:
                errors[name] = "invalid"
                continue
            row[name] = n
            continue
        if spec.get("max") and len(v) > spec["max"]:
            errors[name] = "too_long"
            continue
        if t == "email" and not re.fullmatch(r"[^\s@<>()\",;:]+@[^\s@<>()\",;:]+\.[A-Za-z]{2,}", v):
            errors[name] = "invalid"
            continue
        if t == "phone" and not re.fullmatch(r"[0-9+().\-\s/x#ext]{7,40}", v, re.I):
            errors[name] = "invalid"
            continue
        if t == "url":
            if re.search(r"\s", v) or not re.fullmatch(r"(https?://)?[^/\s.]+\.[^\s]{2,}", v, re.I):
                errors[name] = "invalid"
                continue
            if not re.match(r"https?://", v, re.I):
                row[name] = "https://" + v
    return row, errors


def cell(v):
    if v is None:
        return ""
    if isinstance(v, int):
        return str(v)
    return "'" + v if re.match(r"[=+\-@]", v) else v


def handle(out_dir, params, multi):
    form = params.get("form", "")
    defn = SCHEMA["forms"].get(form)
    if not defn:
        return {"ok": False, "error": "unknown_form"}
    if params.get(SCHEMA["honeypot"], "").strip():
        return {"ok": True}
    row, errors = validate(defn, params, multi)
    if errors:
        return {"ok": False, "error": "validation", "fields": errors}
    version = params.get("form_version", "").strip()
    row["form_version"] = version if re.fullmatch(form + r"-\d{1,3}\.\d{1,3}", version) else form + "-unknown"
    row["source"] = "website"
    row["submitted_at"] = datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
    sub_id = params.get("submission_id", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{8,64}", sub_id):
        sub_id = ""
    with LOCK:
        if sub_id and sub_id in SEEN:
            return {"ok": True, "duplicate": True}
        bucket = int(time.time() // 600)
        if RATE.get(bucket, 0) >= RATE_LIMIT_PER_10_MIN:
            return {"ok": False, "error": "busy"}
        path = os.path.join(out_dir, defn["sheet"] + ".csv")
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        if not new:
            with open(path, newline="", encoding="utf-8") as f:
                header = next(csv.reader(f), [])
            if header != defn["columns"]:
                return {"ok": False, "error": "sheet_header_mismatch"}
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(defn["columns"])
            w.writerow([cell(row.get(c, "")) for c in defn["columns"]])
        with open(path, newline="", encoding="utf-8") as f:
            row_number = sum(1 for _ in csv.reader(f))
        RATE[bucket] = RATE.get(bucket, 0) + 1
        if sub_id:
            SEEN[sub_id] = time.time()
        subject = re.sub(r"\{(\w+)\}", lambda m: str(row.get(m.group(1), "")), defn["subject"])
        with open(os.path.join(out_dir, "notifications.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": row["submitted_at"], "to": NOTIFY_TO, "reply_to": row.get("contact_email", ""),
                                "subject": subject, "sheet": defn["sheet"], "row": row_number}) + "\n")
    return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    out_dir = "."

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        # Apps Script does not answer CORS preflight requests, so the site must never send one.
        # Logged so the end-to-end test can assert there were none.
        with LOCK, open(os.path.join(self.out_dir, "preflight.log"), "a", encoding="utf-8") as f:
            f.write(self.path + "\n")
        self._send(405, json.dumps({"ok": False, "error": "no_preflight"}))

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/count":
            q = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
            with LOCK, open(os.path.join(self.out_dir, "analytics.log"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), **q}) + "\n")
            return self._send(200, GIF, "image/gif")
        if u.path == "/result":
            rid = parse_qs(u.query).get("id", [""])[0]
            body = RESULTS.pop(rid, None)
            if body is None:
                return self._send(404, json.dumps({"ok": False, "error": "gone"}))
            return self._send(200, body)
        if u.path == "/exec":
            return self._send(200, json.dumps({"ok": True, "service": "website-intake", "forms": list(SCHEMA["forms"])}))
        return self._send(404, json.dumps({"ok": False}))

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/exec":
            return self._send(404, json.dumps({"ok": False}))
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype not in ("application/x-www-form-urlencoded", "text/plain", ""):
            result = {"ok": False, "error": "server"}
        else:
            multi = parse_qs(raw, keep_blank_values=True)
            params = {k: v[0] for k, v in multi.items()}
            try:
                result = handle(self.out_dir, params, multi)
            except Exception as err:  # noqa: BLE001
                print("mock error:", err, file=sys.stderr)
                result = {"ok": False, "error": "server"}
        rid = uuid.uuid4().hex
        RESULTS[rid] = json.dumps(result)
        # Apps Script answers a POST with a redirect to a one-time URL that holds the output.
        self._send(302, b"", "text/plain", {"Location": "/result?id=" + rid})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--out", default=os.path.join(HERE, "out", "mock"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    Handler.out_dir = a.out
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print("mock endpoint on http://127.0.0.1:%d/exec, writing to %s" % (a.port, a.out), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
