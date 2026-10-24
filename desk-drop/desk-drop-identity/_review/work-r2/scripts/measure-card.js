// Reviewer round 2: load the tent card with a JSON file, measure every text element on both faces.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [tpl, dataPath] = process.argv.slice(2);
  let data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const dir = path.dirname(path.resolve(dataPath));
  const fix = (v) => (typeof v === 'string' && /\.(svg|png|jpe?g)$/i.test(v) && !/^(file|data|https?):/.test(v)) ? 'file://' + path.resolve(dir, v) : v;
  const walk = (o) => { if (Array.isArray(o)) return o.map(walk); if (o && typeof o === 'object') { const n = {}; for (const k in o) n[k] = walk(o[k]); return n; } return fix(o); };
  data = walk(data);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.addInitScript((d) => { window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; }, data);
  await p.goto('file://' + path.resolve(tpl)); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  await p.evaluate(() => document.fonts.ready);
  const r = await p.evaluate(() => {
    const pt = (e) => +(parseFloat(getComputedStyle(e).fontSize) * 72 / 96).toFixed(2);
    const vis = (e) => e && getComputedStyle(e).display !== 'none' && e.offsetParent !== null;
    return [...document.querySelectorAll('.dd-sheet')].map((s, si) => ({ sheet: si, faces: [...s.querySelectorAll('.face')].map(f => {
      const q = (sel) => [...f.querySelectorAll(sel)].filter(vis);
      const safe = f.querySelector('.safe').getBoundingClientRect();
      const allEls = [...f.querySelectorAll('.safe *')].filter(vis);
      const overflowEls = allEls.filter(e => { const rr = e.getBoundingClientRect(); return rr.height > 0 && (rr.bottom > safe.bottom + 0.5 || rr.right > safe.right + 0.5); }).map(e => e.className + ':' + (e.innerText||'').slice(0,30));
      return {
        cls: f.className,
        allergen: q('.allergen-text').map(e => ({ pt: pt(e), w: getComputedStyle(e).fontWeight, color: getComputedStyle(e).color, words: e.innerText.trim().split(/\s+/).length })),
        allergenLabel: q('.allergen-label').map(e => ({ pt: pt(e), t: e.innerText.slice(0,80) })),
        name: q('.name').map(e => ({ pt: pt(e), px: parseFloat(getComputedStyle(e).fontSize), stretch: getComputedStyle(e).fontStretch, fam: getComputedStyle(e).fontFamily.slice(0,30), t: e.innerText })),
        logo: q('.logo').map(e => ({ h_in: +(e.getBoundingClientRect().height/96).toFixed(2), w_in: +(e.getBoundingClientRect().width/96).toFixed(2) })),
        story: q('.story').map(e => ({ pt: pt(e), t: e.innerText.slice(0,40) })),
        product: q('.product').map(e => ({ pt: pt(e) })),
        find: q('.find').map(e => ({ pt: pt(e), t: e.innerText })),
        cta: q('.cta-take,.cta-tell').map(e => ({ pt: pt(e), t: e.innerText })),
        qr: q('.qr-box svg').map(e => ({ w_in: +(e.getBoundingClientRect().width/96).toFixed(2) })),
        by: q('.by').map(e => ({ pt: pt(e), t: e.innerText })),
        cardId: q('.card-id').map(e => ({ pt: pt(e), t: e.innerText, bottom_from_trim_in: +((f.getBoundingClientRect().bottom - e.getBoundingClientRect().bottom)/96).toFixed(3) })),
        blocker: q('.blocker').map(e => e.innerText.slice(0,100)),
        overflow: overflowEls.slice(0,5),
      };
    }) }));
  });
  const st = await p.evaluate(() => window.__DD_STATUS__);
  console.log(JSON.stringify({ status: { errors: st.errors, warnings: st.warnings, placeholders: st.placeholders, sample: st.sample }, sheets: r }, null, 1));
  await b.close();
})();
