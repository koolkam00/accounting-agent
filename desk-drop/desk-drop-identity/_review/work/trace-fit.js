const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [tpl, dataPath] = process.argv.slice(2);
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage();
  await p.addInitScript((d) => {
    window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; window.__TRACE__ = [];
    let real; Object.defineProperty(window, 'DDDocs', { configurable: true, get() { return real; }, set(v) { real = v;
      const orig = v.fitPages; v.fitPages = function (sheet, i, steps, what, only) {
        const pages = only || [...sheet.querySelectorAll('.page')];
        const m = () => pages.map(p => { const b = p.querySelector('.bd'); return b ? (b.scrollHeight - b.clientHeight) : null; });
        window.__TRACE__.push({ when: 'before', over: m() });
        const wrapped = steps.map((s, k) => () => { const r = s(); if (r) window.__TRACE__.push({ step: k, over: m() }); return r; });
        const res = orig.call(this, sheet, i, wrapped, what, only); window.__TRACE__.push({ when: 'after', over: m(), res }); return res; }; } });
  }, data);
  await p.goto('file://' + path.resolve(tpl)); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  console.log(JSON.stringify(await p.evaluate(() => ({ trace: window.__TRACE__, errors: window.__DD_STATUS__.errors }))));
  await b.close();
})();
