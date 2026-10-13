const fs=require('fs'),assert=require('assert'),vm=require('vm');
const {cy,el,views,window,allYears}=require('./frontend-fixture.cjs')();
assert.equal(window.atlasStudentFirstAuthor([{id:'mentor',name:'Yuheng Jia'},{id:'student',name:'Student'}]).id,'student');
assert.equal(window.atlasStudentFirstAuthor([{id:'student',name:'Student'},{id:'mentor',name:'Yuheng Jia'}]).id,'student');
assert.equal(window.atlasStudentFirstAuthor([{id:'mentor',name:'Yuheng Jia'}]).id,'mentor');
allYears();views[1].onclick();
el('author-relation').onchange({target:{value:'keywords'}});
const original=new Map(cy.nodes().map(n=>[n.id(),n.data('papers').slice()]));
assert([...original.values()].some(ids=>ids.length>1));
el('first-author-only').onclick();
let removed=0;
for(const n of cy.nodes()){
 for(const id of n.data('papers')){
  const p=window.ATLAS_DATA.nodes.find(p=>p.id===id);
  assert.equal(n.id(),'a-'+window.atlasStudentFirstAuthor(window.resolveAtlasPaperAuthors(p)).id,'only student first authors contribute');
 }
 removed+=(original.get(n.id())?.length||0)-n.data('papers').length;
}
assert(removed>0,'non-first-author papers removed');
for(const edge of cy.edges())for(const profile of edge.data('evidence').profiles)
 assert(profile.paper_contributions.every(p=>p.first_author&&p.weight===1));
assert(!el('relation-explanation').innerHTML.includes('其他署名0.2'));
el('first-author-only').onclick();
for(const edge of cy.edges())for(const profile of edge.data('evidence').profiles)assert(profile.paper_contributions.every(p=>p.weight===1),'all authors equal weight');
el('first-author-only').onclick();
assert.deepEqual(new Map(cy.nodes().map(n=>[n.id(),n.data('papers').slice()])),original,'toggle restores all contributions');
console.log('First-author profile filtering passed');
cy.destroy();
