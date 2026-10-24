// Reviewer round 2: the Chrome-only details path. Fill details.html, save brand.js, move it into system/, reload a template.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const root = path.resolve(process.argv[2]);
  const b = await chromium.launch(); const ctx = await b.newContext({ acceptDownloads: true }); const p = await ctx.newPage();
  await p.goto('file://' + root + '/details.html'); await p.waitForTimeout(800);
  const vals = { FOUNDER_NAME: 'Alexandra Kowalczyk-Reyes', PHONE: '(646) 555-0187', EMAIL: 'alexandra@deskdrop-example.com', POSTAL_ADDRESS: '1178 Broadway, Suite 300 PMB 4417, New York, NY 10001' };
  for (const [k, v] of Object.entries(vals)) await p.fill(`input[data-k="${k}"]`, v);
  await p.check('#no-site');
  const st1 = await p.$eval('#status', (e) => e.innerText);
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#save')]);
  const name = dl.suggestedFilename(); const tmp = path.join(root, '..', 'downloaded-' + name); await dl.saveAs(tmp);
  fs.copyFileSync(tmp, path.join(root, 'system', 'brand.js'));
  await p.reload(); await p.waitForTimeout(800);
  const st2 = await p.$eval('#status', (e) => e.innerText);
  const sig = await p.$eval('#sig-plain', (e) => e.innerText);
  await p.screenshot({ path: path.join(root, '..', 'details-after.png'), fullPage: true });
  const t = await ctx.newPage();
  await t.goto('file://' + root + '/templates/office-one-pager/office-one-pager.html');
  await t.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const s = await t.evaluate(() => window.__DD_STATUS__);
  await t.screenshot({ path: path.join(root, '..', 'office-panel-after-details.png'), fullPage: false });
  console.log(JSON.stringify({ download: name, status_before_save: st1, status_after_reload: st2, plain: sig, office_status: { errors: s.errors, placeholders: s.placeholders } }, null, 1));
  await b.close();
})();
