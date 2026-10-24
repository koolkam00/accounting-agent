// Renders every page at phone and desktop widths into _shots/ (full page).
// Usage (from website/): node tests/shoot.js [siteDirOrBaseUrl] [outDir] [scheme]
//   siteDirOrBaseUrl: a folder (default site/), served on a free local port, or an http:// base URL.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const net = require('net');
const path = require('path');
const arg = process.argv[2] || path.join(__dirname, '..', 'site');
const out = process.argv[3] || path.join(__dirname, '..', '_shots');
const scheme = process.argv[4] || 'light';
const pages = ['index', 'brands', 'offices', 'privacy', 'survey-privacy', '404'];
const sizes = [['phone', 390, 844, true], ['desktop', 1280, 800, false]];
const freePort = () => new Promise(res => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
(async () => {
  let base = arg, server = null;
  if (!/^https?:\/\//.test(arg)) {
    const port = await freePort();
    server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', arg], { stdio: 'ignore' });
    base = `http://127.0.0.1:${port}/`;
    await new Promise(r => setTimeout(r, 900));
  }
  const browser = await chromium.launch();
  try {
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
  } finally {
    await browser.close();
    if (server) server.kill();
  }
})().catch(e => { console.error('FAIL:', e.message); process.exitCode = 1; });
