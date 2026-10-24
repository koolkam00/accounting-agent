const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [tpl, dataPath] = process.argv.slice(2);
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage();
  await p.addInitScript((d) => { window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; }, data);
  await p.goto('file://' + path.resolve(tpl)); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  console.log(JSON.stringify(await p.evaluate(() => [...document.querySelectorAll('.page .bd')].map(e => ({ scroll: e.scrollHeight, client: e.clientHeight, over_px: e.scrollHeight - e.clientHeight, ft: (e.parentElement.querySelector('.ft')||{}).offsetHeight })))));
  await b.close();
})();
