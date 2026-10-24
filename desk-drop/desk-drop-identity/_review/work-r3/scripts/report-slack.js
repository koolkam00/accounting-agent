// Measure page-1 slack of a rendered report, and whether the placement-only strip would have fit.
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const SB=path.resolve(__dirname,'../sb/desk-drop-identity');
const [dataPath]=process.argv.slice(2);
(async()=>{
 const data=JSON.parse(fs.readFileSync(dataPath,'utf8'));
 (function walk(v,p,k){ if(Array.isArray(v)) return v.forEach((x,i)=>walk(x,v,i)); if(v&&typeof v==='object') return Object.keys(v).forEach(kk=>walk(v[kk],v,kk)); if(typeof v==='string'&&/\.(png|jpe?g)$/i.test(v)) p[k]='file://'+path.resolve(path.dirname(dataPath),v);})(data,null,null);
 const b=await chromium.launch(); const pg=await b.newPage();
 await pg.addInitScript(d=>{window.__DD_DATA__=d;window.__DD_HEADLESS__=true;},data);
 await pg.goto('file://'+SB+'/templates/report/report.html');
 await pg.waitForFunction(()=>window.__DD_STATUS__&&window.__DD_STATUS__.ready,null,{timeout:30000});
 await pg.emulateMedia({media:'print'});
 const r=await pg.evaluate(()=>{
   const p=document.querySelector('.page.rpt'); const bd=p.querySelector('.bd');
   const kids=[...bd.children]; const last=kids[kids.length-1];
   const used = Math.max(...kids.map(k=>k.getBoundingClientRect().bottom)) - bd.getBoundingClientRect().top;
   const out={client_in: bd.clientHeight/96, used_in: used/96, slack_in:(bd.clientHeight-used)/96, cls:p.className};
   // try placement-only strip
   const wasMoved=p.classList.contains('ev-moved');
   p.classList.remove('ev-moved'); p.classList.add('ev-later-moved');
   out.with_placement_row_overflow_in=(bd.scrollHeight-bd.clientHeight)/96;
   const used2 = Math.max(...[...bd.children].map(k=>k.getBoundingClientRect().bottom)) - bd.getBoundingClientRect().top;
   out.with_placement_row_slack_in=(bd.clientHeight-used2)/96;
   return out;});
 console.log(JSON.stringify(r)); await b.close();})();
