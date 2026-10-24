const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  for (const t of ['case-label', 'tent-card', 'report', 'proposal', 'office-one-pager']) {
    await p.goto('file://' + path.resolve(`/home/user/accounting-agent/desk-drop/desk-drop-identity/templates/${t}/${t}.html`));
    await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
    const v = await p.evaluate(() => [...document.querySelectorAll('.dd-panel input:not([type=checkbox]):not([type=file]), .dd-panel textarea')].slice(0, 6).map(e => ({ value: e.value, ph: e.placeholder })));
    console.log(t, JSON.stringify(v));
  }
  await b.close(); })();
