#!/usr/bin/env bash
# Rebuild every workstream B deliverable from _work/ research files. Run from anywhere.
# Needs: python3 with pandas and openpyxl; node with playwright; a python with fontTools
# for the public SVG fonts (pass its path as $1; a scratch venv works: python3 -m venv v && v/bin/pip install fonttools).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$HERE")"
FTPY="${1:-python3}"
cd "$HERE"
python3 grid.py >/dev/null          # grid model from NYC street centerlines (_work/geo/streets_raw.geojson)
python3 assemble.py                 # merge, resolve, enrich, boundary flags  -> _build/out/master_*.csv
python3 build.py                    # IDs, tabs, route, walk                    -> CSVs in cluster-1-flatiron/
python3 stats.py >/dev/null         # numbers for Method, README, REPORT        -> _build/out/stats.json
python3 maps.py                     # GeoJSON, KML, private HTML map, route sheet
python3 public_map.py "$FTPY"       # public-map.svg
# per-brand landscape map for D's proposal (review round 1, R1-08): the SAMPLE layout test only.
# For a real brand: python3 public_map.py "$FTPY" --brand <slug> --stores <retailer_ids>  (writes brand-maps/<slug>.svg)
python3 public_map.py "$FTPY" --brand SAMPLE-brightside --stores B-R-011,B-R-010,B-R-025 --sample
# review round 3 (R3-02): label QA maps (D's long-name set, six stores, numbers-only) -> _build/out/qa/brand-map/ (render.js makes the PNGs)
mkdir -p out/qa/brand-map
{ python3 public_map.py "$FTPY" --brand SAMPLE-long-names --stores B-R-018,B-R-020,B-R-013,B-R-016 --sample --out-dir out/qa/brand-map
  python3 public_map.py "$FTPY" --brand SAMPLE-long-names-numbers-only --stores B-R-018,B-R-020,B-R-013,B-R-016 --sample --labels numbers --out-dir out/qa/brand-map
  python3 public_map.py "$FTPY" --brand SAMPLE-six-stores --stores B-R-011,B-R-012,B-R-013,B-R-014,B-R-015,B-R-016 --sample --out-dir out/qa/brand-map
  python3 public_map.py "$FTPY" --brand SAMPLE-brightside-numbers-only --stores B-R-011,B-R-010,B-R-025 --sample --labels numbers --out-dir out/qa/brand-map
} > out/qa/brand-map/brand_map_qa.txt
python3 xlsx.py                     # cluster-1-flatiron.xlsx
python3 pin_qa.py | head -3         # pin checks incl. the CSCL block-face test  -> _build/out/pin_qa.csv
NODE_PATH="$(npm root -g)" node render.js "$ROOT"   # public-map.png, route-private.png, QA screenshots
