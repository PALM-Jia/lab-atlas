"""Summarize checked labels, retaining only unaccepted entries in the issue report."""
from collections import Counter
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import validate


ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    report = validate.validate(ROOT)
    if report['setup_errors']:
        raise ValueError(report['setup_errors'])
    papers = {p['paper_id']: p for f in sorted((ROOT / 'inputs').glob('batch-*.json'))
              for p in validate.read_json(f)['papers']}
    unresolved = []
    for item in report['review_papers']:
        pid = item['paper_id']
        if item['status'] in ('review_pass', 'review_revised'):
            continue
        raw_path, review_path = ROOT / 'results' / (pid + '.json'), ROOT / 'reviews' / (pid + '.json')
        raw = validate.read_json(raw_path) if raw_path.exists() else None
        review = validate.read_json(review_path) if review_path.exists() else None
        reasons = []
        if review and review.get('patch'):
            reasons.extend(review['patch']['input_issues'])
        elif raw:
            reasons.extend(raw['input_issues'])
        if review and not reasons:
            reasons.extend(i['reason_zh'] for i in review['issues'] if i['kind'] == 'input_problem' or review['verdict'] == 'needs_review')
        reasons.extend(item['errors'])
        unresolved.append({'paper_id': pid, 'title': papers[pid]['title'],
                           'cohort': '实验室' if pid.startswith('lab-') else '外部',
                           'status': item['status'], 'has_annotation': raw is not None,
                           'reasons': list(dict.fromkeys(reasons))})
    attempts, usage = Counter(), Counter()
    for f in (ROOT / 'attempts').glob('*/*.metadata.json'):
        metadata = validate.read_json(f)
        attempts[str(metadata.get('http_status', metadata.get('status')))] += 1
        for key, value in (metadata.get('usage') or {}).items():
            if isinstance(value, (int, float)):
                usage[key] += value
        usage['reasoning_tokens'] += (metadata.get('usage') or {}).get('completion_tokens_details', {}).get('reasoning_tokens', 0)
    accepted = validate.read_json(ROOT / 'accepted' / 'aggregate.json')
    cohorts = {}
    statuses = {x['paper_id']: x['status'] for x in report['review_papers']}
    for key, is_lab in (('lab', True), ('external', False)):
        group_ids = [pid for pid in papers if pid.startswith('lab-') == is_lab]
        cohorts[key] = {'total': len(group_ids), 'review_counts': dict(Counter(statuses[pid] for pid in group_ids))}
    summary = {'generated_at': datetime.now(timezone.utc).isoformat(),
               'input_count': len(papers), 'annotation_counts': report['counts'],
               'review_counts': report['review_counts'],
               'review_finished': report['review_counts']['review_pending'] == 0 and report['review_counts']['review_invalid'] == 0,
               'accepted_count': accepted['accepted_count'],
               'accepted_nonempty': sum(bool(p['annotations']) for p in accepted['papers']),
               'accepted_empty': sum(not p['annotations'] for p in accepted['papers']),
               'input_title_only': sum(not p.get('abstract') for p in papers.values()),
               'keyword_count': len(validate.read_json(ROOT / 'vocabulary.json')['keywords']),
               'cohorts': cohorts,
               'attempts': dict(attempts), 'usage_all_attempts': dict(usage),
               'estimated_annotation_cost_usd': (usage['prompt_cache_hit_tokens'] * .003 + usage['prompt_cache_miss_tokens'] * .15 + usage['completion_tokens'] * .6) / 1_000_000,
               'unaccepted_papers': unresolved}
    closure_path = ROOT / 'control' / 'closure.json'
    if closure_path.exists():
        summary['user_decision'] = validate.read_json(closure_path)
    save(ROOT / 'control' / 'summary.json', summary)
    save(ROOT / 'control' / 'unaccepted-papers.json', unresolved)
    lines = [f"关键词标注：{len(papers)} 篇，{summary['keyword_count']} 个关键词。",
             '标注状态：' + json.dumps(report['counts'], ensure_ascii=False),
             '验收状态：' + json.dumps(report['review_counts'], ensure_ascii=False),
             f"采用 {accepted['accepted_count']} 篇；其中有标签 {summary['accepted_nonempty']} 篇，空标签 {summary['accepted_empty']} 篇。",
             '空标签表示未在现有标题/摘要中找到49词表的充分依据；不等同于请求失败。',
             'input_issues 或未解决的审阅问题保留在待核查清单；原始结果和审阅补丁分别保留。',
             '现有网页网络数据未改写。', '', '待核查清单：']
    for item in unresolved:
        lines.extend([f"{item['paper_id']} | {item['title']} | {item['status']}"] + item['reasons'])
    (ROOT / 'summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    names = {'review_pending': '等待验收', 'review_needs_review': '输入待核查', 'review_invalid': '审阅格式错误'}
    rows = []
    for item in unresolved:
        reasons = '<br>'.join(html.escape(r) for r in item['reasons']) or ('未取得标注结果' if not item['has_annotation'] else '等待验收')
        rows.append('<tr><td><strong>' + html.escape(item['title']) + '</strong><small>' +
                    html.escape(item['paper_id']) + ' · ' + item['cohort'] + '</small></td><td>' +
                    names.get(item['status'], item['status']) + '</td><td>' + reasons + '</td></tr>')
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab Atlas · 关键词待核查</title><style>*{box-sizing:border-box}body{margin:0;background:#f6f7fa;color:#243044;font:16px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:24px}header{display:flex;align-items:center;gap:24px;border-bottom:1px solid #e1e6ee;padding-bottom:12px}h1{font-size:22px;margin:0}a{color:#4772cf;text-decoration:none}a:hover{text-decoration:underline}p{color:#64748b}table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #e1e6ee}th{background:#eef1f6}th:first-child{width:35%}th:nth-child(2){width:12%}small{display:block;color:#64748b;font-size:13px;margin-top:4px}td:last-child{background:#fbf9fd}</style>
<main><header><h1>关键词待核查</h1><a href="progress.html">标注进度</a></header>'''
    page += f"<p>{len(unresolved)} 篇暂未采用。</p>"
    page += '<table><thead><tr><th>论文</th><th>状态</th><th>原因</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></main></html>'
    if closure_path.exists():
        page = page.replace('关键词待核查', '关键词未采用条目').replace('输入待核查', '未采用').replace('篇暂未采用。', '篇未采用。')
    (ROOT / 'issues.html').write_text(page, encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('input_count', 'accepted_count', 'review_finished', 'accepted_nonempty', 'accepted_empty')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
