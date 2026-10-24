#!/usr/bin/env node
/*
  allergen-size-sweep.js: TEST ONLY. Renders the 25-word allergen card with the allergen
  text forced to 11, 12, 13 and 14 pt, so the photo simulation can show which sizes stay
  legible. The production template has no way to change the locked size; this script
  overrides the token inside its own headless browser only.

    node tests/photo-sim/allergen-size-sweep.js
*/
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const ROOT = path.resolve(__dirname, '../..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'templates/tent-card/samples/SAMPLE-allergen-25-words.json'), 'utf8'));
const OUT = path.join(__dirname, 'out/sweep');
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  for (const pt of [11, 12, 13, 14]) {
    const ctx = await browser.newContext({ deviceScaleFactor: 300 / 96 });
    const page = await ctx.newPage();
    await page.addInitScript(({ data, pt }) => {
      window.__DD_DATA__ = data; window.__DD_HEADLESS__ = true;
      document.addEventListener('DOMContentLoaded', () => {
        const s = document.createElement('style');
        s.textContent = `:root{--dd-print-allergen-size:${pt}pt !important}`;
        document.head.appendChild(s);
      });
    }, { data, pt });
    await page.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
    await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
    const face = path.join(OUT, `face-${pt}pt.png`);
    await (await page.$('.face.front')).screenshot({ path: face });
    await ctx.close();
    execFileSync('node', [path.join(__dirname, 'photo-sim.js'), face, OUT, `${pt}pt`], { stdio: 'inherit' });
  }
  await browser.close();
  // one comparison strip per photo size: allergen crops stacked, 11 pt at the top
  for (const w of [2048, 1280]) {
    execFileSync('convert', [11, 12, 13, 14].map(pt => path.join(OUT, `close-${pt}pt-${w}-crop-allergen.png`)).concat(['-append', path.join(OUT, `compare-allergen-${w}.png`)]));
  }
  console.log('sweep done:', OUT);
})().catch(e => { console.error(e); process.exit(1); });
