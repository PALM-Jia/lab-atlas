"""Bounded public API collector. Secrets are read only from environment variables.
Run: python collect.py --cache ../../work/api-cache --source ../../work/papers-source.html
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCE_URL = 'https://jyh-learning.github.io/papers.html'
TOPICS = [
    ('clustering', '聚类与表示学习', '#6877ce', r'cluster|matrix factorization|subspace|representation learning'),
    ('labels', '弱监督与标签学习', '#d99850', r'partial label|multi.label|label distribution|label enhancement|complementary label|label proportions'),
    ('foundation', '大模型与多模态', '#54a3a0', r'large language|large model|foundation|vision.language|multimodal|lora|llm|lvlm|zero.shot|open.vocabulary'),
    ('trust', '鲁棒与可信学习', '#bd6c8c', r'robust|uncertainty|hallucination|calibrat|adversarial|trustworthy|noisy'),
    ('hsi', '高光谱与遥感', '#839c56', r'hyperspectral|hyerspectral|\bhsi\b|remote sensing'),
    ('traffic', '交通与数据恢复', '#679aba', r'traffic|freeway|tensor completion|data recovery|imputation'),
    ('other', '其他方向', '#969aa4', r'$^'),
]

def norm(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).lower())

def clean(text):
    return re.sub(r'\s+', ' ', text).strip(' ,.;\n')

def author_names(text):
    text = re.sub(r'^\[[^]]+\]\s*', '', text)
    text = re.sub(r'\band\s+', '', text)
    names = [clean(v).title() for v in text.split(',') if clean(v)]
    # Only correct the unambiguous case variant; retain other source spelling.
    return list(dict.fromkeys(names))

def parse_source(source):
    soup = BeautifulSoup(source, 'html.parser')
    papers = {}
    for p in soup.select('#layout-content p'):
        heading = p.find_previous('h2')
        if not heading:
            continue
        section = clean(heading.get_text(' ', strip=True))
        # Malformed source HTML nests li/p elements: keep only this paragraph's text.
        text = clean(' '.join(str(s) for s in p.strings if s.find_parent('p') is p))
        if len(text) < 12:
            continue
        anchors = [a for a in p.find_all('a') if a.find_parent('p') is p]
        title_links = [a for a in anchors if clean(a.get_text(' ', strip=True)).lower() not in ('code', 'pdf')]
        urls = []
        authors = []
        venue = re.match(r'^\[([^]]+)\]', text)
        venue = venue.group(1) if venue else None
        if section == 'Preprint':
            title = text
        elif title_links:
            title = clean(title_links[0].get_text(' ', strip=True))
            title_at = text.find(title)
            if title_at < 0:
                # Normalize each text fragment before searching.
                text = clean(p.get_text(' ', strip=True).split('[TCSVT]')[0]) if not venue else text
            authors = author_names(text[:title_at]) if title_at >= 0 else []
            urls = [a.get('href') for a in title_links if a.get('href')]
        elif venue:
            body = re.sub(r'^\[[^]]+\]\s*', '', text)
            parts = body.split(',')
            start = next((i for i, v in enumerate(parts) if len(v.split()) > 5 or ':' in v or re.search(r'\b(Towards|Learning|Discovering|Generalization|Individuals|Samples|Attention|Exploiting|Mismatch|Progressive|Beyond|Reliable|Comprehensive|Question|Fragmented|Unsupervised|Robust|On the|Mini-cluster|Partial Label)\b', v)), None)
            if start is None:
                raise ValueError('Cannot split paper: ' + text)
            authors = author_names(','.join(parts[:start]))
            remainder = ','.join(parts[start:])
            # One source byline has no comma before the title.
            if 'Yuheng Jia Towards Better' in remainder:
                authors = author_names(','.join(parts[:start]) + ',' + remainder.split('Towards Better')[0])
                remainder = 'Towards Better' + remainder.split('Towards Better', 1)[1]
            title = re.split(r',\s*(?:IEEE|EEE |International|The |Thirty|Twenty|Forty|34th|Pattern Recognition|Briefings|Journal of|Conference on|Empirical Methods|ACM |AAAI |Transportation Research|Intelligent Systems|Genetic and|Information Sciences|20\d{2})', remainder, maxsplit=1)[0]
            title = clean(title)
        else:
            continue
        if len(title) < 8:
            continue
        if len(title) % 2 == 1 and title[:len(title)//2] == title[len(title)//2+1:]:
            title = title[:len(title)//2]
        key = norm(title)
        year_tokens = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
        year = int(year_tokens[0]) if year_tokens else None
        record = {'id': 'lab-' + hashlib.sha1(key.encode()).hexdigest()[:12], 'title': title,
                  'lab': True, 'authors': authors, 'year': year, 'venue': venue,
                  'publication_status': '预印本' if section == 'Preprint' else '列表标注的发表条目',
                  'source_url': SOURCE_URL, 'links': urls, 'raw': text,
                  'match_status': 'not_checked', 'source': '实验室列表', 'references': [],
                  'citations': None, 'abstract': None, 'api_topics': [], 'author_ids': [],
                  'reference_status': 'unknown', 'citing_status': 'not_collected'}
        if key in papers:
            prev = papers[key]
            prev['links'] = list(dict.fromkeys(prev['links'] + urls))
            prev['year'] = prev['year'] or year
            prev['featured'] = True
        else:
            record['featured'] = 'personally' in section
            papers[key] = record
    return list(papers.values())

class API:
    def __init__(self, cache):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.errors = []
        self.requests = 0
        self.cache_only = False

    def get(self, url, provider='OpenAlex'):
        cache_file = self.cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding='utf8'))
        if self.cache_only:
            return None
        key = os.getenv('OPENALEX_API_KEY') if provider == 'OpenAlex' else os.getenv('S2_API_KEY')
        headers = {}
        if key:
            headers['Authorization' if provider == 'OpenAlex' else 'x-api-key'] = ('Bearer ' if provider == 'OpenAlex' else '') + key
        for attempt in range(2):
            try:
                self.requests += 1
                # curl is the native HTTPS client in this Windows workspace.
                # Feed headers over stdin: API keys never appear in process arguments.
                config = '\n'.join('header = '+json.dumps(k+': '+v) for k,v in headers.items())
                response = subprocess.run(['curl.exe' if os.name=='nt' else 'curl','--silent','--show-error',
                                           '--fail-with-body','--max-time','20','--config','-',url],
                                          input=config.encode(),capture_output=True,timeout=24)
                if response.returncode:
                    if response.returncode == 22:
                        try:
                            message = json.loads(response.stdout).get('message', 'HTTP error')
                        except (ValueError,AttributeError):
                            message = 'HTTP request rejected'
                    else:
                        message = response.stderr.decode(errors='replace')[:120]
                    raise OSError(message)
                result = json.loads(response.stdout)
                cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding='utf8')
                return result
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if isinstance(e, urllib.error.HTTPError) and e.code == 429 and attempt == 0:
                    time.sleep(3)
                    continue
                self.errors.append({'provider': provider, 'url': url, 'error': str(e)[:180]})
                return None

    def works(self, **params):
        return self.get('https://api.openalex.org/works?' + urllib.parse.urlencode(params))

def abstract_from(index):
    if not index:
        return None
    words = {pos: word for word, positions in index.items() for pos in positions}
    return ' '.join(words[p] for p in sorted(words))

def from_openalex(w):
    return {'id': w['id'].rsplit('/', 1)[-1], 'title': w.get('title') or '(Untitled)', 'lab': False,
            'year': w.get('publication_year'), 'venue': ((w.get('primary_location') or {}).get('source') or {}).get('display_name'),
            'authors': [a['author']['display_name'] for a in w.get('authorships', [])],
            'author_ids': [a['author']['id'] for a in w.get('authorships', []) if a['author'].get('id')],
            'institutions': list({i['display_name'] for a in w.get('authorships', []) for i in a.get('institutions', [])}),
            'doi': w.get('doi'), 'openalex': w['id'], 'links': [w.get('doi') or w['id']],
            'abstract': abstract_from(w.get('abstract_inverted_index')), 'citations': w.get('cited_by_count'),
            'references': [v.rsplit('/', 1)[-1] for v in w.get('referenced_works', [])],
            'reference_status': 'database_observed', 'citing_status': 'not_collected',
            'api_topics': w.get('topics', []), 'source': 'OpenAlex', 'match_status': 'database',
            'publication_status': w.get('type', '数据库记录')}

def match_paper(api, p):
    result = api.works(search=p['title'], per_page=3)
    if not result:
        p['match_status'] = 'api_error'
        return p
    candidates = []
    for w in result.get('results', []):
        score = SequenceMatcher(None, norm(p['title']), norm(w.get('title') or '')).ratio()
        names = {norm(a['author']['display_name']) for a in w.get('authorships', [])}
        corroborated = 'yuhengjia' in names or bool(names & {norm(a) for a in p['authors']})
        if score >= .93 and corroborated:
            candidates.append((score, w))
    if len(candidates) == 1:
        score, w = candidates[0]
        resolved = from_openalex(w)
        resolved['id'] = p['id']
        resolved['lab'] = True
        resolved['source_url'] = p['source_url']
        resolved['list_year'] = p['year']
        resolved['list_authors'] = p['authors']
        resolved['list_title'] = p['title']
        resolved['title'] = p['title']
        resolved['links'] = list(dict.fromkeys(p['links'] + resolved['links']))
        resolved['featured'] = p['featured']
        resolved['match_status'] = 'matched'
        resolved['match_score'] = round(score, 3)
        return resolved
    p['match_status'] = 'ambiguous' if len(candidates) > 1 else 'not_matched'
    p['candidates'] = [{'title': w.get('title'), 'id': w['id']} for w in result.get('results', [])[:2]]
    return p

def tags_for(p):
    if p.get('manual_tags'):
        return p['manual_tags']
    text = p['title'] + ' ' + (p.get('abstract') or '')
    tags = [t[0] for t in TOPICS[:-1] if re.search(t[3], text, re.I)]
    return tags or ['other']

def build_graph(nodes, api, citing_sets):
    by_oa = {p['openalex'].rsplit('/', 1)[-1]: p['id'] for p in nodes if p.get('openalex')}
    by_id = {p['id']: p for p in nodes}
    edges = []
    def add(a, b, kind, score, evidence, tentative=False):
        edges.append({'id': f'{kind}:{a}:{b}', 'source': a, 'target': b, 'kind': kind,
                      'score': round(score, 4), 'evidence': evidence, 'tentative': tentative})
    for p in nodes:
        p['tags'] = tags_for(p)
        p['tag_source'] = '标题与摘要规则推断' if p.get('abstract') else '仅标题规则推断'
        for ref in p['references']:
            if ref in by_oa and by_oa[ref] != p['id'] and (p['lab'] or by_id[by_oa[ref]]['lab']):
                add(p['id'], by_oa[ref], 'citation', 1, {'source': 'OpenAlex', 'text': '数据库记录的直接引用'})
    # Compute lab-lab and lab-background relations; never external-external all-pairs.
    lab = [p for p in nodes if p['lab']]
    for a in lab:
        ra = set(a['references'])
        ca = citing_sets.get(a['id'], set())
        for b in nodes:
            if a['id'] == b['id'] or (b['lab'] and a['id'] > b['id']):
                continue
            rb = set(b['references'])
            shared = ra & rb
            if len(shared) >= 2:
                score = len(shared) / math.sqrt(len(ra) * len(rb))
                if score >= .06:
                    add(a['id'], b['id'], 'coupling', score, {'count': len(shared), 'ids': sorted(shared), 'text': '共同参考文献；余弦归一化'})
            ta = {t['id']:t['display_name'] for t in a.get('api_topics', [])}
            tb = {t['id']:t['display_name'] for t in b.get('api_topics', [])}
            shared_api = sorted(set(ta) & set(tb))
            if shared_api:
                add(a['id'],b['id'],'topic',len(shared_api)/len(set(ta)|set(tb)),
                    {'topic_names':[ta[t] for t in shared_api], 'text':'共享 OpenAlex 自动分类主题；候选关联'},True)
            if b['lab']:
                cb = citing_sets.get(b['id'], set())
                shared_c = ca & cb
                if shared_c:
                    add(a['id'], b['id'], 'cocitation', len(shared_c)/math.sqrt(len(ca)*len(cb)),
                        {'count': len(shared_c), 'ids': sorted(shared_c), 'text': '已采集的外部论文共同引用；采样关系'})
                # Names from lab list are usable but not fully disambiguated author identities.
                shared_a = {norm(n): n for n in a['authors'] if norm(n) != 'yuhengjia'}
                shared_a = [shared_a[norm(n)] for n in b['authors'] if norm(n) in shared_a]
                if shared_a:
                    add(a['id'], b['id'], 'author', len(shared_a), {'authors': shared_a, 'text': '共同署名（默认排除 Yuheng Jia）；姓名标准化，未完整消歧'})
                overlap = sorted(set(a['tags']) & set(b['tags']) - {'other'})
                if overlap and not shared_api:
                    add(a['id'], b['id'], 'topic', len(overlap)/len(set(a['tags']) | set(b['tags'])),
                        {'tags': overlap, 'text': '规则推断的共享主题；不是引用或研究延续证据'}, True)
                shared_i = sorted(set(a.get('institutions', [])) & set(b.get('institutions', [])))
                if shared_i:
                    add(a['id'], b['id'], 'institution', len(shared_i), {'institutions':shared_i, 'text':'OpenAlex 记录中的共享署名机构'})
                shared_s = sorted(set(a.get('series', [])) & set(b.get('series', [])))
                if shared_s:
                    add(a['id'], b['id'], 'series', 1, {'series':shared_s, 'text':'实验室人工确认的同系列论文'})
            va, vb = a.get('embedding'), b.get('embedding')
            if va and vb and len(va) == len(vb):
                score = sum(x*y for x,y in zip(va,vb))/math.sqrt(sum(x*x for x in va)*sum(y*y for y in vb))
                if math.isfinite(score):
                    add(a['id'], b['id'], 'semantic', score, {'text': 'Semantic Scholar SPECTER2 向量余弦相似度'})
    retained = edges
    # Deterministic, topic-seeded coordinates. Browser can optionally run force layout.
    for p in nodes:
        idx = next(i for i,t in enumerate(TOPICS) if t[0] == p['tags'][0])
        angle = idx*2*math.pi/len(TOPICS)
        seed = int(hashlib.sha1(p['id'].encode()).hexdigest()[:12],16)
        theta = (seed%10000)/10000*2*math.pi
        radius = 30 + (seed//10000%10000)/10000*(135 if p['lab'] else 190)
        p['x'],p['y'] = round(410*math.cos(angle)+radius*math.cos(theta),2),round(310*math.sin(angle)+radius*math.sin(theta),2)
        if p.get('manual_tags'):
            p['tag_source'] = '实验室人工确认'
        p.pop('embedding', None)
    return retained

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=str(ROOT/'source-papers.html'))
    parser.add_argument('--cache', default=str(ROOT.parent.parent/'work/api-cache'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--cached-matches', action='store_true', help='Reuse only cached title search results, but allow neighborhood requests')
    parser.add_argument('--seeds', type=int, default=12)
    args = parser.parse_args()
    api = API(Path(args.cache))
    source = Path(args.source).read_text(encoding='utf8')
    lab = parse_source(source)
    (ROOT/'lab-papers.json').write_text(json.dumps(lab, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'Parsed {len(lab)} unique laboratory papers', flush=True)
    if not args.offline:
        api.cache_only = args.cached_matches
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            lab = list(pool.map(lambda p: match_paper(api,p), lab))
        api.cache_only = False
        print(f'Matched {sum(p["match_status"]=="matched" for p in lab)} papers', flush=True)
    overrides_file = ROOT/'overrides.json'
    overrides = json.loads(overrides_file.read_text(encoding='utf8')) if overrides_file.exists() else {}
    for p in lab:
        for field, value in overrides.get(p['id'], {}).items():
            if field in ('abstract','authors','year','links','manual_tags','series'):
                p[field] = value
    nodes = {p['id']:p for p in lab}
    by_oa = {p['openalex'].rsplit('/',1)[-1]:p['id'] for p in lab if p.get('openalex')}
    citing_sets = {}
    available = sorted([p for p in lab if p.get('openalex') and (p['references'] or p.get('citations'))],
                       key=lambda p:(not p.get('featured'),-(p.get('citations') or 0)))
    seeds = []
    for topic in TOPICS[:-1]:
        candidates = [p for p in available if topic[0] in tags_for(p) and p not in seeds]
        if candidates and len(seeds) < args.seeds:
            seeds.append(candidates[0])
    seeds += [p for p in available if p not in seeds][:max(0,args.seeds-len(seeds))]
    if not args.offline:
        for i,p in enumerate(seeds):
            oid = p['openalex'].rsplit('/',1)[-1]
            # One page per seed, bounded to 25 incoming citations.
            citing = api.works(filter='cites:'+oid, per_page=25, sort='cited_by_count:desc')
            if citing:
                ws = citing.get('results', [])
                citing_sets[p['id']] = {w['id'].rsplit('/',1)[-1] for w in ws}
                p['citing_status'] = 'sampled' if (citing.get('meta',{}).get('count',0)>len(ws)) else 'database_observed'
                p['citing_collected'] = len(ws)
                for w in ws:
                    ext = from_openalex(w)
                    if ext['id'] not in by_oa:
                        nodes.setdefault(ext['id'], ext)
            ref_ids = p['references'][:30]
            if ref_ids:
                refs = api.works(filter='openalex_id:'+'|'.join(ref_ids), per_page=100)
                if refs:
                    for w in refs.get('results',[]):
                        ext = from_openalex(w)
                        if ext['id'] not in by_oa:
                            nodes.setdefault(ext['id'],ext)
            print(f'Neighborhood {i+1}/{len(seeds)}: {len(nodes)} nodes', flush=True)
        # Probe real S2 vector service, keep it optional; never replace missing vectors with title scores.
        for p in seeds[:3]:
            identifier = 'DOI:'+p['doi'].replace('https://doi.org/','') if p.get('doi') else 'URL:'+p['openalex']
            s2 = api.get('https://api.semanticscholar.org/graph/v1/paper/'+urllib.parse.quote(identifier,safe='')+'?fields=title,embedding.specter_v2', 'Semantic Scholar')
            if s2 and (s2.get('embedding') or {}).get('vector'):
                p['embedding'] = s2['embedding']['vector']
                p['semantic_source'] = 'Semantic Scholar SPECTER2'
    all_nodes = list(nodes.values())
    edges = build_graph(all_nodes,api,citing_sets)
    for p in all_nodes:
        if p.get('manual_tags'):
            p['tags'] = p['manual_tags']
            p['tag_source'] = '实验室人工确认'
    stats = {'lab': len(lab), 'external': len(all_nodes)-len(lab), 'matched': sum(p['match_status']=='matched' for p in lab),
             'abstracts':sum(bool(p.get('abstract')) for p in lab), 'title_only':sum(not p['authors'] and not p.get('abstract') for p in lab),
             'neighborhood_seeds': len(seeds), 'requests':api.requests,
             'edges':{k:sum(e['kind']==k for e in edges) for k in ('citation','coupling','cocitation','author','topic','semantic','institution','series')}}
    meta = {'updated': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec='seconds'),
            'source':SOURCE_URL,'stats':stats,'limits':{'neighborhood_seeds':args.seeds,'citing_per_seed':25,'reference_nodes_per_seed':30},
            'notes':['所有实验室论文均保留；仅部分匹配论文采集外部邻域。','主题标签采用关键词规则推断。','共同被引基于已采集引用论文。','预置坐标按主题分区。']}
    graph = {'meta':meta,'topics':[{'id':t[0],'name':t[1],'color':t[2]} for t in TOPICS],'nodes':all_nodes,'edges':edges}
    (ROOT/'data.json').write_text(json.dumps(graph,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (ROOT/'data.js').write_text('window.ATLAS_DATA='+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    report = {'meta':meta,'errors':api.errors,'unmatched':[{'id':p['id'],'title':p['title'],'status':p['match_status'],'candidates':p.get('candidates',[])} for p in lab if p['match_status']!='matched']}
    (ROOT/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(stats,ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
