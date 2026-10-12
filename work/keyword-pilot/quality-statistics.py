"""Reproduce post-blind-audit set metrics; preserve production, annotations and references."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def write(relative, value):
    (ROOT / relative).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


frozen = read('control/frozen-inputs-and-results.json')
for item in frozen['files']:
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], 'Frozen bytes changed: ' + item['path']
runs = read('control/run-map.json')['runs']
reference = read('audit/reference-final.json')
initial_hash = hashlib.sha256((ROOT / 'audit/reference-initial.json').read_bytes()).hexdigest()
assert initial_hash.lower() == reference['provenance']['initial_sha256'].lower()
audit = read('audit/blind-audit.json')
assert initial_hash.lower() == audit['initial_reference_sha256'].lower()
references = {s['sample_id']: s for s in reference['samples']}
audited = {s['sample_id']: s for s in audit['samples']}
vocabulary = read('vocabulary-for-annotation.json')
names = {k['id']: k['canonical_zh'] for k in vocabulary['keywords']}
assert len(names) == 49
manifest = read('sample-manifest.json')['samples']
assert len(manifest) == 10 and sum(s['lab'] for s in manifest) == 5
assert sum(s['abstract_available'] for s in manifest) == 8
repeatability = {m['model']: m for m in read('control/repeatability.json')['models']}
results = []
mismatches = []
for run in runs:
    sample = run['sample_id']
    required = {a['keyword_id'] for a in references[sample]['required']}
    optional = {a['keyword_id'] for a in references[sample]['optional']}
    assert not required & optional
    result = read(run['output_path'])
    selected = {a['keyword_id'] for a in result['annotations']}
    assert result['sample_id'] == sample
    assert len(selected) == len(result['annotations'])
    assert selected <= set(names)
    accepted = selected & (required | optional)
    covered = selected & required
    fp, fn = selected - (required | optional), required - selected
    blind = audited[sample]['results'][run['blind_label']]
    comparisons = {'selected_ids': selected, 'false_positives': fp, 'false_negatives': fn,
                   'accepted_required_ids': covered, 'accepted_optional_ids': selected & optional}
    for field, expected in comparisons.items():
        actual = {v['keyword_id'] if isinstance(v, dict) else v for v in blind[field]}
        if actual != expected:
            mismatches.append({'run_id': run['run_id'], 'sample_id': sample, 'field': field,
                               'calculated': sorted(expected), 'audit': sorted(actual)})
    results.append({**run, 'selected_ids': sorted(selected), 'selected_zh': [names[k] for k in sorted(selected)],
                    'accepted_count': len(accepted), 'selected_count': len(selected),
                    'covered_required_count': len(covered), 'required_opportunities': len(required),
                    'false_positive_ids': sorted(fp), 'false_negative_ids': sorted(fn),
                    'false_positive_zh': [names[k] for k in sorted(fp)], 'false_negative_zh': [names[k] for k in sorted(fn)],
                    'unique_issue_ids': blind['unique_issue_ids'], 'problem_free': blind['unique_issue_count'] == 0})
write('control/audit-set-consistency.json', {'all_consistent': not mismatches, 'checked_outputs': len(results), 'mismatches': mismatches})
assert not mismatches, 'Computed sets differ from Astra audit; metrics/report not generated; see control/audit-set-consistency.json'
assert len(results) == 40
assert sum(len(r['false_positive_ids']) for r in results) == audit['summary']['false_positive_count']
assert sum(len(r['false_negative_ids']) for r in results) == audit['summary']['false_negative_count']
assert sum(r['problem_free'] for r in results) == audit['summary']['problem_free_result_count']
grouped = defaultdict(list)
for r in results:
    grouped[r['model']].append(r)
models = []
for model, rows in sorted(grouped.items()):
    assert len(rows) == 20
    accepted = sum(r['accepted_count'] for r in rows)
    selected = sum(r['selected_count'] for r in rows)
    covered = sum(r['covered_required_count'] for r in rows)
    required = sum(r['required_opportunities'] for r in rows)
    rep = repeatability[model]
    models.append({'model': model, 'result_count': len(rows), 'acceptable_selected': accepted,
                   'all_selected': selected, 'micro_precision': accepted / selected if selected else None,
                   'covered_required': covered, 'required_opportunities': required,
                   'micro_recall': covered / required if required else None,
                   'false_positives': sum(len(r['false_positive_ids']) for r in rows),
                   'false_negatives': sum(len(r['false_negative_ids']) for r in rows),
                   'problem_free_results': sum(r['problem_free'] for r in rows),
                   'unique_problems': len({i for r in rows for i in r['unique_issue_ids']}),
                   'identical_set_samples': rep['identical_set_samples'],
                   'repeatability_sample_count': rep['sample_count'], 'mean_jaccard': rep['mean_jaccard']})
coverage = {'new_abstracts': 128, 'abstracts': 1464, 'total': 1673, 'lab_abstracts': 126,
            'lab_total': 144, 'external_abstracts': 1338, 'external_total': 1529,
            'provenance': 'Task-confirmed abstract enrichment snapshot; not annotation quality denominator'}
metrics = {'scope': 'Only these 10 samples and Astra final blind-audit judgments',
           'precision_definition': 'micro acceptable selected / all selected; required and optional are acceptable',
           'recall_definition': 'micro covered required / all required opportunities; optional omission is not FN',
           'empty_selection_policy': 'No automatic error; evaluate against required/optional sets',
           'formal_results': 40, 'fresh_independent_contexts': True, 'failed_cli_probes_included': False,
           'keyword_count': 49, 'audit_set_consistency': True, 'abstract_coverage': coverage,
           'reference_initial_sha256': initial_hash, 'reference_revisions': reference['reference_revisions'],
           'models': models, 'results': results}
write('metrics.json', metrics)


def pct(number):
    return f'{number:.1%}' if number is not None else '无分母'


def pair_labels(model, sample):
    rows = sorted((r for r in results if r['model'] == model and r['sample_id'] == sample), key=lambda r: r['replicate'])
    labels = ['、'.join(r['selected_zh']) or '空集' for r in rows]
    return '两次：' + labels[0] if labels[0] == labels[1] else '①' + labels[0] + '；②' + labels[1]


def issues_for(sample):
    issues = []
    for model in ['gpt-6.1-sol', 'gpt-6-luna']:
        for r in sorted((r for r in results if r['model'] == model and r['sample_id'] == sample), key=lambda r: r['replicate']):
            if r['false_positive_zh'] or r['false_negative_zh']:
                label = 'Sol' if model == 'gpt-6.1-sol' else 'Luna'
                parts = []
                if r['false_positive_zh']:
                    parts.append('多选' + '、'.join(r['false_positive_zh']))
                if r['false_negative_zh']:
                    parts.append('漏选' + '、'.join(r['false_negative_zh']))
                issues.append(label + str(r['replicate']) + '：' + '；'.join(parts))
    return '；'.join(issues) if issues else '无明确问题'


lines = [
    '本次补齐128份摘要，当前1464/1673篇有摘要（实验室126/144，外部1338/1529）。关键词pilot抽取实验室与外部各5篇，共8篇有摘要、2篇仅标题；固定49词与共同指令，以40次fresh独立上下文标注。实际模型ID为gpt-6.1-sol（Sol）与gpt-6-luna（Luna），两个队列并行进行，每模型每篇重复两次。两次失败CLI探测不计入正式结果。',
    '',
    '按Astra匿名盲审的final必选集与可选集计算micro指标：精确率＝可接受已选/全部已选；召回率＝已覆盖必选/全部必选机会。可选项不选不算漏标。下表的明确错标与漏标按关键词机会计数；无明确问题按结果份数计数。集合推导的40份FP/FN与逐份盲审结论完全一致；同一多选及其证据问题只计一次。',
    '',
    '| 实际模型 | 精确率 | 召回率 | 明确错标 | 漏标 | 无明确问题 | 两次集合一致 | 平均集合重合率（Jaccard） |',
    '|---|---:|---:|---:|---:|---:|---:|---:|'
]
for m in models:
    lines.append(f"| {m['model']} | {pct(m['micro_precision'])} ({m['acceptable_selected']}/{m['all_selected']}) | {pct(m['micro_recall'])} ({m['covered_required']}/{m['required_opportunities']}) | {m['false_positives']} | {m['false_negatives']} | {m['problem_free_results']}/20 | {m['identical_set_samples']}/10 | {pct(m['mean_jaccard'])} |")
lines.extend(['', '逐篇所选中文标签（①②为同模型的两次独立输出；“两次”表示集合相同）：', '',
              '| 样本与标题 | Sol | Luna | 明确问题 |', '|---|---|---|---|'])
for s in manifest:
    origin = '实验室' if s['lab'] else '外部'
    text = '标题＋摘要' if s['abstract_available'] else '仅标题'
    lines.append(f"| {s['sample_id']} · {origin} · {text}<br>{s['title']} | {pair_labels('gpt-6.1-sol', s['sample_id'])} | {pair_labels('gpt-6-luna', s['sample_id'])} | {issues_for(s['sample_id'])} |")
lines.extend(['',
    '关键判断：S01的共同偏好分布实质建模标签间排序，不能只依词面漏掉标签相关性建模；S07增强样本共关联矩阵实质修正亲和结构，需识别图结构学习。S06仅标题的非负矩阵分解不自动支持低秩建模，Luna一次因此多选。S01多标记排序与偏好分布、S03迭代置信度训练、S09图神经网络与伪标签机制存在定义或文本边界，Astra按可选项处理，未强行计错。',
    '',
    '参考集修订：S01在final新增弱监督学习为必选。原文以主观不一致的多人排序替代单一客观标签排序，且方法专门处理这一条件，符合不精确监督的定义；初审把较窄的噪声标签要求误用于弱监督。修订依据原文与词表，未依据匿名结果投票。reference-initial.json及其原SHA256保留，final记录完整修订；其余必选/可选未变。',
    '',
    '空标签不是自动失败：词表可能没有该研究方向。S05的谱聚类、S08的ELM和S10的ADMM均被本次盲审接受为空集，不能因此视作模型未理解论文。40份结构与连续原文引文校验通过，也不等于全部语义标签正确。',
    '',
    '这些数字只描述本10篇与Astra盲审判断，不构成全量准确率。样本没有大模型类论文，无法据此验证完整49词。建议先澄清多标记排序/偏好分布、迭代训练信号等词表边界，并补强“标签间排序”“亲和矩阵修正”的关键漏标示例；仅有NMF名称时继续要求明确低秩证据。随后增加大模型类及边界样本复核，再决定是否全量标注；本报告不自动启动全量，也不作成本或速度结论。',
    '',
    '复现：运行quality-statistics.py；它先核对冻结输入与40原结果SHA256、initial参考指纹，再逐份对照Astra结论，写metrics.json与本报告。原始标注、production及参考文件不修改。'
])
(ROOT / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'audit_set_consistency': True, 'models': models}, ensure_ascii=False, indent=2))
