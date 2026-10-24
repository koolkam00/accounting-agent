#!/usr/bin/env node
/*
  build-avatar.js: the social avatar (LinkedIn, Slack, Gmail profile, Instagram), from the symbol.

    node render/build-avatar.js        (run from the desk-drop-identity folder)

  The avatar is the symbol alone (a box dropping onto a shelf), never the name, so it survives a
  rename and stays legible at 40 px. It is drawn inside the circle that most apps crop to.
  Writes avatar/avatar-<variant>-<size>.png and avatar/avatar-<variant>.svg for three variants:
    cobalt (default): white symbol on cobalt. Reads at 40 px on light and dark screens.
    paper: cobalt box, ink shelf on warm paper.
    ink: light-cobalt box, warm-white shelf on ink.
  Sizes: 1024 (Slack maximum), 512 (Slack minimum), 400 (LinkedIn Page logo), 320, 160, 80, 40.
  Sources: Slack help 115005506003, LinkedIn help a563309 (both opened 2026-10-24).
  Also writes avatar/test-sheet.png: every variant at 40 px and 24 px, circle and square crops,
  on a light and a dark app background.
*/
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'avatar');
fs.mkdirSync(OUT, { recursive: true });

// colors (tokens/tokens.json)
const C = { ink: '#1F1D1A', paperWarm: '#F7F3EA', white: '#FFFFFF', cobalt: '#2E47C9', cobaltLight: '#9AABFF' };
const VARIANTS = {
  cobalt: { bg: C.cobalt, box: C.white, bar: C.white },
  paper: { bg: C.paperWarm, box: C.cobalt, bar: C.ink },
  ink: { bg: C.ink, box: C.cobaltLight, bar: C.paperWarm },
};
const SIZES = [1024, 512, 400, 320, 160, 80, 40];

// The symbol geometry is the one in render/build-brand.js (symbolShapes), in a 96 x 100 box.
// It is read from the generated SVG so the avatar can never drift from the wordmark's symbol.
const symSvg = fs.readFileSync(path.join(ROOT, 'wordmark/symbol-mono-ink.svg'), 'utf8');
const rects = [...symSvg.matchAll(/<rect [^>]*\/>/g)].map((m) => m[0]);
if (rects.length !== 2) { console.error('symbol-mono-ink.svg: expected two shapes (shelf and box). Run node render/build-brand.js first.'); process.exit(1); }

function avatarSvg(v) {
  // 1000-unit canvas. The symbol (96 x 100 units) is scaled to 50% of the canvas height and centred
  // optically: its visual centre sits a little above the shelf, so it is nudged up 2%.
  const S = 1000, symH = 0.5 * S, k = symH / 100, w = 96 * k;
  const x = (S - w) / 2, y = (S - symH) / 2 - 0.02 * S;
  const shapes = rects.map((r, j) => r.replace(/fill="[^"]*"/, `fill="${j === 0 ? v.bar : v.box}"`)).join('');
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}" role="img" aria-label="Symbol">
<rect width="${S}" height="${S}" fill="${v.bg}"/>
<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${k.toFixed(4)})">${shapes}</g>
</svg>
`;
}

(async () => {
  const { chromium } = require('playwright');
  const b = await chromium.launch();
  const p = await b.newPage();
  for (const [name, v] of Object.entries(VARIANTS)) {
    const svg = avatarSvg(v);
    fs.writeFileSync(path.join(OUT, `avatar-${name}.svg`), svg);
    const url = 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
    for (const s of SIZES) {
      await p.setViewportSize({ width: s, height: s });
      await p.setContent(`<html><body style="margin:0"><img src="${url}" style="display:block;width:${s}px;height:${s}px"></body></html>`);
      await p.screenshot({ path: path.join(OUT, `avatar-${name}-${s}.png`), clip: { x: 0, y: 0, width: s, height: s } });
    }
  }
  // test sheet at true pixel size (1x), then the same sheet enlarged 3x without smoothing to inspect pixels
  const cell = (name, size, shape) => `<div style="display:flex;align-items:center;gap:8px;margin:6px 0;">
      <img src="avatar-${name}-400.png" style="width:${size}px;height:${size}px;border-radius:${shape === 'circle' ? '50%' : '22%'};display:block">
      <div style="font:600 13px/1.2 Arial;color:inherit">SAMPLE Founder<div style="font:400 12px/1.3 Arial;opacity:.7">${name}, ${size} px, ${shape}</div></div></div>`;
  const col = (bg, fg) => `<div style="background:${bg};color:${fg};padding:12px 16px;width:250px">${Object.keys(VARIANTS).map((n) => [40, 24].map((s) => ['circle', 'square'].map((sh) => cell(n, s, sh)).join('')).join('')).join('')}</div>`;
  const sheet = `<html><body style="margin:0;display:flex;font-family:Arial">${col('#FFFFFF', '#1D1C1D')}${col('#1A1D21', '#D1D2D3')}</body></html>`;
  const sheetFile = path.join(OUT, '_test-sheet.html');
  fs.writeFileSync(sheetFile, sheet);
  await p.setViewportSize({ width: 564, height: 900 });
  await p.goto('file://' + sheetFile);
  const h = await p.evaluate(() => document.body.scrollHeight);
  await p.setViewportSize({ width: 564, height: h });
  await p.screenshot({ path: path.join(OUT, 'test-sheet.png'), fullPage: true });
  fs.unlinkSync(sheetFile);
  await b.close();
  console.log(`Wrote avatar/: ${Object.keys(VARIANTS).length} variants x ${SIZES.length} sizes, SVGs and test-sheet.png`);
})().catch((e) => { console.error(e); process.exit(1); });
