const assert=require('node:assert/strict'),build=require('../outputs/paper-atlas/author-relations.js');
const authors=Array.from({length:13},(_,i)=>({id:'a'+i,name:'a'+i,papers:['p'+i],paperWeights:{['p'+i]:1}}));
const papers=authors.map((a,i)=>({id:'p'+i,tags:[]}));const pairs=[];
for(let i=0;i<13;i++)for(let j=i+1;j<13;j++)pairs.push({source:'p'+i,target:'p'+j,kind:'semantic',score:i===0?.95:.3+((i+j)%7)/100});
const result=build({authors,papers,paperEdges:pairs,mode:'semantic'});
const expected=new Set();
for(let i=0;i<13;i++){
 const candidates=pairs.filter(e=>e.source==='p'+i||e.target==='p'+i).map(e=>{const [a,b]=[e.source.replace('p','a'),e.target.replace('p','a')].sort((a,b)=>a.localeCompare(b));return {id:'author_semantic:'+a+':'+b,score:e.score};}).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5);
 for(const e of candidates)expected.add(e.id);
}
assert.deepEqual(new Set(result.map(e=>e.id)),expected);
assert.equal(result.filter(e=>e.source==='a0'||e.target==='a0').length,12,'incoming choices may exceed five');
assert(result.some(e=>e.score<.88),'no hidden .88 threshold');
const reversed=build({authors:[...authors].reverse(),papers:[...papers].reverse(),paperEdges:[...pairs].reverse(),mode:'semantic'});
assert.deepEqual(result.map(e=>e.id),reversed.map(e=>e.id),'stable ties independent of input order');
const small=build({authors:authors.slice(0,3),papers:papers.slice(0,3),paperEdges:pairs,mode:'semantic'});assert.equal(small.length,3,'fewer than five candidates kept');
console.log('PASS: exact top-five union, stable ties, no score threshold, insufficient candidates and popular-author degree');
