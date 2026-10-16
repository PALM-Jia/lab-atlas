const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../../outputs/paper-atlas');
const facts=path.resolve(__dirname,'../../data/atlas');
const data=JSON.parse(fs.readFileSync(path.join(facts,'data.json'),'utf8'));
const keywords=JSON.parse(fs.readFileSync(path.join(facts,'paper-keywords.json'),'utf8'));
const retrieval=JSON.parse(fs.readFileSync(path.join(facts,'retrieval-data.json'),'utf8'));
const paperRelations=require(path.join(root,'keyword-relations.js'));
const authorKeywords=require(path.join(root,'author-keywords.js'));
const tasks=require(path.join(root,'author-relations.js'));
const ids=new Set(data.nodes.map(p=>p.id)),terms=new Set(keywords.vocabulary.map(k=>k.id));
assert.equal(ids.size,data.nodes.length);assert(ids.size>0);assert.equal(terms.size,keywords.vocabulary.length);assert(terms.size>0);
const rows=new Map([...retrieval.papers,...retrieval.external].map(p=>[p.id,p]));
for(const p of data.nodes){
 assert.equal(rows.get(p.id).fields.keywords.state,p.keyword_status);
 assert.deepEqual(rows.get(p.id).fields.keywords.value,p.keywords);
 assert.deepEqual(p.tags,p.keywords.map(k=>k.id));
 for(const k of p.keywords)assert(terms.has(k.id)&&k.exact_quote&&k.evidence_field);
 if(p.keyword_status==='excluded')assert.equal(p.keywords.length,0);
}
const start=performance.now();const edges=paperRelations({papers:data.nodes,keywordData:keywords});
const elapsed=performance.now()-start,map=new Map(data.nodes.map(p=>[p.id,p]));
for(const e of edges){
 assert(map.get(e.source).lab||map.get(e.target).lab);
 assert(e.score>0&&e.score<=1&&e.evidence.shared_keywords.length);
 for(const k of e.evidence.shared_keywords)assert(k.source_evidence[0].exact_quote&&k.target_evidence[0].exact_quote);
}
// Compare static retrieval profiles with the live default-weight computation,
// using the exact resolved person IDs and adopted author order in the dashboard.
const authors=retrieval.authors.map(a=>({id:a.id,name:a.name,papers:a.papers,paperWeights:Object.fromEntries(a.papers.map(pid=>{const authors=rows.get(pid).fields.authors.value||[],first=authors[0],second=authors[1];return [pid,first?.id===a.id|| (first?.name==='Yuheng Jia'&&second?.id===a.id)?1:.2];}))}));
const relations=authorKeywords({authors,papers:data.nodes.filter(p=>p.lab),keywordData:keywords});
for(const a of retrieval.authors){
 const profile=relations.profiles.find(p=>p.author_id===a.id),actual=new Map(profile.keywords.map(k=>[k.id,k.weight]));
 assert.equal(actual.size,a.keywords.length);
 for(const k of a.keywords)assert(Math.abs(actual.get(k.id)-k.weight)<1e-12);
}
const taskEdges=tasks({authors,papers:data.nodes.filter(p=>p.lab),keywordData:keywords,mode:'topic'});
for(const p of taskEdges.profiles)for(const k of p.topics)assert.equal(keywords.vocabulary.find(t=>t.id===k.id).dimension,'research_task');
const result={papers:ids.size,vocabulary:terms.size,keyword_paper_edges:edges.length,keyword_author_edges:relations.length,task_author_edges:taskEdges.length,paper_relation_build_ms:Math.round(elapsed),retrieval_profile_parity:true};
console.log(JSON.stringify(result));
