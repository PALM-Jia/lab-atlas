const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const root='outputs/paper-atlas/',D=JSON.parse(fs.readFileSync(root+'retrieval-data.json','utf8'));
assert.deepEqual(D.meta.coverage,{total:144,authors:138,venue:138,references:79,referenceIDs:3593,referenceTitles:2449,keywords:116,citingTotal:2077,citingIDs:2077,citingTitles:2077,openalex:118,semantic_scholar:116,crossref:100});
const graph=JSON.parse(fs.readFileSync(root+'data.json','utf8'));
const graphIDs=new Set(graph.nodes.map(p=>p.openalex?.split('/').pop()||p.id));
const outsideGraph=D.papers.flatMap(p=>p.fields.citing.ids).filter(id=>!graphIDs.has(id));
assert.equal(outsideGraph.length,1250);
assert(outsideGraph.every(id=>D.bibliography[id]?.title&&D.bibliography[id]?.source==='OpenAlex'));
const evidenceContext={window:{}};vm.runInNewContext(fs.readFileSync(root+'network-evidence.js','utf8'),evidenceContext);
const networkEvidence=evidenceContext.window.ATLAS_NETWORK_EVIDENCE;
for(const p of D.papers){assert.deepEqual(JSON.parse(JSON.stringify(networkEvidence.papers[p.id].fields.references)),p.fields.references);assert.deepEqual(JSON.parse(JSON.stringify(networkEvidence.papers[p.id].fields.citing)),p.fields.citing);}
assert.equal(networkEvidence.bibliography[outsideGraph[0]].title,D.bibliography[outsideGraph[0]].title);
for(const page of ['index.html','retrieval.html'])assert(fs.readFileSync(root+page,'utf8').includes('href="theme.css"'));
assert.equal(D.authors.length,216);
assert.equal(D.authors.filter(a=>a.state==='unlinked').length,14);
assert(!D.authors.some(a=>a.id==='person-e6da050b2d62'));
assert.equal(D.authors.filter(a=>a.state==='review').length,2);
const normalizeVenue=require('./venue-normalization.cjs');
for(const alias of ['NeurIPS','NIPS','neural information processing systems','Advances in Neural Information Processing Systems'])assert.equal(normalizeVenue(alias).label,'NeurIPS');
assert.notEqual(normalizeVenue('ICML').id,normalizeVenue('ICMLC').id);
assert.notEqual(normalizeVenue('CVPR').id,normalizeVenue('CVPR Findings').id);
assert.notEqual(normalizeVenue('EMNLP').id,normalizeVenue('EMNLP Findings').id);
assert.notEqual(normalizeVenue('ECCV').id,normalizeVenue('Lecture notes in computer science').id);
const neurips=D.papers.find(p=>p.id==='lab-dec46f74923a').fields.venue;
assert.equal(neurips.different,false);assert.equal(neurips.observations.length,1);
assert.equal(neurips.observations[0].value,'NeurIPS');
assert(neurips.observations[0].sources.some(s=>s.originalValue==='neural information processing systems'));
assert(neurips.observations[0].sources.some(s=>s.originalValue==='NeurIPS'));
assert.equal(D.papers.find(p=>p.id==='lab-af85f8a01211').fields.venue.relationship,'预印本／发表记录');
const calibrated=D.papers.find(p=>p.id==='lab-af85f8a01211');assert.equal(calibrated.fields.venue.adoptedValue,'ICLR');assert.equal(calibrated.fields.year.adoptedValue,2025);assert(calibrated.fields.year.observations.some(o=>o.value===2024&&!o.adopted));assert.equal(D.bibliography[calibrated.id].year,2025);
assert.equal(D.papers.find(p=>p.id==='lab-80376da04947').fields.venue.relationship,'会议／论文集系列');
for(const p of D.papers){
 assert.equal(p.fields.references.total,p.fields.references.value.length);
 assert.equal(p.fields.references.parsed,p.fields.references.value.filter(id=>D.bibliography[id]).length);
 assert.equal(p.fields.references.sources[0].name,'OpenAlex');
 assert.equal(p.fields.citing.ids.length,p.fields.citing.value||0);
 assert.equal(p.fields.citing.parsed,p.fields.citing.ids.filter(id=>D.bibliography[id]).length);
 for(const key of ['openalex','semantic_scholar','crossref']){
  const f=p.fields[key];if(f.state==='ready')assert.equal(typeof f.value,'number');else assert.equal(f.value,null);
 }
 for(const a of p.fields.authors.value)if(!a.excluded)assert(D.authors.some(person=>person.id===a.id));
}
for(const a of D.authors){
 const expected=new Map();let total=0;
 for(const id of a.papers){const p=D.papers.find(p=>p.id===id);if(!p.fields.keywords.value.length)continue;const weight=p.fields.authors.value[0]?.id===a.id?1:.2;total+=weight;for(const k of p.fields.keywords.value)expected.set(k.id,(expected.get(k.id)||0)+weight);}
 assert.equal(a.keywords.length,expected.size);
 for(const k of a.keywords)assert(Math.abs(k.weight-expected.get(k.id)/total)<1e-10);
}
const storage=new Map(),elements=new Map(),events={},tabs=['papers','authors','external'].map(view=>({dataset:{view},classList:{toggle(){}}}));
function el(id){if(!elements.has(id))elements.set(id,{id,innerHTML:'',textContent:'',hidden:false,value:'',style:{},attributes:{},setAttribute(k,v){this.attributes[k]=v;},getAttribute(k){return this.attributes[k];},classList:{toggle(){}},events:{},addEventListener(type,fn){this.events[type]=fn;},querySelector(){return {style:{width:'330px'}};},scrollIntoView(){}});return elements.get(id);}
const document={getElementById:el,querySelectorAll:()=>tabs,addEventListener:(type,fn)=>events[type]=fn,createElement:()=>({click(){}})};
const window={ATLAS_RETRIEVAL:D,localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},location:{search:''}};
const exportsCaptured=[];
const ctx=vm.createContext({window,document,URLSearchParams,Blob:class extends Blob{constructor(parts,options){super(parts,options);exportsCaptured.push(parts.join(''));}},URL:{createObjectURL:()=>'',revokeObjectURL(){}},setTimeout:fn=>fn()});
vm.runInContext(fs.readFileSync(root+'search-match.js','utf8'),ctx);vm.runInContext(fs.readFileSync(root+'retrieval.js','utf8'),ctx);
const count=n=>assert.match(el('data-table').getAttribute('aria-label'),new RegExp(' '+n+' /'));
const change=(id,value)=>el(id).onchange({target:{value}});
const click=(selector,dataset)=>events.click({target:{closest:s=>s===selector?{dataset}:null}});
el('reset').onclick();change('page-size','0');click('[data-sort]',{sort:'year'});
const tableOrder=()=>el('table-body').innerHTML.split('<tr ').slice(1).map(row=>D.papers.find(p=>p.id===row.match(/data-paper="([^"]+)"/)[1]));
const preprints=D.papers.filter(p=>p.fields.year.isPreprint).length;
assert.equal(preprints,9);
const yearProblem=p=>p.fields.year.state==='review'||(p.fields.year.different&&!p.fields.year.relationship);
const yearGroups=()=>[tableOrder().filter(yearProblem),tableOrder().filter(p=>!yearProblem(p))];
for(const rows of yearGroups()){const n=rows.filter(p=>p.fields.year.isPreprint).length;assert(rows.slice(0,n).every(p=>p.fields.year.isPreprint));}
click('[data-sort]',{sort:'year'});
for(const rows of yearGroups()){const n=rows.filter(p=>p.fields.year.isPreprint).length;if(n)assert(rows.slice(-n).every(p=>p.fields.year.isPreprint));}
assert(el('table-head').innerHTML.includes('data-key="citations"'));assert(!el('table-head').innerHTML.includes('data-key="semantic_scholar"'));
el('reset').onclick();
assert.equal(D.papers.filter(p=>p.fields.citations.state==='ready').length,122);
const citationDifferences=D.papers.filter(p=>p.fields.citations.different).length;
assert.equal(citationDifferences,97);
const renamed=D.papers.find(p=>p.id==='lab-1ba64af37485');
assert.equal(renamed.fields.year.adoptedValue,'预印');
assert.equal(renamed.fields.year.observations[0].value,'预印');
assert(renamed.fields.year.observations.some(o=>o.value===2026&&o.sources.some(s=>s.name==='OpenAlex')));
assert(renamed.fields.year.different);
for(const p of D.papers){
 const f=p.fields.citations;
 if(f.state==='ready'){
  assert.equal(f.observations.filter(o=>o.adopted).length,1);
  assert.equal(f.observations[0].value,f.adoptedValue);
  if(f.adoptedSources.some(s=>s.name==='OpenAlex 施引查询'))assert.equal(f.adoptedValue,p.fields.citing.total);
 }
}
assert(el('coverage').innerHTML.includes('68.2%'));
assert(el('coverage').innerHTML.includes('100.0%'));
assert.equal(renamed.fields.title.observations.length,2);
el('search').oninput({target:{value:'Learning Adaptive and Visually Aligned Conditions'}});count(1);
click('[data-paper]',{paper:renamed.id});
assert(el('detail-content').innerHTML.includes('被引次数'));
assert(el('detail-content').innerHTML.includes('id="citing"'));
assert(el('detail-content').innerHTML.includes('class="adopted">预印'));
assert(el('detail-content').innerHTML.includes('>2026</span>'));
assert(!el('table-body').innerHTML.includes('预印本 · 按最新排序'));
assert(!el('detail-content').innerHTML.includes('undefined'));
el('reset').onclick();change('field','citations');change('status','missing');count(22);
change('status','different');count(citationDifferences);
el('reset').onclick();
count(144);assert.equal((el('table-body').innerHTML.match(/<tr /g)||[]).length,50);
change('field','authors');change('status','missing');count(6);
el('reset').onclick();change('field','keywords');change('status','missing');
assert.equal(Number(el('data-table').getAttribute('aria-label').split(' ')[1]),D.papers.filter(p=>p.fields.keywords.state==='missing').length);
el('reset').onclick();change('field','references');change('status','empty');count(39);
el('reset').onclick();change('page-size','25');assert.equal((el('table-body').innerHTML.match(/<tr /g)||[]).length,25);el('next').onclick();assert.match(el('page-count').textContent,/2 \/ 6/);
tabs[1].onclick();count(216);change('field','papers');change('status','unlinked');count(14);
tabs[1].onclick();change('group','current');count(D.authors.filter(a=>a.group==='current').length);
const author=D.authors.find(a=>a.papers.length&&a.keywords.length);click('[data-author]',{author:author.id});assert(!el('detail').hidden);assert(el('detail-content').innerHTML.includes((author.keywords[0].weight*100).toFixed(1)+'%'));
const p=D.papers.find(p=>p.fields.references.total>p.fields.references.parsed);click('[data-paper]',{paper:p.id});count(1);assert(el('detail-content').innerHTML.includes(p.fields.references.value.find(id=>!D.bibliography[id])));
for(const k of p.fields.keywords.value)assert(el('detail-content').innerHTML.includes(k.name.replace(/&/g,'&amp;')));
el('close-detail').onclick();assert(el('detail').hidden);
el('reset').onclick();el('search').oninput({target:{value:'Mixed Blessing'}});count(1);el('export').onclick();
const mixed=D.papers.find(p=>p.title.includes('Mixed Blessing'));
for(const id of mixed.fields.citing.ids)assert(exportsCaptured.at(-1).includes(id));
assert(!el('table-head').innerHTML.includes('采集缺口'));
el('reset').onclick();el('search').oninput({target:{value:'Mixed Blessing'}});
const widthHandle={dataset:{resize:'title'}};el('table-head').events.keydown({target:{closest:()=>widthHandle},key:'ArrowRight',preventDefault(){}});
assert.equal(JSON.parse(storage.get('lab-atlas-retrieval-v1')).widths.papers.title,350);
vm.runInContext(fs.readFileSync(root+'search-match.js','utf8'),ctx);vm.runInContext(fs.readFileSync(root+'retrieval.js','utf8'),ctx);count(1);assert.match(el('columns').innerHTML,/width:350px/);
assert(fs.readFileSync(root+'index.html','utf8').includes('href="retrieval.html"'));
for(const file of ['retrieval.html','retrieval.js','retrieval.css','retrieval-data.js'])assert(fs.existsSync(root+file));
tabs[2].onclick();count(1529);assert(el('table-head').innerHTML.includes('SPECTER2 语义向量'));assert(!el('table-head').innerHTML.includes('采集缺口'));change('field','vector');change('status','missing');count(0);change('field','abstract');change('status','missing');count(D.external.filter(p=>p.fields.abstract.state==='missing').length);const external=D.external.find(p=>p.fields.abstract.state==='missing');click('[data-paper]',{paper:external.id});assert(el('detail-content').innerHTML.includes('field-vector'));el('export').onclick();assert(exportsCaptured.at(-1).includes('SPECTER2 语义向量'));tabs[0].onclick();assert(el('table-head').innerHTML.includes('OpenAlex 研究主题'));change('field','vector');change('status','missing');count(0);
console.log('PASS: coverage, field provenance, citation null/zero semantics, author identities, weighted profiles, filtering, paging, cross-table details, CSV, column resize and state memory.');

for(const rows of [D.papers,D.external]){
 assert.equal(rows.filter(p=>p.fields.vector.state==='ready').length,rows.length);
 for(const p of rows){const f=p.fields.vector;assert.equal(f.model,'specter2_proximity');assert(f.sources.some(s=>s.name==='本地 SPECTER2'&&s.url==='https://huggingface.co/allenai/specter2'));assert(p.providers.includes('本地 SPECTER2'));assert.deepEqual(f.routes,[]);assert(f.input.fields.includes('title'));assert(f.explanation.includes(f.input.fields.includes('abstract')?'标题＋摘要':'仅标题'));}
 for(const p of rows){assert(p.fields.topics&&p.fields.directions&&p.fields.vector);assert(p.fields.vector.explanation);if(p.fields.vector.state==='ready')assert.equal(p.fields.vector.dimensions,768);}
}
const parsedName=D.papers.find(p=>p.id==='lab-6e4e588f3743').fields.authors;assert.equal(parsedName.different,false);assert(parsedName.observations[0].sources.some(s=>s.rawValue?.includes('Haoye')));
const typo=D.papers.find(p=>p.id==='lab-bc765488bcf7').fields.authors;assert.equal(typo.different,false);assert(typo.observations[0].sources.some(s=>s.originalValue?.includes('Jing Wnag')));
assert(D.papers.find(p=>p.id==='lab-532faa4a2fc2').fields.authors.different,'real member difference remains');
assert(D.papers.find(p=>p.id==='lab-c0b4fa3ab5d5').fields.authors.different,'author order remains significant');
const localVector=D.papers.find(p=>p.id==='lab-dec46f74923a').fields.vector;assert.equal(localVector.state,'ready');assert.equal(localVector.identifier,null);assert.deepEqual(localVector.routes,[]);
console.log('PASS: network dependency coverage, local vector provenance and conservative author-list equivalence.');

el('reset').onclick();change('field','authors');change('status','different');
assert(el('table-body').innerHTML.includes('data-field="authors" class="cell-conflict"'));
el('reset').onclick();change('field','abstract');change('status','missing');
assert(el('table-body').innerHTML.includes('data-field="abstract" class="cell-missing"'));
tabs[2].onclick();change('field','abstract');change('status','missing');
assert(el('table-body').innerHTML.includes('data-field="abstract" class="cell-missing"'));
tabs[1].onclick();change('field','identity');change('status','review');
assert(el('table-body').innerHTML.includes('data-field="identity" class="cell-conflict"'));
el('reset').onclick();tabs[1].onclick();change('field','papers');change('status','unlinked');
assert(el('table-body').innerHTML.includes('data-field="papers" class="cell-missing"'));
tabs[0].onclick();el('reset').onclick();change('field','citing');change('status','empty');
assert(!el('table-body').innerHTML.includes('data-field="citing" class="cell-missing"'));
assert(fs.readFileSync(root+'theme.css','utf8').includes('tr:is(:hover,.selected) td.cell-conflict'));
console.log('PASS: conflict/missing cell tints across paper, author and external tabs; confirmed zero citing counts remain normal.');

function assertProblemFirst(key){
 const rows=el('table-body').innerHTML.split('<tr ').slice(1);
 const flags=rows.map(row=>row.includes(`data-field="${key}" class="cell-conflict"`)||row.includes(`data-field="${key}" class="cell-missing"`));
 assert(flags.some(Boolean));assert(flags.some(f=>!f));
 assert(flags.every((f,i)=>!f||flags.slice(0,i).every(Boolean)),'problem cells must precede normal cells: '+key);
}
for(const [tab,key] of [[0,'authors'],[0,'abstract'],[0,'citations'],[1,'identity'],[1,'papers'],[2,'abstract']]){
 tabs[tab].onclick();change('page-size','0');click('[data-sort]',{sort:key});assertProblemFirst(key);
 click('[data-sort]',{sort:key});assertProblemFirst(key);
}
console.log('PASS: selected-column problems sort first in both value directions across all tabs.');

for(const tab of tabs){tab.onclick();const head=el('table-head').innerHTML;assert(head.includes('到位率：'));assert(!head.includes('操作：'));const headings=head.split('<th ').slice(1);assert(headings.every(h=>/title="[^"]+"/.test(h)));}
const unqueried=D.papers.filter(p=>p.fields.vector.explanation.includes('未查询'));
assert.equal(unqueried.length,0);assert(D.papers.every(p=>p.fields.vector.state==='ready'&&p.fields.vector.routes.length===0));
console.log('PASS: all column headings explain meaning and collection; local vectors contain no stale missing-identifier reasons.');

el('reset').onclick();
const vectorCoverage=`当前筛选结果 ${D.papers.length} / ${D.papers.length}`;
assert(el('table-head').innerHTML.includes('class="column-coverage">(100.0%)'));
assert(el('table-head').innerHTML.includes(vectorCoverage));
change('page-size','25');assert(el('table-head').innerHTML.includes(vectorCoverage));
change('field','abstract');change('status','missing');const missingAbstractCount=D.papers.filter(p=>p.fields.abstract.state==='missing').length;assert(el('table-head').innerHTML.includes(`当前筛选结果 0 / ${missingAbstractCount}`));
el('search').oninput({target:{value:'zzzz-no-matching-paper'}});assert(el('table-head').innerHTML.includes('class="column-coverage">(—)'));
for(const tab of tabs){tab.onclick();assert.equal((el('table-head').innerHTML.match(/class="column-coverage"/g)||[]).length,(el('table-head').innerHTML.match(/<th /g)||[]).length);}
console.log('PASS: each column reports filtered full-result coverage, independent of pagination, with empty results handled.');

tabs[0].onclick();change('page-size','0');
assert(el('table-body').innerHTML.includes('citation-primary'));
assert(el('table-body').innerHTML.includes('citation-alternatives'));
assert(!el('table-body').innerHTML.includes('Google Scholar · 未采集'));
const citationPaper=D.papers.find(p=>p.fields.citations.different);
el('search').oninput({target:{value:citationPaper.title}});
assert(el('table-body').innerHTML.includes(`class="count-link citation-count adopted" data-paper="${citationPaper.id}"`));
click('[data-paper]',{paper:citationPaper.id,section:'field-citations'});
assert(el('detail-content').innerHTML.includes('id="field-citations"'));
assert(!el('detail-content').innerHTML.includes('Google Scholar · 未采集'));
console.log('PASS: compact citation counts preserve adopted/source values and move full query details to the detail panel.');

el('reset').onclick();change('source','本地 SPECTER2');count(D.papers.length);
assert(el('table-body').innerHTML.includes('SPECTER2 · 768维'));
assert(!el('table-body').innerHTML.includes('<div class="source">未发起查询'));
const titleOnlyVector=D.papers.find(p=>p.fields.vector.input.fields.length===1);assert(titleOnlyVector);
click('[data-paper]',{paper:titleOnlyVector.id,section:'field-vector'});
assert(el('detail-content').innerHTML.includes('仅标题'));
assert(el('detail-content').innerHTML.includes('本地 SPECTER2'));
assert(!el('detail-content').innerHTML.includes('未查询：缺少 DOI/arXiv 查询标识。'));
assert(!el('detail-content').innerHTML.includes('paperId／标题兜底未执行'));
assert(!el('table-head').innerHTML.includes('尚未接入'));
console.log('PASS: local-vector source filtering and title-only inputs appear in cells and details without stale API failure reasons.');
