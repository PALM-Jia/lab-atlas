"""Sync the retrieval dashboard from the reviewed graph keyword annotations.

Run after the graph writer: python work/sync-keyword-retrieval.py
"""
import copy
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'paper-atlas'
SOURCE = [{'name': '标题/摘要标注', 'url': ''}]
METHOD = 'DeepSeek V4.1 Flash 标注，GPT-6.1 Sol 复核；按标题及可用摘要从 49 个关键词中标注。'
LABELS = {'annotated': '已标注关键词', 'empty': '无匹配关键词', 'excluded': '标注未采用'}


def synchronize(graph, dashboard):
    nodes = {p['id']: p for p in graph['nodes']}
    rows = dashboard['papers'] + dashboard.get('external', [])
    assert len(rows) == 1673 and len(nodes) == 1673, 'Expected the full 1673-paper annotation scope'
    assert set(nodes) == {p['id'] for p in rows}, 'Retrieval and graph paper IDs differ'
    counts = Counter()
    for paper in rows:
        node = nodes[paper['id']]
        status = node['keyword_status']
        assert status in LABELS, (paper['id'], status)
        items = copy.deepcopy(node.get('keywords', []))
        assert (status == 'annotated') == bool(items), (paper['id'], status)
        assert all(k['score'] == 1 and k.get('exact_quote') and k.get('evidence_field') in ('title', 'abstract') for k in items)
        counts[status] += 1
        fields = paper['fields']
        reason = node.get('keyword_reason') or node.get('keyword_exclusion_reason') or node.get('keyword_status_reason') or ''
        if isinstance(reason, list):
            reason = '；'.join(map(str, reason))
        explanation = METHOD + ' ' + LABELS[status] + ('：' + str(reason) if reason else '。')
        fields['keywords'] = {
            'value': items, 'state': status, 'sources': copy.deepcopy(SOURCE),
            'explanation': explanation, 'annotationStatus': status,
            'observations': [{'value': items, 'sources': copy.deepcopy(SOURCE), 'adopted': True}] if items else [],
            'different': False, 'adoptedValue': items,
        }
        tasks = [copy.deepcopy(k) for k in items if k['dimension'] == 'research_task']
        fields.pop('directions', None)
        fields['research_task'] = {
            'value': tasks, 'state': status if status != 'annotated' else ('annotated' if tasks else 'empty'),
            'sources': copy.deepcopy(SOURCE),
            'explanation': '已采用关键词中的研究任务，与关键词共用标题或摘要原文依据。',
        }
        fields['topics']['explanation'] = 'OpenAlex 自动研究主题及相关度，用于查看数据库分类结果。'
        paper['issues'] = [i for i in paper.get('issues', []) if i.get('field') not in ('keywords', 'directions', '关键词', '推断研究方向')]
    assert sum(counts.values()) == 1673
    assert counts['excluded'] == 40, counts
    lab = {p['id']: p for p in dashboard['papers']}
    for author in dashboard['authors']:
        totals = defaultdict(float)
        evidence = defaultdict(list)
        names = {}
        denominator = 0.0
        for pid in author['papers']:
            paper = lab[pid]
            if paper['fields']['keywords']['state'] not in ('annotated', 'empty'):
                continue
            authors = paper['fields']['authors']['value']
            first = authors[0] if authors else None
            weight = 1.0 if first and first['id'] == author['id'] else 0.2
            denominator += weight
            for keyword in paper['fields']['keywords']['value']:
                kid = keyword['id']
                totals[kid] += weight
                evidence[kid].append(pid)
                names[kid] = keyword['name']
        author['keywords'] = sorted([
            {'id': kid, 'name': names[kid], 'weight': score / denominator, 'papers': evidence[kid]}
            for kid, score in totals.items()
        ], key=lambda item: (-item['weight'], item['name']))
        author['keywordSource'] = '标题/摘要标注 · 按作者汇总'
    dashboard['meta']['coverage']['keywords'] = sum(p['fields']['keywords']['state'] == 'annotated' for p in dashboard['papers'])
    dashboard['meta']['keywordAnnotations'] = dict(counts)
    dashboard['meta']['keywordMethod'] = METHOD
    dashboard['meta']['statuses'].update(LABELS)
    return counts


if __name__ == '__main__':
    graph = json.loads((OUT / 'data.json').read_text(encoding='utf-8'))
    path = OUT / 'retrieval-data.json'
    dashboard = json.loads(path.read_text(encoding='utf-8'))
    counts = synchronize(graph, dashboard)
    payload = json.dumps(dashboard, ensure_ascii=False, separators=(',', ':'))
    path.write_text(payload + '\n', encoding='utf-8')
    (OUT / 'retrieval-data.js').write_text('window.ATLAS_RETRIEVAL=' + payload + ';\n', encoding='utf-8')
    evidence_path = OUT / 'network-evidence.js'
    prefix = 'window.ATLAS_NETWORK_EVIDENCE='
    existing = evidence_path.read_text(encoding='utf-8').strip()
    assert existing.startswith(prefix)
    network = json.loads(existing[len(prefix):].rstrip(';'))
    for paper in dashboard['papers']:
        evidence_fields = network['papers'][paper['id']]['fields']
        for field in ('keywords', 'research_task'):
            evidence_fields[field] = copy.deepcopy(paper['fields'][field])
        evidence_fields.pop('directions', None)
    network['coverage']['keywords'] = dashboard['meta']['coverage']['keywords']
    network['keywordAnnotations'] = dict(counts)
    evidence_path.write_text(prefix + json.dumps(network, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    runpy.run_path(str(ROOT / 'work' / 'refresh-retrieval-copy.py'), run_name='__main__')
    print(json.dumps({'papers': sum(counts.values()), 'statuses': counts}, ensure_ascii=False))
