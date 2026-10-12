import json
from pathlib import Path
p=Path('outputs/paper-atlas');a=json.loads((p/'acceptance.json').read_text(encoding='utf8'))
for k in ['11_relation_validation','12_frontend_checks']:
 print(k,json.dumps(a['steps'][k]['items'],ensure_ascii=False))
