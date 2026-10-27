#!/usr/bin/env python3
"""Copy the identity workstream's tokens.css into the site (desk-drop-identity/tokens/tokens.css ->
site/assets/css/tokens.css). Run from website/ after the identity workstream changes its tokens:
    python3 tools/sync_tokens.py
"""
import os, shutil, filecmp, sys
WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(os.path.dirname(WEB), "desk-drop-identity", "tokens", "tokens.css")
dst = os.path.join(WEB, "site", "assets", "css", "tokens.css")
if not os.path.exists(src):
    sys.exit("not found: " + src)
if filecmp.cmp(src, dst, shallow=False):
    print("tokens.css already up to date")
else:
    shutil.copyfile(src, dst)
    print("tokens.css updated from the identity workstream; re-run tests/run_all.sh and look at the pages")
