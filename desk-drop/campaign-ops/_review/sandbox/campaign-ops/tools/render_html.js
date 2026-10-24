// Render a local HTML file to PDF (Letter) and optionally a PNG of the first page.
// node tools/render_html.js page.html out.pdf [--png out.png] [--landscape] [--width 390]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const a = process.argv.slice(2);
  const src = path.resolve(a[0]), out = a[1] ? path.resolve(a[1]) : null;
  const pngI = a.indexOf('--png'), wI = a.indexOf('--width');
  const landscape = a.includes('--landscape');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: wI > 0 ? +a[wI + 1] : 1100, height: 1400 } });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(String(e)));
  await page.goto('file://' + src);
  await page.waitForLoadState('networkidle');
  if (out && out.endsWith('.pdf')) await page.pdf({ path: out, format: 'Letter', landscape, printBackground: true, margin: { top: '0.4in', bottom: '0.4in', left: '0.4in', right: '0.4in' } });
  if (pngI > 0) await page.screenshot({ path: path.resolve(a[pngI + 1]), fullPage: true });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  await browser.close();
  console.log(JSON.stringify({ ok: errs.length === 0, errors: errs, horizontal_overflow: overflow }));
  process.exit(errs.length ? 1 : 0);
})();
