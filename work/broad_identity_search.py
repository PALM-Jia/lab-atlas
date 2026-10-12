import sys,json,urllib.parse,concurrent.futures,collections
from pathlib import Path
from difflib import SequenceMatcher
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages');sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API,WORK,ROOT,base
api=API(WORK/'api-cache')
a=json.loads((ROOT/'acceptance.json').read_text(encoding='utf8'))
source={p['id']:p for p in json.loads((ROOT/'lab-papers.json').read_text(encoding='utf8'))}
failed=[source[r['id']] for r in a['steps']['02_match']['items']if r['reason']=='no_title_author_or_identifier_verified_candidate']
d=json.loads((ROOT/'data.json').read_text(encoding='utf8'))
author_ids=sorted({r['id'].split('/')[-1]for p in d['nodes']if p['lab'] for r in p.get('author_records',[])if base.norm(r['name'])=='yuhengjia'})
corpus={};corpus_events=[];cursor='*'
for page in range(5):
 data,event=api.works(filter='authorships.author.id:'+'|'.join(author_ids),per_page=200,cursor=cursor)
 corpus_events.append(event)
 if not data:break
 corpus.update({w['id']:w for w in data.get('results',[])})
 cursor=data.get('meta',{}).get('next_cursor')
 if not cursor or len(corpus)>=data.get('meta',{}).get('count',0):break
print('Author corpus',len(corpus),flush=True)
def score(p,w):return SequenceMatcher(None,base.norm(p['title']),base.norm(w.get('title')or'')).ratio()
def names(w):return {base.norm(r['author']['display_name']) for r in w.get('authorships',[])}
def search(p):
 pool=dict(corpus);events=[];cross=[]
 title=p['title'].replace('Hyerspectral','Hyperspectral').replace('Poistive','Positive')
 for query in [title, title.split(':')[-1].strip() if ':' in title else ' '.join(title.split()[:7])]:
  data,event=api.works(filter='title.search:'+query.replace(',',' ').replace(':',' '),per_page=50)
  events.append(event)
  if data:pool.update({w['id']:w for w in data.get('results',[])})
  if query==title and ':' not in title and len(title.split())<=7:break
 url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.title':title,'rows':10})
 data,event=api.request(url,'Crossref');events.append(event)
 if data:
  for r in data.get('message',{}).get('items',[]):
   t=(r.get('title')or[''])[0];s=SequenceMatcher(None,base.norm(title),base.norm(t)).ratio()
   an={base.norm(v.get('given','')+' '+v.get('family','')) for v in r.get('author',[])}
   cross.append({'title':t,'doi':r.get('DOI'),'authors':sorted(an),'score':round(s,4)})
   if s>=.90 and (an & {base.norm(v)for v in p['authors']} or 'yuhengjia'in an):
    w,e=api.request('https://api.openalex.org/works/'+urllib.parse.quote('https://doi.org/'+r['DOI'],safe=''))
    events.append(e)
    if w and w.get('id'):pool[w['id']]=w
 ranked=sorted(pool.values(),key=lambda w:score(p,w),reverse=True)
 qualified=[w for w in ranked if score(p,w)>=.93 and (names(w)&{base.norm(v)for v in p['authors']} or 'yuhengjia'in names(w))]
 formal=[w for w in qualified if w.get('type')in ('article','conference-paper')]
 selected=formal[0] if len(formal)==1 else qualified[0] if len(qualified)==1 else None
 closest=[{'id':w['id'],'title':w.get('title'),'score':round(score(p,w),4),'authors':sorted(names(w)),'doi':w.get('doi'),'type':w.get('type')}for w in ranked[:3]]
 exact=[w for w in ranked if score(p,w)>=.93]
 reason='broad_search_verified' if selected else 'multiple_candidates_after_broad_search' if qualified else 'title_found_author_not_verified' if exact else 'search_incomplete_api_failure' if any(e['status']=='failure'for e in events+corpus_events) else 'no_verified_title_in_completed_search'
 out={'id':p['id'],'title':p['title'],'status':'success'if selected else'failure','reason':reason,'source_authors':p['authors'],'source_year':p['year'],'source_links':p['links'],'closest_openalex':closest,'crossref_candidates':sorted(cross,key=lambda r:-r['score'])[:3],'queries':events,'author_corpus_queries':corpus_events,'selected':selected}
 print(p['id'],reason,closest[0]['score']if closest else None,flush=True)
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool: results=list(pool.map(search,failed))
(ROOT/'identity-search-audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
manifest={r['id']:{'openalex':r['selected']['id'],'method':'broader_public_search','evidence':{'audit':'identity-search-audit.json','queries':r['queries']}} for r in results if r['selected']}
(ROOT/'identity-discoveries.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('Finished',len(manifest),'/',len(results),flush=True)
