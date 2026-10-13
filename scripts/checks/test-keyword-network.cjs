'use strict';
const assert=require('node:assert/strict');
const authorKeywords=require('../../outputs/paper-atlas/author-keywords.js');
const authorRelations=require('../../outputs/paper-atlas/author-relations.js');
const paperRelations=require('../../outputs/paper-atlas/keyword-relations.js');
const vocabulary=[{id:'task-a',name:'Task A',dimension:'research_task',color:'#123'},
  {id:'task-b',name:'Task B',dimension:'research_task',color:'#456'},
  {id:'method',name:'Method',dimension:'method',color:'#789'}];
const label=(id,quote)=>({id,name:id,dimension:'wrong-input-dimension',score:1,evidence_field:'abstract',exact_quote:quote,reason_zh:'原文依据'});
const data={vocabulary,idf:{'task-a':2,'task-b':1,method:3},statuses:{p:'annotated',q:'annotated',empty:'empty',excluded:'excluded',missing:undefined},
  papers:{p:[label('task-a','p task a'),label('task-b','p task b'),label('method','p method'),label('method','p method')],
    q:[label('task-a','q task a')],empty:[label('method','must ignore empty payload')],excluded:[label('method','must ignore excluded payload')]}};
const papers=['p','q','empty','excluded','missing'].map(id=>({id,lab:true,tags:['clustering'],api_topics:[{id:'old',display_name:'Old API',score:1}]}));
const authors=[{id:'a',name:'A',papers:['p','q','empty','excluded','missing'],paperWeights:{p:1,q:.2,empty:1,excluded:1}},
  {id:'b',name:'B',papers:['q'],paperWeights:{q:1}}];
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-12,`${a} != ${b}`);
const a=authorKeywords({authors,papers,keywordData:data});
assert.equal(a.length,1);
const pa=a.profiles.find(p=>p.author_id==='a');
assert.equal(pa.profiled_papers,3); // accepted empty participates; excluded and unannotated are absent
near(pa.contribution_weight,2.2);
near(pa.keywords.find(k=>k.id==='task-a').weight,1.2/2.2);
near(pa.keywords.find(k=>k.id==='task-b').weight,1/2.2);
near(a[0].score,(2*1.2/2.2)/(2+4/2.2));
assert.equal(a[0].evidence.shared_keywords[0].source_evidence[0].exact_quote,'p task a');
assert.equal(a[0].evidence.shared_keywords[0].target_evidence[0].exact_quote,'q task a');
assert.equal(a[0].evidence.shared_keywords[0].dimension,'research_task');
const directions=authorRelations({authors,papers,mode:'topic',keywordData:data});
const da=directions.profiles.find(p=>p.author_id==='a');
assert.equal(da.profiled_papers,3);
assert.deepEqual(da.topics.map(t=>t.id).sort(),['task-a','task-b']);
near(da.topics.find(t=>t.id==='task-a').weight,.7/2.2);
near(da.topics.find(t=>t.id==='task-b').weight,.5/2.2);
near(directions[0].score,.7/Math.sqrt(.7*.7+.5*.5));
assert.equal(directions[0].evidence.sharedtopic_sources[0],'vocabulary_research_task');
assert.equal(directions[0].evidence.shared_topics[0].source_evidence[0].exact_quote,'p task a');
assert.deepEqual(authorRelations({authors,papers,mode:'topic',keywordData:{}}).profiles[0].topics,[]);
assert.equal(authorRelations({authors,papers,mode:'database-topic',keywordData:data}).length,1);
assert.equal(authorRelations({authors,papers,mode:'keywords',keywordData:data}).length,1);
const paperEdges=paperRelations({papers,keywordData:data});
assert.equal(paperEdges.length,1);
near(paperEdges[0].score,2/6);
assert.equal(paperEdges.profiles.length,3);
assert.equal(paperEdges[0].evidence.shared_keywords[0].source_evidence[0].exact_quote,'p task a');
assert.equal(paperEdges[0].evidence.shared_keywords[0].target_evidence[0].exact_quote,'q task a');
assert.equal(paperEdges[0].evidence.threshold_rule,'top_k_union');
// A laboratory hub has seven external neighbors. Their own choices preserve all seven edges.
const starPapers=[{id:'hub',lab:true},...Array.from({length:7},(_,i)=>({id:'ext'+i,lab:false}))];
const starData={vocabulary,idf:data.idf,statuses:Object.fromEntries(starPapers.map(p=>[p.id,'annotated'])),
  papers:Object.fromEntries(starPapers.map(p=>[p.id,[label('task-a',p.id+' quote')]]))};
const star=paperRelations({papers:starPapers,keywordData:starData});
assert.equal(star.length,7);
assert.ok(star.every(e=>e.source==='hub'||e.target==='hub'));
assert.equal(star.stats.positive_pairs,7);
assert.equal(star.filter(e=>e.evidence.selected_by.includes('hub')).length,5);
const manyAuthors=starPapers.map(p=>({id:p.id,name:p.id,papers:[p.id],paperWeights:{[p.id]:1}}));
for(const result of [authorKeywords({authors:manyAuthors,papers:starPapers,keywordData:starData}),
  authorRelations({authors:manyAuthors,papers:starPapers,keywordData:starData})]){
  assert.equal(result.filter(e=>e.source==='ext0'||e.target==='ext0').length,7);
  assert.ok(result.every(e=>e.score===1));
}
assert.equal(paperRelations({papers:starPapers.filter(p=>!p.lab),keywordData:starData}).length,0);
console.log('Keyword network fixtures passed: weighting, empty/excluded status, task profiles, quotes, IDF, top-5 union, external scope.');
