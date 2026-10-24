// Drive tmsearch.uspto.gov by typing into the search box; log every XHR/fetch.
// Usage: node tmsearch2.js "<query>" <outdir> <tag>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const q = process.argv[2];
  const out = process.argv[3];
  const tag = process.argv[4] || 'q';
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    viewport: { width: 1400, height: 1600 },
  });
  const page = await ctx.newPage();
  const log = [];
  const captured = [];
  page.on('request', (r) => {
    const t = r.resourceType();
    if (t === 'xhr' || t === 'fetch') log.push(`${r.method()} ${r.url()} ${(r.postData() || '').slice(0, 300)}`);
  });
  page.on('response', async (resp) => {
    const r = resp.request();
    const t = r.resourceType();
    if ((t === 'xhr' || t === 'fetch') && /tmsearch|search/i.test(resp.url()) && !/config|menu|chatbot|translat/i.test(resp.url())) {
      try { captured.push({ url: resp.url(), method: r.method(), status: resp.status(), req: r.postData(), body: await resp.text() }); }
      catch (e) { captured.push({ url: resp.url(), err: String(e) }); }
    }
  });
  await page.goto('https://tmsearch.uspto.gov/search/search-information', { waitUntil: 'networkidle', timeout: 90000 }).catch(e => console.log('goto err', String(e)));
  await page.waitForTimeout(4000);
  const inputs = await page.$$eval('input', els => els.map(e => ({ id: e.id, name: e.name, type: e.type, ph: e.placeholder, aria: e.getAttribute('aria-label') })));
  console.log('inputs', JSON.stringify(inputs));
  const box = await page.$('input#searchbar, input[type=search], input[placeholder*="earch"], input[aria-label*="earch"]');
  if (!box) { console.log('no search box found'); }
  else {
    await box.click();
    await box.fill(q);
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(8000);
  }
  await page.screenshot({ path: path.join(out, `tm_${tag}.png`), fullPage: false });
  const text = await page.evaluate(() => document.body.innerText);
  fs.writeFileSync(path.join(out, `tm_${tag}_page.txt`), text);
  fs.writeFileSync(path.join(out, `tm_${tag}_api.json`), JSON.stringify(captured, null, 1));
  fs.writeFileSync(path.join(out, `tm_${tag}_netlog.txt`), log.join('\n'));
  console.log('url now', page.url());
  console.log('NETLOG\n' + log.join('\n'));
  const i = text.indexOf('Export');
  console.log('PAGE after Export:\n' + text.slice(i, i + 4000));
  await browser.close();
})();
