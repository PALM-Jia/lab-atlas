"""Public, bounded, resumable collection with per-item acceptance accounting.

No private submissions, manual series or full-text downloads. Semantic features use a bounded local model.
"""
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.parse
from difflib import SequenceMatcher

import collect as base

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent.parent / 'work'
KINDS = ('citation','coupling','cocitation','author','topic','institution','semantic','series')


class API:
    def __init__(self, cache):
        self.cache = cache; cache.mkdir(parents=True, exist_ok=True)
        self.events = []; self.lock = threading.Lock(); self.last = {}; self.blocked = {}
        self.cached_works={}
        for path in cache.glob('*.json'):
            try:
                data=json.loads(path.read_text(encoding='utf8'))
                ws=data.get('results',[]) if isinstance(data,dict) else []
                if isinstance(data,dict) and str(data.get('id','')).startswith('https://openalex.org/W'):ws=[data]
                for w in ws:
                    if w.get('id') and w.get('authorships') and 'referenced_works' in w:self.cached_works[w['id'].split('/')[-1]]=w
            except (ValueError,OSError,AttributeError):pass

    def request(self, url, provider='OpenAlex', body=None, text=False):
        signature = url if body is None else url+'\n'+json.dumps(body,sort_keys=True)
        path = self.cache/(hashlib.sha256(signature.encode()).hexdigest()+('.html' if text else '.json'))
        if path.exists():
            try:
                value=path.read_text(encoding='utf8')
                event={'provider':provider,'status':'success','reason':'cached','url':url,'attempts':[]}
                result=value if text else json.loads(value)
                with self.lock:self.events.append(event)
                return result,event
            except (ValueError,OSError): pass
        if provider in self.blocked and (provider!='OpenAlex' or '/works?' in url):
            event={'provider':provider,'url':url,'status':'failure','reason':self.blocked[provider]['reason'],'attempts':[], 'detail':self.blocked[provider].get('detail'),'trigger_url':self.blocked[provider]['url']}
            with self.lock:self.events.append(event)
            return None,event
        headers={}
        key=os.getenv('OPENALEX_API_KEY') if provider=='OpenAlex' else os.getenv('S2_API_KEY') if provider=='Semantic Scholar' else None
        if key: headers['Authorization' if provider=='OpenAlex' else 'x-api-key']=('Bearer ' if provider=='OpenAlex' else '')+key
        if body is not None: headers['Content-Type']='application/json'
        payload=self.cache/(hashlib.sha256(signature.encode()).hexdigest()+'.request')
        if body is not None: payload.write_text(json.dumps(body),encoding='utf8')
        event={'provider':provider,'url':url,'status':'failure','reason':'request_not_completed','attempts':[]}
        for attempt in range(3):
            with self.lock:
                interval=1.1 if provider=='Semantic Scholar' else .12
                time.sleep(max(0,interval-(time.monotonic()-self.last.get(provider,0))))
                self.last[provider]=time.monotonic()
            timeout=45 if provider=='Semantic Scholar' else 18
            args=['curl.exe' if os.name=='nt' else 'curl','--silent','--show-error','--max-time',str(timeout),'--write-out','\n%{http_code}','--config','-',url]
            if body is not None: args+=['--request','POST','--data-binary','@'+str(payload)]
            config='\n'.join('header = '+json.dumps(k+': '+v) for k,v in headers.items())
            try:
                r=subprocess.run(args,input=config.encode(),capture_output=True,timeout=timeout+5)
                raw,_,code=r.stdout.rpartition(b'\n'); status=int(code) if code.isdigit() else 0
                reason=f'curl_{r.returncode}' if r.returncode else f'http_{status}'
                event['attempts'].append({'http':status,'curl':r.returncode})
                if r.returncode==0 and 200<=status<300:
                    value=raw.decode('utf8')
                    result=value if text else json.loads(value)
                    path.write_text(value,encoding='utf8')
                    event.update(status='success',reason='received')
                    with self.lock: self.events.append(event)
                    return result,event
                event['reason']=reason
                event['detail']=r.stderr.decode(errors='replace')[:180] if not status else raw.decode(errors='replace')[:180]
                if status==429 and 'Insufficient budget' in raw.decode(errors='replace'):
                    event['reason']='anonymous_daily_budget_exhausted';event['detail']=json.loads(raw)
                    with self.lock:self.blocked[provider]=dict(event)
                    break
                if r.returncode==0 and status not in (0,408,429,500,502,503,504): break
            except (subprocess.TimeoutExpired,ValueError,UnicodeError) as e:
                event['attempts'].append({'error':type(e).__name__})
                event['reason']=type(e).__name__
            if attempt<2: time.sleep(2**(attempt+1))
        with self.lock: self.events.append(event)
        return None,event

    def works(self, **params):
        return self.request('https://api.openalex.org/works?'+urllib.parse.urlencode(params))


