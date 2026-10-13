import json,re,os,time,hashlib,subprocess,threading,concurrent.futures,urllib.parse,unicodedata,collections,argparse
from pathlib import Path
from difflib import SequenceMatcher
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'work/abstract-backfill'
OUT.mkdir(parents=True,exist_ok=True)
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s or '').lower())
def doi(s):return re.sub(r'^https?://(?:dx\.)?doi.org/','',s or '',flags=re.I).lower().strip().rstrip('.')
def text_abstract(w):
    a=w.get('abstract')
    if isinstance(a,str):return a.strip()
    ix=w.get('abstract_inverted_index')
    if ix:return ' '.join(x[1] for x in sorted((p,t) for t,ps in ix.items() for p in ps))
    return None
def valid(a):
    if not a or len(a.split())<25:return False,'absent_or_too_short'
    if len(a.split())<80 and a.count(',')>=5 and re.search(r'Proceedings of .*\b(?:19|20)\d{2}\.?$',a,re.I):return False,'bibliographic_citation_not_abstract'
    if re.search(r'<(?:html|div|script|!DOCTYPE)|Access Denied|Just a moment',a,re.I):return False,'html_or_access_page'
    if a.count('Google Scholar')>1 or len(re.findall(r'\[\d+\]',a))>6:return False,'reference_list'
    if len(re.findall(r'\b(?:19|20)\d{2}\b',a))>=5 and len(re.findall(r'\b(?:IEEE|Springer|Proceedings|pp\.)',a))>=4:return False,'reference_list'
    return True,'substantive_abstract'
