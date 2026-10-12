import json,collections
from pathlib import Path
root=Path('outputs/paper-atlas')
a=json.loads((root/'acceptance.json').read_text(encoding='utf8'))
audit=json.loads(Path('work/external-lookup-audit.json').read_text(encoding='utf8'))
for r in a['steps']['05_external_metadata']['items']:
 if r['status']=='failure' and r['id'] in audit:
  prior=audit[r['id']]
  r['reason']=prior['reason']
  r['lookup_evidence']=prior['lookup_evidence']
a['steps']['05_external_metadata']['reasons']=dict(collections.Counter(r['reason'] for r in a['steps']['05_external_metadata']['items']))
a['external_lookup_audit']=[r['lookup_evidence'] for r in audit.values()]
(root/'acceptance.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
