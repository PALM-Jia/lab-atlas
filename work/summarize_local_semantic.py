import json
from pathlib import Path
p=Path('outputs/paper-atlas');a=json.loads((p/'acceptance.json').read_text(encoding='utf8'));r=json.loads((p/'semantic-generation.json').read_text(encoding='utf8'))
print(json.dumps({'vector_total':a['steps']['08_content_vector']['total'],'vector_success':a['steps']['08_content_vector']['success'],'vector_accounted':a['steps']['08_content_vector']['accounted_rate'],'lab_success':a['steps']['07_readiness_semantic']['success'],'lab_title_only':r['model']['lab_title_only'],'truncated_all':sum(x.get('input',{}).get('truncated',False) for x in r['coverage']['items']),'other_steps':{k:v['total'] for k,v in a['steps'].items() if k.startswith(('11','12'))}}))
