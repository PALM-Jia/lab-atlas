import json,sys,concurrent.futures,collections
from pathlib import Path
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages')
sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API, WORK
root=Path('outputs/paper-atlas')
a=json.loads((root/'acceptance.json').read_text(encoding='utf8'))
api=API(WORK/'api-cache')
rows=a['steps']['05_external_metadata']['items']
missing=[r for r in rows if r['status']=='failure' and r['reason']=='openalex_id_not_returned']
def probe(r):
 data,event=api.request('https://api.openalex.org/works/'+r['id'])
 r['lookup_evidence']=event
 if data:
  r['returned_id']=data.get('id')
  r['reason']='external_id_redirect_requires_reconciliation' if data.get('id','').split('/')[-1]!=r['id'] else 'external_record_found_after_graph_build'
 else:
  r['reason']='external_id_http_404' if event['reason']=='http_404' else 'external_direct_lookup_'+event['reason']
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 list(pool.map(probe,missing))
a['steps']['05_external_metadata']['reasons']=dict(collections.Counter(r['reason'] for r in rows))
a['external_lookup_audit']=api.events
(root/'acceptance.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(collections.Counter(r['reason'] for r in missing)))
