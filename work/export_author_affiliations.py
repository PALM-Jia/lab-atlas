"""Export per-signature institutions from the existing OpenAlex cache; no requests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'outputs/paper-atlas'
nodes = json.loads((ATLAS / 'data.json').read_text(encoding='utf-8'))['nodes']
needed = {p['openalex']: p for p in nodes if p['lab'] and p.get('openalex')}
found = {}
for path in (ROOT / 'work/api-cache').glob('*.json'):
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        continue
    records = payload.get('results', []) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
    if isinstance(payload, dict) and payload.get('id'):
        records = [payload]
    for work in records:
        if isinstance(work, dict) and work.get('id') in needed and work.get('authorships'):
            if len(work['authorships']) > len(found.get(work['id'], {}).get('authorships', [])):
                found[work['id']] = work
rows = {}
for oid, work in found.items():
    rows[needed[oid]['id']] = [
        {'name': a['author']['display_name'], 'id': a['author'].get('id'),
         'institutions': [{'id': i['id'], 'name': i['display_name']}
                          for i in a.get('institutions', []) if i.get('id')]}
        for a in work['authorships']
    ]
(ATLAS / 'author-affiliations.js').write_text(
    "'use strict';\nwindow.ATLAS_AUTHOR_AFFILIATIONS="
    + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print(f'Per-author affiliations: {len(found)}/{len(needed)} matched laboratory papers')
