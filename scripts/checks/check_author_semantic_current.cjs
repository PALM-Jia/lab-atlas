const fs=require('fs'),assert=require('assert');
const {cy,el,window,detailClick,views}=require('./frontend-fixture.cjs')();
views.find(v=>v.dataset.view==='authors').onclick();
el('author-relation').onchange({target:{value:'semantic'}});
assert(cy.edges().length>0);assert(cy.edges().every(e=>e.data('kind')==='author_semantic'));
assert(cy.nodes().every(n=>n.degree()>=5),'default authors retain their five closest candidates');
assert(cy.edges().length<=cy.nodes().length*5,'only union of per-author top five');
const initial={nodes:cy.nodes().length,edges:cy.edges().length,threshold:cy.edges()[0].data('evidence').threshold};
const scoreMap=new Map(window.ATLAS_DATA.edges.filter(e=>e.kind==='semantic').map(e=>[[e.source,e.target].sort().join('|'),e.score]));
for(const edge of cy.edges()){
 const d=edge.data(),[a,b]=d.evidence.profiles;let numerator=0,denominator=0,count=0;
 for(const x of a.paper_contributions)for(const y of b.paper_contributions){if(x.paper_id===y.paper_id)continue;const score=scoreMap.get([x.paper_id,y.paper_id].sort().join('|'));if(score==null)continue;const w=x.weight*y.weight;numerator+=w*score;denominator+=w;count++;}
 assert(Math.abs(d.score-numerator/denominator)<1e-12);assert.equal(d.evidence.pair_count,count);
 assert.equal(d.evidence.threshold,null);assert.equal(d.evidence.threshold_rule,'top_k_union');assert.equal(d.evidence.top_k,5);
}
const e=cy.edges()[0];detailClick({edge:e.id()});assert(el('detail-content').innerHTML.includes('代表论文对'));assert(el('detail-content').innerHTML.includes('data-paper=')&&el('detail-content').innerHTML.includes('data-edge='),'semantic evidence links expose both edge and paper targets');
const id=e.data('evidence').paper_pairs[0].source;detailClick({edge:e.id(),paper:id});assert(cy.getElementById(e.id()).hasClass('focus'));assert(el('detail-content').innerHTML.includes(window.ATLAS_DATA.nodes.find(p=>p.id===id).title));
el('first-author-only').onclick();assert(cy.edges().every(e=>e.data('evidence').profiles.every(p=>p.paper_contributions.every(c=>c.weight===1))));
el('first-author-only').onclick();assert(cy.edges().every(e=>e.data('evidence').profiles.every(p=>p.paper_contributions.every(c=>c.weight===1))));

const pairs=cy.edges().flatMap(e=>e.data('evidence').paper_pairs);for(const p of pairs)for(const id of [p.source,p.target])assert(window.ATLAS_DATA.nodes.some(n=>n.id===id&&n.lab));
cy.destroy();console.log('PASS: default author semantic graph',initial,'all scores independently recomputed; three-state authorship and evidence navigation');
