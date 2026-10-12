"""Compute the relaxed author-network paper similarities from cached SPECTER2 vectors."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'outputs/paper-atlas'
data = json.loads((ATLAS / 'data.json').read_text(encoding='utf8'))
vectors = {}
for path in (ROOT / 'work/api-cache').glob('*.json'):
    try:
        raw = json.loads(path.read_text(encoding='utf8'))
    except (ValueError, OSError):
        continue
    for record in raw if isinstance(raw, list) else [raw]:
        if not isinstance(record, dict) or not record.get('paperId'):
            continue
        embedding = record.get('embedding') or {}
        if str(embedding.get('model', '')).lower() not in ('specter_v2', 'specter2'):
            continue
        v = np.array(embedding.get('vector', []), dtype=np.float32)
        if len(v) == 768 and np.all(np.isfinite(v)) and np.linalg.norm(v) > 0:
            vectors[record['paperId']] = v / np.linalg.norm(v)
papers = [p for p in data['nodes'] if p['lab'] and p.get('semantic_paper_id') in vectors]
matrix = np.array([vectors[p['semantic_paper_id']] for p in papers])
scores = matrix @ matrix.T
edges = []
for i, a in enumerate(papers):
    for j in range(i + 1, len(papers)):
        edges.append({'source': a['id'], 'target': papers[j]['id'], 'kind': 'semantic', 'score': round(float(scores[i, j]), 6)})
result = {'threshold': None, 'paper_count': len(papers), 'edges': edges}
(ATLAS / 'author-semantic.js').write_text("'use strict';\nwindow.ATLAS_AUTHOR_SEMANTIC=" + json.dumps(result, separators=(',', ':')) + ';\n', encoding='utf8')
print(f'Cached SPECTER2: {len(papers)} lab papers; {len(edges)} complete pairs, {sum(e["score"] >= .8 for e in edges)} at >=0.8. No similarity cutoff or paper-graph sparsification.')
