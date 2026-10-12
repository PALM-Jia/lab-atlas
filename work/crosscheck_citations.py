"""Fetch independent citation counts; preserve each provider and identity evidence."""
import concurrent.futures as futures
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'outputs/paper-atlas'
CACHE = ROOT / 'work/citation-cache'
CACHE.mkdir(exist_ok=True)
data = json.loads((SITE / 'data.json').read_text(encoding='utf8'))
public = json.loads((SITE / 'public-paper-metadata.json').read_text(encoding='utf8'))
events = []
lock = threading.Lock()

def request(url, body=None):
    signature = url + (json.dumps(body, sort_keys=True) if body is not None else '')
    path = CACHE / (hashlib.sha256(signature.encode()).hexdigest() + '.json')
    event = {'url': url, 'body': body, 'time': dt.datetime.now(dt.timezone.utc).isoformat(), 'attempts': []}
    if path.exists():
        result = json.loads(path.read_text(encoding='utf8'))
        event['status'] = 'cached'
        with lock: events.append(event)
        return result, event
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                headers={'User-Agent': 'LabPaperAtlas/1.0 (citation metadata comparison)', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=25) as response:
                result = json.load(response)
                event['attempts'].append({'http': response.status})
            path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf8')
            event['status'] = 'success'
            event.pop('reason', None)
            with lock: events.append(event)
            return result, event
        except urllib.error.HTTPError as e:
            event['attempts'].append({'http': e.code})
            event['reason'] = f'HTTP {e.code}'
            if e.code not in (429, 500, 502, 503, 504): break
        except Exception as e:
            event['attempts'].append({'error': str(e)[:250]})
            event['reason'] = type(e).__name__ + ': ' + str(e)[:250]
        if attempt < 2: time.sleep(2 ** (attempt + 1))
    event['status'] = 'failure'
    with lock: events.append(event)
    return None, event

def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s or '').lower())

def doi(p):
    return re.sub(r'^https?://(?:dx\.)?doi.org/', '', p.get('doi') or '', flags=re.I)

def identifier(p):
    if p.get('semantic_paper_id'): return p['semantic_paper_id']
    if doi(p): return 'DOI:' + doi(p)
    links = (p.get('links') or []) + public.get(p['id'], {}).get('links', [])
    for link in links:
        match = re.search(r'arxiv.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', link)
        if match: return 'ARXIV:' + match[1]
    return None

def s2_record(p, record, route):
    if record is None: return {'status': 'missing', 'reason': 'Semantic Scholar returned null for identifier', 'route': route}
    count = record.get('citationCount')
    external = record.get('externalIds') or {}
    if p.get('match_status') == 'ambiguous' and not doi(p):
        return {'status': 'missing', 'reason': 'Unresolved State/TRB versus Speed/TITS version identity; candidate count not adopted',
                'route': route, 'candidate': {'title': record.get('title'), 'paperId': record.get('paperId'), 'externalIds': external,
                                            'citationCount': record.get('citationCount')}}
    same_doi = bool(doi(p) and doi(p).lower() == (external.get('DOI') or '').lower())
    title_score = max(difflib.SequenceMatcher(None, norm(t), norm(record.get('title'))).ratio()
                      for t in [p['title'], p.get('list_title') or p['title']])
    expected_names = p.get('authors') or public.get(p['id'], {}).get('authors') or []
    names = {norm(a.get('name')) for a in record.get('authors') or []}
    matched_author = any(norm(name) in names or norm(' '.join(name.split(',')[::-1])) in names for name in expected_names)
    trusted_id = route == p.get('semantic_paper_id') or route.startswith(('DOI:', 'ARXIV:'))
    if not (same_doi or (title_score >= .85 and trusted_id) or (title_score >= .92 and matched_author)):
        return {'status': 'missing', 'reason': 'Candidate failed title/author identity validation', 'route': route,
                'candidate': {'title': record.get('title'), 'paperId': record.get('paperId'), 'title_score': title_score}}
    if not isinstance(count, int) or count < 0:
        return {'status': 'missing', 'reason': 'citationCount absent or invalid', 'route': route}
    return {'status': 'success', 'count': count, 'identifier': record['paperId'], 'route': route,
            'title': record.get('title'), 'year': record.get('year'), 'externalIds': external, 'authors': record.get('authors'),
            'identity': 'exact DOI' if same_doi else 'identifier and title' if trusted_id else 'title and author',
            'url': 'https://www.semanticscholar.org/paper/' + record['paperId']}

rows = {p['id']: {'id': p['id'], 'title': p['title'], 'lab': p['lab'], 'openalex': {
    'status': 'success' if isinstance(p.get('citations'), int) else 'missing',
    'count': p.get('citations'), 'url': p.get('openalex'), 'snapshot': data['meta']['updated']}}
    for p in data['nodes']}
