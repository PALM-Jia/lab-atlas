const fs=require('fs'),assert=require('node:assert/strict');
const select=require('../outputs/paper-atlas/paper-density.js').selectTopEdges;
const all=[];for(let i=0;i<12;i++)for(let j=i+1;j<12;j++)all.push({id:`e-${i}-${j}`,source:String(i),target:String(j),score:(i+j)%6/10});
const expected=new Set();for(let i=0;i<12;i++)for(const e of all.filter(e=>e.source===String(i)||e.target===String(i)).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5))expected.add(e.id);
assert.deepEqual(new Set(select(all).map(e=>e.id)),expected);assert.deepEqual(select(all).map(e=>e.id),select([...all].reverse()).map(e=>e.id));assert(all.every(e=>!e.evidence),'candidate evidence not mutated');
const topic=require('../outputs/paper-atlas/author-relations.js');
const authors=[{id:'a',papers:['p1'],paperWeights:{p1:1}},{id:'b',papers:['p2','p3'],paperWeights:{p2:.2,p3:1}}];
const papers=[{id:'p1',tags:['labels']},{id:'p2',tags:['labels']},{id:'p3',tags:['clustering']}];const low=topic({authors,papers});assert.equal(low.length,1);assert(low[0].score<.6,'low but evidenced topic overlap must survive');assert.equal(low[0].evidence.threshold,null);
const fixture=fs.readFileSync('work/check_frontend_viewport.cjs','utf8').split('const labCount=')[0];
const {cy,el,views,detailClick}=new Function('require',fixture+';return {cy,el,views,detailClick};')(require);
const counts=[];
for(const view of ['authors','papers','timeline']){
 views.find(v=>v.dataset.view===view).onclick();
 for(const mode of view==='authors'?['coauthor','semantic','topic','keywords']:['citation','author','semantic']){
  el(view==='authors'?'author-relation':'relation').onchange({target:{value:mode}});
  assert(cy.edges().length>0,view+'/'+mode);assert(cy.edges().every(e=>e.data('evidence').top_k===5&&e.data('evidence').threshold===null));
  assert(!/中位数|60.0%|95%|平均.*4/.test(el('relation-explanation').innerHTML));
  assert(el('relation-explanation').innerHTML.includes('任一端选中'));
  const choices=new Map();for(const edge of cy.edges())for(const id of edge.data('evidence').selected_by)choices.set(id,(choices.get(id)||0)+1);assert([...choices.values()].every(n=>n<=5));
  if(view!=='authors')assert(cy.edges().every(e=>e.source().data('lab')||e.target().data('lab')));
  counts.push({view,mode,nodes:cy.nodes().length,edges:cy.edges().length});
 }
}
cy.destroy();console.log(JSON.stringify(counts));console.log('PASS: exact shared top-five selection, weak topic evidence, no candidate mutation, all ten view/rule combinations');
