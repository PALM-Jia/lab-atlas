"""Refresh only semantic features/edges, preserving all other collected fields."""
import collections,datetime,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ATLAS=ROOT/'data/atlas';REPORTS=ROOT/'work/reports';sys.path.insert(0,str(Path(__file__).resolve().parent))
from semantic_features import generate_embeddings,semantic_edges

def summary(rows):
 good=sum(r['status']=='success' for r in rows);total=len(rows)
 return {'total':total,'success':good,'explained_failure':total-good,'success_rate':round(good/total*100,4) if total else 0,'failure_rate':round((total-good)/total*100,4) if total else 0,'accounted_rate':100 if total else 0,'unexplained':0,'reasons':dict(collections.Counter(r['reason'] for r in rows)),'items':rows}

def save(name,value,pretty=False):
 p=ATLAS/name;p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.partial');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2 if pretty else None,separators=None if pretty else (',',':')),encoding='utf8');temp.replace(p)

def run():
 d=json.loads((ATLAS/'data.json').read_text(encoding='utf8'));rows,model=generate_embeddings(d['nodes'])
 edges=semantic_edges(d['nodes']);d['edges']=[e for e in d['edges'] if e['kind']!='semantic']+edges
 d['meta']['semantic']={**model,'updated':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')}
 d['meta']['stats']['vectors']=model['ready']
 for key in ['edges','full_edges']:d['meta']['stats'][key]['semantic']=len(edges)
 for p in d['nodes']:p.pop('embedding',None)
 report=summary(rows);save('semantic-generation.json',{'model':d['meta']['semantic'],'coverage':report},True)
 acceptance=json.loads((ATLAS/'acceptance.json').read_text(encoding='utf8'))
 history=REPORTS/'semantic-api-history.json'
 if not history.exists():history.write_text(json.dumps({k:acceptance['steps'][k] for k in ['08_content_vector','07_readiness_semantic']},ensure_ascii=False,indent=2),encoding='utf8')
 acceptance['steps']['08_content_vector']=report
 acceptance['steps']['07_readiness_semantic']=summary([{**r,'reason':'relation_input_ready' if r['status']=='success' else r['reason']} for r in rows if next(p['lab'] for p in d['nodes'] if p['id']==r['id'])])
 acceptance['meta']=d['meta'];save('acceptance.json',acceptance,True)
 coverage=json.loads((ATLAS/'coverage.json').read_text(encoding='utf8'));coverage['meta']=d['meta'];save('coverage.json',coverage,True)
 save('data.json',d)
 print(json.dumps({'model':model,'edges':len(edges),'lab_success':acceptance['steps']['07_readiness_semantic']['success']},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
