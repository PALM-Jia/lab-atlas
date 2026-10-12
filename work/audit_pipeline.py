import importlib.util,json,hashlib,collections
from pathlib import Path
sp=importlib.util.spec_from_file_location('collector','outputs/paper-atlas/collect.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
d=json.loads(Path('outputs/paper-atlas/data.json').read_text(encoding='utf8'))
lab=[p for p in d['nodes'] if p['lab']]
api=m.API(Path('work/api-cache'));api.cache_only=True
summary=collections.Counter();examples=[]
for p in lab:
 if p['match_status']!='ambiguous':continue
 r=api.works(search=p['title'],per_page=3)
 qualified=[]
 for w in (r or {}).get('results',[]):
  score=m.SequenceMatcher(None,m.norm(p['title']),m.norm(w.get('title')or'')).ratio()
  names={m.norm(a['author']['display_name']) for a in w.get('authorships',[])}
  if score>=.93 and ('yuhengjia' in names or names&{m.norm(a)for a in p['authors']}):
   qualified.append({'id':w['id'],'title':w['title'],'doi':w.get('doi'),'type':w.get('type'),'year':w.get('publication_year')})
 summary['ambiguous_papers']+=1
 summary['with_exact_title_candidate']+=any(m.norm(w['title'])==m.norm(p['title'])for w in qualified)
 summary['all_exact_titles']+=all(m.norm(w['title'])==m.norm(p['title'])for w in qualified)
 summary['with_different_years']+=len({w['year']for w in qualified})>1
 if len(examples)<5:examples.append({'list_title':p['title'],'links':p.get('links'), 'qualified':qualified})
print('ambiguity',dict(summary));print('examples',json.dumps(examples,ensure_ascii=False))
unmatched=[p for p in lab if p['match_status']!='matched']
print('unmatched links',sum(bool(p.get('links'))for p in unmatched), 'of',len(unmatched))
print('errors',[(p['title'],p.get('links'))for p in unmatched if p['match_status']=='api_error'])
print('unmatched withlinks',[(p['title'],p.get('links'))for p in unmatched if p.get('links')][:8])
print('manual_overrides',json.loads(Path('outputs/paper-atlas/overrides.json').read_text(encoding='utf8')))
print('unique authors IDs',sum(bool(p.get('author_ids'))for p in lab))
print('raw api cache records',len(list(Path('work/api-cache').glob('*.json'))))
