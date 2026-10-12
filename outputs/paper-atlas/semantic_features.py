"""Reproducible SPECTER2 features from adopted titles and available abstracts.

Model and vector caches remain in work/, outside the published static site.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time

BASE = 'allenai/specter2_base'
ADAPTER = 'allenai/specter2'
BASE_REVISION = '3447645e1def9117997203454fa4495937bfbd83'
ADAPTER_REVISION = '2081559630a80fc5851d8f798a05ba81e9468089'
DIMENSIONS = 768
MAX_TOKENS = 512
WORK = Path(__file__).resolve().parents[2] / 'work'
MODEL = {'model':'specter2_proximity','base':BASE,'adapter':ADAPTER,
         'base_revision':BASE_REVISION,'adapter_revision':ADAPTER_REVISION,
         'dimensions':DIMENSIONS,'method':'local','max_tokens':MAX_TOKENS,
         'pooling':'CLS','normalization':'L2','text_policy':'title + [SEP] + available abstract'}


def input_text(paper):
    title = (paper.get('title') or '').strip()
    abstract = (paper.get('abstract') or '').strip()
    text = title + '[SEP]' + abstract
    digest = hashlib.sha256(text.encode('utf8')).hexdigest()
    key = hashlib.sha256((json.dumps(MODEL,sort_keys=True)+digest).encode('utf8')).hexdigest()
    return text, {'fields':['title','abstract'] if abstract else ['title'], 'sha256':digest}, key


def valid_vector(vector):
    return (isinstance(vector,list) and len(vector)==DIMENSIONS
            and all(isinstance(v,(float,int)) and math.isfinite(v) for v in vector)
            and abs(sum(v*v for v in vector)-1)<.0001)


def read_vector(cache,key):
    path=Path(cache)/(key+'.json')
    if not path.exists():return None
    try:
        value=json.loads(path.read_text(encoding='utf8'))
        return value if value.get('key')==key and value.get('model')==MODEL and valid_vector(value.get('vector')) else None
    except (ValueError,OSError):return None


def attach(paper,record):
    paper['embedding']=record['vector']
    paper['semantic_status']='available'
    paper['semantic_source']='本地 SPECTER2'
    paper['semantic_model']=MODEL['model']
    paper['semantic_vector_key']=record['key']
    paper['semantic_input']=record['input']


def generate_embeddings(nodes,cache=None,model_dir=None,batch_size=8,threads=8):
    """Cache each exact input/model pair; commit nothing to site files here."""
    import torch
    from transformers import AutoTokenizer
    from adapters import AutoAdapterModel
    cache=Path(cache or WORK/'semantic-vector-cache');cache.mkdir(parents=True,exist_ok=True)
    model_dir=Path(model_dir or WORK/'semantic-models')
    torch.set_num_threads(min(threads,os.cpu_count() or 1))
    tokenizer=None;model=None;pending={};records={};failures={}
    started=time.monotonic()
    for p in nodes:
        if not (p.get('title') or '').strip():
            p.pop('embedding',None);p['semantic_status']='not_available';failures[p['id']]='empty_title';continue
        text,info,key=input_text(p);record=read_vector(cache,key)
        if record:attach(p,record);records[p['id']]=record
        else:pending.setdefault(key,{'text':text,'input':info,'nodes':[]})['nodes'].append(p)
    print(f'Local SPECTER2: {len(records)} cached papers, {len(pending)} distinct inputs to encode',flush=True)
    if pending:
        for name,revision in [('specter2_base',BASE_REVISION),('specter2',ADAPTER_REVISION)]:
            manifest=json.loads((model_dir/name/'revision.json').read_text(encoding='utf8'))
            if manifest['revision']!=revision:raise ValueError('Model revision mismatch: '+name)
        tokenizer=AutoTokenizer.from_pretrained(str(model_dir/'specter2_base'),local_files_only=True)
        if tokenizer.sep_token!='[SEP]':raise ValueError('Unexpected separator token')
        model=AutoAdapterModel.from_pretrained(str(model_dir/'specter2_base'),local_files_only=True)
        model.load_adapter(str(model_dir/'specter2'),load_as='proximity',set_active=True)
        if not model.active_adapters or set(model.active_adapters.flatten())!={'proximity'}:
            raise ValueError('SPECTER2 proximity adapter is not active')
        model.eval()
        for value in pending.values():
            tokens=len(tokenizer(value['text'],truncation=False,verbose=False)['input_ids'])
            value['input'].update(tokens=tokens,truncated=tokens>MAX_TOKENS)
        ordered=sorted(pending.items(),key=lambda kv:kv[1]['input']['tokens'])
        for start in range(0,len(ordered),batch_size):
            batch=ordered[start:start+batch_size]
            inputs=tokenizer([v['text'] for k,v in batch],padding=True,truncation=True,
                             return_tensors='pt',return_token_type_ids=False,max_length=MAX_TOKENS)
            with torch.inference_mode():
                raw=model(**inputs).last_hidden_state[:,0,:]
                vectors=torch.nn.functional.normalize(raw,p=2,dim=1).cpu().tolist()
            for (key,value),vector in zip(batch,vectors):
                if not valid_vector(vector):raise ValueError('Invalid generated vector: '+key)
                record={'key':key,'model':MODEL,'input':value['input'],'vector':vector}
                temp=cache/(key+'.partial');temp.write_text(json.dumps(record,separators=(',',':')),encoding='utf8');temp.replace(cache/(key+'.json'))
                for p in value['nodes']:attach(p,record);records[p['id']]=record
            progress={'ready':len(records),'total':len(nodes),'elapsed_seconds':round(time.monotonic()-started,1),'failures':failures}
            (WORK/'semantic-generation-progress.json').write_text(json.dumps(progress),encoding='utf8')
            if start==0 or (start//batch_size)%10==0 or start+batch_size>=len(ordered):
                print(f"Encoded {len(records)}/{len(nodes)} papers ({progress['elapsed_seconds']} s)",flush=True)
    rows=[]
    for p in nodes:
        if p['id'] in records:
            record=records[p['id']];rows.append({'id':p['id'],'title':p['title'],'status':'success',
             'reason':'local_specter2_title_abstract' if 'abstract' in record['input']['fields'] else 'local_specter2_title_only',
             'input':record['input'],'vector_key':record['key'],'source':'本地 SPECTER2','dimensions':DIMENSIONS})
        else:rows.append({'id':p['id'],'title':p.get('title',''),'status':'failure','reason':failures[p['id']]})
    return rows,{**MODEL,'papers':len(nodes),'ready':len(records),'title_only':sum(r['reason']=='local_specter2_title_only' for r in rows),
                 'lab_ready':sum(p['lab'] and p['id'] in records for p in nodes),'lab_title_only':sum(p['lab'] and p.get('semantic_input',{}).get('fields')==['title'] for p in nodes)}


def semantic_evidence(a,b):
    local=a.get('semantic_source')=='本地 SPECTER2' and b.get('semantic_source')=='本地 SPECTER2'
    if local:
        basis=lambda p:'标题＋摘要' if 'abstract' in p['semantic_input']['fields'] else '仅标题'
        return {'model':MODEL['model'],'source':'local','source_ids':[a['id'],b['id']],
                'text':f'本地 SPECTER2：{basis(a)} ↔ {basis(b)}；余弦相似度'}
    return {'model':'specter_v2','source_ids':[a['semantic_paper_id'],b['semantic_paper_id']],
            'text':'Semantic Scholar SPECTER2 标题与摘要向量的余弦相似度'}


def semantic_edges(nodes):
    import numpy as np
    available=[p for p in nodes if p.get('embedding')]
    if not available:return []
    models={(p.get('semantic_source'),p.get('semantic_model')) for p in available}
    if len(models)>1:raise ValueError('Cannot compare vectors from different model spaces')
    mat=np.asarray([p['embedding'] for p in available],dtype=np.float32)
    mat/=np.linalg.norm(mat,axis=1,keepdims=True)
    labs=[i for i,p in enumerate(available) if p['lab']]
    scores=mat[labs]@mat.T
    edges=[]
    for row,i in enumerate(labs):
        a=available[i]
        for j,b in enumerate(available):
            if a['id']==b['id'] or (b['lab'] and a['id']>b['id']):continue
            edges.append({'id':f"semantic:{a['id']}:{b['id']}",'source':a['id'],'target':b['id'],'kind':'semantic',
                          'score':round(float(np.clip(scores[row,j],-1,1)),6),'tentative':True,'evidence':semantic_evidence(a,b)})
    return edges
