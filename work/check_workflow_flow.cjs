const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('node:url'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page=await browser.newPage({viewport:{width:1800,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve('outputs/paper-atlas/workflow.html')).href);assert.deepEqual(errors,[]);
 assert.equal(await page.locator('.key-line').count(),1);assert(await page.locator('.flow-visible').evaluateAll(es=>es.every(e=>getComputedStyle(e).strokeDasharray==='none')));assert.equal(await page.locator('.flow-row-header').first().evaluate(e=>e.getBoundingClientRect().width),88);assert(await page.locator('.stage-header').first().evaluate(e=>e.getBoundingClientRect().width<130));
 assert(await page.locator('.flow-visible[d*="Q"]').count()>0,'Rounded corners required');const d=await page.evaluate(()=>WORKFLOW_FLOW);
 assert.deepEqual(d.rows.map(r=>r.id),['basic','content','citations','paperfeatures','profiles']);
 const aligned=await page.evaluate(()=>{const header=document.querySelector('.stage-header').getBoundingClientRect(),corner=document.querySelector('.flow-corner').getBoundingClientRect(),rows=[...document.querySelectorAll('.flow-row')].map(e=>e.getBoundingClientRect()),cols=[...document.querySelectorAll('.flow-column')].map(e=>e.getBoundingClientRect());return corner.y===header.y&&corner.height===header.height&&rows[0].y===header.bottom&&cols.every(c=>c.y===rows[0].y&&c.bottom===rows.at(-1).bottom);});assert(aligned,'Header, row labels and content columns must share top and bottom boundaries');
 assert(!d.nodes.some(n=>n.id.startsWith('cached-')));
 for(const id of ['abstract','keywords','topics','counts']){assert.equal(d.nodes.find(n=>n.id==='lab-'+id).stage,2);assert.deepEqual(d.edges.filter(e=>e.to==='lab-'+id).map(e=>e.from),['collect']);}
 assert.deepEqual(d.edges.filter(e=>e.to==='collect').map(e=>e.from),['identity']);
 assert(d.nodes.filter(n=>n.id.endsWith('-resolved')).every(n=>n.stage===3));
 assert.deepEqual(d.edges.filter(e=>e.to==='features').map(e=>e.from).sort(),['feature-abstract','feature-title']);
 assert.deepEqual(d.edges.filter(e=>e.to==='profile').map(e=>e.from).sort(),['profile-authors','profile-directions','profile-keywords']);
 for(const e of d.edges.filter(e=>['features','profile'].includes(e.to))){const n=d.nodes.find(n=>n.id===e.from);assert.equal(n.stage,4);assert(n.sourceIds.length);for(const source of n.sourceIds)assert(d.nodes.some(n=>n.id===source));}
 assert(!d.edges.some(e=>e.note));
 assert.deepEqual(d.edges.filter(e=>e.from==='external'&&e.type==='value').map(e=>e.to).sort(),['citing-list-resolved','external-info','reference-list-resolved']);
 const outputs=d.nodes.filter(n=>['citing-list-resolved','external-info','reference-list-resolved'].includes(n.id));assert.equal(new Set(outputs.map(n=>n.slot)).size,1);
 assert(!d.edges.some(e=>e.from==='external-info'&&e.to.endsWith('-resolved')));
 assert.deepEqual(d.edges.filter(e=>e.to==='external').map(e=>e.from).sort(),['citing-list','reference-list']);
 for(const id of ['reference-list','citing-list'])assert.deepEqual(d.edges.filter(e=>e.to===id+'-resolved').map(e=>e.from),['external']);
 assert.equal(d.processes.find(p=>p.id==='external').label,'采集外部文献\n并补全记录');
 assert.equal(d.processes.find(p=>p.id==='external').offset,d.nodes.find(n=>n.id==='reference-list').offset);
 for(const id of ['reference-list','citing-list'])assert.equal(d.nodes.find(n=>n.id===id).offset,d.nodes.find(n=>n.id===id+'-resolved').offset);
 assert.equal(await page.locator('.flow-node').count(),d.nodes.length+d.processes.length);
 assert.equal(await page.locator('#stage-navigation').count(),0);assert(await page.locator('#clear').isHidden());
 await page.locator('[data-flow-node="lab-title"]').click();assert(await page.locator('#clear').isVisible());await page.locator('#clear').click();assert(await page.locator('#clear').isHidden());
 assert.equal(await page.locator('#inspector a[href="retrieval.html"]').count(),1);
 // A row title selects its entire semantic group, including related traces.
 for(const row of d.rows){
  const title=page.locator(`[data-flow-group="${row.id}"]`);await title.scrollIntoViewIfNeeded();await title.click();
  for(const n of [...d.nodes,...d.processes].filter(n=>n.row===row.id)){assert.equal(await page.locator(`[data-flow-node="${n.id}"]`).getAttribute('aria-pressed'),'true',row.id+' group omitted '+n.id);assert(!(await page.locator(`[data-flow-node="${n.id}"]`).getAttribute('class')).includes('dimmed'));}
  const centered=await title.evaluate(e=>{const b=e.getBoundingClientRect(),r=e.closest('.flow-row').getBoundingClientRect();return Math.abs(b.y+b.height/2-r.y-r.height/2)<1&&Math.abs(b.x+b.width/2-e.parentElement.getBoundingClientRect().x-e.parentElement.getBoundingClientRect().width/2)<1&&getComputedStyle(e).textAlign==='center';});assert(centered,row.id+' group title off center');
  await page.locator('#clear').click();
 }
 await page.locator('main').evaluate(e=>e.scrollTop=0);



 // Every element type selects its documented scope, without changing page position.
 await page.locator('[data-flow-node="lab-title"]').click();
 for(const n of d.nodes.filter(n=>n.info==='title'))assert.equal(await page.locator(`[data-flow-node="${n.id}"]`).getAttribute('aria-pressed'),'true');
 await page.locator('.stage-header[data-stage="collect"]').click();
 for(const n of [...d.nodes,...d.processes].filter(n=>n.stage===2))assert.equal(await page.locator(`[data-flow-node="${n.id}"]`).getAttribute('aria-pressed'),'true');
 await page.locator('[data-flow-node="collect"]').click();
 assert.equal(await page.locator('.flow-node[aria-pressed="true"]').count(),1);
 assert.equal(await page.locator('[data-flow-node="collect"]').getAttribute('aria-pressed'),'true');
 const firstEdge=page.locator('[data-flow-edge="flow-edge-0"]');
 const point=await firstEdge.evaluate(e=>{const p=e.getPointAtLength(10),r=e.ownerSVGElement.getBoundingClientRect();return{x:r.x+p.x,y:r.y+p.y};});
 await page.mouse.click(point.x,point.y);
 assert.equal(await firstEdge.getAttribute('aria-pressed'),'true');assert.equal(await page.locator('.flow-node[aria-pressed="true"]').count(),2);
 assert.equal(await page.locator('[data-flow-node="home-title"]').getAttribute('aria-pressed'),'true');assert.equal(await page.locator('[data-flow-node="locate"]').getAttribute('aria-pressed'),'true');
 await page.keyboard.press('Escape');assert.equal(await page.locator('.flow-node.dimmed').count(),0);assert(await page.locator('#clear').isHidden());
 await firstEdge.focus();await page.keyboard.press('Enter');assert.equal(await firstEdge.getAttribute('aria-pressed'),'true');
 await page.locator('h1').click();assert.equal(await firstEdge.getAttribute('aria-pressed'),'false');assert(await page.locator('#clear').isHidden());
 const labels=await page.locator('.flow-node').evaluateAll(es=>es.map(e=>{const range=document.createRange();range.selectNodeContents(e);const t=range.getBoundingClientRect(),b=e.getBoundingClientRect();return{id:e.dataset.flowNode,text:e.textContent,inside:t.left>=b.left&&t.right<=b.right&&t.top>=b.top&&t.bottom<=b.bottom,center:Math.abs(t.left+t.width/2-b.left-b.width/2)};}));for(const label of labels){assert(label.inside,label.id);assert(label.center<1,label.id);}
 const geometry=await page.locator('.flow-node').evaluateAll(es=>es.map(e=>({id:e.dataset.flowNode,x:parseFloat(e.style.left)-parseFloat(e.style.width)/2,y:parseFloat(e.style.top),w:parseFloat(e.style.width),h:parseFloat(e.style.height)})));
 for(let a=0;a<geometry.length;a++)for(let b=a+1;b<geometry.length;b++){const x=geometry[a],y=geometry[b];assert(!(Math.min(x.x+x.w,y.x+y.w)>Math.max(x.x,y.x)&&Math.min(x.y+x.h,y.y+y.h)>Math.max(x.y,y.y)),x.id+' overlap '+y.id);}
 const routeProblems=await page.evaluate(()=>{const nodes=[...document.querySelectorAll('.flow-node')].map(e=>({id:e.dataset.flowNode,x:parseFloat(e.style.left),y:parseFloat(e.style.top)+parseFloat(e.style.height)/2,w:parseFloat(e.style.width),h:parseFloat(e.style.height)})),byId=new Map(nodes.map(n=>[n.id,n])),problems=[];WORKFLOW_FLOW.edges.forEach((e,i)=>{const path=document.querySelector(`[data-flow-edge="flow-edge-${i}"]`),len=path.getTotalLength(),start=path.getPointAtLength(0),next=path.getPointAtLength(.5),end=path.getPointAtLength(len),prev=path.getPointAtLength(len-.5),a=byId.get(e.from),b=byId.get(e.to);if(Math.abs(start.x-a.x-a.w/2)>.1||Math.abs(start.y-a.y)>.1||Math.abs(end.x-b.x+b.w/2)>.1||Math.abs(end.y-b.y)>.1||next.x<=start.x||end.x<=prev.x||Math.abs(next.y-start.y)>.1||Math.abs(end.y-prev.y)>.1)problems.push('port '+i);const nearStart=path.getPointAtLength(16),nearEnd=path.getPointAtLength(len-16);if(Math.abs(nearStart.y-start.y)>.02||Math.abs(nearEnd.y-end.y)>.02||Math.abs(nearStart.x-start.x-16)>.02||Math.abs(end.x-nearEnd.x-16)>.02)problems.push('straight clearance '+i);let previousX=start.x;for(let d=0;d<len;d+=3){const p=path.getPointAtLength(d);if(p.x<previousX-.1)problems.push('backward '+i);previousX=p.x;if(nodes.some(n=>n.id!==e.from&&n.id!==e.to&&p.x>n.x-n.w/2&&p.x<n.x+n.w/2&&p.y>n.y-n.h/2&&p.y<n.y+n.h/2)){problems.push('collision '+i);break;}}});return problems;});assert.deepEqual(routeProblems,[]);
 for(const p of d.processes){const target=page.locator(`[data-flow-node="${p.id}"]`);await target.scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await target.hover();await page.locator('#workflow-tooltip').waitFor({state:'visible'});assert(await page.locator('#workflow-tooltip').isVisible());assert((await page.locator('#workflow-tooltip p').count())<=2);const before=await page.locator('main').evaluate(e=>e.scrollTop);await target.click();assert.equal(await page.locator('main').evaluate(e=>e.scrollTop),before);}
 await page.locator('#clear').click();await page.locator('main').evaluate(e=>e.scrollTop=0);await page.mouse.move(0,0);await page.screenshot({path:'work/workflow-flow-desktop.png'});await page.locator('#lifecycle-board').screenshot({path:'work/workflow-flow-full.png'});
 assert.equal(await page.locator('[role=tablist],#dependency-board').count(),0);assert.equal(await page.locator('.explanation-section:visible').count(),6);
 await page.locator('.explanation-section').first().click();assert.equal(await page.locator('.explanation-section:visible').count(),6);assert.equal(await page.locator('.flow-node.dimmed').count(),0);
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'work/workflow-flow-mobile.png'});



 assert.deepEqual(errors,[]);await browser.close();console.log('PASS: semantic groups, identity query boundary, second-search-only details, complete labels, routes, tooltips, stable selection, continuous prose, mobile.');
})().catch(e=>{console.error(e);process.exit(1)});
