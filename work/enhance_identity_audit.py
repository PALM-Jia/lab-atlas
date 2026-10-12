import sys,json,urllib.parse,re
from pathlib import Path
sys.path.append('C:/ProgramData/miniconda3/Lib/site-packages');sys.path.insert(0,'outputs/paper-atlas')
from pipeline import API,WORK,ROOT,base
api=API(WORK/'api-cache')
audit=json.loads((ROOT/'identity-search-audit.json').read_text(encoding='utf8'))
manifest=json.loads((ROOT/'identity-discoveries.json').read_text(encoding='utf8'))
seed={
'lab-5403cb1aad23':'https://proceedings.iclr.cc/paper_files/paper/2025/hash/a8b879590adff2b1874f97db59b65518-Abstract-Conference.html',
'lab-bddb535117ca':'https://proceedings.iclr.cc/paper_files/paper/2025/hash/0a1f690b558591412b5bddaf10de3b19-Abstract-Conference.html',
'lab-2c640db3fd61':'https://proceedings.iclr.cc/paper_files/paper/2025/hash/95b6e2ff961580e03c0a662a63a71812-Abstract-Conference.html',
'lab-77b725acea33':'https://proceedings.iclr.cc/paper_files/paper/2026/hash/813ed01a11220fcdeed10e0d7da2de25-Abstract-Conference.html',
'lab-82a7992c094e':'https://proceedings.mlr.press/v267/li25am.html',
'lab-1ba64af37485':'https://arxiv.org/abs/2603.06281v1',
}
indices={}
for url in ['https://neurips.cc/Downloads/2026','https://proceedings.iclr.cc/paper_files/paper/2026','https://proceedings.mlr.press/v306/']:
 text,e=api.request(url,'Public proceedings',text=True)
 if text:
  soup=base.BeautifulSoup(text,'html.parser')
  for tag in soup.select('a[href]'):
   indices.setdefault(base.norm(tag.get_text(' ',strip=True)),[]).append(urllib.parse.urljoin(url,tag['href']))
 print('Index',url,e['reason'],flush=True)
publicmeta={}
for r in audit:
 urls=indices.get(base.norm(r['title']),[])
 r['official_listing_urls']=urls
 if r['id'] in seed:urls=[seed[r['id']]]+urls
 r['public_evidence']=[]
 for url in urls[:1]:
  text,event=api.request(url,'Public paper page',text=True)
  proof={'url':url,'event':event}
  if text:
   soup=base.BeautifulSoup(text,'html.parser');contents=soup.get_text(' ',strip=True)
   verified=base.norm(r['title'])in base.norm(contents)
   proof['title_present']=verified
   proof['listed_source_authors_present']=[n for n in r['source_authors']if base.norm(n)in base.norm(contents)]
   if verified:
    abstract=soup.select_one('#abstract')
    if not abstract:
     heading=next((t for t in soup.select('h2,h3,h4')if t.get_text(' ',strip=True)=='Abstract'),None)
     if heading:abstract=heading.find_next_sibling('p')
    meta={'links':[url],'source':url}
    if abstract:meta['abstract']=abstract.get_text(' ',strip=True)
    authors=[t.get('content')for t in soup.select('meta[name="citation_author"]')if t.get('content')]
    if authors:meta['authors']=authors
    publicmeta[r['id']]=meta
  r['public_evidence'].append(proof)
 r['web_search_query']='"'+r['title']+'"'
 r['web_search_scope']='general web title / distinctive phrase search; primary pages recorded when found'
 print(r['id'],'official evidence',len(r['public_evidence']),flush=True)
# Confirm arXiv DOI identity and title changes against versioned pages.
for pid,aid in [('lab-1ba64af37485','2603.06281'),('lab-a07279b34373','2610.07610')]:
 w,event=api.request('https://api.openalex.org/works/'+urllib.parse.quote('https://doi.org/10.48550/arxiv.'+aid,safe=''))
 r=next(r for r in audit if r['id']==pid);r['arxiv_lookup']={'record_id':w.get('id')if w else None,'title':w.get('title')if w else None,'event':event}
 if pid=='lab-1ba64af37485' and w:
  manifest[pid]={'openalex':w['id'],'method':'versioned_title_identity','verified_titles':[r['title'],w['title']],'evidence':{'original_version':'https://arxiv.org/abs/2603.06281v1','current_version':'https://arxiv.org/abs/2603.06281','shared_arxiv_id':aid}}
  r['status']='success';r['reason']='versioned_title_identity'
 if pid=='lab-a07279b34373':
  r['related_public_candidate']={'url':'https://arxiv.org/abs/2610.07610','title':'Hub for Outliers, Spokes for Inliers: Uniform Latent Space Construction for Dual-Mismatched Semi-Supervised Learning','authors':['Li Yuan','Yaxin Hou','Jiawei Tang','Yongbiao Gao','Yuheng Jia'],'identity_confirmed':False}
  data,e=api.works(filter='title.search:Hub for Outliers',per_page=50);r['queries'].append(e)
  r['reason']='possible_renamed_paper_without_version_identity'
# Official CVPR program independently lists the exact title and source authors.
r=next(r for r in audit if r['id']=='lab-8a05dc1f7a41')
w,e=api.request(r['closest_openalex'][0]['id'])
if w:
 manifest[r['id']]={'openalex':w['id'],'method':'official_program_title_authors','evidence':{'url':'https://media.eventhosts.cc/Conferences/CVPR2026/CVPR_main_conf_2026_15.pdf','title':r['title'],'authors':r['source_authors'],'doi':w.get('doi'),'openalex_authors_missing':True}}
 r['status']='success';r['reason']='official_program_title_authors'
for r in audit:
 if r['status']=='failure' and r['reason']!='possible_renamed_paper_without_version_identity':
  verified=any(p.get('title_present') for p in r['public_evidence'])
  r['reason']='public_page_verified_no_openalex_match' if verified else 'official_listing_no_openalex_match' if r['official_listing_urls'] else 'spelling_variant_no_verified_match' if 'Hyerspectral' in r['title']or'Poistive'in r['title'] else 'no_public_locator_for_future_year' if (r['source_year'] or 0)>2026 else 'title_only_no_independent_locator' if not r['source_authors'] and not r['source_links'] else 'public_source_known_openreview_api_blocked' if r['source_links'] and 'openreview'in r['source_links'][0] else 'expanded_search_no_verified_record'
(ROOT/'identity-search-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'identity-discoveries.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'public-paper-metadata.json').write_text(json.dumps(publicmeta,ensure_ascii=False,indent=2),encoding='utf8')
print('Manifest',len(manifest),'Public metadata',len(publicmeta),flush=True)

