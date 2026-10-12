'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const build = require('../outputs/paper-atlas/author-relations.js');
const close = (actual, expected, message) => assert.ok(Math.abs(actual-expected)<1e-12,message);
const paper = (id, tags) => ({id, tags});
const author = (id, papers) => ({id, name: id, papers});
const p = [paper('p1', ['clustering']), paper('p2', ['clustering']), paper('p3', ['traffic']), paper('p4', ['other'])];
let edges = build({authors: [author('a', ['p1']), author('b', ['p2']), author('c', ['p3']), author('d', ['p4'])], papers: p});
assert.equal(edges.length, 1);
assert.equal(edges[0].score, 1);
assert.deepEqual(edges[0].evidence.paper_pairs, [{source: 'p1', target: 'p2', topic_names: ['聚类与表示学习']}]);
assert.deepEqual(edges[0].evidence.shared_papers, []);
const averaged = build({authors: [author('a', ['p1', 'p2', 'p3']), author('b', ['p1'])], papers: p})[0];
assert.ok(Math.abs(averaged.score - 2 / Math.sqrt(5)) < 1e-12);
close(averaged.evidence.profiles[0].topics.find(t => t.id === 'clustering').weight, 2 / 3);
const firstWeighted=build({authors:[{...author('a',['p1','p3']),paperWeights:{p1:1,p3:.2}},author('b',['p2'])],papers:p})[0];
close(firstWeighted.evidence.profiles[0].topics.find(t=>t.id==='clustering').weight,5/6,'first-author work contributes five times the later-author work');
close(firstWeighted.evidence.profiles[0].topics.find(t=>t.id==='traffic').weight,1/6);
assert.equal(firstWeighted.evidence.profiles[0].first_author_papers,1);
assert.equal(firstWeighted.evidence.profiles[0].contribution_weight,1.2);
assert.ok(Math.abs(firstWeighted.score-5/Math.sqrt(26))<1e-12,'weighted profile cosine remains normalized');
assert.equal(build({authors: [author('a', ['p1']), author('a', ['p2'])], papers: p}).length, 0);
const shared = build({authors: [author('a', ['p1']), author('b', ['p1'])], papers: p})[0];
assert.deepEqual(shared.evidence.shared_papers, ['p1']);
assert.deepEqual(shared.evidence.paper_pairs, []);
const dp = [
  {...paper('d1', ['clustering']), api_topics: [{id: 'T1', display_name: 'Specific topic', score: 0.8}, {id: 'T2', display_name: 'Other topic', score: 0.2}]},
  {...paper('d2', ['traffic']), api_topics: [{id: 'T1', display_name: 'Specific topic', score: 1}]},
  paper('d3', ['clustering'])
];
const de = build({authors: [author('a', ['d1', 'd3']), author('b', ['d2'])], papers: dp, mode: 'database-topic'})[0];
assert.equal(de.kind, 'author_database_topic');
assert.deepEqual(de.evidence.topic_names, ['Specific topic']);
assert.equal(de.evidence.profiles[0].total_papers, 2);
assert.equal(de.evidence.profiles[0].profiled_papers, 1);
close(de.evidence.profiles[0].topics[0].weight, 0.8);
const weightedDp=[...dp,{...paper('d4',[]),api_topics:[{id:'T2',display_name:'Other topic',score:1}]}];
const weightedDb=build({authors:[{...author('a',['d1','d4']),paperWeights:{d1:1,d4:.2}},author('b',['d2'])],papers:weightedDp,mode:'database-topic'})[0];
assert.ok(Math.abs(weightedDb.evidence.profiles[0].topics.find(t=>t.id==='T1').weight-2/3)<1e-12,'database topics also use first-author 1:0.2 weighting');
assert.ok(Math.abs(de.score - 0.8 / Math.sqrt(0.68)) < 1e-12);
assert.equal(build({authors: [author('a', ['d3']), author('b', ['d2'])], papers: dp, mode: 'database-topic'}).length, 0);
const semanticInput = {authors: [author('a', ['p1', 'p3']), author('b', ['p2', 'p3'])], papers: p,
  mode: 'semantic', paperEdges: [{kind: 'semantic', source: 'p1', target: 'p2', score: 0.91},
    {kind: 'semantic', source: 'p2', target: 'p1', score: 0.90},
    {kind: 'semantic', source: 'p3', target: 'p3', score: 1},
    {kind: 'topic', source: 'p1', target: 'p3', score: 1}]};
