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
// v1.4 (review round 3, R3-08): a JSON value "{color.ink}" is a reference; in tokens.css it is var(--dd-ink)
const refCss = (v) => { const m = /^\{color\.([\w-]+)\}$/.exec(String(v)); return m && json.color[m[1]] ? `var(${json.color[m[1]].css})` : null; };
(function walk(o) {
  if (o && typeof o === 'object') {
    if (o.css && o.$value !== undefined) {
      checked++;
      const want = refCss(o.$value) || (Array.isArray(o.$value) ? o.$value.map(f => /\s/.test(f) ? `"${f}"` : f).join(', ') : String(o.$value));
      const have = vars[o.css];
      if (have === undefined) problems.push(`${o.css} is in tokens.json but not in tokens.css`);
      else if (have.toLowerCase() !== want.toLowerCase()) problems.push(`${o.css}: css "${have}" vs json "${want}"`);
    }
    Object.values(o).forEach(walk);
  }
})(json);
// every custom property in the light block, aliases included (v1.4: aliases are no longer skipped),
// needs a tokens.json entry whose "css" is that name
const cssNames = new Set();
(function names(o) { if (o && typeof o === 'object') { if (o.css) cssNames.add(o.css); Object.values(o).forEach(names); } })(json);
for (const k of Object.keys(vars)) {
  if (!cssNames.has(k)) problems.push(`${k} is in tokens.css but has no tokens.json entry with "css": "${k}"${vars[k].startsWith('var(') ? ' (a semantic alias: add it to the "semantic" group)' : ''}`);
}
// the dark blocks: each role in tokens.css resolves to the hex tokens.json's dark-mode gives
{
  const hexOf = (v) => { v = v.trim(); const m = /^var\((--dd-[\w-]+)\)$/.exec(v); return m ? (vars[m[1]] || '').toLowerCase() : v.toLowerCase(); };
  const darkBlocks = [...css.matchAll(/(@media \(prefers-color-scheme: dark\)\s*\{\s*:root[^{]*|:root\[data-theme="dark"\])\s*\{([^}]*)\}/g)].map((m) => m[2]);
  if (darkBlocks.length !== 2) problems.push(`expected 2 dark blocks in tokens.css, found ${darkBlocks.length}`);
  darkBlocks.forEach((b, bi) => {
    for (const m of b.matchAll(/--dd-([\w-]+):\s*([^;]+);/g)) {
      const want = json['dark-mode'] && json['dark-mode'][m[1]];
      if (!want) problems.push(`dark block ${bi + 1}: --dd-${m[1]} has no dark-mode entry in tokens.json`);
      else if (hexOf(m[2]) !== String(want).toLowerCase()) problems.push(`dark block ${bi + 1}: --dd-${m[1]} is ${hexOf(m[2])} in tokens.css, ${want} in tokens.json`);
      checked++;
    }
  });
  for (const k of Object.keys(json.semantic || {})) if (!k.startsWith('$') && !(json['dark-mode'] || {})[k]) problems.push(`semantic role ${k} has no dark-mode value`);
}
// v1.3 (review round 2, R2-10): one custom property, one meaning. A name defined twice in the
// same block (or as a color in one block and a width in another) fails.
{
  const blocks = [...css.matchAll(/(:root[^{]*|@media[^{]*\{\s*:root[^{]*)\{([^}]*)\}/g)].map((m) => m[2]);
  const kind = (v) => /^(#|rgb|hsl|var\(--dd-(ink|paper|cobalt|stone|mist|apricot|placeholder|error|sample))/.test(v) ? 'color' : /^-?[\d.]+(px|pt|in|rem|em|%)?$/.test(v) ? 'dimension' : 'other';
  const seen = {};
  blocks.forEach((b, bi) => {
    const here = {};
    for (const m of b.matchAll(/(--dd-[\w-]+):\s*([^;]+);/g)) {
      if (here[m[1]]) problems.push(`${m[1]} is defined twice in the same block of tokens.css`);
      here[m[1]] = true;
      const k = kind(m[2].trim());
      if (seen[m[1]] && seen[m[1]] !== k && k !== 'other' && seen[m[1]] !== 'other') problems.push(`${m[1]} is a ${seen[m[1]]} in one block of tokens.css and a ${k} in another`);
      if (!seen[m[1]] || seen[m[1]] === 'other') seen[m[1]] = k;
    }
  });
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
console.log('PASS: tokens.css, tokens.json and build-brand.js agree (core colors, the eight light-mode semantic roles and both dark blocks); all text pairs meet WCAG 2.2 AA.');
