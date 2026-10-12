import sys,json,urllib.parse
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages');sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API,WORK,ROOT
api=API(WORK/'api-cache')
results={}
for aid in ['2603.06281','2610.07610']:
 w,e=api.request('https://api.openalex.org/works/'+urllib.parse.quote('https://doi.org/10.48550/arxiv.'+aid,safe=''))
 results[aid]={'record':w,'event':e}
 print(aid,e['reason'],w.get('id')if w else None,w.get('title')if w else None)
(ROOT/'identity-arxiv-lookups.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