def make_manifest():
    nodes=json.loads((ROOT/'data/atlas/data.json').read_text(encoding='utf8'))['nodes']
    rows=[]
    for p in nodes:
        if valid(p.get('abstract'))[0]:continue
        links=[x for x in p.get('links',[])+[p.get('doi'),p.get('openalex')]if x]
        arxiv=list(dict.fromkeys(re.findall(r'(?:arxiv\.org/(?:abs|pdf)/|arxiv\.)(\d{4}\.\d{4,5})(?:v\d+)?',' '.join(links),re.I)))
        rows.append({'id':p['id'],'title':p['title'],'lab':p['lab'],'year':p.get('year'),'authors':p.get('authors',[]),'doi':doi(p.get('doi')) or None,'arxiv':arxiv,'openalex':p.get('openalex'),'semantic_scholar':p.get('semantic_paper_id'),'landing_urls':list(dict.fromkeys(x for x in links if x)),'versions':p.get('versions',[]),'target_reason':valid(p.get('abstract'))[1] if p.get('abstract') else 'missing_abstract'})
    (OUT/'api-manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    return rows
def match(p,w):
    title=w.get('title')or w.get('display_name')or''
    sim=SequenceMatcher(None,norm(p['title']),norm(title)).ratio()
    if sim<.96:return False,f'title_similarity_{sim:.3f}'
    ext=w.get('externalIds')or{}
    wd=doi(w.get('doi') or ext.get('DOI'));wid=w.get('id')or''
    ident=(p.get('openalex')==wid or (p.get('doi') and p['doi']==wd) or (p.get('semantic_scholar') and p['semantic_scholar']==w.get('paperId')) or (ext.get('ArXiv') in p.get('arxiv',[]) if ext.get('ArXiv') else False))
    wy=w.get('publication_year')or w.get('year')
    if not ident and p.get('year') and wy and abs(p['year']-wy)>2:return False,'year_mismatch'
    if not ident and sim<.995:return False,'nonexact_title_without_identifier'
    if p.get('doi') and wd and p['doi']!=wd:
        return False,'different_doi_version'
    return True,('matched_existing_identifier_and_title' if ident else 'exact_title_and_compatible_year')
class Run:
    def __init__(self):
        self.targets=make_manifest();self.rows={p['id']:{**p,'status':'not_queried','attempts':[],'candidates':[],'abstract':None,'reason':'pending'} for p in self.targets};self.blocked={};self.lock=threading.Lock();self.start=time.monotonic();self.key=os.getenv('OPENALEX_API_KEY');self.s2key=os.getenv('S2_API_KEY');self.last={};self.calls=0
    def save(self):
        rows=list(self.rows.values());summary={'total':len(rows),'lab':sum(x['lab']for x in rows),'status':dict(collections.Counter(x['status']for x in rows)),'successful_lab':sum(x['lab']and x['status']=='success'for x in rows),'calls':self.calls,'blocked':self.blocked,'elapsed_seconds':round(time.monotonic()-self.start,1)}
        (OUT/'api-results.json').write_text(json.dumps({'summary':summary,'results':rows},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary),flush=True)
    def candidate(self,p,w,source,path,http=None):
        a=text_abstract(w);ok,why=match(p,w);good,quality=valid(a)
        if not a:return
        c={'source':source,'path':path,'http':http,'title':w.get('title')or w.get('display_name'),'openalex':w.get('id'),'semantic_scholar':w.get('paperId'),'doi':w.get('doi')or(w.get('externalIds')or{}).get('DOI'),'abstract':a,'accepted':ok and good,'reason':why if not ok else quality if not good else why}
        self.rows[p['id']]['candidates'].append(c)
        if ok and good and self.rows[p['id']]['status']!='success':self.rows[p['id']].update(status='success',abstract=a,source=source,source_path=path,reason=why)
    def cache(self):
        ws=[];files=0
        for folder in ['api-cache','citation-cache']:
            for f in (ROOT/'work'/folder).glob('*.json'):
                try:d=json.loads(f.read_text(encoding='utf8'))
                except Exception:continue
                files+=1
                records=d if isinstance(d,list) else d.get('results',[d]) if isinstance(d,dict) else []
                for w in records:
                    if isinstance(w,dict)and(w.get('title')or w.get('display_name')):ws.append((w,str(f.relative_to(ROOT)).replace('\\','/')))
        bytitle=collections.defaultdict(list);byid=collections.defaultdict(list)
        for w,path in ws:
            bytitle[norm(w.get('title')or w.get('display_name'))].append((w,path))
            for x in [w.get('id'),w.get('paperId'),doi(w.get('doi')or(w.get('externalIds')or{}).get('DOI'))]:
                if x:byid[x].append((w,path))
        for p in self.targets:
            candidates=bytitle[norm(p['title'])][:]
            for x in [p.get('openalex'),p.get('semantic_scholar'),p.get('doi')]:candidates+=byid.get(x,[])
            seen=set()
            for w,path in candidates:
                k=(path,w.get('id'),w.get('paperId'))
                if k in seen:continue
                seen.add(k);self.candidate(p,w,'existing_cache',path)
            self.rows[p['id']]['attempts'].append({'provider':'existing_cache','status':'checked','records_matched':len(seen),'http':None})
        print(json.dumps({'cache_files':files,'work_records':len(ws),'cached_abstracts':sum(x['status']=='success'for x in self.rows.values()),'openalex_key_present':bool(self.key),'s2_key_present':bool(self.s2key)}),flush=True)
    def request(self,provider,url,body=None):
        event={'provider':provider,'path':url,'http':None}
        if provider in self.blocked:return None,{**event,'status':'not_queried','reason':self.blocked[provider]}
        if time.monotonic()-self.start>560:return None,{**event,'status':'not_queried','reason':'time_budget_exhausted'}
        headers={'Content-Type':'application/json'} if body is not None else {}
        key=self.key if provider=='OpenAlex' else self.s2key
        if key:headers['Authorization'if provider=='OpenAlex'else'x-api-key']=('Bearer 'if provider=='OpenAlex'else'')+key
        sig=hashlib.sha256((url+json.dumps(body,sort_keys=True)).encode()).hexdigest();hf=OUT/('api-headers-'+sig+'.txt')
        config='\n'.join('header = '+json.dumps(k+': '+v)for k,v in headers.items())
        args=['curl.exe','--silent','--show-error','--max-time','20','--dump-header',str(hf),'--write-out','\n%{http_code}','--config','-',url]
        if body is not None:
            bf=OUT/('api-request-'+sig+'.json');bf.write_text(json.dumps(body),encoding='utf8');args+=['--request','POST','--data-binary','@'+str(bf)]
        with self.lock:self.calls+=1
        try:
            r=subprocess.run(args,input=config.encode(),capture_output=True,timeout=24);raw,_,code=r.stdout.rpartition(b'\n');status=int(code)if code.isdigit()else 0;event['http']=status
            if r.returncode==0 and 200<=status<300:
                d=json.loads(raw);(OUT/('api-response-'+sig+'.json')).write_text(raw.decode(),encoding='utf8');return d,{**event,'status':'received','response_file':'api-response-'+sig+'.json'}
            reason='http_'+str(status)if status else 'curl_'+str(r.returncode)
            if status in (403,429):
                h=hf.read_text(encoding='utf8',errors='replace')if hf.exists()else'';retry=re.search(r'(?im)^retry-after:\s*(.+)',h);self.blocked[provider]=reason+('_retry_after_'+retry[1].strip()if retry else'')
            return None,{**event,'status':'query_failed','reason':reason}
        except Exception as e:return None,{**event,'status':'query_failed','reason':type(e).__name__}
    def process_oa(self,group):
        vals=[p['openalex'].split('/')[-1]for p in group];url='https://api.openalex.org/works?'+urllib.parse.urlencode({'filter':'openalex:'+'|'.join(vals),'per-page':100,'select':'id,title,doi,publication_year,abstract_inverted_index,ids,primary_location'})
        d,e=self.request('OpenAlex',url);ws=(d or{}).get('results',[])
        for p in group:
            row=self.rows[p['id']];row['attempts'].append(e)
            matches=[w for w in ws if w['id']==p['openalex']]
            for w in matches:self.candidate(p,w,'OpenAlex',url,e.get('http'))
            if row['status']!='success':row.update(status='no_abstract'if d else e['status'],reason='matching_record_has_no_acceptable_abstract'if matches else'no_matching_record'if d else e['reason'])
    def online(self):
        unresolved=[p for p in self.targets if self.rows[p['id']]['status']!='success']
        oa=[p for p in unresolved if p.get('openalex')]
        for i in range(0,len(oa),50):self.process_oa(oa[i:i+50])
        for p in [x for x in unresolved if not x.get('openalex')]:
            url='https://api.openalex.org/works?'+urllib.parse.urlencode({'search':p['title'],'per-page':3,'select':'id,title,doi,publication_year,abstract_inverted_index,ids,primary_location'})
            d,e=self.request('OpenAlex',url);row=self.rows[p['id']];row['attempts'].append(e)
            for w in(d or{}).get('results',[]):self.candidate(p,w,'OpenAlex',url,e.get('http'))
            if row['status']!='success':row.update(status='no_abstract'if d else e['status'],reason='no_verified_abstract_in_search'if d else e['reason'])
        self.save()
        pairs=[]
        for p in self.targets:
            if self.rows[p['id']]['status']=='success':continue
            ident=p.get('semantic_scholar')or('DOI:'+p['doi']if p.get('doi')else'ARXIV:'+p['arxiv'][0]if p['arxiv']else None)
            if ident:pairs.append((p,ident))
            else:self.rows[p['id']]['attempts'].append({'provider':'Semantic Scholar','status':'not_queried','http':None,'reason':'no_supported_identifier'})
        for i in range(0,len(pairs),50):
            group=pairs[i:i+50];url='https://api.semanticscholar.org/graph/v1/paper/batch?fields=paperId,title,abstract,year,externalIds';d,e=self.request('Semantic Scholar',url,{'ids':[x[1]for x in group]})
            for j,(p,ident)in enumerate(group):
                row=self.rows[p['id']];row['attempts'].append({**e,'identifier':ident});w=d[j]if isinstance(d,list)and j<len(d)else None
                if w:self.candidate(p,w,'Semantic Scholar',url,e.get('http'))
                if row['status']!='success'and d is not None:row.update(status='no_abstract',reason='matching_record_has_no_acceptable_abstract'if w else'no_matching_record')
                elif row['status']!='success'and d is None and row['status']!='no_abstract':row.update(status=e['status'],reason=e['reason'])
            self.save()
            if i+50<len(pairs)and'Semantic Scholar'not in self.blocked:time.sleep(1.1)
        self.save()
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--online',action='store_true');ap.add_argument('--key-file');args=ap.parse_args()
    if args.key_file:os.environ['OPENALEX_API_KEY']=Path(args.key_file).read_text(encoding='utf8').strip()
    run=Run();run.cache();run.save()
    if args.online:run.online()
