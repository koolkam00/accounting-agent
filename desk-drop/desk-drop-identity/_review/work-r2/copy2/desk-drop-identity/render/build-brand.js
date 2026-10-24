#!/usr/bin/env node
/*
  build-brand.js: rebuilds everything that carries the name, from brand.json.

  Usage (run from the desk-drop-identity folder):
    node render/build-brand.js                 rebuild wordmark/*.svg, wordmark/*.png, system/brand.js
    node render/build-brand.js --name "Dropp" --out tests/name-length/dropp
                                               test a different name without touching the real files
    node render/build-brand.js --no-png        skip PNG export (no Playwright needed)

  What it writes (all names are rename-proof, none contain the working name):
    wordmark/wordmark-light.svg     ink name + cobalt symbol, for light backgrounds
    wordmark/wordmark-dark.svg      warm-white name + light-cobalt symbol, for dark backgrounds
    wordmark/wordmark-mono-ink.svg  one color (ink), for one-color print, stamps, faxes
    wordmark/wordmark-mono-white.svg
    wordmark/wordmark-stacked-light.svg / -dark.svg   symbol above name, for square spaces
    wordmark/symbol-light.svg / symbol-dark.svg / symbol-mono-ink.svg   the name-independent mark
    wordmark/png/...                PNG exports of each at several widths, transparent and on white
    system/brand.js                 window.DD_BRAND for the HTML templates (file:// cannot read JSON)

  The name is converted to outlines (SVG paths) from fonts/static/Bricolage-96-Normal-800.ttf,
  so the SVGs render the same everywhere, with or without the font installed.
*/
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const opentype = require(path.join(ROOT, 'system/vendor/opentype-1.3.4.js'));

// ---------- args ----------
const args = process.argv.slice(2);
function arg(name, dflt) {
  const i = args.indexOf(name);
  if (i === -1) return dflt;
  const v = args[i + 1];
  return v === undefined || v.startsWith('--') ? true : v;
}
// details typed into details.html (Chrome only) and saved as system/brand.js come back into brand.json first
if (!args.includes('--out')) require('./brand-sync.js').adoptDetails(ROOT, console.log);
const brand = JSON.parse(fs.readFileSync(path.join(ROOT, 'brand.json'), 'utf8'));
const NAME = arg('--name', brand.BRAND_NAME);
const LINE_BREAK = arg('--break', brand.WORDMARK_LINE_BREAK || ''); // e.g. "Desk Drop|Collective"
const OUT = path.resolve(ROOT, arg('--out', '.'));
const WANT_PNG = !args.includes('--no-png');
const IS_TEST = OUT !== ROOT;

if (LINE_BREAK && LINE_BREAK.replace(/\|/g, ' ') !== NAME) {
  console.error(`WORDMARK_LINE_BREAK "${LINE_BREAK}" does not match BRAND_NAME "${NAME}" (with | read as a space). Fix brand.json.`);
  process.exit(1);
}
const LINES = LINE_BREAK ? LINE_BREAK.split('|') : [NAME];

// ---------- tokens (kept in step with tokens/tokens.json) ----------
const C = {
  ink: '#1F1D1A', paperWarm: '#F7F3EA', white: '#FFFFFF',
  cobalt: '#2E47C9', cobaltLight: '#9AABFF',
};

// ---------- geometry ----------
const FONT_FILE = path.join(ROOT, 'fonts/static/Bricolage-96-Normal-800.ttf');
const font = opentype.loadSync(FONT_FILE);
const UPM = font.unitsPerEm;
const CAP = font.tables.os2.sCapHeight / UPM; // 0.66 for this font
const FS = 100;                 // font size in SVG user units
const CAPH = CAP * FS;          // cap height in user units
const TRACK = -0.01 * FS;       // -1% tracking, matches .dd-brand-name
const LEADING = 1.02 * FS;      // baseline-to-baseline for two-line names

