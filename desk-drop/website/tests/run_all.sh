#!/usr/bin/env bash
# Runs every website check. From website/:  bash tests/run_all.sh   (add --no-lighthouse to skip the slow part)
# Needs: python3, node 22, Playwright with Chromium (global), and `npm install` once in tests/.
# To keep a log:  bash tests/run_all.sh 2>&1 | tee tests/out/run_all.log
set -euo pipefail
cd "$(dirname "$0")/.."
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
mkdir -p tests/out/tmp
echo "== 1. HTML validity (site/ and a SAMPLE production copy)"
node -e "require('./tests/sample_build').buildSample(require('path').resolve('tests/out/tmp/publish-validate'))"
tests/node_modules/.bin/html-validate -c tests/.htmlvalidate.json site/*.html tests/out/tmp/publish-validate/*.html && echo "0 problems"
echo "== 2. Static checks";            python3 tests/check_site.py | tail -1
echo "== 2b. Publish gate and production copy"; python3 tests/test_preflight.py | tail -1
echo "== 3. Code.gs contract";         node tests/test_code_gs.js | tail -1
echo "== 4. End to end (forms, production copy)"; node tests/e2e.js | tail -1
echo "== 5. Accessibility, keyboard, weight, layout"; node tests/quality.js | tail -1
if [[ "${1:-}" != "--no-lighthouse" ]]; then
  echo "== 6. Lighthouse";             node tests/lighthouse.js | tail -1
fi
echo "== 7. Screenshots"
node tests/shoot.js site _shots light >/dev/null && node tests/shoot.js site _shots dark >/dev/null && echo "_shots/ updated"
echo "== 8. Publish preflight (blocks until the founder's steps in SETUP.md section 10 are done; informational here)"
python3 tools/preflight.py | tail -1 || true
echo "== all steps ran"
