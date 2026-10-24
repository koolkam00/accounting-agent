// Renders key pages at phone and desktop widths into _shots/ (full page).
// Usage: node tests/shoot.js [baseUrl] [outDir] [scheme]
const { chromium } = require('playwright');
const path = require('path');
const base = process.argv[2] || 'http://127.0.0.1:8000/';
const out = process.argv[3] || path.join(__dirname, '..', '_shots');
const scheme = process.argv[4] || 'light';
const pages = ['index', 'brands', 'offices', 'privacy', 'survey-privacy', '404'];
const sizes = [['phone', 390, 844, true], ['desktop', 1280, 800, false]];
(async () => {
  const browser = await chromium.launch();
  for (const [label, w, h, mobile] of sizes) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile, colorScheme: scheme });
    const page = await ctx.newPage();
    for (const p of pages) {
      await page.goto(base + p + '.html', { waitUntil: 'networkidle' });
      await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); } window.scrollTo(0, 0); });
      await page.evaluate(() => document.querySelectorAll('img[loading="lazy"]').forEach(i => { i.loading = 'eager'; }));
      await page.waitForFunction(() => [...document.images].every(i => i.complete && i.naturalWidth > 0), null, { timeout: 10000 });
      await page.waitForTimeout(200);
      const file = path.join(out, `${p}-${label}${scheme === 'dark' ? '-dark' : ''}.png`);
      await page.screenshot({ path: file, fullPage: true });
      console.log('wrote', path.relative(process.cwd(), file));
    }
    await ctx.close();
  }
  await browser.close();
})();
