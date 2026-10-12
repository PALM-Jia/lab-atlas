'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),http=require('node:http');
const root=path.resolve(__dirname,'../outputs/paper-atlas');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const data=read('data.json'),retrieval=read('retrieval-data.json'),generation=read('semantic-generation.json');
const lab=data.nodes.filter(p=>p.lab),nodeMap=new Map(data.nodes.map(p=>[p.id,p]));
assert(lab.length>0,'No laboratory papers');
assert.equal(data.meta.semantic.method,'local');
assert.equal(data.meta.semantic.model,'specter2_proximity');
assert.equal(data.meta.semantic.dimensions,768);
assert.equal(data.meta.semantic.base,'allenai/specter2_base');
assert.equal(data.meta.semantic.adapter,'allenai/specter2');
assert(data.meta.semantic.base_revision&&data.meta.semantic.adapter_revision,'Missing pinned model revisions');
assert(generation&&typeof generation==='object','Missing generation report');
assert.equal(generation.coverage.total,data.nodes.length,'Generation report scope differs from network nodes');
assert.equal(generation.coverage.success,generation.coverage.items.filter(p=>p.status==='success').length,'Generation success count');
assert.equal(generation.coverage.success+generation.coverage.explained_failure,generation.coverage.total,'Unaccounted generation failures');
assert.equal(generation.model.ready,generation.coverage.success,'Model readiness count');
assert.equal(generation.model.papers,data.nodes.length,'Model paper scope');
assert.equal(generation.model.lab_ready,lab.length,'Generation report has laboratory vector gaps');
assert.equal(generation.model.lab_title_only,lab.filter(p=>!p.abstract).length,'Title-only laboratory input count');
const generated=new Map(generation.coverage.items.map(p=>[p.id,p]));
assert.equal(generated.size,data.nodes.length,'Generation rows duplicated or missing');
const rows=new Map(retrieval.papers.map(p=>[p.id,p]));
for(const p of lab){
 assert.equal(p.semantic_status,'available',p.title);
 assert.equal(p.semantic_source,'本地 SPECTER2',p.title);
 assert.equal(p.semantic_model,'specter2_proximity',p.title);
 assert.deepEqual(p.semantic_input.fields,p.abstract?['title','abstract']:['title'],p.title);
 assert.match(p.semantic_input.sha256,/^[a-f0-9]{64}$/i,p.title);
 assert(Number.isInteger(p.semantic_input.tokens)&&p.semantic_input.tokens>0,p.title);
 assert.equal(typeof p.semantic_input.truncated,'boolean',p.title);
 const report=generated.get(p.id);assert(report,`Missing generation report row ${p.id}`);
 assert.equal(report.status,'success',p.title);
 assert.equal(report.dimensions,768,p.title);
 assert(report.vector_key,`Missing vector cache key ${p.title}`);
 assert.deepEqual(report.input,p.semantic_input,p.title);
 const r=rows.get(p.id);assert(r,`Missing retrieval row ${p.id}`);
 assert.equal(r.fields.vector.state,'ready',p.title);
 assert.equal(r.fields.vector.model,p.semantic_model,p.title);
 assert(r.fields.vector.sources.some(s=>s.name==='本地 SPECTER2'&&s.url==='https://huggingface.co/allenai/specter2'),p.title);
 assert(r.providers.includes('本地 SPECTER2'),p.title);
 assert.deepEqual(r.fields.vector.routes,[],`Stale vector failure routes: ${p.title}`);
 assert.doesNotMatch(r.fields.vector.explanation,/未查询|缺少 DOI|返回 null|向量查询未完成/,p.title);
}
for(const e of data.edges){
 if(['semantic','citation'].includes(e.kind))assert(nodeMap.get(e.source)?.lab||nodeMap.get(e.target)?.lab,`External-only ${e.kind} edge ${e.id}`);
}
const W={};const context={window:W,console};
for(const file of ['author-identities.js','author-groups.js','author-identity-resolver.js','paper-author-interest.js','paper-density.js'])vm.runInNewContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
const interest=W.createPaperAuthorInterest({resolveAuthors:W.resolveAtlasPaperAuthors});
const eligible=data.nodes.filter(p=>{
 const adopted=rows.get(p.id)?.fields.year.adoptedValue;const y=Number.isFinite(adopted)?adopted:p.year;
 return interest.keep(p,W.ATLAS_AUTHOR_GROUPS.defaultPaperInterest)&&(y==null||y>=2023&&y<=2027);
});
const ids=new Set(eligible.map(p=>p.id));
const candidates=data.edges.filter(e=>e.kind==='semantic'&&ids.has(e.source)&&ids.has(e.target));
const limited=W.coverSemanticPapers(eligible,candidates,5);
const degrees=new Map(eligible.map(p=>[p.id,0]));
for(const e of limited.edges){degrees.set(e.source,degrees.get(e.source)+1);degrees.set(e.target,degrees.get(e.target)+1);}
const selectedLab=eligible.filter(p=>p.lab),covered=selectedLab.filter(p=>degrees.get(p.id)>=2);
assert(selectedLab.length>0,'Default filter has no laboratory papers');
assert(covered.length/selectedLab.length>=.95,`Two-edge coverage ${covered.length}/${selectedLab.length}`);
const retained=eligible.filter(p=>p.lab||degrees.get(p.id)>0);
const meanDegree=2*limited.edges.length/retained.length;
assert(limited.edges.length<=5*retained.length);assert.equal(limited.stats.top_k,5);assert.equal(limited.stats.threshold,null);
const oldMissing=[];
function collect(value){
 if(!value||typeof value!=='object')return;
 if(value.reason==='no_supported_public_identifier'){
  const p=nodeMap.get(value.id||value.paper_id);if(p?.lab)oldMissing.push(p.id);
 }
 for(const v of Object.values(value))if(v&&typeof v==='object')collect(v);
}
const history=JSON.parse(fs.readFileSync(path.join(__dirname,'semantic-api-history.json'),'utf8'));
collect(history['08_content_vector']);
const samples=[...new Set(oldMissing)];
assert(samples.length>0,'No old unsupported-identifier laboratory samples found');
for(const id of samples){assert.equal(nodeMap.get(id).semantic_status,'available');assert(data.edges.some(e=>e.kind==='semantic'&&(e.source===id||e.target===id)),`Old identifier gap remains isolated ${id}`);}
async function browserChecks(){
 const {chromium}=require('C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
 const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};
  fs.readFile(file,(err,body)=>{res.writeHead(err?404:200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});res.end(err?'Missing':body);});
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try{
  browser=await chromium.launch({headless:true,executablePath:'C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe'});
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const base=`http://127.0.0.1:${server.address().port}`;
  await page.goto(base+'/index.html?relation=semantic&from=2023&to=2027');
  await page.waitForFunction(()=>document.getElementById('relation')?.value==='semantic'&&document.getElementById('visible-count')?.textContent);
  assert.match(await page.locator('#relation-explanation').innerText(),/本地|SPECTER2/);
  assert.equal(await page.locator('#empty').isVisible(),false);
  assert.equal(await page.locator('#author-relation option[value="semantic"]').count(),1);
  await page.goto(base+'/retrieval.html');
  await page.waitForFunction(()=>document.querySelector('#source option[value="本地 SPECTER2"]'));
  await page.locator('#source').selectOption('本地 SPECTER2');
  await page.waitForFunction(()=>document.querySelector('#data-table')?.getAttribute('aria-label')?.includes('论文'));
  assert.match(await page.locator('#table-body').innerText(),/SPECTER2/);
  await page.goto(base+'/retrieval.html?paper='+encodeURIComponent(samples[0]));
  await page.waitForFunction(()=>document.querySelector('#field-vector'));
  assert.match(await page.locator('#detail').innerText(),/本地 SPECTER2/);
  assert.equal(errors.length,0,errors.join('\n'));
 }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
}
browserChecks().then(()=>{const result={lab:lab.length,defaultLab:selectedLab.length,twoEdgeCoverage:covered.length/selectedLab.length,meanDegree,oldIdentifierSamples:samples.length,browser:'passed'};fs.writeFileSync(path.join(__dirname,'local-semantic-browser-check.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));}).catch(err=>{console.error(err);process.exitCode=1;});
