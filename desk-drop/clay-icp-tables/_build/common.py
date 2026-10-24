"""Shared helpers for the Clay ICP table builds (workstream A).

Paths are relative to desk-drop/. Nothing here writes outside clay-icp-tables/,
except _shared/geocode.py's own cache, which CONTRACTS section 5 sanctions.
"""
import json
import math
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # never leave .pyc files in B's folder

HERE = os.path.dirname(os.path.abspath(__file__))
A_DIR = os.path.dirname(HERE)                     # clay-icp-tables/
ROOT = os.path.dirname(A_DIR)                     # desk-drop/
B_DIR = os.path.join(ROOT, "cluster-1-flatiron")
WORK = os.path.join(A_DIR, "_work")
TODAY = "2026-10-24"

# B's grid and boundary code, imported read-only (no bytecode written).
sys.path.insert(0, os.path.join(B_DIR, "_build"))
import boundary as b_boundary  # noqa: E402


def blocks_outside(lat, lon):
    """B's ten-block measure: grid walking distance from the boundary in street blocks (79.4 m)."""
    return round(b_boundary.blocks_outside(float(lat), float(lon)), 1)


def inside(lat, lon):
    return b_boundary.inside(float(lat), float(lon))


def geocode(addr):
    """Run the project geocoder (sequential, cached). Returns dict or None."""
    try:
        out = subprocess.run([sys.executable, os.path.join(ROOT, "_shared", "geocode.py"), addr],
                             cwd=ROOT, capture_output=True, text=True, timeout=120)
        d = json.loads(out.stdout.strip().splitlines()[-1])
        if d.get("lat") is None:
            return None
        return d
    except Exception:
        return None


def num(s):
    """Parse a count such as '393', '130+', '4,082'. Returns int or None."""
    if s is None:
        return None
    m = re.search(r"(\d[\d,]*)", str(s))
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def load_registry(path):
    try:
        return json.load(open(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_registry(path, reg):
    json.dump(reg, open(path, "w"), indent=1, sort_keys=True)


def one_sentence(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(". ", "; ")
    if not s.endswith("."):
        s += "."
    return s[0].upper() + s[1:]
