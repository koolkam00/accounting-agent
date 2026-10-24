// After passing the WAF on tmsearch.uspto.gov, run custom read-only Elasticsearch
// queries against the same search endpoint the UI uses, from inside the page.
// Usage: node tmsearch3.js <outdir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SRC = ['wordmark', 'wordmarkPseudoText', 'alive', 'filedDate', 'registrationId', 'registrationDate',
  'abandonDate', 'cancelDate', 'ownerName', 'internationalClass', 'goodsAndServices', 'currentBasis', 'id'];

let queries = {
  both_words_WM: { query: { bool: { must: [{ match: { WM: 'desk' } }, { match: { WM: 'drop' } }] } } },
  both_words_PM: { query: { bool: { must: [{ match: { PM: 'desk' } }, { match: { PM: 'drop' } }] } } },
  wildcard_deskdrop_WM: { query: { wildcard: { WM: { value: '*deskdrop*' } } } },
  wildcard_deskdrop_PM: { query: { wildcard: { PM: { value: '*deskdrop*' } } } },
  wildcard_desk_drop_both: { query: { bool: { must: [{ wildcard: { WM: { value: 'desk*' } } }, { wildcard: { WM: { value: 'drop*' } } }] } } },
};

(async () => {
  const out = process.argv[2];
  if (process.argv[3]) queries = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const outName = process.argv[4] || 'tm_custom_queries.json';
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    viewport: { width: 1400, height: 1600 },
  });
  const page = await ctx.newPage();
  let uiHeaders = null;
  page.on('request', (r) => {
    if (r.url().includes('prod-stage-v1-0-0/tmsearch') && r.method() === 'POST') uiHeaders = r.headers();
  });
  await page.goto('https://tmsearch.uspto.gov/search/search-information', { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(3000);
  const box = await page.$('input#searchbar, input[type=search], input[placeholder*="earch"], input[aria-label*="earch"]');
  await box.fill('desk drop');
  await page.keyboard.press('Enter');
  await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(5000);
  console.log('ui headers', JSON.stringify(uiHeaders));
  const results = {};
  for (const [name, q] of Object.entries(queries)) {
    const body = Object.assign({}, q, { size: 100, from: 0, track_total_hits: true, _source: SRC });
    const res = await page.evaluate(async ({ body, hdrs }) => {
      const h = { 'content-type': 'application/json' };
      if (hdrs) for (const k of Object.keys(hdrs)) if (/^x-|authorization/i.test(k)) h[k] = hdrs[k];
      const r = await fetch('/prod-stage-v1-0-0/tmsearch', { method: 'POST', headers: h, body: JSON.stringify(body), credentials: 'include' });
      return { status: r.status, text: await r.text() };
    }, { body, hdrs: uiHeaders });
    results[name] = { request: body, status: res.status, body: res.text };
    let summary = `${name}: HTTP ${res.status}`;
    try {
      const j = JSON.parse(res.text);
      summary += ` total=${j.hits.totalValue}`;
      for (const hit of j.hits.hits.slice(0, 30)) {
        const s = hit.source;
        summary += `\n   ${hit.id} ${s.wordmark} alive=${s.alive} filed=${s.filedDate} reg=${s.registrationId} aband=${s.abandonDate} cancel=${s.cancelDate} owner=${JSON.stringify(s.ownerName)} class=${JSON.stringify(s.internationalClass)}`;
      }
    } catch (e) { summary += ' (non-JSON) ' + res.text.slice(0, 300); }
    console.log(summary);
  }
  fs.writeFileSync(path.join(out, outName), JSON.stringify(results, null, 1));
  await browser.close();
})();