function fmt(n) { return Math.round(n * 100) / 100; }

// Text outline for one line, baseline at y=0, starting x=0. Returns {d, width, bbox}
function lineOutline(text) {
  // opentype.js applies kerning; we add tracking per glyph by laying glyphs out ourselves
  const glyphs = font.stringToGlyphs(text);
  let x = 0;
  const parts = [];
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (let i = 0; i < glyphs.length; i++) {
    const g = glyphs[i];
    const p = g.getPath(x, 0, FS);
    const bb = p.getBoundingBox();
    if (isFinite(bb.x1) && (bb.x2 - bb.x1) > 0) {
      minX = Math.min(minX, bb.x1); maxX = Math.max(maxX, bb.x2);
      minY = Math.min(minY, bb.y1); maxY = Math.max(maxY, bb.y2);
    }
    parts.push(p.toPathData(2));
    let adv = g.advanceWidth * FS / UPM;
    if (i < glyphs.length - 1) adv += font.getKerningValue(g, glyphs[i + 1]) * FS / UPM + TRACK;
    x += adv;
  }
  return { d: parts.join(''), width: x, bbox: { minX, maxX, minY, maxY } };
}

// The symbol: a box dropping onto a shelf. Name-independent, so it survives any rename.
// Built in a unit box where 1 = cap height. Origin bottom-left, y up (converted to SVG y-down).
function symbolShapes(h, x0, baseline, colors) {
  // h: total symbol height in user units (normally = cap height)
  const barH = 0.19 * h, barW = 0.96 * h, gap = 0.085 * h, tilt = -12; // degrees
  const s = (h - barH - gap) / (Math.cos(Math.PI * 12 / 180) + Math.sin(Math.PI * 12 / 180));
  const cx = x0 + barW / 2 + 0.03 * h;                  // box sits a touch right of centre, as if still sliding
  const boxBottom = baseline - barH - gap;             // lowest point of the tilted box
  const boxHalfDiag = s * (Math.cos(Math.PI * 12 / 180) + Math.sin(Math.PI * 12 / 180)) / 2;
  const cy = boxBottom - boxHalfDiag;
  const r = 0.035 * h;
  const bar = `<rect x="${fmt(x0)}" y="${fmt(baseline - barH)}" width="${fmt(barW)}" height="${fmt(barH)}" rx="${fmt(r)}" fill="${colors.bar}"/>`;
  const box = `<rect x="${fmt(cx - s / 2)}" y="${fmt(cy - s / 2)}" width="${fmt(s)}" height="${fmt(s)}" rx="${fmt(r * 1.2)}" fill="${colors.box}" transform="rotate(${tilt} ${fmt(cx)} ${fmt(cy)})"/>`;
  return { svg: bar + box, width: barW, height: h };
}

