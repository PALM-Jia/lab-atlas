/* Offline annual counts, identity, availability, chronology and top-K checks. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const api = require(path.join(root, 'outputs/paper-atlas/timeline-history.js'));
const graph = read('data/atlas/data.json'), retrieval = read('data/atlas/retrieval-data.json');
const history = read('data/atlas/citation-history.json');
assert.deepEqual(Object.keys(history.papers).sort(), graph.nodes.map(p => p.id).sort());
const states = {ready: 0, empty: 0, missing: 0};
let collected = 0;
for (const paper of retrieval.papers) {
  const field = paper.fields.citing, entry = history.papers[paper.id];
  states[field.state]++;
  if (field.state === 'missing') {
    assert.equal(api.citationAt(entry, 2026).count, null);
    assert.equal(entry.databaseTotal, null);
    continue;
  }
  const ids = [...new Set(field.ids)]; collected += ids.length;
  const known = ids.map(id => retrieval.bibliography[id]?.year).filter(Number.isInteger);
  for (const year of [2000, 2018, 2022, 2026]) assert.equal(api.citationAt(entry, year).count, known.filter(y => y <= year).length);
  assert.equal(entry.unknownYearCount, ids.length - known.length);
  assert.equal(entry.observedCount, ids.length);
  assert.equal(entry.complete, ids.length === field.total);
}
assert.deepEqual(states, {ready: 85, empty: 30, missing: 29});
assert.equal(collected, 2048);
for (const paper of retrieval.external) assert.equal(history.papers[paper.id].databaseTotal, null);
const entry = {annual: [{year: 2019, count: 2}, {year: 2025, count: 8}], unknownYearCount: 3, status: 'partial', scope: 'database_citing_list', observedCount: 13, complete: false};
assert.equal(api.citationAt(entry, 2020).count, 2);
assert.equal(api.citationAt(entry, 2020).unknownYearCount, 3);
assert.equal(api.citationAt(undefined, 2020).count, null);
assert.equal(api.citationAt({annual: [], status: 'complete', complete: true}, 2020).count, 0);
const papers = [{id: 'a', lab: true, year: 2018}, {id: 'b', lab: true, year: 2019}, {id: 'f', lab: true, year: 2025}, {id: 'old', year: 1996}, {id: 'unknown', year: null}];
const edges = [{id: 'old', source: 'a', target: 'b', kind: 'citation', score: 1}, {id: 'future', source: 'f', target: 'a', kind: 'citation', score: 99}];
const original = JSON.stringify({papers, edges, entry});
const slices = api.buildAnnualSlices(papers, edges, {papers: {a: entry}}, {yearFrom: 2000, yearTo: 2025});
assert.equal(slices.slices[0].label, '≤2000');
assert.equal(slices.slices[0].appearances[0].paperId, 'old');
assert.equal(slices.unknown.length, 0);
assert.equal(slices.slices.find(s => s.year === 2025).appearances.some(n => n.paperId === 'unknown'), false);
const early = slices.slices.find(s => s.year === 2020);
assert.deepEqual(early.edges.map(e => e.id), ['old']);
assert.equal(early.appearances.find(n => n.paperId === 'a').citation.count, 2);
assert.notEqual(slices.slices.find(s => s.year === 2018).appearances.find(n => n.paperId === 'a').id, early.appearances.find(n => n.paperId === 'a').id);
assert.equal(JSON.stringify({papers, edges, entry}), original);
assert.equal(api.edgeActiveAt({source: 'a', target: 'f'}, new Map(papers.map(p => [p.id, p])), 2020), false);
assert.equal(api.edgeActiveAt({source: 'old', target: 'old', kind: 'citation'}, new Map(papers.map(p => [p.id, p])), 2020), false);
assert.equal(api.publicationYear({year: 2024, versions: [{year: 2023}, {publication_date: '2022-12-01'}]}), 2022);
assert.equal(api.publicationYear({year: 2024, versions: [{publication_date: '2022-02-30'}]}), 2024);
assert.equal(api.publicationYear({year: null, versions: [{date: 'undated'}]}), 2027);
// Future stronger candidates must not remove an older weak edge at both endpoints.
const many = [...papers, ...Array.from({length: 12}, (_, i) => ({id: 'f' + i, year: 2025, lab: true}))];
const candidates = [...edges, ...many.filter(p => p.id.startsWith('f')).flatMap(p => ['a', 'b'].map(id => ({id: p.id + id, source: p.id, target: id, kind: 'citation', score: 50})))];
assert.deepEqual(api.buildAnnualSlices(many, candidates, {}, {yearFrom: 2020, yearTo: 2020}).slices[0].edges.map(e => e.id), ['old']);
// Browser fallback agrees with shared selector; it does not require the DOM.
const context = {window: {}};
vm.runInNewContext(fs.readFileSync(path.join(root, 'outputs/paper-atlas/timeline-history.js'), 'utf8'), context);
assert.deepEqual(JSON.parse(JSON.stringify(context.window.ATLAS_TIMELINE_HISTORY.buildAnnualSlices(many, candidates, {}, {yearFrom: 2025, yearTo: 2025}))), JSON.parse(JSON.stringify(api.buildAnnualSlices(many, candidates, {}, {yearFrom: 2025, yearTo: 2025}))));
console.log('Timeline history passed: annual counts, chronology, future counts/top-K, latest-year fallback, deduplication and version fallback.');
