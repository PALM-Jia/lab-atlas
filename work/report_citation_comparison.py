"""Summarize independent counts and publish comparison and failure routes."""
import collections
import csv
import html
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'outputs/paper-atlas'
LEGACY = Path(__file__).resolve().parents[1] / 'work/archive/paper-atlas-legacy-2026-10-13'
LEGACY.mkdir(parents=True, exist_ok=True)
report = json.loads((ROOT / 'citation-comparison.json').read_text(encoding='utf8'))
for event in report['requests']:
    if event['status'] in ('success', 'cached'): event.pop('reason', None)
rows = report['rows']
identity_missing = {r['id']:r for r in json.loads((ROOT / 'citation-coverage.json').read_text(encoding='utf8'))['missing']}
for row in rows:
    if row['openalex']['status'] == 'missing':
        row['openalex']['reason'] = identity_missing[row['id']].get('reason') or identity_missing[row['id']]['match_status']
providers = ['openalex', 'semantic_scholar', 'crossref']
labels = {'openalex': 'OpenAlex', 'semantic_scholar': 'Semantic Scholar', 'crossref': 'Crossref'}
summary = {}
for lab in (True, False):
    subset = [r for r in rows if r['lab'] == lab]
    summary['lab' if lab else 'external'] = {'total': len(subset)}
    for provider in providers:
        good = [r for r in subset if r[provider]['status'] == 'success']
        not_requested = sum(r[provider]['status'] == 'not_requested' for r in subset)
        summary['lab' if lab else 'external'][provider] = {
            'success': len(good), 'zero': sum(r[provider]['count'] == 0 for r in good),
            'missing': len(subset) - len(good) - not_requested, 'not_requested': not_requested,
            'failure_reasons': dict(collections.Counter(r[provider].get('reason', 'unknown') for r in subset if r[provider]['status'] == 'missing'))}
lab_rows = [r for r in rows if r['lab']]
for provider in providers[1:]:
    comparable = [r for r in lab_rows if r['openalex']['status'] == r[provider]['status'] == 'success']
    summary['lab'][provider]['comparison'] = {
        'paired': len(comparable), 'equal': sum(r['openalex']['count'] == r[provider]['count'] for r in comparable),
        'higher': sum(r[provider]['count'] > r['openalex']['count'] for r in comparable),
        'lower': sum(r[provider]['count'] < r['openalex']['count'] for r in comparable),
        'newly_available': sum(r['openalex']['status'] != 'success' and r[provider]['status'] == 'success' for r in lab_rows)}
