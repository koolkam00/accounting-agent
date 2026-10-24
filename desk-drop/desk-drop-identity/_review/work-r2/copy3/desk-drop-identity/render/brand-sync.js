/*
  brand-sync.js: keeps brand.json and system/brand.js in step for the two ways of filling in
  your details (v1.2, 2026-10-24, review round 1).

    Chrome only:  details.html saves a new system/brand.js (it carries "details_saved": "<date>").
    Terminal:     you edit brand.json and run node render/build-brand.js, which rewrites brand.js.

  adoptDetails(root, log): when system/brand.js was saved by details.html AFTER brand.json last
  changed, and its contact details differ, copy those details into brand.json, so a later terminal
  build keeps them instead of putting the placeholders back. The name (BRAND_NAME) is never taken
  from brand.js: a rename always starts in brand.json.
*/
const fs = require('fs');
const path = require('path');

const KEYS = ['FOUNDER_NAME', 'FOUNDER_TITLE', 'PHONE', 'EMAIL', 'WEBSITE', 'DOMAIN', 'POSTAL_ADDRESS'];

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
  if (!js.details_saved) return false;
  if (fs.statSync(jsFile).mtimeMs <= fs.statSync(jsonFile).mtimeMs) return false;
  const brand = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
  const from = js.contact || {}, to = brand.contact || {};
  const changed = KEYS.filter((k) => from[k] !== undefined && from[k] !== to[k]);
  if (!changed.length) return false;
  changed.forEach((k) => { to[k] = from[k]; });
  brand.contact = to;
  fs.writeFileSync(jsonFile, JSON.stringify(brand, null, 2) + '\n');
  log(`Took your details saved from details.html on ${js.details_saved} (${changed.join(', ')}) into brand.json.`);
  return true;
}

module.exports = { adoptDetails, readBrandJs, KEYS };
