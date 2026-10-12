"""Small Scholar probe: aliases first, then explicitly selected cites/cluster IDs.

Credentials are read only from SERPAPI_API_KEY. Results remain in work/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'work' / 'serpapi-probe'
QUERIES = [
    '"Attribute Distribution Modeling and Semantic-Visual Alignment for Generative Zero-shot Learning"',
    '"Learning Adaptive and Visually Aligned Conditions for Generative Zero-Shot Learning"',
    '"2603.06281"',
]


def probe(params, key):
    public = {'engine': 'google_scholar', 'hl': 'en', 'num': 10, **params}
    cache = OUT / (hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()[:20] + '.json')
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    event = {'parameters': public, 'collected_at': datetime.now(timezone.utc).isoformat()}
    url = 'https://serpapi.com/search.json?' + urlencode({**public, 'api_key': key})
    try:
        with urlopen(Request(url, headers={'User-Agent': 'LabAtlas/1.0'}), timeout=45) as response:
            event['http'] = response.status
            event['response'] = json.load(response)
            event['status'] = 'error' if event['response'].get('error') else 'success'
    except HTTPError as exc:
        event.update(status='error', http=exc.code)
        event['error'] = exc.read().decode('utf-8', errors='replace')[:2000]
    except (URLError, TimeoutError, ValueError) as exc:
        event.update(status='error', error=str(exc))
    # Scrub credentials even if an upstream error or URL echoes the request.
    safe = json.dumps(event, ensure_ascii=False, indent=2).replace(key, '[REDACTED]')
    if event['status'] == 'success':
        cache.write_text(safe + '\n', encoding='utf-8')
    return json.loads(safe)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--cites', help='Fetch first page of citing papers for a checked Scholar cites_id')
    group.add_argument('--cluster', help='Fetch first page of versions for a checked Scholar cluster_id')
    args = parser.parse_args()
    key = os.environ.get('SERPAPI_API_KEY', '').strip()
    if not key:
        print('SERPAPI_API_KEY is not configured; no requests sent.')
        return 2
    OUT.mkdir(exist_ok=True)
    requests = [{'cites': args.cites}] if args.cites else [{'cluster': args.cluster}] if args.cluster else [{'q': q} for q in QUERIES]
    events = []
    for params in requests:
        event = probe(params, key)
        events.append(event)
        results = event.get('response', {}).get('organic_results', [])
        print(json.dumps({'query': params, 'status': event['status'], 'results': [
            {'title': row.get('title'), 'link': row.get('link'), 'publication_info': row.get('publication_info'),
             'cited_by': row.get('inline_links', {}).get('cited_by'),
             'versions': row.get('inline_links', {}).get('versions')}
            for row in results]}, ensure_ascii=False))
        if event['status'] != 'success':
            break
    name = 'cites-' + args.cites if args.cites else 'cluster-' + args.cluster if args.cluster else 'aliases'
    # IDs come from API output; prohibit filesystem path characters.
    name = ''.join(c for c in name if c.isalnum() or c == '-')
    (OUT / (name + '-report.json')).write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if all(e['status'] == 'success' for e in events) else 1


if __name__ == '__main__':
    raise SystemExit(main())