const se = build(semanticInput);
assert.equal(se.length, 1);
close(se[0].score,.91);close(se[0].evidence.paper_pairs[0].weight,.04);assert.equal(se[0].evidence.aggregation,'weighted_mean');
assert.equal(build({...semanticInput, paperEdges: []}).length, 0);
assert.equal(build({...semanticInput,paperEdges:[{kind:'semantic',source:'p1',target:'p2',score:.72}]}).length,1,'relaxed threshold accepts a genuine cached pair below .8');
assert.equal(build({...semanticInput,paperEdges:[{kind:'semantic',source:'p1',target:'p2',score:.1}]}).length,1,'low paper scores remain eligible for averaging and relative thresholds');
const semanticContext={window:{}};
require('node:vm').runInNewContext(fs.readFileSync(path.join(__dirname,'../outputs/paper-atlas/author-semantic.js'),'utf8'),semanticContext);
const authorSemantic=semanticContext.window.ATLAS_AUTHOR_SEMANTIC;
assert.equal(authorSemantic.threshold,null);
const meanPapers=['x1','x2','y1','y2'].map(id=>paper(id,[]));
const meanEdges=[['x1','y1',.9],['x1','y2',.6],['x2','y1',.5],['x2','y2',.4]].map(([source,target,score])=>({source,target,score,kind:'semantic'}));
const mean=build({authors:[{...author('x',['x1','x2']),paperWeights:{x1:1,x2:.2}},{...author('y',['y1','y2']),paperWeights:{y1:1,y2:.2}}],papers:meanPapers,paperEdges:meanEdges,mode:'semantic'});
assert.ok(Math.abs(mean[0].score-1.136/1.44)<1e-12,'all four scores enter weighted mean at weights 1,.2,.2,.04');
close(mean[0].evidence.weighted_sum,1.136);
assert.equal(mean[0].evidence.pair_count,4);close(mean[0].evidence.total_pair_weight,1.44);
assert.equal(mean.stats.threshold,null,'semantic relations have no threshold');
const medianPapers=[['m1',1,0],['m2',.8,.2],['m3',0,1]].map(([id,v1,v2])=>({...paper(id,[]),api_topics:[{id:'T1',display_name:'T1',score:v1},{id:'T2',display_name:'T2',score:v2}]}));
const maximum=build({authors:[author('a',['m1']),author('b',['m2']),author('c',['m3']),author('missing',[])],papers:medianPapers,mode:'database-topic-max'});
assert.equal(maximum.stats.valid_pairs,2,'missing and disjoint profiles supply no common-topic evidence');
assert.equal(maximum.stats.threshold,null);
assert.equal(maximum.length,2);maximum.map(e=>e.score).sort().forEach((score,i)=>close(score,[.2,.8][i]));
assert(maximum.every(e=>e.evidence.threshold===null&&e.evidence.top_k===5));
const many = Array.from({length: 10}, (_, i) => author('a' + i, ['p1']));
const trimmed = build({authors: many, papers: p});
assert.equal(trimmed.length,35,'union of top-five choices with stable ties');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../outputs/paper-atlas/data.json'), 'utf8'));
const lab = data.nodes.filter(n => n.lab), authors = new Map();
for (const p of lab) for (const name of p.authors || []) {
  if (!authors.has(name)) authors.set(name, author(name, []));
  authors.get(name).papers.push(p.id);
}
const top = [...authors.values()].sort((a, b) => b.papers.length - a.papers.length).slice(0, 65);
for (const mode of ['topic', 'database-topic','database-topic-max', 'semantic']) {
  const paperEdges=data.edges;
  const result = build({authors: top, papers: lab, paperEdges, mode});
  for (const e of result) {
    assert.notEqual(e.source, e.target);
    if(mode==='semantic')assert.equal(e.evidence.threshold_rule,'top_k_union');else assert(e.score>=e.evidence.threshold,'every edge passes its threshold');
    assert.equal(result.length,result.stats.selected_pairs,'reported selected pairs match');
    if(mode==='database-topic-max')assert.equal(e.score,e.evidence.shared_topics[0].product);
    if(mode==='database-topic')assert.ok(Math.abs(e.score-e.evidence.cosine_parts.dot/(e.evidence.cosine_parts.source_norm*e.evidence.cosine_parts.target_norm))<1e-12);
    if(mode==='semantic')assert.ok(Math.abs(e.score-e.evidence.weighted_sum/e.evidence.total_pair_weight)<1e-12);
    assert.ok(Number.isFinite(e.score));
    for (const pair of e.evidence.paper_pairs) {
      assert.notEqual(pair.source, pair.target);
      if (mode === 'semantic') assert.ok(paperEdges.some(x => x.kind === 'semantic' && x.score === pair.score &&
        ((x.source === pair.source && x.target === pair.target) || (x.source === pair.target && x.target === pair.source))));
    }
  }
  console.log(mode + ': ' + result.length + ' author relations; evidence checked');
}
console.log('Author relation checks passed.');

const appSource=fs.readFileSync(path.join(__dirname,'../outputs/paper-atlas/app.js'),'utf8');
const meaningSource=appSource.slice(appSource.indexOf('  function authorRelationMeaning(e) {'),appSource.indexOf('  function edgeDetail(e) {'));
const renderContext={esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;')};
require('node:vm').runInNewContext(meaningSource,renderContext);
assert.match(renderContext.authorRelationMeaning(mean[0]),/论文相似度加权平均 78.9% · 4 对论文/);
assert.match(renderContext.authorRelationMeaning(maximum[0]),/最强共同主题/);
assert.match(renderContext.authorRelationMeaning(de),/主要共同主题/);
assert.match(renderContext.authorRelationMeaning(de),/Specific topic \(a: 80.0%, b: 100.0%\)/);
assert.match(renderContext.authorRelationMeaning(de),/Specific topic \(a: 80.0%, b: 100.0%\)/);
for(const e of [mean[0],maximum[0],de])assert.doesNotMatch(renderContext.authorRelationMeaning(e),/÷|×|中位数|因此保留|第 .* 强连接/);
console.log('Passed: concise edge evidence shows author-topic percentages or representative paper context without arithmetic.');