class Ledger:
    def __init__(self): self.rows=collections.defaultdict(list)
    def add(self,step,p,ok,reason,**detail):
        self.rows[step].append({'id':p['id'],'title':p.get('title',p['id']),'status':'success' if ok else 'failure','reason':reason,**detail})
    def report(self):
        result={}
        for step,rows in self.rows.items():
            assert len({r['id'] for r in rows})==len(rows),step+' duplicate accounting'
            assert all(r['reason'] and r['status'] in ('success','failure') for r in rows)
            good=sum(r['status']=='success' for r in rows); total=len(rows)
            result[step]={'total':total,'success':good,'explained_failure':total-good,
                          'success_rate':round(100*good/total,4) if total else 0,
                          'failure_rate':round(100*(total-good)/total,4) if total else 0,
                          'accounted_rate':100 if total else 0,'unexplained':0,
                          'reasons':dict(collections.Counter(r['reason'] for r in rows)), 'items':rows}
        return result
    def checkpoint(self):
        (WORK/'pipeline-progress.json').write_text(json.dumps(self.report(),ensure_ascii=False,indent=2),encoding='utf8')


def chunks(items,n):
    return [items[i:i+n] for i in range(0,len(items),n)]


def identifiers(urls):
    result=[]
    for url in urls:
        match=re.search(r'(10\.\d{4,9}/[^?#\s]+)',urllib.parse.unquote(url),re.I)
        if match: result.append(('doi',match.group(1).rstrip('/.')))
        match=re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?',url)
        if match: result.append(('arxiv',match.group(1)))
    return list(dict.fromkeys(result))


def enrich(w):
    p=base.from_openalex(w)
    p['author_records']=[{'id':a['author'].get('id'),'name':a['author']['display_name']} for a in w.get('authorships',[])]
    p['institution_records']=list({i['id']:{'id':i['id'],'name':i['display_name']} for a in w.get('authorships',[]) for i in a.get('institutions',[]) if i.get('id')}.values())
    p['metadata_sources']={'authors':'OpenAlex','abstract':'OpenAlex' if p.get('abstract') else None,'references':'OpenAlex','year':'OpenAlex','institutions':'OpenAlex'}
    p['referenced_works_count']=w.get('referenced_works_count')
    return p


def public_metadata(p,api):
    for url in p.get('links',[]):
        if 'openreview.net/' in url:
            note=urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('id',[None])[0]
            if not note: continue
            data,event=api.request('https://api2.openreview.net/notes?'+urllib.parse.urlencode({'id':note}),'OpenReview')
            if not data: continue
            for record in data.get('notes',[]):
                def value(k):
                    v=record.get('content',{}).get(k)
                    return v.get('value') if isinstance(v,dict) else v
                if SequenceMatcher(None,base.norm(value('title')or''),base.norm(p['title'])).ratio()<.93: continue
                for field in ('abstract','authors'):
                    val=value(field)
                    if val and (field!='authors' or not any('anonymous' in str(v).lower() for v in val)) and not p.get(field):
                        p[field]=val;p.setdefault('metadata_sources',{})[field]='OpenReview public note '+note
                p['public_metadata_note']=note
        elif 'arxiv.org/' in url and not p.get('abstract'):
            found=identifiers([url]); aid=next((v for k,v in found if k=='arxiv'),None)
            if not aid: continue
            html,event=api.request('https://arxiv.org/abs/'+aid,'arXiv',text=True)
            if html:
                soup=base.BeautifulSoup(html,'html.parser')
                title=soup.find('meta',attrs={'name':'citation_title'})
                if not title or SequenceMatcher(None,base.norm(title.get('content','')),base.norm(p['title'])).ratio()<.93: continue
                abstract=soup.select_one('blockquote.abstract')
                if abstract: p['abstract']=re.sub(r'^Abstract:\s*','',abstract.get_text(' ',strip=True));p.setdefault('metadata_sources',{})['abstract']='arXiv '+aid
                names=[v.get('content') for v in soup.find_all('meta',attrs={'name':'citation_author'})]
                if names and not p.get('authors'):p['authors']=names;p.setdefault('metadata_sources',{})['authors']='arXiv '+aid
    return p


