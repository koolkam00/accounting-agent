#!/usr/bin/env node
/*
  check-tokens.js: fails (exit 1) if tokens/tokens.css, tokens/tokens.json and the colors baked
  into render/build-brand.js have drifted apart, or if a color pair used for text falls under
  WCAG 2.2 contrast minimums (4.5:1 text, 3:1 large text and graphics).

    node tests/check-tokens.js
*/
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const css = fs.readFileSync(path.join(ROOT, 'tokens/tokens.css'), 'utf8');
const json = JSON.parse(fs.readFileSync(path.join(ROOT, 'tokens/tokens.json'), 'utf8'));
const build = fs.readFileSync(path.join(ROOT, 'render/build-brand.js'), 'utf8');

// first :root block only (the light defaults)
const rootBlock = css.slice(css.indexOf(':root {'), css.indexOf('}', css.indexOf(':root {')));
const vars = {};
for (const m of rootBlock.matchAll(/(--dd-[\w-]+):\s*([^;]+);/g)) vars[m[1]] = m[2].trim();

const problems = [];
let checked = 0;
(function walk(o) {
  if (o && typeof o === 'object') {
    if (o.css && o.$value !== undefined) {
      checked++;
      const want = Array.isArray(o.$value) ? o.$value.map(f => /\s/.test(f) ? `"${f}"` : f).join(', ') : String(o.$value);
      const have = vars[o.css];
      if (have === undefined) problems.push(`${o.css} is in tokens.json but not in tokens.css`);
      else if (have.toLowerCase() !== want.toLowerCase()) problems.push(`${o.css}: css "${have}" vs json "${want}"`);
    }
    Object.values(o).forEach(walk);
  }
})(json);
for (const k of Object.keys(vars)) {
  if (vars[k].startsWith('var(')) continue; // semantic aliases
  if (!JSON.stringify(json).includes(`"${k}"`)) problems.push(`${k} is in tokens.css but not in tokens.json`);
}
// build-brand.js color constants
const pairs = { ink: 'ink', paperWarm: 'paper-warm', cobalt: 'cobalt', cobaltLight: 'cobalt-light' };
for (const [jsKey, tok] of Object.entries(pairs)) {
  const m = build.match(new RegExp(jsKey + ":\\s*'(#[0-9A-Fa-f]{6})'"));
  if (!m) problems.push(`build-brand.js has no ${jsKey} color`);
  else if (m[1].toLowerCase() !== json.color[tok].$value.toLowerCase()) problems.push(`build-brand.js ${jsKey} ${m[1]} vs tokens ${json.color[tok].$value}`);
}
// contrast
const lum = (h) => { const c = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const C = Object.fromEntries(Object.entries(json.color).map(([k, v]) => [k, v.$value]));
const textPairs = [['ink', 'paper', 4.5], ['ink', 'paper-warm', 4.5], ['stone', 'paper', 4.5], ['stone', 'paper-warm', 4.5], ['paper', 'cobalt', 4.5], ['cobalt', 'paper', 4.5], ['ink', 'placeholder', 4.5], ['ink', 'cobalt-tint', 4.5], ['cobalt-light', 'ink', 4.5], ['paper-warm', 'ink', 4.5], ['ink', 'apricot', 4.5], ['paper', 'sample', 4.5]];
const contrast = textPairs.map(([f, b, min]) => { const r = ratio(C[f], C[b]); if (r < min) problems.push(`contrast ${f} on ${b} ${r.toFixed(2)} < ${min}`); return `${f} on ${b}: ${r.toFixed(2)}:1`; });

console.log(`checked ${checked} tokens; contrast: ${contrast.join('; ')}`);
if (problems.length) { console.log('FAIL\n' + problems.map(p => '  ' + p).join('\n')); process.exit(1); }
console.log('PASS: tokens.css, tokens.json and build-brand.js agree; all text pairs meet WCAG 2.2 AA.');
