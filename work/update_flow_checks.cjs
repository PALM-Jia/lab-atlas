const fs=require('fs');let s=fs.readFileSync('work/check_workflow_flow.cjs','utf8');let start=s.indexOf(' assert(await page.locator'),end=s.indexOf(' assert.equal(await page.locator',start);
s=s.slice(0,start)+` assert(await page.locator('.flow-visible[d*="Q"]').count()>0,'Rounded corners required');const d=await page.evaluate(()=>WORKFLOW_FLOW);
 assert.deepEqual(d.rows.map(r=>r.id),['basic','content','citations','paperfeatures','profiles']);
 assert(!d.nodes.some(n=>n.id.startsWith('cached-')));
 for(const id of ['abstract','keywords','topics','counts']){assert.equal(d.nodes.find(n=>n.id==='lab-'+id).stage,2);assert.deepEqual(d.edges.filter(e=>e.to==='lab-'+id).map(e=>e.from),['collect']);}
 assert.deepEqual(d.edges.filter(e=>e.to==='collect').map(e=>e.from),['identity']);
 assert(d.nodes.filter(n=>n.id.endsWith('-resolved')).every(n=>n.stage===3));
 assert(!d.edges.some(e=>['features','profile'].includes(e.to)),'Computational dependencies belong in companion graph');
`+s.slice(end);
s=s.replace('h:28','h:parseFloat(e.style.height)');
s=s.replace("y:parseFloat(e.style.top)+14,w:parseFloat(e.style.width)","y:parseFloat(e.style.top)+parseFloat(e.style.height)/2,w:parseFloat(e.style.width),h:parseFloat(e.style.height)");
s=s.replace('p.y>n.y-14&&p.y<n.y+14','p.y>n.y-n.h/2&&p.y<n.y+n.h/2');
start=s.indexOf(' const core=');end=s.indexOf(' for(const p of d.processes)',start);s=s.slice(0,start)+s.slice(end);
s=s.replace("await page.screenshot({path:'work/workflow-flow-desktop.png'});","await page.screenshot({path:'work/workflow-flow-desktop.png'});await page.locator('#lifecycle-board').screenshot({path:'work/workflow-flow-full.png'});");
s=s.replace("await page.evaluate(()=>WORKFLOW_MAP.artifacts.length));", "await page.evaluate(()=>WORKFLOW_MAP.artifacts.length));await page.locator('#dependency-board').screenshot({path:'work/workflow-dependencies-fresh.png'});");
s=s.replace('PASS: shared processes, core order, explicit query inputs, complete centered labels, nonoverlapping nodes, tooltips, stable selection, companion DAG, mobile.','PASS: semantic groups, identity query boundary, second-search-only details, complete labels, routes, tooltips, stable selection, DAG, mobile.');
fs.writeFileSync('work/check_workflow_flow.cjs',s);
