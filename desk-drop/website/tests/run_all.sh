#!/usr/bin/env bash
# Runs every website check. From website/:  bash tests/run_all.sh   (add --no-lighthouse to skip the slow part)
# Needs: python3, node 22, Playwright with Chromium (global), and `npm install` once in tests/.
set -euo pipefail
cd "$(dirname "$0")/.."
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
echo "== 1. HTML validity";            tests/node_modules/.bin/html-validate -c tests/.htmlvalidate.json site/*.html && echo "0 problems"
echo "== 2. Static checks";            python3 tests/check_site.py | tail -1
echo "== 3. Code.gs contract";         node tests/test_code_gs.js | tail -1
echo "== 4. End to end (forms)";       node tests/e2e.js | tail -1
echo "== 5. Accessibility, keyboard, weight, layout"; node tests/quality.js | tail -1
if [[ "${1:-}" != "--no-lighthouse" ]]; then
  echo "== 6. Lighthouse";             node tests/lighthouse.js | tail -1
fi
echo "== 7. Screenshots"
python3 -m http.server 8131 --bind 127.0.0.1 --directory site >/dev/null 2>&1 & SHOT_PID=$!
trap 'kill "$SHOT_PID" 2>/dev/null || true' EXIT
sleep 1
node tests/shoot.js http://127.0.0.1:8131/ _shots light >/dev/null && node tests/shoot.js http://127.0.0.1:8131/ _shots dark >/dev/null && echo "_shots/ updated"
