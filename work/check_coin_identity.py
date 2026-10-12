import sys,json
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages');sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API,WORK,ROOT
api=API(WORK/'api-cache')
r,e=api.request('https://api2.openreview.net/notes?id=LhhFsfAzL6','OpenReview')
a=json.loads((ROOT/'identity-search-audit.json').read_text(encoding='utf8'))
v=next(v for v in a if v['id']=='lab-b4f457369e13')
v['queries'].append(e)
if e['status']=='failure':
 v['reason']='public_candidate_page_access_blocked'
 v['public_evidence'].append({'url':'https://openreview.net/forum?id=LhhFsfAzL6','title_present':False,'event':e,'evidence_type':'search_located_candidate_access_blocked'})
(ROOT/'identity-search-audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
print(e['reason'])
