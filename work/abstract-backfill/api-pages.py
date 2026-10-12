import json,re,subprocess,hashlib,concurrent.futures,collections,urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
OUT=Path(__file__).resolve().parent
targets=[p for p in json.loads((OUT/'api-manifest.json').read_text(encoding='utf8'))if p['lab']]
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def fetch(url):
    path=OUT/('api-page-'+hashlib.sha256(url.encode()).hexdigest()+'.html')
    if path.exists():return path.read_text(encoding='utf8'),{'url':url,'http':200,'status':'cached','file':path.name}
    try:
        r=subprocess.run(['curl.exe','-L','--silent','--show-error','--max-time','20','--write-out','\n%{http_code}',url],capture_output=True,timeout=24)
        raw,_,code=r.stdout.rpartition(b'\n');status=int(code)if code.isdigit()else 0
        if not r.returncode and 200<=status<300:
            text=raw.decode('utf8',errors='replace');path.write_text(text,encoding='utf8');return text,{'url':url,'http':status,'status':'received','file':path.name}
        return None,{'url':url,'http':status,'status':'query_failed','reason':'http_'+str(status)if status else'curl_'+str(r.returncode)}
    except Exception as e:return None,{'url':url,'http':None,'status':'query_failed','reason':type(e).__name__}
def extract(html,url):
    if 'api2.openreview.net' in url or 'api.openreview.net' in url:
        d=json.loads(html);ns=d.get('notes',[])
        if not ns:return None
        c=ns[0].get('content',{});v=lambda k:c.get(k,{}).get('value')if isinstance(c.get(k),dict)else c.get(k)
        return {'title':v('title'),'abstract':v('abstract'),'authors':v('authors'),'doi':None}
    s=BeautifulSoup(html,'html.parser')
    def meta(*names):
        for name in names:
            v=s.find('meta',attrs={'name':name})or s.find('meta',attrs={'property':name})
            if v:return v.get('content')
    title=meta('citation_title','DC.Title','dc.title','og:title');a=None
    if 'neurips.cc/virtual' in url or 'cvpr.thecvf.com/virtual' in url or 'icml.cc/virtual' in url:
        title=(s.select_one('.event-title')or s.select_one('.maincardBody')).get_text(' ',strip=True)if(s.select_one('.event-title')or s.select_one('.maincardBody'))else title
        el=s.select_one('.abstract-text-inner')or s.select_one('.abstract')or s.select_one('#abstract')or s.select_one('.card-text');a=el.get_text(' ',strip=True)if el else None
    elif 'aclanthology.org' in url:
        el=s.select_one('.acl-abstract');a=el.get_text(' ',strip=True)if el else None
    elif 'thecvf.com' in url:
        el=s.select_one('#abstract');a=el.get_text(' ',strip=True)if el else None
    elif 'arxiv.org' in url:
        el=s.select_one('blockquote.abstract');a=el.get_text(' ',strip=True)if el else None
    elif 'springer' in url:
        el=s.select_one('#Abs1-content')or s.select_one('.c-article-section__content');a=el.get_text(' ',strip=True)if el else None
    elif 'sciencedirect.com' in url:
        el=s.select_one('#abstracts')or s.select_one('.abstract');a=el.get_text(' ',strip=True)if el else None
    elif 'nips.cc' in url or 'neurips.cc/paper_files' in url:
        title=s.select_one('.paper-title').get_text(' ',strip=True)if s.select_one('.paper-title')else title
        el=s.select_one('.paper-abstract');a=el.get_text(' ',strip=True)if el else None
    elif 'nature.com' in url:
        el=s.select_one('#Abs1-content')or s.select_one('#abstract-content');a=el.get_text(' ',strip=True)if el else None
    elif 'proceedings.mlr.press' in url:
        el=s.select_one('#abstract')or s.select_one('.abstract');a=el.get_text(' ',strip=True)if el else None
    authors=[v.get('content')for v in s.find_all('meta',attrs={'name':'citation_author'})]
    return {'title':title,'abstract':re.sub(r'^Abstract\s*:?\s*','',a).strip()if a else None,'authors':authors,'doi':meta('citation_doi','dc.identifier')}
download=BeautifulSoup((OUT/'api-neurips-downloads.html').read_text(encoding='utf8'),'html.parser')
neurips={norm(a.get_text(' ',strip=True)):'https://neurips.cc'+a['href']for a in download.find_all('a',href=True)}
extra={'lab-b4f457369e13':['https://api2.openreview.net/notes?id=LhhFsfAzL6','https://openreview.net/forum?id=LhhFsfAzL6'],'lab-d99ee9ba4a13':['https://aclanthology.org/2025.acl-long.175/'],'lab-a07279b34373':['https://arxiv.org/abs/2610.07610'],'lab-cafae06c3f4f':['https://arxiv.org/abs/2411.05842'],'lab-cfe1c0f8487f':['https://openaccess.thecvf.com/content/ICCV2025/html/Li_Boosting_Class_Representation_via_Semantically_Related_Instances_for_Robust_Long-Tailed_ICCV_2025_paper.html'],'lab-10ec9a4b941d':['https://papers.nips.cc/paper_files/paper/2023/hash/6b97236d90d945be7c58268207a14f4f-Abstract-Conference.html']}
extra['lab-b4f457369e13']=['https://icml.cc/virtual/2026/poster/64609']
extra['lab-8a05dc1f7a41']=['https://cvpr.thecvf.com/virtual/2026/poster/40839']
extra['lab-10ec9a4b941d']=['https://papers.neurips.cc/paper_files/paper/2023/hash/6b97236d90d945be7c58268207a14f4f-Abstract-Conference.html']
def process(p):
    row={'id':p['id'],'title':p['title'],'status':'no_abstract','abstract':None,'attempts':[],'candidates':[]}
    urls=extra.get(p['id'],[])[:]
    if norm(p['title'])in neurips:urls.insert(0,neurips[norm(p['title'])])
    if p.get('doi')and p['doi'].startswith('10.1007/'):urls.append('https://link.springer.com/chapter/'+p['doi'])
    urls += [u for u in p['landing_urls']if'openalex.org'not in u and'openreview.net/pdf'not in u]
    urls=list(dict.fromkeys(urls))
    if not urls:row.update(status='not_found',reason='exact_title_web_search_found_no_verifiable_publication_page')
    for url in urls:
        h,event=fetch(url);row['attempts'].append(event)
        if h:
            w=extract(h,url)
            if w and w.get('abstract'):
                accepted=norm(w.get('title')or'')==norm(p['title'])and len(w['abstract'].split())>=25
                cand={**w,'source_url':url,'accepted':accepted,'reason':'exact_title_on_official_publication_page'if accepted else'title_mismatch_requires_review'};row['candidates'].append(cand)
                if accepted:row.update(status='success',abstract=w['abstract'],source_url=url,reason=cand['reason']);break
        elif row['status']!='success':row.update(status='query_failed',reason=event.get('reason','empty_response'))
    if row['status']=='no_abstract':row['reason']='pages_returned_no_verified_abstract'
    return row
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(process,targets))
    (OUT/'lab-results.json').write_text(json.dumps({'summary':dict(collections.Counter(x['status']for x in rows)),'results':rows},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'summary':dict(collections.Counter(x['status']for x in rows)),'successes':[x['title']for x in rows if x['status']=='success']}))
