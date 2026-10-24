/*
  brand-sync.js: keeps brand.json and system/brand.js in step for the two ways of filling in
  your details (v1.3, 2026-10-24, review round 2).

    Chrome only:  details.html saves a new system/brand.js (it carries "details_saved": "<date>").
    Terminal:     you edit brand.json and run node render/build-brand.js, which rewrites brand.js.

  adoptDetails(root, log), run before every terminal build. For each contact key:
    - brand.js has a value you filled in, brand.json still has the [PLACEHOLDER] (or nothing):
      the brand.js value is copied into brand.json. This is what keeps your details through a
      rename: editing BRAND_NAME makes brand.json the newer file, and in v1.2 that made the build
      skip the copy and write the placeholders back (review round 2, R2-04).
    - both are filled and differ: the newer file wins. brand.js counts as newer only when
      details.html saved it (details_saved) after brand.json last changed. Either way the build
      prints which value it kept.
    - brand.js has a placeholder: brand.json is left alone.
  An empty value ("") is a choice you made (the website left off), not a placeholder, except for
  FOUNDER_TITLE, where empty means the default "Founder".
  The name (BRAND_NAME) is never taken from brand.js: a rename always starts in brand.json.
*/
const fs = require('fs');
const path = require('path');

const KEYS = ['FOUNDER_NAME', 'FOUNDER_TITLE', 'PHONE', 'EMAIL', 'WEBSITE', 'DOMAIN', 'POSTAL_ADDRESS'];
const isPh = (v) => v == null || /\[[A-Z][A-Z0-9 ,.'&_\-/]*(?::[^\]]*)?\]/.test(String(v));
// FOUNDER_TITLE empty means the default ("Founder"), not a choice, so a filled title is never lost to it
const unfilled = (k, v) => isPh(v) || (k === 'FOUNDER_TITLE' && String(v).trim() === '');

function readBrandJs(file) {
  const src = fs.readFileSync(file, 'utf8');
  const m = /window\.DD_BRAND\s*=\s*(\{[\s\S]*\})\s*;?\s*$/.exec(src);
  if (!m) throw new Error(`${file} does not look like a brand.js file`);
  return JSON.parse(m[1]);
}

function adoptDetails(root, log) {
  log = log || (() => {});
  const jsonFile = path.join(root, 'brand.json');
  const jsFile = path.join(root, 'system/brand.js');
  if (!fs.existsSync(jsonFile) || !fs.existsSync(jsFile)) return false;
  let js;
  try { js = readBrandJs(jsFile); } catch (e) { log('NOTE    system/brand.js could not be read (' + e.message + '); brand.json is used.'); return false; }
  const brand = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
  const from = js.contact || {}, to = Object.assign({}, brand.contact || {});
  const jsNewer = !!js.details_saved && fs.statSync(jsFile).mtimeMs > fs.statSync(jsonFile).mtimeMs;
  const took = [], kept = [];
  for (const k of KEYS) {
    const a = from[k], b = to[k];
    if (a === undefined || unfilled(k, a) || a === b) continue;
    if (unfilled(k, b)) { to[k] = a; took.push(k); continue; }
    // both filled and different: the newer file wins, and the build says so
    if (jsNewer) { to[k] = a; took.push(k); log(`NOTE    ${k}: kept "${a}" from details.html (saved ${js.details_saved}), newer than brand.json's "${b}".`); }
    else { kept.push(k); log(`NOTE    ${k}: kept "${b}" from brand.json, newer than "${a}" in system/brand.js.`); }
  }
  if (!took.length) return false;
  brand.contact = to;
  fs.writeFileSync(jsonFile, JSON.stringify(brand, null, 2) + '\n');
  log(`Kept your details${js.details_saved ? ` saved from details.html on ${js.details_saved}` : ' from system/brand.js'} (${took.join(', ')}): copied into brand.json, so this build does not put the placeholders back.`);
  return true;
}

module.exports = { adoptDetails, readBrandJs, KEYS, isPh };