def resolve(p,api):
    p=dict(p);p['metadata_sources']={'authors':'实验室列表' if p['authors'] else None,'year':'实验室列表' if p['year'] else None}
    direct=[];errors=[]
    discovery_path=ROOT/'identity-discoveries.json'
    discovery=json.loads(discovery_path.read_text(encoding='utf8')).get(p['id']) if discovery_path.exists() else None
    if discovery:
        w,event=api.request('https://api.openalex.org/works/'+discovery['openalex'].split('/')[-1])
        if w and w.get('id'):direct.append(w)
        else:errors.append(event)
    for kind,value in identifiers(p.get('links',[])):
        doi=value if kind=='doi' else '10.48550/arxiv.'+value
        w,event=api.request('https://api.openalex.org/works/'+urllib.parse.quote('https://doi.org/'+doi,safe=''))
        if w and w.get('id'):direct.append(w)
        elif event['reason']!='http_404':errors.append(event)
    result,event=api.works(search=p['title'],per_page=3)
    if not result:errors.append(event)
    pool={w['id']:w for w in direct+((result or {}).get('results',[]))}
    def qualified(w):
        score=SequenceMatcher(None,base.norm(p['title']),base.norm(w.get('title')or'')).ratio()
        version_title_verified=bool(discovery and w['id']==discovery['openalex'] and base.norm(w.get('title')or'') in {base.norm(t) for t in discovery.get('verified_titles',[])})
        names={base.norm(a['author']['display_name']) for a in w.get('authorships',[])}
        overlap=names&{base.norm(a) for a in p['authors']}
        return (score>=.93 or version_title_verified) and ('yuhengjia' in names or bool(overlap) or w['id'] in {v['id']for v in direct})
    candidates=[w for w in pool.values() if qualified(w)]
    if not candidates and result:
        more,event=api.works(search=p['title'],per_page=10)
        if more:
            pool.update({w['id']:w for w in more.get('results',[])});candidates=[w for w in pool.values() if qualified(w)]
        else:errors.append(event)
    selected=None;method=None
    exact_direct=[w for w in direct if qualified(w)]
    if len(exact_direct)==1:selected=exact_direct[0];method='source_identifier'
    if not selected:
        exact_links=[]
        for w in candidates:
            links={v for l in w.get('locations',[]) for v in (l.get('landing_page_url'),l.get('pdf_url')) if v}
            if links&set(p.get('links',[])):exact_links.append(w)
        if len(exact_links)==1:selected=exact_links[0];method='source_url'
    if not selected and len(candidates)==1:selected=candidates[0];method='title_author_unique'
    if not selected and len(candidates)>1:
        formal=[w for w in candidates if w.get('type') in ('article','conference-paper')]
        # Prefer the unique qualified formal publication; preserve other candidates as versions.
        if len(formal)==1:selected=formal[0];method='formal_publication_preferred'
    formal=[w for w in candidates if w.get('type') in ('article','conference-paper')]
    if len(formal)==1 and selected is not formal[0]:selected=formal[0];method='formal_publication_preferred'
    identity_collision=False
    if selected and base.norm(selected.get('title')or'')!=base.norm(p['title']):
        listed=json.loads((ROOT/'lab-papers.json').read_text(encoding='utf8'))
        identity_collision=any(v['id']!=p['id'] and base.norm(v['title'])==base.norm(selected.get('title')or'') for v in listed)
        if identity_collision:selected=None;method=None
    info=[{'id':w['id'],'title':w.get('title'),'doi':w.get('doi'),'type':w.get('type'),'year':w.get('publication_year')}for w in candidates]
    if selected:
        q=enrich(selected);q.update(id=p['id'],lab=True,title=p['title'],source_url=p['source_url'],list_title=p['title'],list_year=p['year'],list_authors=p['authors'],featured=p['featured'],list_venue=p.get('venue'),match_status='matched',match_method=method,match_score=round(SequenceMatcher(None,base.norm(p['title']),base.norm(selected.get('title')or'')).ratio(),3),versions=info)
        q['links']=list(dict.fromkeys(p.get('links',[])+q['links']))
        if not q.get('authors') and p.get('authors'):q['authors']=p['authors'];q['metadata_sources']['authors']='实验室列表'
        if discovery:q['identity_search_evidence']=discovery.get('evidence');q['match_method']='broader_public_search' if method=='source_identifier' else method
        return q
    p['candidates']=info or [{'id':w['id'],'title':w.get('title')}for w in pool.values()]
    p['match_status']='ambiguous' if candidates else 'not_matched' if result else 'api_error'
    p['match_reason']='multiple_qualified_records_without_identity_evidence' if candidates else 'no_title_author_or_identifier_verified_candidate' if result else 'title_query_failed_after_retries'
    if identity_collision:p['match_reason']='title_variant_collides_with_another_lab_paper'
    p['match_errors']=errors
    audit_path=ROOT/'identity-search-audit.json'
    if audit_path.exists():
        audit=next((r for r in json.loads(audit_path.read_text(encoding='utf8')) if r['id']==p['id']),None)
        if audit:p['match_reason']=audit['reason'];p['identity_search_evidence']=audit
    metadata_path=ROOT/'public-paper-metadata.json'
    if metadata_path.exists():
        extra=json.loads(metadata_path.read_text(encoding='utf8')).get(p['id'],{})
        p['links']=list(dict.fromkeys(p.get('links',[])+extra.get('links',[])))
        for field in ('authors','abstract','year'):
            if not p.get(field) and extra.get(field):p[field]=extra[field];p['metadata_sources'][field]=extra['source']
    return public_metadata(p,api)


