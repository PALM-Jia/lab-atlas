"""Export all cached cosine scores without a fixed semantic threshold."""
import json,sys
from pathlib import Path
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages')
import numpy as np
root=Path('outputs/paper-atlas')
d=json.loads((root/'data.json').read_text(encoding='utf-8'));vectors={}
if d.get('meta',{}).get('semantic',{}).get('method')=='local':
 from generate_local_semantic import run
 run()
 raise SystemExit(0)
for path in Path('work/api-cache').glob('*.json'):
 try:raw=json.loads(path.read_text(encoding='utf-8'))
 except (ValueError,OSError):continue
 for r in raw if isinstance(raw,list) else [raw]:
  if not isinstance(r,dict):continue
  e=r.get('embedding') or {}
  if str(e.get('model','')).lower() not in ('specter_v2','specter2'):continue
  v=np.asarray(e.get('vector',[]),dtype=np.float32)
  if len(v)==768 and np.all(np.isfinite(v)) and np.linalg.norm(v)>0:vectors[r['paperId']]=v/np.linalg.norm(v)
nodes=[p for p in d['nodes'] if p.get('semantic_paper_id') in vectors];matrix=np.asarray([vectors[p['semantic_paper_id']] for p in nodes]);edges=[]
for i,a in enumerate(nodes):
 if not a['lab']:continue
 scores=matrix@matrix[i]
 for j,b in enumerate(nodes):
  if a['id']==b['id'] or (b['lab'] and a['id']>b['id']):continue
  edges.append({'id':f"semantic:{a['id']}:{b['id']}",'source':a['id'],'target':b['id'],'kind':'semantic','score':round(float(np.clip(scores[j],-1,1)),6),'tentative':True,'evidence':{'model':'specter_v2','source_ids':[a['semantic_paper_id'],b['semantic_paper_id']],'text':'Semantic Scholar SPECTER2 标题与摘要向量的余弦相似度'}})
d['edges']=[e for e in d['edges'] if e['kind']!='semantic']+edges
for key in ['edges','full_edges']:d['meta']['stats'][key]['semantic']=len(edges)
(root/'data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8');(root/'data.js').write_text('window.ATLAS_DATA='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(root/'relations-full.json').write_text(json.dumps(d['edges'],ensure_ascii=False,separators=(',',':')),encoding='utf-8')
for name in ['acceptance.json','coverage.json']:
 p=root/name;v=json.loads(p.read_text(encoding='utf-8'));v['meta']['stats']['edges']['semantic']=len(edges);v['meta']['stats']['full_edges']['semantic']=len(edges);p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
p=root/'acceptance-report.html';s=p.read_text(encoding='utf-8').replace('<td>109782</td>','<td>'+str(len(edges))+'</td>');p.write_text(s,encoding='utf-8')
print(json.dumps({'vectors':len(nodes),'lab_vectors':sum(p['lab'] for p in nodes),'semantic_pairs':len(edges)}))
