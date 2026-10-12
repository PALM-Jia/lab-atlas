import json,urllib.request
from pathlib import Path
p=Path('outputs/paper-atlas');d=json.loads((p/'data.json').read_text(encoding='utf8'));a=json.loads((p/'acceptance.json').read_text(encoding='utf8'))
print(json.dumps({'nodes':len(d['nodes']),'lab':sum(n['lab'] for n in d['nodes']),'abstract':sum(bool(n.get('abstract')) for n in d['nodes']),'vectors':sum(n.get('semantic_status')=='available' for n in d['nodes']),'steps':{k:{x:v[x] for x in ['total','success','explained_failure','reasons']} for k,v in a['steps'].items() if 'vector' in k or k=='07_readiness_semantic'}}))
for model in ['allenai/specter2_base','allenai/specter2']:
 req=urllib.request.Request('https://huggingface.co/api/models/'+model+'?blobs=true')
 with urllib.request.urlopen(req,timeout=40)as r:meta=json.load(r)
 print(json.dumps({'model':model,'sha':meta['sha'],'files':[{k:f[k] for k in ['rfilename','size'] if k in f} for f in meta['siblings']]}))
 (Path('work')/(model.split('/')[-1]+'-manifest.json')).write_text(json.dumps(meta),encoding='utf8')