def neighborhood(p,api):
    if not p.get('openalex'):return p,[],None,'no_verified_database_id'
    incoming=[];cursor='*';complete=False;total=None;event=None
    for page in range(3):
        data,event=api.works(filter='cites:'+p['openalex'].split('/')[-1],per_page=200,cursor=cursor,sort='publication_date:desc')
        if not data:break
        total=data.get('meta',{}).get('count');incoming+=data.get('results',[])
        cursor=data.get('meta',{}).get('next_cursor')
        if not cursor or len(incoming)>=(total or 0):complete=True;break
    if not incoming and not complete:
        # Reuse the earlier pilot query, but keep its truncation/failure provenance explicit.
        old,old_event=api.works(filter='cites:'+p['openalex'].split('/')[-1],per_page=25,sort='cited_by_count:desc')
        if old:
            incoming=old.get('results',[]);total=old.get('meta',{}).get('count');complete=total is not None and len(incoming)>=total
            p['citing_fallback']='pilot_cached_25_high_cited'
    p['citing_collected']=len({w['id']for w in incoming});p['citing_total']=total
    p['citing_status']='database_observed' if complete else 'sampled' if incoming else 'api_error'
    p['citing_complete']=complete
    reason='complete_database_neighborhood' if complete else 'pilot_cache_partial_after_'+(event or {}).get('reason','no_response') if p.get('citing_fallback') else 'incoming_limit_600' if incoming and page==2 and data else 'incoming_request_failed_'+(event or {}).get('reason','no_response')
    return p,incoming,complete,reason


