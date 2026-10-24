#!/usr/bin/env node
/*
  run-name-test.js: proves the identity survives a rename to a shorter or longer name.

    node tests/name-length/run-name-test.js

  For each test name it rebuilds the wordmark in a throwaway copy of the system (in the OS
  temp folder), renders the tent card and case label from that copy, and draws one test
  sheet per name plus a side-by-side comparison into tests/name-length/. The real
  wordmark/ and system/brand.js are never touched.
*/
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '../..');
const OUT = __dirname;
const CASES = [
  { slug: 'desk-drop', name: 'Desk Drop', brk: '' },
  { slug: 'dropp', name: 'Dropp', brk: '' },
  { slug: 'desk-drop-collective', name: 'Desk Drop Collective', brk: '' },
  { slug: 'desk-drop-collective-two-line', name: 'Desk Drop Collective', brk: 'Desk Drop|Collective' },
];

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}

const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'dd-name-test-'));
const results = [];
for (const c of CASES) {
  const site = path.join(tmpRoot, c.slug);
  // throwaway copy of the system: templates, tokens, fonts, runtime, brand.json, render scripts
  for (const d of ['templates', 'tokens', 'fonts', 'system', 'render']) copyDir(path.join(ROOT, d), path.join(site, d));
  const brand = JSON.parse(fs.readFileSync(path.join(ROOT, 'brand.json'), 'utf8'));
  brand.BRAND_NAME = c.name; brand.WORDMARK_LINE_BREAK = c.brk;
  fs.writeFileSync(path.join(site, 'brand.json'), JSON.stringify(brand, null, 2));
  execFileSync('node', [path.join(site, 'render/build-brand.js'), '--no-png'], { stdio: 'inherit' });
  const metrics = JSON.parse(fs.readFileSync(path.join(site, 'wordmark/wordmark-metrics.json'), 'utf8'));
  // render tent card + case label from the copy
  const tc = path.join(OUT, `${c.slug}-tent-card-face.png`);
  const cl = path.join(OUT, `${c.slug}-case-label.png`);
  execFileSync('node', [path.join(site, 'render/render.js'), path.join(site, 'templates/tent-card/tent-card.html'), path.join(ROOT, 'templates/tent-card/samples/SAMPLE-basic.json'), path.join(site, 'tc.pdf'), '--face-png', tc, '--dpi', '150'], { stdio: 'inherit' });
  execFileSync('node', [path.join(site, 'render/render.js'), path.join(site, 'templates/case-label/case-label.html'), path.join(ROOT, 'templates/case-label/samples/SAMPLE-office-and-reserve.json'), path.join(site, 'cl.pdf'), '--png', cl, '--dpi', '96'], { stdio: 'inherit' });
  const foot = path.join(site, 'foot.png');
  execFileSync('convert', [tc, '-gravity', 'SouthEast', '-crop', '1050x120+0+0', '+repage', foot]);
  results.push({ ...c, site, metrics, tc, cl, foot });
}

