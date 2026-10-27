// Render every examples/*.html at 390 px wide (iPhone-class width) to examples/png/*.png.
// Run from desk-drop/desk-drop-outreach/messages/:  node _render/shoot.js [name-filter]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const dir = path.join(__dirname, '..', 'examples');
  const out = path.join(dir, 'png');
  fs.mkdirSync(out, { recursive: true });
  const filter = process.argv[2] || '';
  const files = fs.readdirSync(dir).filter((f) => f.endsWith('.html') && f.includes(filter)).sort();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  for (const f of files) {
    await page.goto('file://' + path.join(dir, f));
    const w = await page.evaluate(() => document.documentElement.scrollWidth);
    if (w > 390) console.log(`WARN ${f}: page is ${w}px wide, wider than 390`);
    await page.screenshot({ path: path.join(out, f.replace('.html', '.png')), fullPage: true });
    console.log('wrote', f.replace('.html', '.png'));
  }
  await browser.close();
})();