def api_embeddings(nodes,api,ledger):
    queries=[]
    for p in nodes:
        doi=p.get('doi')
        ids=identifiers(p.get('links',[]))
        identifier='DOI:'+doi.replace('https://doi.org/','') if doi else next(('ARXIV:'+v if k=='arxiv' else 'DOI:'+v for k,v in ids),None)
        if identifier:queries.append((p,identifier))
        else:ledger.add('08_content_vector',p,False,'no_supported_public_identifier')
    fields='paperId,title,authors,abstract,year,externalIds,embedding.specter_v2'
    identifier_cache={}
    for cached in api.cache.glob('*.request'):
        try:
            ids=json.loads(cached.read_text(encoding='utf8')).get('ids',[])
            records=json.loads(cached.with_suffix('.json').read_text(encoding='utf8'))
            if isinstance(records,list) and len(ids)==len(records):identifier_cache.update(zip((i.lower() for i in ids),records))
        except (ValueError,OSError,AttributeError):pass
    for index,batch in enumerate(chunks(queries,100)):
        if all(i.lower() in identifier_cache for p,i in batch):
            data=[identifier_cache[i.lower()] for p,i in batch]
            event={'provider':'Semantic Scholar','status':'success','reason':'cached','url':'https://api.semanticscholar.org/graph/v1/paper/batch?fields='+fields,'attempts':[]}
            api.events.append(event)
        else:data,event=api.request('https://api.semanticscholar.org/graph/v1/paper/batch?fields='+fields,'Semantic Scholar',{'ids':[i for p,i in batch]})
        # A blocked batch is an observed failure for every submitted identifier.
        if not isinstance(data,list) or len(data)!=len(batch):
            for p,i in batch:ledger.add('08_content_vector',p,False,'batch_'+event['reason'],identifier=i,url=event['url'])
        else:
            for (p,i),r in zip(batch,data):
                if not r:ledger.add('08_content_vector',p,False,'semantic_scholar_no_record',identifier=i);continue
                verified_titles=[p['title']]+[v['title'] for v in p.get('versions',[]) if v['id']==p.get('openalex')]
                same=max(SequenceMatcher(None,base.norm(t),base.norm(r.get('title')or'')).ratio() for t in verified_titles)>=.9
                vector=(r.get('embedding')or{}).get('vector')
                good=same and isinstance(vector,list) and len(vector)==768 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in vector) and sum(v*v for v in vector)>0
                if good:
                    p['embedding']=vector;p['semantic_source']='Semantic Scholar SPECTER2';p['semantic_paper_id']=r['paperId']
                ledger.add('08_content_vector',p,good,'specter2_vector_verified' if good else 'title_identity_mismatch' if not same else 'vector_missing_or_invalid',identifier=i)
                if same:
                    if not p.get('abstract') and r.get('abstract'):p['abstract']=r['abstract'];p.setdefault('metadata_sources',{})['abstract']='Semantic Scholar '+r['paperId']
                    if not p.get('authors') and r.get('authors'):p['authors']=[a['name']for a in r['authors']];p.setdefault('metadata_sources',{})['authors']='Semantic Scholar '+r['paperId']
        print(f'Vectors batch {index+1}/{len(chunks(queries,100))}',flush=True);ledger.checkpoint()


def embeddings(nodes,api,ledger):
    from semantic_features import generate_embeddings
    rows,meta=generate_embeddings(nodes)
    for row in rows:
        detail={k:v for k,v in row.items() if k not in ('id','title','status','reason')}
        ledger.add('08_content_vector',row,row['status']=='success',row['reason'],**detail)
    ledger.checkpoint()
    return meta


