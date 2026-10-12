const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');const {pathToFileURL}=require('node:url'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});try{
const page=await browser.newPage({viewport:{width:1550,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.resolve('outputs/paper-atlas/index.html')).href+'?view=authors&authorRelation=coauthor');await page.waitForFunction(()=>document.querySelector('#relation-explanation')?.textContent.includes('任一端选中'));
for(const view of ['authors','papers','timeline']){
 await page.locator('[data-view="'+view+'"]').click();
 for(const relation of view==='authors'?['coauthor','semantic','topic','keywords']:['citation','author','semantic']){
  await page.locator(view==='authors'?'#author-relation':'#relation').selectOption(relation);
  const result=await page.evaluate(()=>{const cy=document.getElementById('graph')._cyreg.cy;return {count:cy.edges().length,valid:cy.edges().every(e=>e.data('evidence')?.top_k===5&&e.data('evidence').threshold===null)};});assert(result.count>0);assert(result.valid);
  const text=await page.locator('#relation-explanation').innerText();assert.match(text,/任一端选中/);assert.doesNotMatch(text,/中位数|60.0%|95%|平均.*4/);
 }
 if(view==='papers'){await page.waitForTimeout(700);await page.screenshot({path:'work/unified-top5-papers.png'});}
}
assert.deepEqual(errors,[]);console.log('PASS: all ten browser view/rule combinations, no stale threshold text or browser errors');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
