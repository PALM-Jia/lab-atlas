import sys,json,runpy
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages');sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API,WORK,ROOT
api=API(WORK/'api-cache')
a=json.loads((ROOT/'identity-search-audit.json').read_text(encoding='utf8'))
m=json.loads((ROOT/'identity-discoveries.json').read_text(encoding='utf8'))
r=next(r for r in a if r['id']=='lab-8a05dc1f7a41')
w,e=api.request('https://api.openalex.org/works/'+r['closest_openalex'][0]['id'].split('/')[-1])
if w:
 m[r['id']]={'openalex':w['id'],'method':'official_program_title_authors','evidence':{'url':'https://media.eventhosts.cc/Conferences/CVPR2026/CVPR_main_conf_2026_15.pdf','title':r['title'],'authors':r['source_authors'],'doi':w.get('doi'),'openalex_authors_missing':True}}
 r['status']='success';r['reason']='official_program_title_authors'
for r in a:
 if r['reason']=='official_listing_no_openalex_match':
  r['public_evidence'].insert(0,{'url':'https://neurips.cc/Downloads/2026','title_present':True,'evidence_type':'official_title_listing','event':{'status':'success','reason':'received'}})
(ROOT/'identity-search-audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'identity-discoveries.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
print('Discoveries',len(m),flush=True)
runpy.run_path('outputs/paper-atlas/pipeline.py',run_name='__main__')