def graph(nodes,citing_sets):
    import numpy as np
    ids={p['id']:p for p in nodes};by_oa={p['openalex'].split('/')[-1]:p['id']for p in nodes if p.get('openalex')}
    edges=[];references={p['id']:set(p['references'])for p in nodes}
    def add(a,b,kind,score,evidence,tentative=False):
        edges.append({'id':f'{kind}:{a}:{b}','source':a,'target':b,'kind':kind,'score':round(float(score),4),'evidence':evidence,'tentative':tentative})
    for p in nodes:
        p['tags']=base.tags_for(p);p['tag_source']='标题与摘要规则推断' if p.get('abstract')else'仅标题规则推断'
        for ref in references[p['id']]:
            if ref in by_oa and by_oa[ref]!=p['id'] and (p['lab'] or ids[by_oa[ref]]['lab']):add(p['id'],by_oa[ref],'citation',1,{'source':'OpenAlex','text':'数据库记录的直接引用','referenced_id':ref})
    lab=[p for p in nodes if p['lab']]
    for a in lab:
        ra=references[a['id']];ca=citing_sets.get(a['id'],set())
        for b in nodes:
            if a['id']==b['id'] or (b['lab'] and a['id']>b['id']):continue
            rb=references[b['id']];shared=ra&rb
            if len(shared)>=2:
                score=len(shared)/math.sqrt(len(ra)*len(rb))
                if score>=.06:add(a['id'],b['id'],'coupling',score,{'count':len(shared),'ids':sorted(shared),'text':'共同参考文献；余弦归一化'})
            ta={t['id']:t['display_name']for t in a.get('api_topics',[])};tb={t['id']:t['display_name']for t in b.get('api_topics',[])};st=ta.keys()&tb.keys()
            if st:add(a['id'],b['id'],'topic',len(st)/len(ta.keys()|tb.keys()),{'topic_ids':sorted(st),'topic_names':[ta[t]for t in sorted(st)],'text':'共享 OpenAlex 自动分类主题；候选关联'},True)
            if b['lab']:
                cb=citing_sets.get(b['id'],set());sc=ca&cb
                if sc:add(a['id'],b['id'],'cocitation',len(sc)/math.sqrt(len(ca)*len(cb)),{'count':len(sc),'ids':sorted(sc),'complete':bool(a.get('citing_complete')and b.get('citing_complete')),'text':'采集的外部论文同时引用这两篇论文；完整度见条目记录'})
                aa={r['id']:r['name']for r in a.get('author_records',[])if r.get('id')and base.norm(r['name'])!='yuhengjia'};ba={r['id']:r['name']for r in b.get('author_records',[])if r.get('id')and base.norm(r['name'])!='yuhengjia'}
                sa=aa.keys()&ba.keys()
                if sa:add(a['id'],b['id'],'author',len(sa),{'author_ids':sorted(sa),'authors':[aa[k]for k in sorted(sa)],'text':'OpenAlex 作者身份 ID 相同；默认排除 Yuheng Jia'})
                elif not a.get('author_records')or not b.get('author_records'):
                    an={base.norm(n):n for n in a['authors']if base.norm(n)!='yuhengjia'};bn={base.norm(n)for n in b['authors']};sn=an.keys()&bn
                    if sn:add(a['id'],b['id'],'author',len(sn),{'authors':[an[k]for k in sorted(sn)],'text':'原始署名姓名相同，作者身份尚未确认'},True)
                overlap=set(a['tags'])&set(b['tags'])-{'other'}
                if overlap and not st:add(a['id'],b['id'],'topic',len(overlap)/len(set(a['tags'])|set(b['tags'])),{'tags':sorted(overlap),'text':'关键词规则推断的共享主题'},True)
                ai={r['id']:r['name']for r in a.get('institution_records',[])};bi={r['id']:r['name']for r in b.get('institution_records',[])};si=ai.keys()&bi.keys()
                if si:add(a['id'],b['id'],'institution',len(si),{'institution_ids':sorted(si),'institutions':[ai[k]for k in sorted(si)],'text':'OpenAlex 发表署名机构 ID 相同'})
    from semantic_features import semantic_edges
    edges.extend(semantic_edges(nodes))
    retained=edges
    # Force-directed coordinates reflect the citation/coupling graph, not title buckets.
    # Bounded iterations and repulsion samples avoid an expensive whole-corpus layout.
    n=len(nodes);index={p['id']:i for i,p in enumerate(nodes)};rng=np.random.default_rng(17)
    pos=rng.normal(0,220,(n,2)).astype(np.float32)
    for i,p in enumerate(nodes):
        t=next(k for k,t in enumerate(base.TOPICS)if t[0]==p['tags'][0]);angle=2*math.pi*t/len(base.TOPICS)
        pos[i]+=np.array([320*math.cos(angle),250*math.sin(angle)],dtype=np.float32)
    layout_edges=[e for e in retained if e['kind']in ('coupling','citation')]
    src=np.array([index[e['source']]for e in layout_edges],dtype=int);dst=np.array([index[e['target']]for e in layout_edges],dtype=int)
    for iteration in range(180):
        forces=np.zeros((n,2),dtype=np.float32)
        if len(src):
            delta=pos[dst]-pos[src];dist=np.maximum(np.linalg.norm(delta,axis=1),1);f=delta*((dist-65)/dist*.012)[:,None]
            np.add.at(forces,src,f);np.add.at(forces,dst,-f)
        for _ in range(12):
            other=rng.integers(0,n,n);delta=pos-pos[other];dist=np.maximum(np.sum(delta*delta,axis=1),25)
            forces+=delta*(700/dist)[:,None]
        forces-=pos*.0008
        pos+=np.clip(forces,-10,10)*(1-iteration/220)
    for i,p in enumerate(nodes):p['x']=round(float(pos[i,0]),2);p['y']=round(float(pos[i,1]),2)
    return retained,edges