(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  const fontsCss = fs.readFileSync(path.join(ROOT, 'fonts/fonts.css'), 'utf8').replace(/url\("([^"]+)"\)/g, (m, f) => `url("data:font/ttf;base64,${fs.readFileSync(path.join(ROOT, 'fonts', f)).toString('base64')}")`);
  const b64 = (f) => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
  const svg = (r, f) => 'data:image/svg+xml;base64,' + fs.readFileSync(path.join(r.site, 'wordmark', f)).toString('base64');
  for (const r of results) {
    const aspect = r.metrics.horizontal_aspect_ratio;
    const html = `<html><head><style>${fontsCss}
      body{margin:0;font-family:"Atkinson Hyperlegible Next";color:#1F1D1A;background:#F7F3EA}
      .wrap{width:1500px;padding:28px 36px}
      h1{font:800 30px/1.1 "Bricolage Grotesque";margin:0 0 4px}
      .meta{font-size:15px;margin:0 0 18px;color:#3A3732}
      .row{display:flex;gap:28px;align-items:center;margin-bottom:18px}
      .tile{background:#fff;padding:22px;border:1px solid #E6E1D6}
      .dark{background:#1F1D1A}
      .cap{font-size:12px;color:#6B675F;margin-top:6px}
      .inline{font-size:16px}
      .inline b{font-family:"Bricolage Grotesque";font-weight:800;letter-spacing:-.01em}
      img{display:block}
    </style></head><body><div class="wrap">
      <h1>Name-length test: "${r.name}"${r.brk ? ' (two-line wordmark)' : ''}</h1>
      <p class="meta">Horizontal lockup aspect ${aspect}:1. ${r.metrics.advice}</p>
      <div class="row">
        <div><div class="tile"><img src="${svg(r, 'wordmark-light.svg')}" style="height:64px"></div><div class="cap">Horizontal, light, 64 px tall</div></div>
        <div><div class="tile dark"><img src="${svg(r, 'wordmark-dark.svg')}" style="height:64px"></div><div class="cap">Horizontal, dark</div></div>
        <div><div class="tile"><img src="${svg(r, 'wordmark-stacked-light.svg')}" style="height:120px"></div><div class="cap">Stacked, 120 px tall</div></div>
      </div>
      <div class="row">
        <div><div class="tile"><img src="${svg(r, 'wordmark-light.svg')}" style="height:18px"></div><div class="cap">Horizontal at 18 px (email signature size)</div></div>
        <div><div class="tile"><img src="${svg(r, 'symbol-light.svg')}" style="height:16px;float:left;margin-right:16px"><img src="${svg(r, 'symbol-light.svg')}" style="height:32px;float:left;margin-right:16px"><img src="${svg(r, 'symbol-light.svg')}" style="height:64px"></div><div class="cap">Symbol at 16, 32, 64 px (name-independent)</div></div>
        <div class="tile inline">Typeset name in running text: Thanks for talking with <b>${r.name}</b> today.</div>
      </div>
      <div class="row" style="align-items:flex-start">
        <div><img src="${b64(r.tc)}" style="width:700px;border:1px solid #ccc"><div class="cap">Tent card face (footer carries the wordmark)</div></div>
        <div><img src="${b64(r.cl)}" style="width:560px;border:1px solid #ccc"><div class="cap">Case labels (footer carries the wordmark)</div></div>
      </div>
    </div></body></html>`;
    await page.setViewportSize({ width: 1572, height: 1000 });
    await page.setContent(html, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(OUT, `${r.slug}-test-sheet.png`), fullPage: true });
  }
  // comparison of footers and lockups only
  const rows = results.map(r => `<div class="r"><div class="n">${r.name}${r.brk ? ' (2 lines)' : ''}</div>
      <div class="t"><img src="${svg(r, 'wordmark-light.svg')}" style="height:48px"></div>
      <div class="t"><img src="${svg(r, 'wordmark-stacked-light.svg')}" style="height:90px"></div>
      <div class="t dark"><img src="${svg(r, 'symbol-dark.svg')}" style="height:48px"></div>
      <div class="t" style="padding:0"><img src="${b64(r.foot)}" style="width:525px"></div></div>`).join('');
  await page.setViewportSize({ width: 1700, height: 800 });
  await page.setContent(`<html><head><style>${fontsCss}body{margin:0;background:#F7F3EA;font-family:"Atkinson Hyperlegible Next";padding:24px}
    .r{display:flex;gap:20px;align-items:center;margin-bottom:16px}.n{width:210px;font:700 16px/1.2 "Atkinson Hyperlegible Next"}
    .t{background:#fff;padding:14px;border:1px solid #E6E1D6}.dark{background:#1F1D1A}
    .foot{width:420px;height:70px;background-size:1050px auto;background-position:right -0px bottom -8px;background-repeat:no-repeat;padding:0}
    h1{font:800 26px "Bricolage Grotesque";margin:0 0 16px}</style></head><body><h1>Name-length comparison: lockups, symbol and tent-card footer</h1>${rows}</body></html>`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(OUT, 'name-length-comparison.png'), fullPage: true });
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results.map(r => ({ name: r.name, line_break: r.brk, aspect: r.metrics.horizontal_aspect_ratio, advice: r.metrics.advice })), null, 2));
  fs.rmSync(tmpRoot, { recursive: true, force: true });
  console.log('name-length test written to', OUT);
})().catch(e => { console.error(e); process.exit(1); });
