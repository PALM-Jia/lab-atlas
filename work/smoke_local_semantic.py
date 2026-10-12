import json,sys
sys.path.insert(0,'outputs/paper-atlas')
from semantic_features import generate_embeddings,semantic_edges,input_text
with open('outputs/paper-atlas/data.json',encoding='utf8')as f:d=json.load(f)
a=next(p.copy() for p in d['nodes'] if p['lab'] and not p.get('doi') and p.get('abstract'))
b=next(p.copy() for p in d['nodes'] if p['lab'] and not p.get('abstract'))
rows,meta=generate_embeddings([a,b]);e=semantic_edges([a,b]);assert len(e)==1
assert len(a['embedding'])==len(b['embedding'])==768
assert a['semantic_input']['fields']==['title','abstract'] and b['semantic_input']['fields']==['title']
_,info,key=input_text(b);b['abstract']='A new abstract.';assert input_text(b)[2]!=key
print(json.dumps({'smoke':'passed','papers':[r['id'] for r in rows],'score':e[0]['score'],'inputs':[r['input']['fields'] for r in rows]}))
