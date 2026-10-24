const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [tpl, dataPath] = process.argv.slice(2);
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage();
  await p.addInitScript((d) => { window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; }, data);
  await p.goto('file://' + path.resolve(tpl)); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const r = await p.evaluate(() => [...document.querySelectorAll('.allergen-text')].map(e => ({ pt: (parseFloat(getComputedStyle(e).fontSize) * 72 / 96).toFixed(2), weight: getComputedStyle(e).fontWeight, family: getComputedStyle(e).fontFamily.slice(0,40), color: getComputedStyle(e).color, text: e.innerText.slice(0, 50) })));
  const name = await p.evaluate(() => [...document.querySelectorAll('.face.front .name')].map(e => ({ pt: (parseFloat(getComputedStyle(e).fontSize) * 72 / 96).toFixed(1), stretch: getComputedStyle(e).fontStretch, w: e.scrollWidth })));
  console.log(JSON.stringify({ allergen: r, name }, null, 1)); await b.close();
})();
