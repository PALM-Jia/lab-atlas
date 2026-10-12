const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('node:url'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 await page.goto(pathToFileURL(path.resolve('outputs/paper-atlas/workflow.html')).href);
 await page.locator('#lifecycle-board .stage-header[data-stage="locate"]').hover();await page.screenshot({path:'work/workflow-stage-tooltip.png'});
 await page.setViewportSize({width:390,height:844});
 for(const stage of ['locate','features']){
  const target=page.locator(`#lifecycle-board .stage-header[data-stage="${stage}"]`);await target.scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.mouse.move(0,0);await target.hover();await page.locator("#workflow-tooltip").waitFor({state:"visible"});
  const r=await page.locator('#workflow-tooltip').boundingBox();assert(r&&r.x>=0&&r.y>=0&&r.x+r.width<=390&&r.y+r.height<=844,stage+' tooltip outside viewport');
  await page.screenshot({path:`work/workflow-${stage}-tooltip-mobile.png`});
 }
 await browser.close();console.log('PASS: main diagram tooltips stay inside desktop and mobile viewports.');
})();
