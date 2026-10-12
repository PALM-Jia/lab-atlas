"""Retry transport/rate-limit failures without repeating successful collection."""
from pathlib import Path
source = Path(__file__).with_name('crosscheck_citations.py').read_text(encoding='utf8')
exec(source.split('rows = {')[0], globals())
report = json.loads((SITE / 'citation-comparison.json').read_text(encoding='utf8'))
rows = {r['id']: r for r in report['rows']}
for p in data['nodes']:
    prior = rows[p['id']]['semantic_scholar']
    if p.get('match_status') == 'ambiguous' and prior['status'] == 'success':
        rows[p['id']]['semantic_scholar'] = {'status': 'missing',
            'reason': 'Unresolved State/TRB versus Speed/TITS version identity; candidate count not adopted',
            'route': prior.get('route'), 'candidate': {'title': prior.get('title'), 'paperId': prior.get('identifier'),
                                                     'externalIds': prior.get('externalIds'), 'citationCount': prior.get('count')}}
pending = [(p, identifier(p)) for p in data['nodes'] if identifier(p)
           and rows[p['id']]['semantic_scholar']['status'] != 'success'
           and rows[p['id']]['semantic_scholar'].get('reason', '').startswith(('HTTP 429', 'HTTP 50', 'TimeoutError', 'URLError'))]
fields = 'title,authors,citationCount,externalIds,year'
for start in range(0, len(pending), 50):
    batch = pending[start:start+50]
    result, event = request('https://api.semanticscholar.org/graph/v1/paper/batch?fields=' + fields,
                            {'ids': [ident for _, ident in batch]})
    for i, (p, ident) in enumerate(batch):
        previous = rows[p['id']]['semantic_scholar']
        record = s2_record(p, result[i], ident) if isinstance(result, list) and i < len(result) else {
            'status': 'missing', 'reason': event.get('reason', 'Invalid batch response'), 'route': ident}
        record['previous_attempt'] = previous
        rows[p['id']]['semantic_scholar'] = record
    print('Retry batch', start + len(batch), '/', len(pending), event['status'], event.get('reason', ''), flush=True)
    time.sleep(2)
for p in data['nodes']:
    prior = rows[p['id']]['semantic_scholar']
    if not p['lab'] or prior['status'] == 'success' or not prior.get('reason', '').startswith('HTTP 429'): continue
    url = 'https://api.semanticscholar.org/graph/v1/paper/search/bulk?' + urllib.parse.urlencode({'query': '"' + p['title'] + '"', 'fields': fields})
    result, event = request(url)
    candidates = result.get('data', []) if isinstance(result, dict) else []
    validated = [s2_record(p, c, 'title search/bulk') for c in candidates]
    valid = [v for v in validated if v['status'] == 'success']
    if len(valid) == 1: record = valid[0]
    elif len(valid) > 1: record = {'status': 'missing', 'reason': 'Multiple title-and-author matched candidates require version confirmation', 'route': url}
    else: record = {'status': 'missing', 'reason': event.get('reason', 'Bulk title search returned no identity-validated record'), 'route': url}
    record['previous_attempt'] = prior
    rows[p['id']]['semantic_scholar'] = record
    print('Retry lab bulk', p['id'], record['status'], record.get('reason', ''), flush=True)
    time.sleep(1.1)
def explain_crossref(row):
    record = row['crossref']
    if record.get('reason') != 'HTTP 404' or not record.get('doi'): return
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(record['doi'], safe='') + '/agency'
    result, event = request(url)
    agency = (result or {}).get('message', {}).get('agency', {}) if isinstance(result, dict) else {}
    record['agency_check'] = {'url': url, 'agency': agency, 'request_status': event['status'], 'reason': event.get('reason')}
    if agency.get('id') and agency['id'] != 'crossref':
        record['reason'] = 'DOI registered with ' + agency.get('label', agency['id']) + '; Crossref works endpoint HTTP 404'
    elif agency.get('id') == 'crossref':
        record['reason'] = 'Crossref registration agency confirmed; DOI record endpoint HTTP 404'
with futures.ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(explain_crossref, [r for r in rows.values() if r['lab']]))
report['rows'] = list(rows.values())
report['requests'].extend(events)
prefetch = ROOT / 'work/crossref-prefetch-requests.json'
if prefetch.exists(): report['requests'].extend(json.loads(prefetch.read_text(encoding='utf8')))
report['collected_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
(SITE / 'citation-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('Retry complete', flush=True)
