// Reviewer round 2: show a signature inside a 600 px email-like body, and the plain-text version.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [htmlFile, txtFile, outPrefix] = process.argv.slice(2);
  const sigHtml = fs.readFileSync(htmlFile, 'utf8').replace(/^[\s\S]*<body[^>]*>/i, '').replace(/<\/body>[\s\S]*$/i, '');
  const txt = fs.readFileSync(txtFile, 'utf8');
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const shell = (inner) => `<!doctype html><html><body style="margin:0;background:#f1f3f4;font-family:Arial,sans-serif">
    <div style="width:600px;margin:0 auto;background:#fff;border:1px solid #ddd;padding:16px 20px;box-sizing:border-box">
    <div style="font-size:12px;color:#5f6368;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:12px">To: office.manager@example.com<br>Subject: A quick question about your pantry</div>
    <div style="font-size:14px;color:#222;line-height:20px">Hi Sam,<br><br>Thanks for the call today. The one-pager is attached.<br><br>Best,</div><br>
    ${inner}</div></body></html>`;
  const b = await chromium.launch();
  for (const [w, suffix] of [[600, '600'], [360, '360']]) {
    const p = await b.newPage({ viewport: { width: w + 40, height: 400 }, deviceScaleFactor: 2 });
    await p.setContent(shell(sigHtml).replace('width:600px', `width:${w}px`)); await p.screenshot({ path: `${outPrefix}-html-${suffix}.png`, fullPage: true });
    await p.close();
  }
  const p = await b.newPage({ viewport: { width: 640, height: 400 }, deviceScaleFactor: 2 });
  await p.setContent(shell(`<pre style="font-family:Arial,sans-serif;font-size:14px;white-space:pre-wrap;margin:0">${esc(txt)}</pre>`)); await p.screenshot({ path: `${outPrefix}-plain-600.png`, fullPage: true });
  const inner = await p.evaluate(() => document.body.innerText); fs.writeFileSync(`${outPrefix}-plain-innerText.txt`, inner);
  await b.close();
})();