identified = [(p, identifier(p)) for p in data['nodes'] if identifier(p)]
fields = 'title,authors,citationCount,externalIds,year'
batch_url = 'https://api.semanticscholar.org/graph/v1/paper/batch?fields=' + fields
for start in range(0, len(identified), 100):
    batch = identified[start:start+100]
    result, event = request(batch_url, {'ids': [ident for _, ident in batch]})
    for i, (p, ident) in enumerate(batch):
        rows[p['id']]['semantic_scholar'] = s2_record(p, result[i], ident) if isinstance(result, list) and i < len(result) else {
            'status': 'missing', 'reason': event.get('reason', 'Invalid batch response'), 'route': ident}
    print('S2 batch', start + len(batch), '/', len(identified), event['status'], event.get('reason', ''), flush=True)
    time.sleep(1.1)

retry = [(p, ident) for p, ident in identified if rows[p['id']]['semantic_scholar']['status'] != 'success'
         and rows[p['id']]['semantic_scholar'].get('reason') != 'Semantic Scholar returned null for identifier']
for start in range(0, len(retry), 50):
    batch = retry[start:start+50]
    result, event = request(batch_url, {'ids': [ident for _, ident in batch]})
    for i, (p, ident) in enumerate(batch):
        previous = rows[p['id']]['semantic_scholar']
        record = s2_record(p, result[i], ident) if isinstance(result, list) and i < len(result) else {
            'status': 'missing', 'reason': event.get('reason', 'Invalid batch response'), 'route': ident}
        record['previous_attempt'] = previous
        rows[p['id']]['semantic_scholar'] = record
    print('S2 retry', start + len(batch), '/', len(retry), event['status'], event.get('reason', ''), flush=True)
    time.sleep(2)

for p in data['nodes']:
    if 'semantic_scholar' not in rows[p['id']]:
        rows[p['id']]['semantic_scholar'] = {'status': 'missing', 'reason': 'No Semantic Scholar ID, DOI or arXiv ID'}
    if not p['lab'] or rows[p['id']]['semantic_scholar']['status'] == 'success': continue
    url = 'https://api.semanticscholar.org/graph/v1/paper/search/match?' + urllib.parse.urlencode({'query': p['title'], 'fields': fields})
    result, event = request(url)
    candidates = result.get('data', []) if isinstance(result, dict) else []
    previous = rows[p['id']]['semantic_scholar']
    rows[p['id']]['semantic_scholar'] = s2_record(p, candidates[0], 'title search/match') if candidates else {
        'status': 'missing', 'reason': event.get('reason', 'Title match returned no candidate'), 'route': url}
    rows[p['id']]['semantic_scholar']['previous_attempt'] = previous
    print('S2 lab fallback', p['id'], rows[p['id']]['semantic_scholar']['status'], flush=True)
    time.sleep(1.1)

def crossref(p):
    primary_doi = doi(p)
    if not primary_doi:
        return p['id'], {'status': 'missing', 'reason': 'No verified DOI; Crossref DOI lookup unavailable'}
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(primary_doi, safe='')
    result, event = request(url)
    record = result.get('message') if isinstance(result, dict) else None
    if not isinstance(record, dict):
        return p['id'], {'status': 'missing', 'reason': event.get('reason', 'Crossref record unavailable'), 'url': url, 'doi': primary_doi}
    count = record.get('is-referenced-by-count')
    if (record.get('DOI') or '').lower() != primary_doi.lower():
        return p['id'], {'status': 'missing', 'reason': 'Returned DOI differs from requested DOI', 'url': url}
    if not isinstance(count, int) or count < 0:
        return p['id'], {'status': 'missing', 'reason': 'is-referenced-by-count absent or invalid', 'url': url}
    return p['id'], {'status': 'success', 'count': count, 'doi': record['DOI'], 'title': record.get('title'),
                      'url': url, 'indexed': record.get('indexed', {}).get('date-time'), 'identity': 'exact DOI'}

lab = [p for p in data['nodes'] if p['lab']]
with futures.ThreadPoolExecutor(max_workers=2) as pool:
    for index, (pid, record) in enumerate(pool.map(crossref, lab)):
        rows[pid]['crossref'] = record
        if index % 15 == 0: print('Crossref lab', index + 1, '/', len(lab), flush=True)
for row in rows.values():
    if 'crossref' not in row: row['crossref'] = {'status': 'not_requested', 'reason': 'Crossref cross-check scoped to lab papers'}
report = {'collected_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'openalex_snapshot': data['meta']['updated'],
          'scope': {'semantic_scholar': 'all graph papers; title fallback for lab papers', 'crossref': 'all lab papers, verified DOI lookup'},
          'rows': list(rows.values()), 'requests': events}
(SITE / 'citation-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('Saved citation-comparison.json', flush=True)