function svgDoc(w, h, body, title, pad = 0) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${fmt(-pad)} ${fmt(-pad)} ${fmt(w + 2 * pad)} ${fmt(h + 2 * pad)}" width="${fmt(w + 2 * pad)}" height="${fmt(h + 2 * pad)}" role="img" aria-label="${title.replace(/"/g, '&quot;')}">
<title>${title.replace(/</g, '&lt;')}</title>
${body}
</svg>
`;
}

// Horizontal lockup: symbol left, name right, symbol height = cap height of line 1 (one line)
// or the full text block height (two lines).
function horizontal(colors) {
  const outlines = LINES.map(lineOutline);
  const textW = Math.max(...outlines.map(o => o.bbox.maxX - Math.min(0, o.bbox.minX)));
  const top = Math.min(...outlines.map((o, i) => o.bbox.minY + i * LEADING)); // highest ink (may be ascender)
  const lastBaseline = (LINES.length - 1) * LEADING;
  const capTop = -CAPH;
  const blockTop = Math.min(top, capTop);
  const bottom = Math.max(...outlines.map((o, i) => o.bbox.maxY + i * LEADING), 0);
  const symH = LINES.length === 1 ? CAPH : (lastBaseline + CAPH);
  const sym = symbolShapes(symH, 0, lastBaseline, colors);
  const gap = 0.27 * CAPH;
  const tx = sym.width + gap;
  const textSvg = outlines.map((o, i) => `<path d="${o.d}" transform="translate(${fmt(tx)} ${fmt(i * LEADING)})" fill="${colors.text}"/>`).join('\n');
  const w = tx + textW;
  const h = bottom - blockTop;
  const body = `<g transform="translate(0 ${fmt(-blockTop)})">\n${sym.svg}\n${textSvg}\n</g>`;
  return { svg: svgDoc(w, h, body, NAME), w, h, capH: CAPH };
}

// Stacked lockup: symbol centred above name.
function stacked(colors) {
  const outlines = LINES.map(lineOutline);
  const widths = outlines.map(o => o.bbox.maxX);
  const textW = Math.max(...widths);
  const symH = 1.7 * CAPH;
  const symW = 0.96 * symH;
  const gap = 0.42 * CAPH;
  const w = Math.max(textW, symW);
  const sym = symbolShapes(symH, (w - symW) / 2, symH, colors);
  const firstTop = Math.min(outlines[0].bbox.minY, -CAPH);
  const textTop = symH + gap;
  const lines = outlines.map((o, i) => {
    const x = (w - widths[i]) / 2;
    const y = textTop - firstTop + i * LEADING;
    return `<path d="${o.d}" transform="translate(${fmt(x)} ${fmt(y)})" fill="${colors.text}"/>`;
  }).join('\n');
  const lastBottom = textTop - firstTop + (LINES.length - 1) * LEADING + Math.max(0, ...outlines.map(o => o.bbox.maxY));
  const h = lastBottom;
  return { svg: svgDoc(w, h, `${sym.svg}\n${lines}`, NAME), w, h };
}

function symbolOnly(colors, title) {
  const h = 100;
  const sym = symbolShapes(h, 0, h, colors);
  return { svg: svgDoc(sym.width, h, sym.svg, title), w: sym.width, h };
}

// ---------- write ----------
const WM = path.join(OUT, 'wordmark');
const PNG = path.join(WM, 'png');
fs.mkdirSync(PNG, { recursive: true });

const palettes = {
  light: { text: C.ink, bar: C.ink, box: C.cobalt },
  dark: { text: C.paperWarm, bar: C.paperWarm, box: C.cobaltLight },
  'mono-ink': { text: C.ink, bar: C.ink, box: C.ink },
  'mono-white': { text: C.white, bar: C.white, box: C.white },
};
const files = [];
function write(rel, content) { fs.writeFileSync(path.join(WM, rel), content); files.push(path.join('wordmark', rel)); }

const stats = {};
for (const [k, pal] of Object.entries(palettes)) {
  const hz = horizontal(pal);
  write(`wordmark-${k}.svg`, hz.svg);
  stats[`wordmark-${k}`] = { w: hz.w, h: hz.h };
  if (k === 'light' || k === 'dark') {
    const st = stacked(pal);
    write(`wordmark-stacked-${k}.svg`, st.svg);
    stats[`wordmark-stacked-${k}`] = { w: st.w, h: st.h };
  }
  if (k !== 'mono-white') {
    const sy = symbolOnly(pal, `${NAME} symbol`);
    write(`symbol-${k}.svg`, sy.svg);
    stats[`symbol-${k}`] = { w: sy.w, h: sy.h };
  }
}
const hz = stats['wordmark-light'];
const aspect = hz.w / hz.h;
fs.writeFileSync(path.join(WM, 'wordmark-metrics.json'), JSON.stringify({
  name: NAME, lines: LINES, generated: new Date().toISOString().slice(0, 10),
  font: 'Bricolage Grotesque 96pt ExtraBold (static instance), outlined',
  horizontal_aspect_ratio: Math.round(aspect * 100) / 100,
  cap_height_fraction_of_horizontal_height: Math.round(CAPH / hz.h * 1000) / 1000,
  cap_height_fraction_of_stacked_height: Math.round(CAPH / stats['wordmark-stacked-light'].h * 1000) / 1000,
  advice: aspect > 7 ? 'Horizontal lockup is wider than 7:1. Use the stacked lockup in square or narrow spaces, or set WORDMARK_LINE_BREAK.' : 'Horizontal lockup is within 7:1.',
  files: stats,
}, null, 2));

// brand.js for templates (only for the real build, not for test names)
if (!IS_TEST || args.includes('--brand-js')) {
  const js = `/* GENERATED by render/build-brand.js from brand.json on ${new Date().toISOString().slice(0, 10)}.
   Do not edit by hand. Your details: open details.html in Chrome (no terminal needed), or edit brand.json and rebuild.
   A rename: edit BRAND_NAME in brand.json and run bash render/build-pdfs.sh (needs the terminal once). */
window.DD_BRAND = ${JSON.stringify({ ...brand, BRAND_NAME: NAME, WORDMARK_LINES: LINES, wordmark_aspect: Math.round(aspect * 100) / 100, wordmark_cap_fraction: Math.round(CAPH / hz.h * 1000) / 1000 }, null, 2)};
`;
  fs.mkdirSync(path.join(OUT, 'system'), { recursive: true });
  fs.writeFileSync(path.join(OUT, 'system/brand.js'), js);
  files.push('system/brand.js');
}

async function pngs() {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const jobs = [];
  const widths = { wordmark: [600, 1200, 2400], 'wordmark-stacked': [600, 1200], symbol: [64, 256, 1024] };
  for (const f of fs.readdirSync(WM).filter(f => f.endsWith('.svg'))) {
    const base = f.replace('.svg', '');
    const fam = base.startsWith('symbol') ? 'symbol' : base.startsWith('wordmark-stacked') ? 'wordmark-stacked' : 'wordmark';
    for (const w of widths[fam]) {
      jobs.push({ f, base, w, bg: null });
      if (base.endsWith('light') || base.endsWith('mono-ink')) jobs.push({ f, base, w, bg: '#FFFFFF' });
      if (base.endsWith('dark') || base.endsWith('mono-white')) jobs.push({ f, base, w, bg: C.ink });
    }
  }
  for (const j of jobs) {
    const svg = fs.readFileSync(path.join(WM, j.f), 'utf8');
    const m = svg.match(/viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"/);
    const vw = +m[3], vh = +m[4];
    const pad = j.bg ? Math.round(j.w * 0.08) : 0;
    const innerW = j.w - 2 * pad;
    const innerH = Math.round(innerW * vh / vw);
    const H = innerH + 2 * pad;
    await page.setViewportSize({ width: j.w, height: H });
    const b64 = Buffer.from(svg).toString('base64');
    await page.setContent(`<html><body style="margin:0;background:${j.bg || 'transparent'}"><img src="data:image/svg+xml;base64,${b64}" style="display:block;width:${innerW}px;height:${innerH}px;margin:${pad}px"></body></html>`);
    const suffix = j.bg ? (j.bg === '#FFFFFF' ? '-on-white' : '-on-ink') : '';
    const out = path.join(PNG, `${j.base}${suffix}-${j.w}w.png`);
    await page.screenshot({ path: out, omitBackground: !j.bg, clip: { x: 0, y: 0, width: j.w, height: H } });
    files.push(path.relative(OUT, out));
  }
  await browser.close();
}

(async () => {
  if (WANT_PNG) await pngs();
  console.log(`Built ${files.length} files for "${NAME}" in ${path.relative(process.cwd(), OUT) || '.'} (horizontal aspect ${aspect.toFixed(2)}:1)`);
})().catch(e => { console.error(e); process.exit(1); });
