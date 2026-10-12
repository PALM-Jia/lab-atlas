"""Synthetic mechanical checks; all result fixtures live in temporary directories."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('keyword_validator', ROOT / 'validate.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
sys.path.insert(0, str(ROOT))
assembler_spec = importlib.util.spec_from_file_location('keyword_assembler', ROOT / 'assemble-reviewed.py')
assembler = importlib.util.module_from_spec(assembler_spec)
assembler_spec.loader.exec_module(assembler)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.schema = validator.read_json(ROOT / 'output.schema.json')
        self.review_schema = validator.read_json(ROOT / 'review-output.schema.json')
        self.vocab = validator.read_json(ROOT / 'vocabulary.json')
        self.keywords = {x['id']: x for x in self.vocab['keywords']}
        self.pid = 'synthetic-fixture-paper'
        self.paper = {'paper_id': self.pid, 'title': 'Deep clustering for images', 'abstract': None}
        self.empty = {'paper_id': self.pid, 'annotations': [], 'abstentions': [], 'input_issues': []}
        self.chosen = copy.deepcopy(self.empty)
        self.chosen['annotations'] = [{'keyword_id': 'deep-clustering', 'exact_quote': 'Deep clustering',
                                      'evidence_field': 'title', 'reason_zh': '标题明确提及。'}]

    def check(self, record):
        return validator.validate_record(record, self.paper, self.keywords, self.schema)

    def test_empty_and_chosen(self):
        self.assertEqual([], self.check(self.empty))
        self.assertEqual([], self.check(self.chosen))

    def test_bad_quotes(self):
        for quote, field in [('Deep images', 'title'), ('Deep clustering', 'abstract'), (' ', 'title')]:
            record = copy.deepcopy(self.chosen)
            record['annotations'][0].update(exact_quote=quote, evidence_field=field)
            self.assertTrue(self.check(record))

    def test_fields_and_types(self):
        for change in [{'unexpected': 1}, {'input_issues': 'oops'}, {'input_issues': [3]},
                       {'annotations': {}}, {'paper_id': 3}]:
            record = dict(self.empty, **change)
            self.assertTrue(self.check(record))
        record = copy.deepcopy(self.chosen)
        record['annotations'][0]['reason_zh'] = ' '
        self.assertTrue(self.check(record))
        record = copy.deepcopy(self.chosen)
        record['annotations'][0]['extra'] = 'forbidden'
        self.assertTrue(self.check(record))

    def test_unknown_duplicate_overlap_and_parent(self):
        record = copy.deepcopy(self.chosen)
        record['annotations'][0]['keyword_id'] = 'unknown'
        self.assertTrue(self.check(record))
        record = copy.deepcopy(self.empty)
        record['abstentions'] = [{'keyword_id': 'deep-clustering', 'reason_zh': '不足'}] * 2
        self.assertTrue(self.check(record))
        record = copy.deepcopy(self.chosen)
        record['annotations'] *= 2
        self.assertTrue(self.check(record))
        record = copy.deepcopy(self.chosen)
        record['abstentions'] = [{'keyword_id': 'deep-clustering', 'reason_zh': '不足'}]
        self.assertTrue(self.check(record))
        child = next(x for x in self.vocab['keywords'] if x['parent_id'])
        record = copy.deepcopy(self.chosen)
        record['annotations'] = [dict(record['annotations'][0], keyword_id=k)
                                 for k in (child['id'], child['parent_id'])]
        self.assertTrue(self.check(record))

    def fixture(self, path):
        def put(name, value):
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')
        put('output.schema.json', self.schema)
        put('review-output.schema.json', self.review_schema)
        put('vocabulary.json', self.vocab)
        put('inputs/batch-001.json', {'papers': [self.paper]})
        put('control/manifest.json', {'synthetic_test_fixture': True})
        for name in ['annotation-instructions.txt', 'worker-task-template.txt', 'review-instructions.txt', 'reviewer-task-template.txt']:
            (path / name).write_text('Synthetic fixture only.\n', encoding='utf-8')
        hashes = {x.relative_to(path).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest()
                  for x in path.rglob('*') if x.is_file()}
        put('control/fingerprints.json', {'prepared_files': hashes, 'source_files': {}})
        return put

    def test_run_states_and_duplicate_extra_results(self):
        with tempfile.TemporaryDirectory(prefix='keyword-validator-fixture-') as temp:
            path = Path(temp)
            put = self.fixture(path)
            report = validator.validate(path)
            self.assertEqual('prepared_not_started', report['state'])
            self.assertEqual([self.pid], report['retry']['missing_ids'])
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'validate.py'), '--root', str(path), '--require-complete'], capture_output=True)
            self.assertNotEqual(0, run.returncode)
            put('results/' + self.pid + '.json', self.empty)
            self.assertTrue(validator.validate(path)['complete'])
            flagged = dict(self.empty, input_issues=['缺少摘要，需人工核验。'])
            put('results/' + self.pid + '.json', flagged)
            report = validator.validate(path)
            self.assertEqual([self.pid], report['flag_for_review_ids'])
            self.assertFalse(report['complete'])
            self.assertEqual([], report['retry']['paper_ids'])
            put('results/duplicate.json', self.empty)
            put('results/extra.json', dict(self.empty, paper_id='unknown-paper'))
            report = validator.validate(path)
            self.assertEqual([self.pid], report['retry']['invalid_ids'])
            self.assertEqual(['unknown-paper'], report['unknown_result_ids'])
            (path / 'inputs/batch-001.json').write_text('{}', encoding='utf-8')
            self.assertTrue(validator.check_fingerprints(path)['errors'])

    def issue(self, kid='deep-clustering', kind='false_negative', quote='Deep clustering', field='title'):
        return {'kind': kind, 'keyword_id': kid, 'reason_zh': '标题提供明确证据。',
                'exact_quote': quote, 'evidence_field': field}

    def review(self, verdict='pass', issues=None, patch=None):
        return {'paper_id': self.pid, 'verdict': verdict, 'issues': issues or [], 'patch': patch}

    def check_review(self, review, raw=None):
        return validator.validate_review(review, raw or self.empty, self.paper, self.keywords, self.schema, self.review_schema)

    def add_patch(self):
        return {'remove_ids': [], 'upsert_annotations': copy.deepcopy(self.chosen['annotations']),
                'abstentions': [], 'input_issues': []}

    def test_valid_pass_and_patch(self):
        errors, candidate = self.check_review(self.review())
        self.assertEqual([], errors)
        self.assertEqual(self.empty, candidate)
        errors, candidate = self.check_review(self.review('revise', [self.issue()], self.add_patch()))
        self.assertEqual([], errors)
        self.assertEqual(self.chosen, candidate)
        self.assertEqual([], self.empty['annotations'])

    def test_review_invalid_and_needs_review(self):
        errors, candidate = self.check_review(self.review('needs_review', [self.issue()]))
        self.assertEqual([], errors)
        self.assertIsNone(candidate)
        for review in [self.review('pass', [self.issue()]),
                       self.review('revise', [], self.add_patch()),
                       self.review('revise', [self.issue(quote='Deep images')], self.add_patch()),
                       self.review('revise', [self.issue(kid='unknown')], self.add_patch()),
                       self.review('pass', patch=self.add_patch())]:
            self.assertTrue(self.check_review(review)[0])
        patch = self.add_patch()
        patch['upsert_annotations'][0]['exact_quote'] = 'Deep images'
        self.assertTrue(self.check_review(self.review('revise', [self.issue()], patch))[0])
        patch = self.add_patch()
        patch['remove_ids'] = ['contrastive-learning']
        self.assertTrue(self.check_review(self.review('revise', [self.issue()], patch))[0])
        self.assertTrue(self.check_review(self.review('revise', [self.issue(kid='contrastive-learning')], self.add_patch()))[0])

    def test_input_issues_need_supported_change(self):
        raw = dict(self.empty, input_issues=['模型错误地声称标题缺失。'])
        patch = {'remove_ids': [], 'upsert_annotations': [], 'abstentions': [], 'input_issues': []}
        self.assertTrue(self.check_review(self.review('revise', [self.issue()], patch), raw)[0])
        unsupported = self.issue(kid=None, kind='input_problem', quote='', field=None)
        self.assertTrue(self.check_review(self.review('revise', [unsupported], patch), raw)[0])
        supported = self.issue(kid=None, kind='input_problem')
        self.assertEqual([], self.check_review(self.review('revise', [supported], patch), raw)[0])

    def test_review_statuses_and_partial_assembly(self):
        with tempfile.TemporaryDirectory(prefix='keyword-review-fixture-') as temp:
            path = Path(temp)
            put = self.fixture(path)
            put('results/' + self.pid + '.json', self.empty)
            report = validator.validate(path)
            self.assertTrue(report['complete'])
            self.assertFalse(report['review_complete'])
            self.assertEqual(1, report['review_counts']['review_pending'])
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'validate.py'), '--root', str(path), '--require-reviewed'], capture_output=True)
            self.assertNotEqual(0, run.returncode)
            raw_bytes = (path / 'results' / (self.pid + '.json')).read_bytes()
            put('reviews/' + self.pid + '.json', self.review('revise', [self.issue()], self.add_patch()))
            review_bytes = (path / 'reviews' / (self.pid + '.json')).read_bytes()
            summary = assembler.assemble(path)
            self.assertTrue(summary['review_complete'])
            self.assertEqual(1, summary['accepted_count'])
            self.assertEqual(1, sum(summary['review_counts'].values()))
            self.assertEqual(self.chosen, validator.read_json(path / 'accepted' / (self.pid + '.json')))
            self.assertEqual(1, next(x for x in summary['keyword_counts'] if x['keyword_id'] == 'deep-clustering')['selected_count'])
            self.assertEqual(raw_bytes, (path / 'results' / (self.pid + '.json')).read_bytes())
            self.assertEqual(review_bytes, (path / 'reviews' / (self.pid + '.json')).read_bytes())
            put('reviews/' + self.pid + '.json', self.review('needs_review', [self.issue()]))
            summary = assembler.assemble(path)
            self.assertFalse(summary['review_complete'])
            self.assertEqual(0, summary['accepted_count'])
            self.assertFalse((path / 'accepted' / (self.pid + '.json')).exists())
            self.assertEqual(1, summary['review_counts']['review_needs_review'])
            put('reviews/unknown.json', dict(self.review(), paper_id='unknown'))
            self.assertEqual(['unknown'], validator.validate(path)['unknown_review_ids'])

    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory(prefix='keyword-validator-fixture-') as temp:
            path = Path(temp) / 'duplicate.json'
            path.write_text('{"paper_id":"a","paper_id":"b"}', encoding='utf-8')
            with self.assertRaises(ValueError):
                validator.read_json(path)

    def test_corrupt_known_file_is_invalid_not_missing(self):
        with tempfile.TemporaryDirectory(prefix='keyword-validator-fixture-') as temp:
            path = Path(temp)
            put = self.fixture(path)
            destination = path / 'results' / (self.pid + '.json')
            destination.parent.mkdir(parents=True)
            for text in ['{bad json', '{}', '{"paper_id":3}', json.dumps(dict(self.empty, paper_id='unknown-paper'))]:
                destination.write_text(text, encoding='utf-8')
                report = validator.validate(path)
                self.assertEqual([self.pid], report['retry']['invalid_ids'])
                self.assertEqual([], report['retry']['missing_ids'])
                self.assertEqual(1, report['counts']['invalid'])
                self.assertTrue(report['file_errors'])


if __name__ == '__main__':
    unittest.main()
