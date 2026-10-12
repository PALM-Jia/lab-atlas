import json
import random
import unicodedata
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
OUT = PROJECT / 'work' / 'keyword-pilot'
if (OUT / 'results').exists() and any((OUT / 'results').glob('*.json')):
    raise SystemExit('Inputs are frozen: annotation results exist. Refusing to overwrite experiment inputs or run map.')
vocabulary = json.loads((PROJECT / 'work/keyword-vocabulary/vocabulary.json').read_text(encoding='utf-8-sig'))
corpus = json.loads((PROJECT / 'work/abstract-backfill/all-papers-with-abstracts.json').read_text(encoding='utf-8-sig'))
rng = random.Random(20261012)

def usable_abstract(paper):
    value = paper.get('abstract')
    return isinstance(value, str) and bool(value.strip()) and paper.get('quality') in ('existing_abstract_not_individually_reverified', 'source_abstract_verified_title_and_identifier')

def normalized_title(paper):
    return ''.join(c for c in unicodedata.normalize('NFKC', paper['title']).casefold() if c.isalnum())

internal_titles = {normalized_title(p) for p in corpus['papers'] if p['lab'] is True}
excluded_external_duplicates = [p for p in corpus['papers'] if p['lab'] is False and normalized_title(p) in internal_titles]
eligible = [p for p in corpus['papers'] if p['lab'] is True or normalized_title(p) not in internal_titles]

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

selected = []
strata = []
for lab in (True, False):
    for has_abstract, count in ((True, 4), (False, 1)):
        pool = sorted((p for p in eligible if p['lab'] is lab and usable_abstract(p) is has_abstract), key=lambda p: p['id'])
        assert len(pool) >= count
        selected.extend(rng.sample(pool, count))
        strata.append({'lab': lab, 'abstract_available': has_abstract, 'population': len(pool), 'sample_count': count})
rng.shuffle(selected)
assert len({normalized_title(p) for p in selected}) == 10, 'Sampled titles must be unique'
(OUT / 'inputs').mkdir(parents=True, exist_ok=True)
manifest = []
for i, paper in enumerate(selected, 1):
    sample_id = 'S%02d' % i
    abstract = paper['abstract'] if usable_abstract(paper) else None
    save(OUT / 'inputs' / (sample_id + '.json'), {'sample_id': sample_id, 'title': paper['title'], 'abstract': abstract})
    manifest.append({'sample_id': sample_id, 'paper_id': paper['id'], 'title': paper['title'], 'lab': paper['lab'], 'abstract_available': abstract is not None})
save(OUT / 'sample-manifest.json', {'seed': 20261012, 'frozen': True, 'sampling': 'Python random.Random; fixed stratum order lab-with-abstract, lab-title-only, external-with-abstract, external-title-only; pools sorted by paper id; sample then shuffle', 'abstract_availability_rule': 'Current all-papers-with-abstracts abstract is nonempty and quality is existing_abstract_not_individually_reverified or source_abstract_verified_title_and_identifier; vocabulary metadata does not determine availability', 'external_duplicate_exclusion': {'normalization': 'Unicode NFKC then casefold, keep alphanumeric characters only; external normalized title identical to any internal title is excluded', 'count': len(excluded_external_duplicates), 'with_abstract': sum(usable_abstract(p) for p in excluded_external_duplicates), 'title_only': sum(not usable_abstract(p) for p in excluded_external_duplicates)}, 'strata': strata, 'samples': manifest})
fields = ('id', 'canonical_en', 'canonical_zh', 'definition_zh', 'aliases', 'primary_dimension', 'parent_id')
clean_keywords = [{key: item[key] for key in fields} for item in vocabulary['keywords']]
assert len(clean_keywords) == 49
save(OUT / 'vocabulary-for-annotation.json', {'keyword_count': 49, 'keywords': clean_keywords})
schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object', 'additionalProperties': False,
    'required': ['sample_id', 'annotations', 'abstentions'],
    'properties': {
        'sample_id': {'type': 'string', 'pattern': '^S(0[1-9]|10)$'},
        'annotations': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False,
            'required': ['keyword_id', 'exact_quote', 'evidence_field', 'reason_zh'],
            'properties': {
                'keyword_id': {'type': 'string', 'enum': [k['id'] for k in clean_keywords]},
                'exact_quote': {'type': 'string', 'minLength': 1},
                'evidence_field': {'enum': ['title', 'abstract']},
                'reason_zh': {'type': 'string', 'minLength': 1}
            }}},
        'abstentions': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False,
            'required': ['keyword_id', 'reason_zh'],
            'properties': {
                'keyword_id': {'type': 'string', 'enum': [k['id'] for k in clean_keywords]},
                'reason_zh': {'type': 'string', 'minLength': 1}
            }}}
    }
}
save(OUT / 'annotation-output.schema.json', schema)
(OUT / 'control').mkdir(exist_ok=True)
(OUT / 'results').mkdir(exist_ok=True)
map_rng = random.Random(20261012)
runs = []
for sample in manifest:
    labels = list('ABCD')
    map_rng.shuffle(labels)
    for (model, replicate), label in zip([('gpt-6.1-sol', 1), ('gpt-6.1-sol', 2), ('gpt-6-luna', 1), ('gpt-6-luna', 2)], labels):
        run_id = 'run%03d' % (len(runs) + 1)
        runs.append({'sample_id': sample['sample_id'], 'model': model, 'replicate': replicate, 'run_id': run_id, 'blind_label': label, 'output_path': 'results/' + run_id + '.json'})
save(OUT / 'control/run-map.json', {'seed': 20261012, 'blind_assignment': 'Independent random.Random(20261012); shuffle A-D separately in sample_id order; fixed model/replicate order', 'runs': runs})
print(json.dumps({'strata': strata, 'samples': [{'sample_id': p['sample_id'], 'title': p['title']} for p in manifest]}, ensure_ascii=False, indent=2))
