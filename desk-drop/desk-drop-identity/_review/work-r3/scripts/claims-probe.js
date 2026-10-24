const path=require('path'),{chromium}=require('playwright');
const SB=path.resolve(__dirname,'../sb/desk-drop-identity');
const phrases=['Calcium builds strong bones.','Fiber maintains bowel regularity.','Antioxidants maintain cell integrity.',
 'Each bite promotes healthy digestion.','Each bite promotes digestion.','It aids digestion after lunch.','Good for your gut.','A gut-friendly snack.',
 'Builds strong bones.','Improves focus through the afternoon.','Helps you sleep better.','Lowers cholesterol.','Reduces bloating.',
 'Rich in antioxidants that protect your cells.','Good for your heart.','Strengthens your immune system.','Fuel for your brain.','Packed with probiotics for digestive balance.',
 'Keeps you full until dinner.','Gives you steady energy all afternoon.','Electrolytes for hydration and recovery.','Made to calm stress.','Clinically studied adaptogens.',
 'A resealable bag prevents crumbs at your desk.','Lift the lid and take one.','Our best flavor yet.','The number one jerky in Brooklyn.',
 'Sales rose 20% after the drop.','The campaign generated 40 new buyers.','Redemptions show a 3x return on spend.','We saw uplift at the store.','Converted 12% of tasters into buyers.','Drove trial-to-purchase of 30%.','Incremental sales of 31 units.'
];
(async()=>{const b=await chromium.launch(); const p=await b.newPage(); await p.goto('file://'+SB+'/templates/tent-card/tent-card.html'); await p.waitForFunction(()=>window.DD&&window.DD.claimsIn);
const r=await p.evaluate((ph)=>ph.map(s=>[s, DD.claimsIn(s), DD.nutrientIn(s)]),phrases);
r.forEach(([s,c,n])=>console.log((c.length?'CAUGHT ':'MISSED ')+JSON.stringify(c)+' '+s)); await b.close();})();
