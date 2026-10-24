const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const SIG=path.resolve(__dirname,'../sb/desk-drop-identity/signature');
const OUT=path.resolve(__dirname,'../sig');
(async()=>{const b=await chromium.launch();
for (const [w,name] of [[600,'600'],[360,'360']]) for (const f of ['signature','signature-outreach']) {
 const html=fs.readFileSync(path.join(SIG,f+'.html'),'utf8');
 const body=(/<body[^>]*>([\s\S]*)<\/body>/i.exec(html)||[,html])[1];
 const page=await b.newPage({viewport:{width:w+80,height:700}});
 await page.setContent(`<html><body style="margin:0;background:#f1f3f4;font-family:Arial"><div style="width:${w}px;margin:20px auto;background:#fff;border:1px solid #ddd;padding:16px;box-sizing:border-box"><div style="font:13px Arial;color:#222;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:12px"><b>To:</b> pantry@example.com<br><b>Subject:</b> A question about your pantry</div><p style="font:14px Arial">Hi Pat,</p><p style="font:14px Arial">Short email body text goes here, two lines at most, to see the signature in context.</p><p style="font:14px Arial">Thanks,</p>${body}</div></body></html>`);
 await page.waitForTimeout(300);
 await page.screenshot({path:path.join(OUT,`${f}-${name}.png`),fullPage:true});
 const ov=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
 console.log(f,w,'horizontal overflow:',ov);
 await page.close();}
for (const f of ['signature','signature-outreach']) { const t=fs.readFileSync(path.join(SIG,f+'.txt'),'utf8'); const page=await b.newPage({viewport:{width:680,height:400}}); await page.setContent(`<div style="width:600px;margin:20px;font:14px monospace;white-space:pre-wrap;border:1px solid #ddd;padding:16px">Hi Pat,\n\nPlain-text email body.\n\nThanks,\n${t.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</div>`); await page.screenshot({path:path.join(OUT,`${f}-plain-600.png`),fullPage:true}); await page.close(); }
await b.close();})();
