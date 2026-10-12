"""Run only after 40 outputs exist. Never modifies annotation content."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def schema_errors(value, rule, path='$'):
    errors = []
    expected = rule.get('type')
    valid_type = (expected is None or
                  expected == 'object' and isinstance(value, dict) or
                  expected == 'array' and isinstance(value, list) or
                  expected == 'string' and isinstance(value, str))
    if not valid_type:
        return [path + ': expected ' + str(expected)]
    if 'enum' in rule and value not in rule['enum']:
        errors.append(path + ': value outside enum')
    if isinstance(value, str):
        import re
        if len(value) < rule.get('minLength', 0):
            errors.append(path + ': string too short')
        if 'pattern' in rule and not re.search(rule['pattern'], value):
            errors.append(path + ': pattern mismatch')
    if isinstance(value, dict):
        props = rule.get('properties', {})
        for key in rule.get('required', []):
            if key not in value:
                errors.append(path + ': missing ' + key)
        if rule.get('additionalProperties') is False:
            for key in set(value) - set(props):
                errors.append(path + ': unknown field ' + key)
        for key in value:
            if key in props:
                errors.extend(schema_errors(value[key], props[key], path + '.' + key))
    if isinstance(value, list) and 'items' in rule:
        for index, item in enumerate(value):
            errors.extend(schema_errors(item, rule['items'], path + '[' + str(index) + ']'))
    return errors

schema = read(ROOT / 'annotation-output.schema.json')
runs = read(ROOT / 'control/run-map.json')['runs']
assert len(runs) == 40
checks = []
for run in runs:
    errors = []
    output = ROOT / run['output_path']
    try:
        result = read(output)
        errors.extend(schema_errors(result, schema))
        if isinstance(result, dict) and result.get('sample_id') != run['sample_id']:
            errors.append('sample_id does not match run assignment')
        if not errors:
            sample = read(ROOT / 'inputs' / (run['sample_id'] + '.json'))
            selected = [a['keyword_id'] for a in result['annotations']]
            abstained = [a['keyword_id'] for a in result['abstentions']]
            if len(selected) != len(set(selected)):
                errors.append('duplicate selected keyword_id')
            if len(abstained) != len(set(abstained)):
                errors.append('duplicate abstention keyword_id')
            if set(selected) & set(abstained):
                errors.append('keyword both selected and abstained')
            for a in result['annotations']:
                source = sample.get(a['evidence_field'])
                if not isinstance(source, str) or a['exact_quote'] not in source:
                    errors.append(a['keyword_id'] + ': exact_quote not continuous substring of evidence_field')
                if not a['reason_zh'].strip() or not a['exact_quote'].strip():
                    errors.append(a['keyword_id'] + ': blank reason or quote')
            for a in result['abstentions']:
                if not a['reason_zh'].strip():
                    errors.append(a['keyword_id'] + ': blank abstention reason')
    except (OSError, ValueError, TypeError) as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    checks.append({'run_id': run['run_id'], 'sample_id': run['sample_id'], 'valid': not errors, 'errors': errors})
report = {'expected_outputs': 40, 'valid_outputs': sum(c['valid'] for c in checks), 'all_valid': all(c['valid'] for c in checks), 'checks': checks, 'annotations_modified': False}
save(ROOT / 'control/validation-report.json', report)
if not report['all_valid']:
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit('Validation failed; no blind files generated and no annotation content repaired.')
for run in runs:
    dest = ROOT / 'blind' / run['sample_id'] / (run['blind_label'] + '.json')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / run['output_path'], dest)
print('Validated 40 outputs; copied unmodified bytes to blind/Sxx/A-D.json.')
