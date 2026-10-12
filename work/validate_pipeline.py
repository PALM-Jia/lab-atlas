"""Independent validation: accounting, identity, edge evidence and public data scope."""
import collections
import json
import math
from pathlib import Path

root=Path('outputs/paper-atlas')
d=json.loads((root/'data.json').read_text(encoding='utf8'))
report=json.loads((root/'acceptance.json').read_text(encoding='utf8'))
nodes={p['id']:p for p in d['nodes']}
lab={p['id']:p for p in nodes.values() if p['lab']}
assert len(nodes)==len(d['nodes'])
assert len(lab)==144
assert len({p['openalex'] for p in lab.values() if p.get('openalex')})==sum(bool(p.get('openalex')) for p in lab.values())
for step,entry in report['steps'].items():
    rows=entry['items']
    assert entry['total']==len(rows)==len({r['id'] for r in rows}),step
    assert entry['success']+entry['explained_failure']==entry['total'],step
    assert entry['unexplained']==0 and all(r['reason'] for r in rows),step
    if step not in ('05_external_metadata','03_api_requests','11_relation_validation','12_frontend_checks') and step not in ('08_content_vector','10_layout'):
        assert {r['id'] for r in rows}==set(lab),step+' denominator changed'
    if step in ('08_content_vector','10_layout'):
        assert {r['id'] for r in rows}==set(nodes),step+' denominator changed'
citing=json.loads(Path('work/citing-sets.json').read_text(encoding='utf8'))
edges=json.loads((root/'relations-full.json').read_text(encoding='utf8'))
assert len({e['id'] for e in edges})==len(edges)
tests=[]
for e in edges:
    reason='evidence_verified'; ok=True
    try:
        a,b=nodes[e['source']],nodes[e['target']]
        assert a['id']!=b['id'] and math.isfinite(e['score'])
        kind=e['kind'];v=e['evidence']
        if kind=='citation':
            assert a['lab'] or b['lab'], 'external-to-external citation prohibited'
            assert b['openalex'].split('/')[-1] in a['references']
        elif kind=='coupling':
            s=set(a['references'])&set(b['references'])
            assert s==set(v['ids']) and len(s)==v['count']
            assert abs(e['score']-len(s)/math.sqrt(len(set(a['references']))*len(set(b['references']))))<.00011
        elif kind=='cocitation':
            s=set(citing.get(a['id'],[]))&set(citing.get(b['id'],[]))
            assert s==set(v['ids']) and len(s)==v['count']
        elif kind=='author':
            if v.get('author_ids'):
                ids_a={r['id'] for r in a['author_records']}
                ids_b={r['id'] for r in b['author_records']}
                assert set(v['author_ids'])<=ids_a&ids_b
            else:assert e['tentative']
            assert all(n.lower()!='yuheng jia' for n in v['authors'])
        elif kind=='institution':
            assert set(v['institution_ids'])<=({r['id']for r in a['institution_records']}&{r['id']for r in b['institution_records']})
        elif kind=='topic':
            assert e['tentative']
            if v.get('topic_ids'):assert set(v['topic_ids'])<=({t['id']for t in a['api_topics']}&{t['id']for t in b['api_topics']})
            else:assert set(v['tags'])<=set(a['tags'])&set(b['tags'])
        elif kind=='semantic':
            assert e['tentative'] and -1.0001<=e['score']<=1.0001
            assert a['semantic_status']==b['semantic_status']=='available'
            keys=[a['id'],b['id']] if v.get('source')=='local' else [a['semantic_paper_id'],b['semantic_paper_id']]
            assert v['source_ids']==keys
        elif kind=='series':raise AssertionError('User excluded manual series')
    except (AssertionError,KeyError,ValueError,ZeroDivisionError) as err:
        ok=False;reason=type(err).__name__+': '+str(err)
    tests.append({'id':e['id'],'kind':e['kind'],'status':'success' if ok else 'failure','reason':reason})
for p in nodes.values():assert math.isfinite(p['x'])and math.isfinite(p['y'])

# Recompute semantic edge scores independently from the public API vector cache.
import numpy as np
vectors={}
if d['meta'].get('semantic',{}).get('method')=='local':
    import sys
    sys.path.insert(0,str(root))
    from semantic_features import input_text,read_vector
    for p in nodes.values():
        if p['semantic_status']!='available':continue
        text,info,key=input_text(p)
        assert key==p['semantic_vector_key'] and info['sha256']==p['semantic_input']['sha256']
        record=read_vector(Path('work/semantic-vector-cache'),key)
        assert record and record['input']==p['semantic_input']
        vectors[p['id']]=np.array(record['vector'],dtype=np.float64)
    available=[p for p in nodes.values() if p['semantic_status']=='available']
    lab_count=sum(p['lab'] for p in available)
    assert sum(e['kind']=='semantic' for e in edges)==lab_count*(len(available)-lab_count)+lab_count*(lab_count-1)//2
else:
    for path in Path('work/api-cache').glob('*.json'):
        raw=json.loads(path.read_text(encoding='utf8'))
        records=raw if isinstance(raw,list) else [raw]
        for r in records:
            if isinstance(r,dict) and r.get('paperId') and (r.get('embedding')or{}).get('vector'):
                assert (r['embedding'].get('model')or'').lower() in ('specter_v2','specter2')
                v=np.array(r['embedding']['vector'],dtype=np.float32)
                assert len(v)==768 and np.all(np.isfinite(v))
                vectors[r['paperId']]=v/np.linalg.norm(v)
semantic=[e for e in edges if e['kind']=='semantic']
for start in range(0,len(semantic),1000):
    batch=semantic[start:start+1000]
    aa=np.array([vectors[e['evidence']['source_ids'][0]]for e in batch])
    bb=np.array([vectors[e['evidence']['source_ids'][1]]for e in batch])
    scores=np.sum(aa*bb,axis=1)
    assert np.all(np.abs(scores-np.array([e['score']for e in batch]))<.00011)

full_ids={e['id']for e in edges}
assert all(e['id']in full_ids for e in d['edges'])
assert d['meta']['stats']['edges']=={k:sum(e['kind']==k for e in d['edges'])for k in d['meta']['stats']['edges']}
counts={}
for kind in d['meta']['stats']['full_edges']:
    rows=[r for r in tests if r['kind']==kind];good=sum(r['status']=='success'for r in rows)
    counts[kind]={'total':len(rows),'success':good,'explained_failure':len(rows)-good,'unexplained':0}
result={'status':'passed' if all(t['status']=='success'for t in tests)else'failed','accounting':'all ledger items classified','relation_evidence':counts,'failed_edges':[r for r in tests if r['status']=='failure']}
(root/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
assert result['status']=='passed'