def run():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--cache',default=str(WORK/'api-cache'));parser.add_argument('--max-external',type=int,default=1600)
    args=parser.parse_args();WORK.mkdir(exist_ok=True);api=API(Path(args.cache));ledger=Ledger()
    source=(ROOT/'source-papers.html').read_text(encoding='utf8');lab=base.parse_source(source)
    for p in lab:ledger.add('01_import',p,True,'unique_source_item_preserved')
    print('Step 1 imported',len(lab),flush=True);ledger.checkpoint()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:lab=list(pool.map(lambda p:resolve(p,api),lab))
    for p in lab:ledger.add('02_match',p,p['match_status']=='matched',p.get('match_method')or p['match_reason'],candidates=p.get('candidates',[]),versions=p.get('versions',[]),errors=p.get('match_errors',[]))
    print('Step 2 matched',sum(p['match_status']=='matched'for p in lab),flush=True);ledger.checkpoint()
    all_incoming={};citing_sets={};lab_ids={p['openalex'].split('/')[-1]for p in lab if p.get('openalex')};external_scores=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for p,ws,ok,reason in pool.map(lambda p:neighborhood(p,api),lab):
            ledger.add('05_incoming_neighborhood',p,ok is True,reason,collected=p.get('citing_collected',0),total=p.get('citing_total'))
            citing_sets[p['id']]={w['id'].split('/')[-1]for w in ws}
            for w in ws:all_incoming[w['id'].split('/')[-1]]=w;external_scores[w['id'].split('/')[-1]]+=1
            for r in p['references']:external_scores[r]+=1
    print('Step 5 incoming records',len(all_incoming),flush=True);ledger.checkpoint()
    # Every known reference ID is retained for relation computation; rendered node budget is explicit.
    selected=[i for i,count in sorted(external_scores.items(),key=lambda v:(-v[1],v[0]))if i not in lab_ids][:args.max_external]
    metadata={i:all_incoming[i]for i in selected if i in all_incoming}
    metadata.update({i:api.cached_works[i] for i in selected if i not in metadata and i in api.cached_works})
    missing=[i for i in selected if i not in metadata]
    def get_records(batch):return batch,api.works(filter='openalex_id:'+'|'.join(batch),per_page=100)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for batch,(data,event)in pool.map(get_records,chunks(missing,100)):
            found={w['id'].split('/')[-1]:w for w in(data or{}).get('results',[])};metadata.update(found)
            for i in batch:ledger.add('05_external_metadata',{'id':i},i in found,'openalex_record_received'if i in found else'lookup_'+event['reason']if data is None else'openalex_id_not_returned')
    for i in selected:
        if i in all_incoming:ledger.add('05_external_metadata',{'id':i},True,'incoming_record_reused')
        elif i in metadata and i in api.cached_works:ledger.add('05_external_metadata',{'id':i},True,'public_api_cache_record_reused')
    nodes=lab+[enrich(metadata[i])for i in selected if i in metadata]
    print('Step 5 graph nodes',len(nodes),flush=True);ledger.checkpoint()
    embeddings(nodes,api,ledger)
    for field in ('authors','year','abstract','references','institution_records'):
        for p in lab:
            ok=bool(p.get(field));reason='public_field_available'if ok else'no_verified_database_id'if field in ('references','institution_records')and not p.get('openalex')else'database_returned_empty'if p.get('openalex')else'public_sources_did_not_supply_field'
            ledger.add('04_'+field,p,ok,reason,source=p.get('metadata_sources',{}).get('institutions'if field=='institution_records'else field))
    for p in lab:ledger.add('09_research_series',p,False,'manual_series_not_provided_by_user')
    ledger.checkpoint();edges,full_edges=graph(nodes,citing_sets)
    for p in nodes:ledger.add('10_layout',p,math.isfinite(p['x'])and math.isfinite(p['y']),'finite_force_layout_coordinates')
    # Relation readiness has a fixed denominator: all lab items, not only successful matches.
    for kind in KINDS:
        for p in lab:
            ready={'citation':bool(p.get('openalex')),'coupling':bool(p['references']),'cocitation':bool(p.get('citing_complete')),'author':bool(p.get('author_records')),'topic':bool(p.get('api_topics')),'institution':bool(p.get('institution_records')),'semantic':bool(p.get('embedding')),'series':False}[kind]
            vector_row=next((r for r in ledger.rows['08_content_vector']if r['id']==p['id']),None)
            neighbor_row=next((r for r in ledger.rows['05_incoming_neighborhood']if r['id']==p['id']),None)
            reason='relation_input_ready'if ready else'manual_series_not_provided_by_user'if kind=='series'else vector_row['reason']if kind=='semantic'else neighbor_row['reason']if kind=='cocitation'else'only_name_evidence_available'if kind=='author'and p['authors']else'only_keyword_topic_available'if kind=='topic'else'no_verified_database_id'if not p.get('openalex')else'database_returned_empty_relation_field'
            ledger.add('07_readiness_'+kind,p,ready,reason)
    for i,event in enumerate(api.events):
        ledger.add('03_api_requests',{'id':'request-'+str(i),'title':event['url']},event['status']=='success',event['reason'],provider=event['provider'],attempts=event.get('attempts',[]),detail=event.get('detail'),trigger_url=event.get('trigger_url'))
    stats={'lab':len(lab),'external':len(nodes)-len(lab),'matched':sum(p['match_status']=='matched'for p in lab),'abstracts':sum(bool(p.get('abstract'))for p in lab),'title_only':sum(not p['authors']and not p.get('abstract')for p in lab),'neighborhood_seeds':sum(bool(p.get('openalex'))for p in lab),'requests':sum(len(e['attempts'])for e in api.events),'edges':{k:sum(e['kind']==k for e in edges)for k in KINDS},'full_edges':{k:sum(e['kind']==k for e in full_edges)for k in KINDS},'vectors':sum(bool(p.get('embedding'))for p in nodes)}
    for p in nodes:
        p['semantic_status']='available'if p.get('embedding')else'not_available';p.pop('embedding',None)
    meta={'updated':dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec='seconds'),'source':base.SOURCE_URL,'stats':stats,'limits':{'neighborhood_seeds':stats['neighborhood_seeds'],'citing_per_seed':600,'reference_nodes_per_seed':'all known reference IDs used','external_nodes':args.max_external},'layout':'citation_and_coupling_force_layout','notes':['所有已匹配实验室论文均尝试采集一跳引用邻域；逐条记录完整度与失败。','引用清单每篇最多 600 条；展示外部节点最多 '+str(args.max_external)+' 篇，按跨实验室论文出现频次选取。','数据库主题、关键词主题及内容相似均为候选关联。','初始坐标由引用与共同参考文献计算；动态排布按当前关系与连接强度调整。','未提供人工系列标注，该关系层明确不可用。']}
    meta['semantic']=semantic_meta
    data={'meta':meta,'topics':[{'id':t[0],'name':t[1],'color':t[2]}for t in base.TOPICS],'nodes':nodes,'edges':edges}
    (ROOT/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (ROOT/'data.js').write_text('window.ATLAS_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    (ROOT/'relations-full.json').write_text(json.dumps(full_edges,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    report={'meta':meta,'errors':[e for e in api.events if e['status']=='failure'],'unmatched':[{'id':p['id'],'title':p['title'],'status':p['match_status'],'reason':p.get('match_reason'),'candidates':p.get('candidates',[])}for p in lab if p['match_status']!='matched']}
    (ROOT/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    from failure_details import enrich_report
    acceptance=enrich_report({'meta':meta,'steps':ledger.report(),'requests':api.events},data,WORK)
    from failure_assessment import assess_failures
    acceptance=assess_failures(acceptance,data,WORK)
    (ROOT/'acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2),encoding='utf8')
    (WORK/'citing-sets.json').write_text(json.dumps({k:sorted(v)for k,v in citing_sets.items()}),encoding='utf8')
    print('Complete',json.dumps(stats,ensure_ascii=False),flush=True)
    # Reapply the closed annotation snapshot after collection so the atlas never
    # silently returns to the retired six-direction or database-keyword scheme.
    if (WORK/'keyword-full/control/closure.json').exists():
        import runpy
        runpy.run_path(str(WORK/'apply-reviewed-keywords.py'),run_name='__main__')


if __name__=='__main__':run()
