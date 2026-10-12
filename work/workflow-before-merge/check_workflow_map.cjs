const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('node:url'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
 await page.goto(pathToFileURL(path.resolve('outputs/paper-atlas/workflow-map.html')).href);
 assert.equal(await page.locator('[data-stage-index]').count(),8);assert.equal(await page.locator('[data-track]').count(),6);assert.equal(await page.locator('[data-type="atlas.Stop"]').count(),32);
 const positions=await page.locator('[data-type="atlas.Stop"]').evaluateAll(es=>es.map(e=>e.getAttribute('transform')));
 for(let i=0;i<8;i++){await page.locator(`[data-stage-index="${i}"]`).click();assert.equal(await page.locator(`[data-stage-index="${i}"]`).getAttribute('aria-pressed'),'true');assert.equal(await page.locator('#inspector dt').count(),3);}
 await page.locator('[data-stage-index="1"]').click();assert.equal(await page.locator('[data-detail]').count(),3);await page.locator('[data-detail="original"]').click();assert.match(await page.locator('#inspector h2').innerText(),/原始来源/);
 for(const id of ['identity','text','authors','keywords','citations','evidence']){await page.locator(`[data-track="${id}"]`).click();assert.equal(await page.locator(`[data-track="${id}"]`).getAttribute('aria-pressed'),'true');}
 for(const id of ['matched','vector','profile','summary']){const node=page.locator(`[model-id="${id}"]`);await node.locator('[joint-selector="body"]').click();assert(await page.locator('#inspector h2').innerText());}
 await page.locator('[model-id="vector"]').focus();await page.keyboard.press('Enter');assert.match(await page.locator('#inspector h2').innerText(),/语义向量/);
 await page.locator('#inspector summary').click();assert.match(await page.locator('#inspector details').innerText(),/Semantic Scholar/);
 assert.deepEqual(await page.locator('[data-type="atlas.Stop"]').evaluateAll(es=>es.map(e=>e.getAttribute('transform'))),positions);
 await page.locator('#clear').click();await page.screenshot({path:'work/workflow-map-desktop.png'});
 await page.locator('[data-track="text"]').click();await page.screenshot({path:'work/workflow-map-selected.png'});
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert(await page.locator('#map-scroll').evaluate(e=>e.scrollWidth>e.clientWidth));
 await page.locator('[data-stage-index="7"]').click();assert.match(await page.locator('#inspector h2').innerText(),/计算关联/);await page.screenshot({path:'work/workflow-map-mobile.png'});
 await page.locator('a[href="workflow.html"]').click();await page.locator('[data-stage]').first().waitFor();assert.equal(await page.locator('[data-stage]').count(),12);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 await browser.close();console.log('PASS: offline rendering; 8 stages; 6 tracks; node and keyboard selection; stable positions; mobile scroll; original page link.');
})().catch(e=>{console.error(e);process.exit(1)});

