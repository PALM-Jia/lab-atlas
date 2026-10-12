"""Remove external-only citation edges and recompute the existing bounded layout offline."""
import collections
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent / 'outputs/paper-atlas'
data = json.loads((ROOT / 'data.json').read_text(encoding='utf8'))
nodes = data['nodes']
by_id = {p['id']: p for p in nodes}
def allowed(edge):
    return edge['kind'] != 'citation' or by_id[edge['source']]['lab'] or by_id[edge['target']]['lab']
removed = sum(not allowed(e) for e in data['edges'])
data['edges'] = [e for e in data['edges'] if allowed(e)]
full = json.loads((ROOT / 'relations-full.json').read_text(encoding='utf8'))
full = [e for e in full if allowed(e)]
stats = data['meta']['stats']
for key, edges in [('edges', data['edges']), ('full_edges', full)]:
    counts = collections.Counter(e['kind'] for e in edges)
    stats[key] = {kind: counts[kind] for kind in stats[key]}
# Same seed, forces and iteration bounds as pipeline.py; excluded edges supply no layout force.
n = len(nodes)
index = {p['id']: i for i, p in enumerate(nodes)}
rng = np.random.default_rng(17)
pos = rng.normal(0, 220, (n, 2)).astype(np.float32)
topic_index = {t['id']: i for i, t in enumerate(data['topics'])}
for i, p in enumerate(nodes):
    angle = 2 * math.pi * topic_index[p['tags'][0]] / len(topic_index)
    pos[i] += np.array([320 * math.cos(angle), 250 * math.sin(angle)], dtype=np.float32)
layout_edges = [e for e in data['edges'] if e['kind'] in ('coupling', 'citation')]
src = np.array([index[e['source']] for e in layout_edges], dtype=int)
dst = np.array([index[e['target']] for e in layout_edges], dtype=int)
for iteration in range(180):
    forces = np.zeros((n, 2), dtype=np.float32)
    if len(src):
        delta = pos[dst] - pos[src]
        dist = np.maximum(np.linalg.norm(delta, axis=1), 1)
        f = delta * ((dist - 65) / dist * .012)[:, None]
        np.add.at(forces, src, f)
        np.add.at(forces, dst, -f)
    for _ in range(12):
        other = rng.integers(0, n, n)
        delta = pos - pos[other]
        dist = np.maximum(np.sum(delta * delta, axis=1), 25)
        forces += delta * (700 / dist)[:, None]
    forces -= pos * .0008
    pos += np.clip(forces, -10, 10) * (1 - iteration / 220)
for i, p in enumerate(nodes):
    p['x'], p['y'] = round(float(pos[i, 0]), 2), round(float(pos[i, 1]), 2)
assert all(allowed(e) for e in data['edges'] + full)
packed = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
(ROOT / 'data.json').write_text(packed, encoding='utf8')
(ROOT / 'data.js').write_text('window.ATLAS_DATA=' + packed + ';', encoding='utf8')
(ROOT / 'relations-full.json').write_text(json.dumps(full, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
for name in ['coverage.json', 'acceptance.json']:
    path = ROOT / name
    report = json.loads(path.read_text(encoding='utf8'))
    report['meta'] = data['meta']
    if name == 'acceptance.json':
        for row in report['steps'].get('11_relation_validation', {}).get('items', []):
            if row['id'] == 'citation':
                row['edge_count'] = stats['full_edges']['citation']
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(f'Removed {removed} external-only citation edges; {stats["edges"]["citation"]} allowed citations remain; layout rebuilt.')