report['summary'] = summary
(ROOT / 'citation-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
(ROOT / 'citation-counts.js').write_text('window.ATLAS_CITATION_COUNTS=' + json.dumps({r['id']: {p:{k:r[p][k] for k in ('status','count','url') if k in r[p]} for p in providers} for r in rows}, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf8')
with (ROOT / 'citation-comparison.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'title', 'lab', *[labels[p] for p in providers], *[labels[p] + ' status' for p in providers]])
    for r in rows: writer.writerow([r['id'], r['title'], r['lab'], *[r[p].get('count', '') for p in providers], *[r[p]['status'] for p in providers]])
esc = html.escape
def cell(row, provider):
    value = row[provider]
    if value['status'] != 'success': return '—'
    return f'<a href="{esc(value.get("url") or "#")}" target="_blank" rel="noopener">{value["count"]}</a>'
parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>被引次数交叉对照</title>',
    '<style>body{font:16px/1.6 system-ui;color:#243143;background:#f5f7fa;margin:0}main{max-width:1180px;margin:auto;padding:24px}h1{font-size:26px}h2{font-size:20px}a{color:#2463a9}table{border-collapse:collapse;background:white;width:100%;margin:16px 0}td,th{text-align:left;border:1px solid #dde3ea;padding:8px 12px}article{background:white;border:1px solid #dde3ea;padding:12px 18px;margin:12px 0;border-radius:8px}code{overflow-wrap:anywhere}input,select{font:inherit;padding:6px;margin-right:12px}.route{font-size:14px;color:#627083}nav{display:flex;gap:18px;flex-wrap:wrap}</style>',
    '<main><nav><a href="index.html">论文地图</a><a href="citation-comparison.csv">完整对照表 CSV</a><a href="citation-comparison.json">来源与请求记录</a><a href="scholar-dblp-probe.html">Google Scholar / DBLP 试查</a></nav><h1>被引次数交叉对照</h1>',
    '<p>OpenAlex 快照：' + esc(report['openalex_snapshot']) + '；本次采集：' + esc(report['collected_at']) + '</p>',
    '<p>Semantic Scholar 核对全部图中论文；Crossref 核对实验室论文的已确认 DOI。各来源分别保留计数，节点大小继续使用 OpenAlex。</p>',
    '<p>Crossref 计数为已提交至 Crossref 的入向引用；Semantic Scholar 与 OpenAlex 使用各自的文献图谱。对照按已确认论文 ID/DOI；标题搜索结果需通过标题和作者校验。</p>',
    '<table><thead><tr><th>范围</th><th>渠道</th><th>已获取</th><th>其中为 0</th><th>失败</th><th>未请求</th></tr></thead><tbody>']
for scope in ['lab', 'external']:
    for p in providers:
        item = summary[scope][p]; total = summary[scope]['total']
        parts.append(f'<tr><td>{"实验室论文" if scope=="lab" else "外部文献"} ({total})</td><td>{labels[p]}</td><td>{item["success"]} ({item["success"]/total:.1%})</td><td>{item["zero"]}</td><td>{item["missing"]}</td><td>{item["not_requested"]}</td></tr>')
parts.append('</tbody></table><h2>实验室论文对照</h2><input id="search" placeholder="搜索标题"><select id="filter"><option value="all">全部</option><option value="different">计数不同</option><option value="missing">有渠道缺失</option><option value="new">补齐 OpenAlex 缺失</option></select><table><thead><tr><th>论文</th><th>OpenAlex</th><th>Semantic Scholar</th><th>Crossref</th></tr></thead><tbody id="papers">')
for r in lab_rows:
    counts = [r[p]['count'] for p in providers if r[p]['status'] == 'success']
    different = len(set(counts)) > 1
    missing = any(r[p]['status'] != 'success' for p in providers)
    new = r['openalex']['status'] != 'success' and len(counts) > 0
    parts.append(f'<tr data-title="{esc(r["title"].lower())}" data-different="{int(different)}" data-missing="{int(missing)}" data-new="{int(new)}"><td>{esc(r["title"])}</td>' + ''.join('<td>'+cell(r,p)+'</td>' for p in providers) + '</tr>')
parts.append('</tbody></table><h2>新增渠道失败明细</h2>')
reason_labels = {
 'No verified DOI; Crossref DOI lookup unavailable': '无已确认 DOI，无法按 DOI 查询 Crossref',
 'HTTP 404': '接口返回 HTTP 404，未返回对应记录',
 'HTTP 429': '接口返回 HTTP 429，请求限流，重试后仍失败',
 'No Semantic Scholar ID, DOI or arXiv ID': '缺少 Semantic Scholar ID、DOI 和 arXiv ID',
 'Semantic Scholar returned null for identifier': '按标识符查询返回 null',
 'Candidate failed title/author identity validation': '返回候选未通过标题／作者身份校验',
 'Title match returned no candidate': '标题匹配接口未返回候选',
 'Bulk title search returned no identity-validated record': '标题批量搜索返回结果中，无标题／作者身份校验通过的记录',
 'Unresolved State/TRB versus Speed/TITS version identity; candidate count not adopted': 'State/TRB 与 Speed/TITS 的版本对应关系未确认，未采用候选被引数',
 'Crossref registration agency confirmed; DOI record endpoint HTTP 404': '注册机构确认为 Crossref，但该 DOI 的记录接口返回 HTTP 404',
 'Multiple title-and-author matched candidates require version confirmation': '多个候选通过标题／作者校验，版本尚未确认'}
for r in lab_rows:
    failures = [p for p in providers[1:] if r[p]['status'] == 'missing']
    if not failures: continue
    parts.append('<article><b>'+esc(r['title'])+'</b>')
    for p in failures:
        v = r[p]; reason = v.get('reason', '')
        description = reason_labels.get(reason, reason)
        if reason.startswith('DOI registered with '): description = 'DOI 注册于 '+reason.split(';')[0].removeprefix('DOI registered with ')+'，Crossref 论文记录接口返回 HTTP 404'
        parts.append('<p>'+labels[p]+'：'+esc(description)+'</p>')
        route = v.get('route') or v.get('url')
        if route: parts.append('<p class="route">查询路径：<code>'+esc(route)+'</code></p>')
        if v.get('candidate'): parts.append('<p class="route">返回候选：'+esc(v['candidate']['title'])+'</p>')
        if v.get('agency_check'): parts.append('<p class="route">注册机构核查：<code>'+esc(v['agency_check']['url'])+'</code></p>')
    parts.append('</article>')
parts.append('<script>function apply(){const q=document.getElementById("search").value.toLowerCase(),f=document.getElementById("filter").value;document.querySelectorAll("#papers tr").forEach(r=>r.hidden=!r.dataset.title.includes(q)||(f!=="all"&&r.dataset[f]!=="1"));}document.getElementById("search").oninput=apply;document.getElementById("filter").onchange=apply;</script></main></html>')
(LEGACY / 'citation-comparison.html').write_text(''.join(parts), encoding='utf8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
