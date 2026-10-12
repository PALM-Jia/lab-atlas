import json
import sys
from pathlib import Path

root = Path('outputs/paper-atlas')
graph = json.loads((root/'data.json').read_text(encoding='utf8'))
nodes = {p['id']:p for p in graph['nodes']}
assert len(nodes)==len(graph['nodes']), 'Duplicate node IDs'
lab = [p for p in nodes.values() if p['lab']]
assert len(lab)==144
assert len({p['title'].lower() for p in lab})==len(lab)
assert any(p['title']=='Mini-cluster Guided Long-tailed Deep Clustering' for p in lab)
assert any(p['title']=='Partial Label Clustering' for p in lab)
assert all(not p['title'].startswith('International Conference') for p in lab)
edges = graph['edges']
assert len({e['id'] for e in edges})==len(edges)
oa_ids = {p.get('openalex','').split('/')[-1]:p['id'] for p in nodes.values() if p.get('openalex')}
for e in edges:
    assert e['source'] in nodes and e['target'] in nodes
    a,b=nodes[e['source']],nodes[e['target']]
    assert a['id']!=b['id']
    if e['kind']=='citation':
        assert b['openalex'].split('/')[-1] in a['references'], 'Citation without source evidence'
    if e['kind']=='coupling':
        shared=set(a['references'])&set(b['references'])
        assert shared==set(e['evidence']['ids'])
        assert len(shared)==e['evidence']['count']
    if e['kind']=='topic':
        assert e['tentative'], 'Automatic theme presented as verified'
    if e['kind']=='author':
        assert all(n.lower()!='yuheng jia' for n in e['evidence']['authors'])
for p in lab:
    if not p['authors'] and not p.get('abstract'):
        assert not any(e['kind'] in ('citation','semantic','author') and p['id'] in (e['source'],e['target']) for e in edges)
assert graph['meta']['stats']['external']>0, 'No real external network'
assert graph['meta']['stats']['edges']['citation']>0
assert graph['meta']['stats']['edges']['coupling']>0
print(json.dumps({'checks':'passed','stats':graph['meta']['stats']},ensure_ascii=False))
