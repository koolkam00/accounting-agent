const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  await p.goto('file://' + path.resolve('/home/user/accounting-agent/desk-drop/desk-drop-identity/templates/case-label/case-label.html'));
  await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const info = await p.evaluate(() => ({ labels: [...document.querySelectorAll('label.dd-field > span')].map(s => s.innerText.split('\n')[0]).slice(0, 40), buttons: [...document.querySelectorAll('.dd-panel button, .dd-panel label.dd-file')].map(x => x.innerText), records: (window.DD && DD.records ? DD.records.length : 'n/a'), sheets: document.querySelectorAll('.dd-sheet').length, intro: (document.querySelector('.dd-panel-help')||{}).innerText }));
  console.log(JSON.stringify(info, null, 1)); await p.screenshot({ path: path.join(__dirname, 'case-label-panel.png') }); await b.close(); })();
