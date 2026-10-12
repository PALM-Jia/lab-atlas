const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('node:url'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});try{
const p=await b.newPage({viewport:{width:1550,height:1000}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
const url=pathToFileURL(path.resolve('outputs/paper-atlas/index.html')).href;
await p.goto(url+'?view=authors&authorRelation=semantic');await p.waitForFunction(()=>document.querySelector('#relation-explanation')?.textContent.includes('全部不同论文对'));
assert.equal(await p.locator('#relation option[value="topic"]').count(),0);
assert.equal(await p.locator('#author-relation').inputValue(),'semantic');
await p.evaluate(()=>{const cy=document.getElementById('graph')._cyreg.cy;cy.edges()[0].emit('tap');});
await p.locator('#detail-content').getByText('代表论文对',{exact:true}).waitFor();
assert.match(await p.locator('#detail-content').innerText(),/语义依据论文/);
await p.screenshot({path:'work/author-semantic-current.png'});
await p.locator('#search').fill('semi-supervised');await p.waitForTimeout(400);
const titles=await p.evaluate(()=>{const cy=document.getElementById('graph')._cyreg.cy;const ids=new Set(cy.nodes().flatMap(n=>n.data('papers')));return window.ATLAS_DATA.nodes.filter(n=>ids.has(n.id)).map(n=>window.atlasSearchMatch([n.title,...n.authors,...n.tags.map(t=>window.ATLAS_DATA.topics.find(v=>v.id===t)?.name||t),...(window.ATLAS_PAPER_KEYWORDS.papers[n.id]||[]).map(k=>k.name)].join(' '),'semi-supervised'));});assert(titles.length>0);assert(titles.every(Boolean));
await p.locator('#search').fill('');await p.waitForTimeout(400);
await p.goto(url);await p.waitForFunction(()=>document.querySelector('#author-relation')?.value==='semantic');assert(await p.locator('[data-view="authors"]').evaluate(e=>e.classList.contains('active')));
await p.goto(url+'?view=papers&relation=topic');await p.waitForFunction(()=>document.querySelector('#relation')?.value==='semantic');
assert.equal(errors.length,0,errors.join('\n'));console.log('PASS: browser author semantic edges/evidence, fuzzy search, remembered view and legacy topic migration');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
