"""Control-only repeatability and byte fingerprints; never opens audit/ or repairs outputs."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def fingerprint(relative):
    contents = (ROOT / relative).read_bytes()
    return {'path': relative, 'sha256': hashlib.sha256(contents).hexdigest(), 'bytes': len(contents)}


def save(relative, value):
    (ROOT / relative).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


runs = read('control/run-map.json')['runs']
assert len(runs) == 40, 'Expected 40 formal independent-agent outputs'
assert len({r['run_id'] for r in runs}) == 40
assert len({r['output_path'] for r in runs}) == 40
samples = sorted({r['sample_id'] for r in runs})
models = sorted({r['model'] for r in runs})
assert samples == [f'S{i:02}' for i in range(1, 11)], 'Expected S01-S10'
assert len(models) == 2, 'Expected two models'
assert {p.name for p in (ROOT / 'inputs').glob('*.json')} == {s + '.json' for s in samples}
assert {p.name for p in (ROOT / 'results').glob('run*.json')} == {Path(r['output_path']).name for r in runs}, 'Missing or unexpected formal output'
shared = ['annotation-instructions.txt', 'vocabulary-for-annotation.json', 'annotation-output.schema.json']
files = [fingerprint('inputs/' + s + '.json') for s in samples]
files.extend(fingerprint(relative) for relative in shared)
files.extend(fingerprint(r['output_path']) for r in runs)
files.append(fingerprint('control/run-map.json'))
hashes = {f['path']: f['sha256'] for f in files}
freeze_path = ROOT / 'control/frozen-inputs-and-results.json'
if freeze_path.exists():
    previous = read('control/frozen-inputs-and-results.json')
    assert {f['path']: f['sha256'] for f in previous['files']} == hashes, 'Frozen input or result changed; original freeze retained'

grouped = defaultdict(dict)
per_run_inputs = []
for run in runs:
    key = (run['model'], run['sample_id'])
    replicate = run['replicate']
    assert replicate in (1, 2) and replicate not in grouped[key]
    result = read(run['output_path'])
    assert result['sample_id'] == run['sample_id']
    keywords = [a['keyword_id'] for a in result['annotations']]
    assert len(keywords) == len(set(keywords)), 'Duplicate keyword in ' + run['run_id']
    grouped[key][replicate] = set(keywords)
    input_path = 'inputs/' + run['sample_id'] + '.json'
    per_run_inputs.append({'run_id': run['run_id'], 'model': run['model'], 'replicate': replicate,
                           'sample_id': run['sample_id'], 'input_path': input_path,
                           'input_sha256': hashes[input_path],
                           'shared_files': {relative: hashes[relative] for relative in shared}})

report_models = []
for model in models:
    items = []
    for sample in samples:
        pair = grouped[(model, sample)]
        assert set(pair) == {1, 2}, 'Missing replicate: ' + model + ' ' + sample
        first, second = pair[1], pair[2]
        union, intersection = first | second, first & second
        items.append({'sample_id': sample, 'identical_keyword_sets': first == second,
                      'replicate1_keyword_count': len(first), 'replicate2_keyword_count': len(second),
                      'intersection_count': len(intersection), 'union_count': len(union),
                      'jaccard': len(intersection) / len(union) if union else 1.0})
    report_models.append({'model': model, 'sample_count': len(items),
                          'identical_set_samples': sum(i['identical_keyword_sets'] for i in items),
                          'mean_jaccard': sum(i['jaccard'] for i in items) / len(items), 'items': items})

for sample in samples:
    assignments = [r for r in per_run_inputs if r['sample_id'] == sample]
    assert len(assignments) == 4
    assert len({r['input_sha256'] for r in assignments}) == 1
    assert all(r['shared_files'] == assignments[0]['shared_files'] for r in assignments)

repeatability = {'formal_result_count': 40, 'input_count': 10,
                 'set_definition': 'Selected annotations.keyword_id; abstentions excluded; order ignored',
                 'jaccard_definition': '|intersection| / |union|; empty/empty = 1',
                 'mean_definition': 'Unweighted mean across 10 samples', 'models': report_models,
                 'semantic_quality_evaluated': False, 'failed_cli_probes_included': False}
frozen = {'algorithm': 'SHA256 over exact file bytes', 'input_count': 10, 'result_count': 40,
          'shared_input_files': shared, 'files': files, 'per_run_shared_inputs': per_run_inputs,
          'same_current_inputs_for_each_model_and_replicate': True,
          'verification_scope': 'Shared assigned input paths and current byte fingerprints; historical agent read events are not independently replayed',
          'annotations_modified': False, 'failed_cli_probes_included': False}
save('control/repeatability.json', repeatability)
save('control/frozen-inputs-and-results.json', frozen)
print(json.dumps({'formal_results': 40, 'same_shared_inputs': True,
                  'models': [{k: model[k] for k in ['model', 'identical_set_samples', 'sample_count', 'mean_jaccard']} for model in report_models]}, ensure_ascii=False, indent=2))
