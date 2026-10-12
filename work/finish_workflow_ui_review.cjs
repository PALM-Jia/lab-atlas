const fs=require('node:fs');const p='outputs/paper-atlas/workflow-explanations.js';let s=fs.readFileSync(p,'utf8').replace('疑问再查原始发布页','有疑问时再查原始发布页').replace('关键词分数是加权论文覆盖率','关键词画像中的占比是加权论文覆盖率');fs.writeFileSync(p,s);
const t='work/check_workflow_flow.cjs';let c=fs.readFileSync(t,'utf8');const anchor="assert.equal(await page.locator('.flow-node').count(),d.nodes.length+d.processes.length);";
if(!c.includes("stage navigation changes only horizontal position"))c=c.replace(anchor,anchor+`
 // Stage navigation changes only horizontal position and exposes offscreen results.
 assert(await page.locator('#clear').isHidden());
 const vertical=await page.locator('main').evaluate(e=>e.scrollTop);
 await page.locator('[data-scroll-stage="4"]').click();
 assert.equal(await page.locator('main').evaluate(e=>e.scrollTop),vertical);
 assert(await page.locator('#lifecycle-scroll').evaluate(e=>e.scrollLeft>0));
 const lastNode=await page.locator('[data-flow-node="direction-profile"]').boundingBox(),viewport=await page.locator('#lifecycle-scroll').boundingBox();assert(lastNode.x>=viewport.x&&lastNode.x+lastNode.width<=viewport.x+viewport.width);
 await page.locator('[data-scroll-stage="0"]').click();
 assert.equal(await page.locator('#lifecycle-scroll').evaluate(e=>e.scrollLeft),0);
 await page.locator('[data-flow-node="lab-title"]').click();assert(await page.locator('#clear').isVisible());await page.locator('#clear').click();assert(await page.locator('#clear').isHidden());
 assert.equal(await page.locator('#inspector a[href="retrieval.html"]').count(),1);
`);
c=c.replace("await page.screenshot({path:'work/workflow-flow-mobile.png'});",`await page.screenshot({path:'work/workflow-flow-mobile.png'});
 assert(await page.locator('#stage-navigation').isVisible());await page.locator('[data-scroll-stage="4"]').click();assert(await page.locator('#lifecycle-scroll').evaluate(e=>e.scrollLeft>0));
 await page.setViewportSize({width:1920,height:1100});await page.locator('[data-scroll-stage="0"]').click();await page.waitForTimeout(50);assert(await page.locator('#stage-navigation').isHidden());
`);
fs.writeFileSync(t,c);
