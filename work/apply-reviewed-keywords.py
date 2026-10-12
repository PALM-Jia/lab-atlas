"""Publish accepted keyword evidence into the static atlas; never request an API."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT / 'outputs' / 'paper-atlas'
LABELS = ROOT / 'work' / 'keyword-full'
COLORS = {'research_task': '#6877ce', 'method': '#54a3a0',
          'application_object': '#d99850', 'research_setting': '#bd6c8c'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value, prefix=''):
    serialized = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    path.write_text(prefix + serialized + (';\n' if prefix else '\n'), encoding='utf-8')


def apply(data):
    accepted = read(LABELS / 'accepted' / 'aggregate.json')
    closure = read(LABELS / 'control' / 'closure.json')
    vocabulary = read(LABELS / 'vocabulary.json')['keywords']
    source = {p['paper_id']: p for f in sorted((LABELS / 'inputs').glob('batch-*.json'))
              for p in read(f)['papers']}
    records = {p['paper_id']: p for p in accepted['papers']}
    excluded = set(closure['excluded_ids'])
    assert set(records).isdisjoint(excluded)
    assert set(records) | excluded == set(source) == {p['id'] for p in data['nodes']}
    vocab = [{**k, 'aliases': list(dict.fromkeys([k['canonical_en'], *k.get('aliases', [])])),
              'name': k['canonical_zh'], 'dimension': k['primary_dimension'],
              'color': COLORS[k['primary_dimension']]} for k in vocabulary]
    terms = {k['id']: k for k in vocab}
    issues = {p['paper_id']: p['reasons'] for p in read(LABELS / 'control' / 'unaccepted-papers.json')}
    papers, statuses, lab_frequency = {}, {}, Counter()
    for node in data['nodes']:
        pid = node['id']
        status = 'excluded' if pid in excluded else 'annotated' if records[pid]['annotations'] else 'empty'
        labels = []
        for annotation in records.get(pid, {}).get('annotations', []):
            term = terms[annotation['keyword_id']]
            quote, field = annotation['exact_quote'], annotation['evidence_field']
            assert quote and quote in (source[pid].get(field) or '')
            labels.append({'id': term['id'], 'name': term['name'], 'dimension': term['dimension'],
                           'score': 1, 'evidence_field': field, 'exact_quote': quote,
                           'reason_zh': annotation['reason_zh']})
        node.update(tags=[k['id'] for k in labels], keywords=labels, keyword_status=status,
                    keyword_reason=issues.get(pid, []), tag_source='标题与摘要标注 · DeepSeek / 6.1sol',
                    keyword_input={'title': source[pid]['title'], 'abstract_available': bool(source[pid].get('abstract')),
                                   'sha256': hashlib.sha256(json.dumps(source[pid], ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
        papers[pid], statuses[pid] = labels, status
        if node['lab'] and status != 'excluded':
            lab_frequency.update(k['id'] for k in labels)
    lab_total = sum(n['lab'] and n['keyword_status'] != 'excluded' for n in data['nodes'])
    data['topics'] = [{k: t[k] for k in ('id', 'name', 'color', 'dimension', 'aliases')} for t in vocab]
    coverage = {'total': len(source), 'accepted': len(records), 'with_keywords': sum(bool(x) for x in papers.values()),
                'empty': sum(s == 'empty' for s in statuses.values()), 'excluded': len(excluded)}
    feature = {'papers': papers, 'statuses': statuses, 'vocabulary': vocab,
               'idf': {k['id']: math.log((lab_total + 1) / (lab_frequency[k['id']] + 1)) + 1 for k in vocab},
               'coverage': coverage, 'source': '标题与摘要标注 · DeepSeek V4.1 Flash / 6.1sol 验收',
               'idf_corpus': '已采用的实验室论文（包括空标注）',
               'updated': datetime.now(timezone.utc).isoformat()}
    data['meta']['keywords'] = {k: feature[k] for k in ('coverage', 'source', 'idf_corpus', 'updated')}
    data['meta']['notes'] = [n for n in data['meta'].get('notes', []) if '候选关联' not in n and '人工系列' not in n]
    return data, feature


def main():
    data = read(ATLAS / 'data.json')
    # Verify that this integration changes only keyword fields, never identities,
    # author order, citation evidence, semantic vectors, positions, or old edges.
    keyword_keys = {'tags', 'keywords', 'keyword_status', 'keyword_reason', 'tag_source', 'keyword_input'}
    snapshot = hashlib.sha256(json.dumps({'nodes': [{k: v for k, v in n.items() if k not in keyword_keys} for n in data['nodes']],
                                         'edges': data['edges']}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    data, feature = apply(data)
    after = hashlib.sha256(json.dumps({'nodes': [{k: v for k, v in n.items() if k not in keyword_keys} for n in data['nodes']],
                                      'edges': data['edges']}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert snapshot == after
    write(ATLAS / 'data.json', data)
    write(ATLAS / 'data.js', data, 'window.ATLAS_DATA=')
    write(ATLAS / 'paper-keywords.json', feature)
    write(ATLAS / 'paper-keywords.js', feature, "'use strict';\nwindow.ATLAS_PAPER_KEYWORDS=")
    out = ROOT / 'work' / 'keyword-integration'
    out.mkdir(exist_ok=True)
    write(out / 'data-check.json', {'coverage': feature['coverage'], 'unchanged_graph_sha256': snapshot,
                                   'vocabulary_count': len(data['topics']), 'all_quotes_checked': True})
    if (ATLAS / 'retrieval-data.json').exists():
        runpy.run_path(str(ROOT / 'work' / 'sync-keyword-retrieval.py'), run_name='__main__')
    if (ROOT / 'work' / 'export-research-fields.cjs').exists():
        subprocess.run(['node', str(ROOT / 'work' / 'export-research-fields.cjs')], check=True)
    print(json.dumps(feature['coverage']))


if __name__ == '__main__':
    main()
