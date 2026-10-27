#!/usr/bin/env node
/*
  render-page.js: print any static HTML page in this folder (spec sheets, guides, one-pagers)
  to PDF, using the page's own @page size. For data-driven templates use render.js instead.
  Exit 2 if a .page is clipped (its text runs past the bottom edge), v1.4.

    node render/render-page.js <page.html> <out.pdf> [--png out.png] [--dpi 110]
*/
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
const pos = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1] || '').startsWith('--'));
const opt = (k) => { const i = args.indexOf('--' + k); return i === -1 ? null : args[i + 1]; };
if (pos.length < 2) { console.error('usage: node render/render-page.js <page.html> <out.pdf> [--png out.png] [--dpi n]'); process.exit(1); }
(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const dpi = Number(opt('dpi') || 110);
  const page = await browser.newPage({ deviceScaleFactor: dpi / 96, viewport: { width: 816, height: 1056 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('requestfailed', r => errors.push('failed to load ' + r.url()));
  await page.goto('file://' + path.resolve(pos[0]), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (errors.length) { console.error(errors.join('\n')); await browser.close(); process.exit(2); }
  fs.mkdirSync(path.dirname(path.resolve(pos[1])), { recursive: true });
  await page.emulateMedia({ media: 'print' });
  // v1.4 (review round 3): a spec page whose text runs past its bottom is cut off by overflow:
  // hidden and nobody sees it. Refuse instead, saying which page and by how much.
  // The content may use the bottom padding, but must end above the page's footer (.foot) and
  // above the page's edge.
  const clipped = await page.evaluate(() => [...document.querySelectorAll('.page')].map((p, k) => {
    const pr = p.getBoundingClientRect();
    const foot = p.querySelector(':scope > .foot');
    const limit = foot ? foot.getBoundingClientRect().top - 2 : pr.bottom;
    const bottom = [...p.children].filter((c) => c !== foot && getComputedStyle(c).position !== 'absolute').reduce((m, c) => Math.max(m, c.getBoundingClientRect().bottom), pr.top);
    return [k + 1, (bottom - limit) / 96, !!foot];
  }).filter(([, o]) => o > 0.005));
  if (clipped.length) { console.error(clipped.map(([k, o, f]) => `${pos[0]}: page ${k} runs ${o.toFixed(2)} in past ${f ? 'the top of its footer' : 'its bottom edge'} (text would be cut off or overprinted). Shorten it.`).join('\n')); await browser.close(); process.exit(2); }
  await page.pdf({ path: pos[1], preferCSSPageSize: true, printBackground: true });
  if (opt('png')) { await page.emulateMedia({ media: 'screen' }); await page.screenshot({ path: opt('png'), fullPage: true }); }
  console.log('Wrote ' + pos[1] + (opt('png') ? ' and ' + opt('png') : ''));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
