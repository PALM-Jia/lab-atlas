'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../data/atlas');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const data=read('data.json'),retrieval=read('retrieval-data.json');
const vectorSnapshot=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../data/two-source/snapshot/05-vectors.json'),'utf8'));
const vectorRows=vectorSnapshot.rows||[];
const generation={coverage:{total:vectorRows.length,success:vectorRows.filter(p=>p.status==='success').length,explained_failure:vectorRows.filter(p=>p.status!=='success').length,items:vectorRows},model:{...vectorSnapshot.model,papers:vectorSnapshot.model.papers,ready:vectorSnapshot.model.ready,lab_ready:vectorSnapshot.model.lab_ready,lab_title_only:vectorSnapshot.model.lab_title_only}};
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
const rows=new Map([...retrieval.papers,...retrieval.external].map(p=>[p.id,p]));
const network=read('network-evidence.json');
if(retrieval.meta.semantic)assert.deepEqual(retrieval.meta.semantic,data.meta.semantic,'retrieval semantic metadata');
if(network.meta?.semantic)assert.deepEqual(network.meta.semantic,data.meta.semantic,'network semantic metadata');
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

const sha=text=>crypto.createHash('sha256').update(text,'utf8').digest('hex');
const vectorRoot=path.resolve(__dirname,'../../data/two-source/snapshot/vectors');
const modelKeys=['model','base','adapter','base_revision','adapter_revision','dimensions','method','max_tokens','pooling','normalization','text_policy'];
const model=Object.fromEntries(modelKeys.map(k=>[k,generation.model[k]]));
const pythonModel='{'+Object.keys(model).sort().map(k=>JSON.stringify(k)+': '+JSON.stringify(model[k])).join(', ')+'}';
let vectors=0;
for(const p of data.nodes){
 const report=generated.get(p.id);assert(report,'Generation row '+p.id);
 const field=rows.get(p.id).fields.vector;
 const networkField=network.papers[p.id]?.fields.vector;
 if(network.meta?.semantic&&network.papers[p.id])assert(networkField,p.id+' refreshed network vector field required');
 if(networkField)assert.deepEqual(networkField,field,p.id+' network vector parity');
 if(report.status!=='success'){
  assert(report.reason||report.failure_summary,'Explained failure '+p.id);
  assert.equal(field.state,'missing',p.id+' failed vector state');
  assert.equal(field.dimensions,null,p.id+' failed vector dimensions');
  assert.deepEqual(field.input,report.input??null,p.id+' failed vector input');
  assert(field.explanation,p.id+' failure explanation');continue;
 }
 assert.deepEqual(field.input,p.semantic_input,p.id+' retrieval vector input');
 assert.equal(field.model,p.semantic_model,p.id+' retrieval vector model');
 assert.equal(field.dimensions,report.dimensions,p.id+' retrieval vector dimensions');
 if(networkField)assert.deepEqual(networkField.input,report.input,p.id+' network vector input');
 const inputHash=sha((p.title||'').trim()+'[SEP]'+(p.abstract||'').trim());
 assert.equal(report.input.sha256,inputHash,p.id+' input digest');
 const key=sha(pythonModel+inputHash);assert.equal(report.vector_key,key,p.id+' model and input key');
 assert.equal(p.semantic_vector_key,key,p.id+' attached vector key');
 const record=JSON.parse(fs.readFileSync(path.join(vectorRoot,key+'.json'),'utf8'));
 assert.equal(record.key,key);assert.deepEqual(record.model,model);assert.deepEqual(record.input,report.input);assert.deepEqual(p.semantic_input,report.input);
 assert.equal(report.dimensions,model.dimensions);assert.equal(record.vector.length,model.dimensions);
 assert(record.vector.every(Number.isFinite),p.id+' finite vector');
 assert(Math.abs(record.vector.reduce((sum,x)=>sum+x*x,0)-1)<.0001,p.id+' L2 normalized vector');
 // Published paper records reference the vector key instead of duplicating embeddings.
 vectors++;
}
console.log(JSON.stringify({check:'semantic-provenance',papers:data.nodes.length,lab:lab.length,vectors,dimensions:model.dimensions}));
