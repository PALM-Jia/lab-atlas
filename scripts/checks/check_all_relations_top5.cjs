const fs=require('fs'),assert=require('node:assert/strict');
const select=require('../../outputs/paper-atlas/paper-density.js').selectTopEdges;
const all=[];for(let i=0;i<12;i++)for(let j=i+1;j<12;j++)all.push({id:`e-${i}-${j}`,source:String(i),target:String(j),score:(i+j)%6/10});
const expected=new Set();for(let i=0;i<12;i++)for(const e of all.filter(e=>e.source===String(i)||e.target===String(i)).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5))expected.add(e.id);
assert.deepEqual(new Set(select(all).map(e=>e.id)),expected);assert.deepEqual(select(all).map(e=>e.id),select([...all].reverse()).map(e=>e.id));assert(all.every(e=>!e.evidence),'candidate evidence not mutated');
const topic=require('../../outputs/paper-atlas/author-relations.js');
const authors=[{id:'a',papers:['p1'],paperWeights:{p1:1}},{id:'b',papers:['p2','p3'],paperWeights:{p2:.2,p3:1}}];
const papers=[{id:'p1',tags:['labels']},{id:'p2',tags:['labels']},{id:'p3',tags:['clustering']}];const keywordData={vocabulary:[{id:'labels',dimension:'research_task',name:'Labels'},{id:'clustering',dimension:'research_task',name:'Clustering'}],statuses:{p1:'annotated',p2:'annotated',p3:'annotated'},papers:{p1:[{id:'labels'}],p2:[{id:'labels'}],p3:[{id:'clustering'}]}};const low=topic({authors,papers,keywordData});assert.equal(low.length,1);assert(low[0].score<.6,'low but evidenced topic overlap must survive');assert.equal(low[0].evidence.threshold,null);
const {cy,el,views,detailClick,window,timelineCalls}=require('./frontend-fixture.cjs')();
const counts=[];
for(const view of ['authors','papers','timeline']){
 views.find(v=>v.dataset.view===view).onclick();
 for(const mode of view==='authors'?['coauthor','semantic','topic','keywords']:['citation','author','semantic']){
  el(view==='authors'?'author-relation':'relation').onchange({target:{value:mode}});
  if(view==='timeline'){
   const payload=timelineCalls.filter(c=>c[0]==='data').at(-1)[1];
   const annual=window.ATLAS_TIMELINE_HISTORY.buildAnnualSlices(payload.papers,payload.edges,payload.history||window.ATLAS_CITATION_HISTORY,{yearFrom:payload.yearFrom||payload.yearBounds?.[0],yearTo:payload.yearTo||payload.yearBounds?.[1],lowerYearBucket:payload.lowerYearBucket});
   assert(annual.slices.length>0,'timeline has annual slices');
   let edgeCount=0;
   for(const slice of annual.slices){
    const choices=new Map();
    for(const e of slice.edges){assert.equal(e.evidence.top_k,5);assert.equal(e.evidence.threshold,null);for(const id of e.evidence.selected_by)choices.set(id,(choices.get(id)||0)+1);}
    assert([...choices.values()].every(n=>n<=5),'each year independently selects at most five neighbors');
    edgeCount+=slice.edges.length;
   }
   assert(edgeCount>0,view+'/'+mode);
   counts.push({view,mode,nodes:payload.papers.length,annualSlices:annual.slices.length,annualEdges:edgeCount});
   continue;
  }
  assert(cy.edges().length>0,view+'/'+mode);assert(cy.edges().every(e=>e.data('evidence').top_k===5&&e.data('evidence').threshold===null));
  const choices=new Map();for(const edge of cy.edges())for(const id of edge.data('evidence').selected_by)choices.set(id,(choices.get(id)||0)+1);assert([...choices.values()].every(n=>n<=5));
  if(view!=='authors')assert(cy.edges().every(e=>e.source().data('lab')||e.target().data('lab')));
  counts.push({view,mode,nodes:cy.nodes().length,edges:cy.edges().length});
 }
}
cy.destroy();console.log(JSON.stringify(counts));console.log('PASS: exact shared top-five selection, weak topic evidence, no candidate mutation, all ten view/rule combinations');
