#!/usr/bin/env python3
"""Write forms/build-forms.gs: the optional Apps Script, with spec/forms.json embedded.
  python3 tools/make_forms_gs.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = json.load(open(os.path.join(ROOT, "spec", "forms.json")))
tpl = open(os.path.join(ROOT, "forms", "build-forms.template.gs"), encoding="utf-8").read()
out = tpl.replace("/*SPEC*/null", json.dumps(spec, ensure_ascii=False))
open(os.path.join(ROOT, "forms", "build-forms.gs"), "w", encoding="utf-8").write(out)
print("wrote forms/build-forms.gs")
