const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const SIG = '/home/user/accounting-agent/desk-drop/desk-drop-identity/signature/';
const body = (f) => fs.readFileSync(SIG + f, 'utf8').replace(/^[\s\S]*?<body[^>]*>/i, '').replace(/<\/body>[\s\S]*$/i, '');
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const shell = (w, inner) => `<!doctype html><html><body style="margin:0;background:#f1f3f4;font-family:Arial">
<div style="width:${w}px;margin:0 auto;background:#fff;border:1px solid #dadce0">
<div style="padding:10px 16px;border-bottom:1px solid #eee;font:13px Arial;color:#5f6368">From: [FOUNDER NAME] &lt;[EMAIL]&gt; · To: SAMPLE Office Manager · Subject: SAMPLE Free snacks for your pantry, with one ask</div>
<div style="padding:16px;font:14px/20px Arial;color:#202124"><p>Hi SAMPLE Jamie,</p><p>SAMPLE body text of a cold email, two short paragraphs.</p><p>Would a 15-minute call on Tuesday work?</p><div>--</div>${inner}</div></div></body></html>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 640, height: 600 }, deviceScaleFactor: 1.5 });
  for (const [f, w] of [['signature.html', 600], ['signature-outreach.html', 600], ['signature-outreach.html', 360]]) {
    await p.setViewportSize({ width: w + 40, height: 600 }); await p.setContent(shell(w, body(f))); await p.waitForTimeout(200);
    const out = `view-${f.replace('.html', '')}-${w}.png`; await p.screenshot({ path: out, fullPage: true }); console.log('wrote', out);
  }
  const txt = fs.readFileSync(SIG + 'signature-outreach.txt', 'utf8');
  await p.setViewportSize({ width: 640, height: 400 }); await p.setContent(shell(600, `<pre style="font:13px/18px monospace;white-space:pre-wrap;margin:0">${esc(txt)}</pre>`)); await p.screenshot({ path: 'view-plain-600.png', fullPage: true });
  // copy-paste fidelity: what text does a select-all copy yield?
  await p.goto('file://' + SIG + 'signature-outreach.html'); const sel = await p.evaluate(() => document.body.innerText); fs.writeFileSync('outreach-innerText.txt', sel); console.log(sel);
  console.log('html chars', fs.readFileSync(SIG + 'signature-outreach.html', 'utf8').length);
  await b.close();
})();
