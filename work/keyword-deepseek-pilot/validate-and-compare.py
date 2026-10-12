# coding: utf-8
"""Mechanical validation and fixed-reference comparison. No network, repair or retries."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'keyword-pilot'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# Reuse exactly the old pilot's schema validator without running its file mutations.
validator_source = (OLD / 'validate-and-blind.py').read_text(encoding='utf-8-sig')
validator_node = next(n for n in ast.parse(validator_source).body if isinstance(n, ast.FunctionDef) and n.name == 'schema_errors')
exec(compile(ast.Module(body=[validator_node], type_ignores=[]), '<old-schema-validator>', 'exec'))

schema = read(OLD / 'annotation-output.schema.json')
names = {k['id']: k['canonical_zh'] for k in read(OLD / 'vocabulary-for-annotation.json')['keywords']}
manifest = read(OLD / 'sample-manifest.json')['samples']
refs = {s['sample_id']: s for s in read(OLD / 'audit/reference-final.json')['samples']}
settings = read(ROOT / 'control/run-settings.json')
provenance_checks = []
for item in settings['inputs']:
    path = OLD / 'inputs' / (item['sample_id'] + '.json')
    provenance_checks.append({'path': str(path), 'matches': hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']})
for item in settings['common']:
    path = OLD / item['name']
    provenance_checks.append({'path': str(path), 'matches': hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']})
for item in read(OLD / 'control/frozen-inputs-and-results.json')['files']:
    path = OLD / item['path']
    provenance_checks.append({'path': str(path), 'matches': hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']})
assert all(c['matches'] for c in provenance_checks), 'Frozen material or request input fingerprint differs; stop.'
checks, results = [], []


def validate(path, sample_id):
    errors, result = [], None
    try:
        result = read(path)
        errors.extend(schema_errors(result, schema))
        if isinstance(result, dict) and result.get('sample_id') != sample_id:
            errors.append('sample_id differs from assignment')
        if not errors:
            sample = read(OLD / 'inputs' / (sample_id + '.json'))
            selected = [a['keyword_id'] for a in result['annotations']]
            abstained = [a['keyword_id'] for a in result['abstentions']]
            if len(selected) != len(set(selected)):
                errors.append('duplicate selected keyword_id')
            if len(abstained) != len(set(abstained)):
                errors.append('duplicate abstained keyword_id')
            if set(selected) & set(abstained):
                errors.append('keyword selected and abstained')
            for a in result['annotations']:
                source = sample.get(a['evidence_field'])
                if not isinstance(source, str) or a['exact_quote'] not in source:
                    errors.append(a['keyword_id'] + ': quote not verbatim continuous substring')
                if not a['exact_quote'].strip() or not a['reason_zh'].strip():
                    errors.append(a['keyword_id'] + ': blank quote or reason')
            for a in result['abstentions']:
                if not a['reason_zh'].strip():
                    errors.append(a['keyword_id'] + ': blank abstention reason')
    except (OSError, ValueError, TypeError) as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    return result, errors


def row(result, sample_id, model, replicate, errors):
    required = {a['keyword_id'] for a in refs[sample_id]['required']}
    optional = {a['keyword_id'] for a in refs[sample_id]['optional']}
    selected = {a['keyword_id'] for a in result['annotations']} if not errors else None
    return {'sample_id': sample_id, 'model': model, 'replicate': replicate,
            'valid': not errors, 'errors': errors,
            'selected_ids': sorted(selected) if selected is not None else None,
            'selected_zh': [names[k] for k in sorted(selected)] if selected is not None else None,
            'required_ids': sorted(required), 'optional_ids': sorted(optional),
            'accepted_count': len(selected & (required | optional)) if selected is not None else None,
            'selected_count': len(selected) if selected is not None else None,
            'covered_required_count': len(selected & required) if selected is not None else None,
            'required_opportunities': len(required),
            'false_positive_ids': sorted(selected - required - optional) if selected is not None else None,
            'false_negative_ids': sorted(required - selected) if selected is not None else None}


for sample in manifest:
    sid = sample['sample_id']
    path = ROOT / 'results' / (sid + '.json')
    result, errors = validate(path, sid)
    metadata = read(ROOT / 'control' / (sid + '.metadata.json'))
    checks.append({'sample_id': sid, 'valid': not errors, 'errors': errors,
                   'result_sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                   'returned_model': metadata.get('returned_model'), 'finish_reason': metadata.get('finish_reason')})
    results.append(row(result, sid, metadata.get('returned_model', 'deepseek-flash'), 1, errors))

for run in read(OLD / 'control/run-map.json')['runs']:
    result, errors = validate(OLD / run['output_path'], run['sample_id'])
    results.append(row(result, run['sample_id'], run['model'], run['replicate'], errors))

deep = results[:10]
valid_ids = {r['sample_id'] for r in deep if r['valid']}
validation = {'expected_outputs': 10, 'valid_outputs': len(valid_ids), 'all_valid': len(valid_ids) == 10,
              'checks': checks, 'annotations_modified': False,
              'provenance_checks': provenance_checks, 'provenance_all_matched': True,
              'old_outputs_checked': 40, 'old_outputs_valid': sum(r['valid'] for r in results[10:]),
              'policy': 'Invalid or missing content is not an empty selection; no repair or retry.'}
save(ROOT / 'control/validation-report.json', validation)


def aggregate(model, replicate, scope):
    rows = [r for r in results if r['model'] == model and (replicate is None or r['replicate'] == replicate)
            and (scope == 'all_10' or r['sample_id'] in valid_ids)]
    valid = [r for r in rows if r['valid']]
    accepted = sum(r['accepted_count'] for r in valid)
    selected = sum(r['selected_count'] for r in valid)
    covered = sum(r['covered_required_count'] for r in valid)
    required = sum(r['required_opportunities'] for r in valid)
    return {'model': model, 'replicate': replicate, 'scope': scope, 'expected_results': len(rows),
            'scored_results': len(valid), 'complete_scope': len(valid) == len(rows),
            'acceptable_selected': accepted, 'all_selected': selected,
            'micro_precision': accepted / selected if selected else None,
            'covered_required': covered, 'required_opportunities': required,
            'micro_recall': covered / required if required else None,
            'false_positives': sum(len(r['false_positive_ids']) for r in valid),
            'false_negatives': sum(len(r['false_negative_ids']) for r in valid),
            'zero_set_error_results': sum(not r['false_positive_ids'] and not r['false_negative_ids'] for r in valid)}


models = sorted({r['model'] for r in results})
groups = [aggregate(m, rep, scope) for scope in ['all_10', 'matched_valid_deepseek_samples']
          for m in models for rep in ([1] if m == 'deepseek-flash' else [None, 1, 2])]
metadata = [read(ROOT / 'control' / (s['sample_id'] + '.metadata.json')) for s in manifest]
failed_attempts = [read(p) for p in sorted((ROOT / 'attempts').glob('*.metadata.json'))]
all_attempts = metadata + failed_attempts
usage_keys = ['prompt_tokens', 'completion_tokens', 'total_tokens']
usage = {k: sum(m.get('usage', {}).get(k, 0) for m in all_attempts) for k in usage_keys}
usage['reasoning_tokens'] = sum(m.get('usage', {}).get('completion_tokens_details', {}).get('reasoning_tokens', 0) for m in all_attempts)
usage['failed_attempt_usage'] = {k: sum(m.get('usage', {}).get(k, 0) for m in failed_attempts) for k in usage_keys}
usage['attempt_count'] = len(all_attempts)
usage['successful_annotation_count'] = len(valid_ids)
usage['per_attempt_metadata'] = all_attempts
usage['retry_settings'] = read(ROOT / 'control/retry-settings.json') if (ROOT / 'control/retry-settings.json').exists() else None
durations = [m['duration_ms'] for m in all_attempts if isinstance(m.get('duration_ms'), (int, float))]
usage.update({'duration_ms_min': min(durations) if durations else None,
              'duration_ms_max': max(durations) if durations else None,
              'duration_ms_mean': sum(durations) / len(durations) if durations else None,
              'batch_wall_time_ms': read(ROOT / 'control/request-summary.json').get('wall_time_ms')})
sol_audit = read(ROOT / 'audit/sol-audit.json')
sol_refs = {s['sample_id']: s for s in read(ROOT / 'audit/sol-reference-final.json')['samples']}
sol_checked = []
reference_differences = []
for sample in sol_audit['samples']:
    sid = sample['sample_id']
    selected = set(next(r for r in deep if r['sample_id'] == sid)['selected_ids'])
    required = {a['keyword_id'] for a in sol_refs[sid]['required']}
    optional = {a['keyword_id'] for a in sol_refs[sid]['optional']}
    audit_fp = {a['keyword_id'] if isinstance(a, dict) else a for a in sample['false_positives']}
    audit_fn = {a['keyword_id'] if isinstance(a, dict) else a for a in sample['false_negatives']}
    assert selected == set(sample['selected_ids'])
    assert selected - required - optional == audit_fp and required - selected == audit_fn
    sol_checked.append({'sample_id': sid, 'false_positive_ids': sorted(audit_fp),
                        'false_negative_ids': sorted(audit_fn), 'evidence_issues': sample['evidence_issues'],
                        'abstention_issues': sample['abstention_issues']})
    for field in ['required', 'optional']:
        old_set = {a['keyword_id'] for a in refs[sid][field]}
        new_set = {a['keyword_id'] for a in sol_refs[sid][field]}
        if old_set != new_set:
            reference_differences.append({'sample_id': sid, 'field': field,
                                          'old_astra': sorted(old_set), 'new_sol': sorted(new_set)})
assert sum(len(s['false_positive_ids']) for s in sol_checked) == sol_audit['summary']['false_positive_count']
assert sum(len(s['false_negative_ids']) for s in sol_checked) == sol_audit['summary']['false_negative_count']
assert sum(len(s['evidence_issues']) for s in sol_checked) == sol_audit['summary']['evidence_issue_count']
metrics = {'reference': 'Unchanged old Astra reference-final required + optional',
           'reference_sha256': hashlib.sha256((OLD / 'audit/reference-final.json').read_bytes()).hexdigest(),
           'precision_definition': 'acceptable selected / all selected (micro)',
           'recall_definition': 'covered required / required opportunities (micro); optional omission not FN',
           'invalid_policy': 'Not an empty set; unscored. Partial metrics explicitly scoped; no 10-sample DeepSeek quality claim.',
           'empty_selection_policy': 'Evaluate fixed reference, never automatically fail',
           'valid_deepseek_sample_ids': sorted(valid_ids), 'settings': settings,
           'deepseek_usage': usage, 'groups': groups, 'results': results,
           'semantic_review': {'reviewer': 'gpt-6.1-sol', 'scope': 'DeepSeek only; separate from primary fixed-Astra comparison',
                               'summary': sol_audit['summary'], 'results': sol_checked,
                               'reference_differences': reference_differences,
                               'initial_reference_sha256': hashlib.sha256((ROOT / 'audit/sol-reference-initial.json').read_bytes()).hexdigest(),
                               'final_reference_sha256': hashlib.sha256((ROOT / 'audit/sol-reference-final.json').read_bytes()).hexdigest(),
                               'audit_set_consistency': True},
           'deepseek_repeatability': None}
save(ROOT / 'metrics.json', metrics)


def pct(v):
    return f'{v:.1%}' if v is not None else '无分母'


def label(r):
    return '输出无效，未评分' if not r['valid'] else ('、'.join(r['selected_zh']) or '空集')


def issues(r):
    if not r['valid']:
        return '未评分'
    parts = []
    for key, title in [('false_positive_ids', '多选'), ('false_negative_ids', '漏选')]:
        if r[key]:
            parts.append(title + '、'.join(names[k] for k in r[key]))
    return '；'.join(parts) or 'FP/FN均为0'


lines = ['DeepSeek V4.1 Flash对原10篇独立请求，API实际返回模型名均为deepseek-flash；thinking=enabled、reasoning_effort=high，初轮max_tokens=8192、并发10。旧Sol/Luna各有2×10份独立结果。', '',
         f'最终{len(valid_ids)}/10通过结构和逐字连续原文引文检查。主比较表统一采用旧Astra final固定必选＋可选参照：精确率＝可接受已选/全部已选；召回率＝覆盖必选/必选机会（micro）。可选遗漏不算漏；结构有效不等于语义正确。', '',
         '| 范围 | 模型/重复 | 有效/请求 | 精确率 | 召回率 | FP | FN |', '|---|---|---:|---:|---:|---:|---:|']
for g in groups:
    if len(valid_ids) == 10 and g['scope'] == 'matched_valid_deepseek_samples':
        continue
    scope = '10篇' if g['scope'] == 'all_10' else f'共同可评{len(valid_ids)}篇'
    repeat = '两次汇总' if g['replicate'] is None else '重复' + str(g['replicate'])
    lines.append(f"| {scope} | {g['model']} / {repeat} | {g['scored_results']}/{g['expected_results']} | {pct(g['micro_precision'])} ({g['acceptable_selected']}/{g['all_selected']}) | {pct(g['micro_recall'])} ({g['covered_required']}/{g['required_opportunities']}) | {g['false_positives']} | {g['false_negatives']} |")
lines.extend(['', '逐篇所选标签及相对固定参照差异（①②为旧模型重复；差异只列机械FP/FN）：', '',
              '| 样本/标题 | DeepSeek | Sol①；② | Luna①；② | 差异 |', '|---|---|---|---|---|'])
for s in manifest:
    sid = s['sample_id']
    ds = next(r for r in deep if r['sample_id'] == sid)
    old = {m: sorted([r for r in results[10:] if r['sample_id'] == sid and r['model'] == m], key=lambda r: r['replicate']) for m in ['gpt-6.1-sol', 'gpt-6-luna']}
    texts = ['①' + label(old[m][0]) + '；②' + label(old[m][1]) for m in ['gpt-6.1-sol', 'gpt-6-luna']]
    diffs = ['DeepSeek：' + issues(ds)]
    for m, short in [('gpt-6.1-sol', 'Sol'), ('gpt-6-luna', 'Luna')]:
        diffs += [short + str(r['replicate']) + '：' + issues(r) for r in old[m] if r['false_positive_ids'] or r['false_negative_ids']]
    lines.append(f"| {sid} {s['title']} | {label(ds)} | {texts[0]} | {texts[1]} | {'；'.join(diffs)} |")
lines.extend(['',
              '新增gpt-6.1-sol独立审阅（仅DeepSeek，单独参照，不替换主表旧Astra）：FP 0、FN 1（S03弱监督）；证据/理由问题3处：S01标签相关性引用既有方法的背景假设，S09图神经网络引用GCN背景，S09深度聚类理由额外推断本文使用GCN。15处quote均逐字连续合法。S03弃权误用未声明的父子关系，与漏标同根，不重复计数。', '',
              '审阅分歧须保留：旧Astra把S10稀疏表示视为多选，新Sol初参照也为空，final因basis pursuit明确表示稀疏基系数，且本文实质综述ADMM应用，将其新增为必选。该修订与证据已留存，未改旧参照；因此主表仍报S10 FP，而新增审阅不报此FP。其他边界：S01弱监督由旧必选变新可选，S02图像分割、S06低秩、S09对比学习在新参照为可选；S03伪标签自训练由旧可选变新不接受。这些是两位审阅者的定义/文本边界差异，不按对DeepSeek有利的参照筛选分数。', '',
              f"初轮7/10成功生成标注，S01/S02/S03在8192预算下reasoning耗尽上限且无标注，作为技术失败保留，不能记成空标签或模型错标。仅对这3篇提高预算到32768技术重试，thinking/high不变，已完成7篇不重跑；总API尝试{usage['attempt_count']}次，每篇仅1份成功标注。", '',
              f"DeepSeek全部实际尝试usage（含技术失败）：prompt {usage['prompt_tokens']}、completion {usage['completion_tokens']}（其中reasoning {usage['reasoning_tokens']}）、total {usage['total_tokens']} tokens。技术失败消耗total {usage['failed_attempt_usage']['total_tokens']} tokens。初轮并发整批墙钟{usage['batch_wall_time_ms']/1000:.3f}秒；全部尝试每请求{usage['duration_ms_min']/1000:.3f}–{usage['duration_ms_max']/1000:.3f}秒，均值{usage['duration_ms_mean']/1000:.3f}秒。最终单篇预算不同，不能作为统一耗时benchmark；无旧模型同口径时长，不作速度或成本比较。DeepSeek无第二次成功重复，不报重复一致性。", '',
              '本10篇按同一旧Astra口径，DeepSeek漏标少于Luna（1/13与4/26必选机会），多选稀疏表示存在审阅分歧，另有3处证据/理由问题需复核。不能由这10篇外推完整49词的准确率。原始标签、旧参照与生产文件未修改。'])
(ROOT / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'valid_deepseek': len(valid_ids), 'groups': [g for g in groups if g['scope'] == 'all_10'],
                  'total_tokens_all_attempts': usage['total_tokens'], 'attempt_count': usage['attempt_count']}, ensure_ascii=False, indent=2))
