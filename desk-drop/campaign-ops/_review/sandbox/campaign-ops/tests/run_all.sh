#!/usr/bin/env bash
# Every check for this folder. Run from campaign-ops/:  bash tests/run_all.sh [--dry-runs]
# --dry-runs also replays both SAMPLE dry runs day by day (about 40 minutes).
set -u
cd "$(dirname "$0")/.."
fail=0
step() { echo; echo "== $1"; shift; "$@" || fail=1; }
step "calendar"            python3 tests/test_opscal.py
step "build blank tracker" python3 tools/build_tracker.py --out _work/test-blank.xlsx
step "recalculate blank"   python3 tools/recalc.py _work/test-blank.xlsx
step "awkward rows"        python3 tests/test_edge_rows.py
if [ "${1:-}" = "--dry-runs" ]; then
  step "dry run zero"      python3 tools/dryrun.py zero
  step "dry run standard"  python3 tools/dryrun.py standard
fi
step "forms script"       node tests/test_forms_gs.js
step "intake mapping"     python3 tests/test_intake_mapping.py
step "outreach handoff"    python3 tests/test_e_handoff.py
step "links and QR"        python3 tests/test_links.py dry-run/zero dry-run/standard
step "office summaries"    python3 tests/test_office_summary.py
step "financial model"     python3 tests/test_h_import.py exports/SAMPLE-zero exports/SAMPLE-standard
step "folder rules"        python3 tests/check_folder.py
echo
[ $fail -eq 0 ] && echo "ALL PASS" || echo "SOMETHING FAILED"
exit $fail
