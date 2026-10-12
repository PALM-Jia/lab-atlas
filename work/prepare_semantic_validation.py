import json,hashlib
from pathlib import Path
p=Path('work/semantic-refresh-baseline.json')
if not p.exists():
 d=json.loads(Path('outputs/paper-atlas/data.json').read_text(encoding='utf8'))
 digest=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 p.write_text(json.dumps({'non_semantic_edges':digest([e for e in d['edges'] if e['kind']!='semantic']),'non_semantic_node_fields':digest([{k:v for k,v in n.items() if not k.startswith('semantic_')} for n in d['nodes']])}),encoding='utf8')
p=Path('work/package_atlas.py');s=p.read_text(encoding='utf8').replace("if p.is_file(): archive.write", "if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.partial'): archive.write");p.write_text(s,encoding='utf8')
