import json,hashlib
from pathlib import Path
before=json.loads(Path('work/semantic-refresh-baseline.json').read_text(encoding='utf8'));d=json.loads(Path('outputs/paper-atlas/data.json').read_text(encoding='utf8'))
digest=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert before['non_semantic_edges']==digest([e for e in d['edges'] if e['kind']!='semantic'])
assert before['non_semantic_node_fields']==digest([{k:v for k,v in n.items() if not k.startswith('semantic_')} for n in d['nodes']])
print('PASS: all other fields and relation layers unchanged')
