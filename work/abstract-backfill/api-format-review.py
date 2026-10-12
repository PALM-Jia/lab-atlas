import json,importlib.util,concurrent.futures,collections
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pages',OUT/'api-pages.py');pages=importlib.util.module_from_spec(spec);spec.loader.exec_module(pages)
manifest={p['id']:p for p in json.loads((OUT/'api-manifest.json').read_text(encoding='utf8'))}
todo=[manifest[p['id']]for p in json.loads((OUT/'merged-abstracts.json').read_text(encoding='utf8'))['results']if p['status']!='success'and str(manifest[p['id']].get('doi')or'').startswith('10.1007/')]
def process(p):
    d=p['doi'];kind='chapter'if'_'in d else'book'if d.split('/')[1].startswith(('978','0-','1-','3-'))else'article';url='https://link.springer.com/'+kind+'/'+d
    h,e=pages.fetch(url);row={'id':p['id'],'title':p['title'],'status':'unresolved','abstract':None,'attempts':[e],'candidates':[],'reason':'canonical_publisher_route_did_not_yield_verified_abstract'}
    if h:
        w=pages.extract(h,url)
        if w and w.get('abstract'):
            ok=pages.norm(w.get('title')or'')==pages.norm(p['title'])and len(w['abstract'].split())>=25
            row['candidates'].append({**w,'source_url':url,'accepted':ok,'reason':'exact_title_at_canonical_DOI_publication_page'if ok else'identity_or_quality_mismatch'})
            if ok:row.update(status='success',abstract=w['abstract'],source_url=url,reason='exact_title_at_canonical_DOI_publication_page')
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(process,todo))
(OUT/'api-format-review-results.json').write_text(json.dumps({'summary':dict(collections.Counter(x['status']for x in rows)),'results':rows},ensure_ascii=False,indent=2),encoding='utf8');print([(x['title'],x['status'])for x in rows])
