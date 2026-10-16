"""Boundary tests for resume, annotation evidence and author weighting."""
import tempfile
import unittest
from pathlib import Path
from derived import reuse_one, anchor, annotation, profiles, people
from pipeline import save, read
from run import Steps


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.paper = {'title': 'Graph learning', 'abstract': 'We learn robust graphs.'}
        self.previous = dict(self.paper)
        self.accepted = {'annotations': [{'keyword_id': 'graph', 'evidence_field': 'title', 'exact_quote': 'Graph learning'}]}

    def test_exact(self):
        value, reason = reuse_one(self.paper, self.previous, self.accepted, True, {'graph'})
        self.assertEqual(reason, 'exact_input_reuse')
        self.assertEqual(value['keyword_ids'], ['graph'])

    def test_text_change_despite_valid_quote(self):
        self.paper['abstract'] = 'A completely different task using the same title.'
        value, reason = reuse_one(self.paper, self.previous, self.accepted, True, {'graph'})
        self.assertIsNone(value)
        self.assertEqual(reason, 'title_or_abstract_changed')

    def test_format_reanchors_literal_quote(self):
        self.paper['title'] = 'GRAPH   learning'
        value, reason = reuse_one(self.paper, self.previous, self.accepted, True, {'graph'})
        self.assertEqual(reason, 'format_only_reanchored')
        self.assertEqual(value['evidence'][0]['quote'], 'GRAPH   learning')

    def test_invalid_quote(self):
        self.accepted['annotations'][0]['exact_quote'] = 'Invented graph evidence'
        self.assertIsNone(reuse_one(self.paper, self.previous, self.accepted, True, {'graph'})[0])

    def test_vocab_change(self):
        self.assertEqual(reuse_one(self.paper, self.previous, self.accepted, False, {'graph'})[1], 'vocabulary_changed')

    def test_accepted_empty_is_complete(self):
        value, _ = reuse_one(self.paper, self.previous, {'annotations': []}, True, {'graph'})
        self.assertIsNotNone(value)
        self.assertEqual(value['keyword_ids'], [])

    def test_missing_old_acceptance_is_pending(self):
        self.assertEqual(reuse_one(self.paper, self.previous, None, True, {'graph'})[1], 'previous_annotation_not_accepted')

    def test_ligature_and_whitespace(self):
        self.assertEqual(anchor('The \ufb01rst\n\n study', 'the first study'), 'The \ufb01rst\n\n study')
        self.assertIsNone(anchor('science', ''))

    def test_background_quote_not_mechanical_semantic_pass(self):
        # Semantic relevance remains the annotation task's responsibility;
        # the importer must still reject nonexistent/unknown IDs mechanically.
        with self.assertRaises(AssertionError):
            annotation(self.paper, {'keyword_ids': ['invented'], 'evidence': []}, {'graph'})


class ResumeTests(unittest.TestCase):
    def test_reuse_changed_input_and_corrupted_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            source, output = path / 'input.txt', path / 'output.txt'
            source.write_text('one')
            step = Steps(path / 'state.json')
            def action(): output.write_text(source.read_text())
            self.assertTrue(step.run('x', [source], [output], action))
            self.assertFalse(step.run('x', [source], [output], action))
            source.write_text('two')
            self.assertTrue(step.run('x', [source], [output], action))
            output.write_text('corrupted')
            self.assertTrue(step.run('x', [source], [output], action))

    def test_failed_step_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            step = Steps(path / 'state.json')
            def fail(): raise RuntimeError('expected')
            with self.assertRaises(RuntimeError): step.run('x', [], [path / 'missing'], fail)
            self.assertEqual(read(path / 'state.json')['steps']['x']['state'], 'failed')


class ProfileTests(unittest.TestCase):
    def test_unique_database_identity_needs_no_manual_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            save(output / '05-feature-inputs.json', {'papers': [{'id': 'a', 'lab': True, 'authors': ['Author']}]})
            save(output / '05-keywords.json', {'papers': [{'paper_id': 'a', 'state': 'ready', 'keyword_ids': ['k']}]})
            save(output / '02-persons.json', {'rows': [{'paper_id': 'a', 'position': 1, 'name': 'Author', 'group': 'other',
                 'resolved_person_id': 'A1', 'resolution': 'database_author_id', 'occurrence_id': 'a:1'}]})
            save(output / '02-person-review-queue.json', {'rows': []})
            profiles(output)
            p = read(output / '05-author-profiles.json')['profiles'][0]
            self.assertEqual(p['state'], 'ready')
            self.assertEqual(p['identity_state'], 'database_identifier')

    def test_weights_duplicate_dedup_and_missing_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            save(output / '05-feature-inputs.json', {'papers': [
                {'id': 'a', 'lab': True, 'authors': ['Yuheng Jia', 'Student']},
                {'id': 'b', 'lab': True, 'authors': ['Other', 'Student']},
                {'id': 'c', 'lab': True, 'authors': ['Student']},
                {'id': 'd', 'lab': True, 'authors': ['Student']}]})
            save(output / '05-keywords.json', {'papers': [
                {'paper_id': 'a', 'state': 'ready', 'keyword_ids': ['k']},
                {'paper_id': 'b', 'state': 'ready', 'keyword_ids': []},
                {'paper_id': 'c', 'state': 'not_generated', 'keyword_ids': []},
                {'paper_id': 'd', 'state': 'ready', 'keyword_ids': []}]})
            rows = [{'paper_id': i, 'position': position, 'resolved_person_id': 'p', 'name': 'Student',
                     'group': 'current', 'resolution': 'confirmed_mapping'} for i, position in [('a',2),('b',2),('c',1),('d',1),('a',2)]]
            save(output / '02-persons.json', {'rows': rows})
            profiles(output)
            p = read(output / '05-author-profiles.json')['profiles'][0]
            self.assertEqual(p['papers'], {'a': 1, 'b': .2, 'c': 1, 'd': 1})
            self.assertEqual(p['state'], 'partial')
            self.assertEqual(p['keyword_papers'], 3)
            self.assertAlmostEqual(p['keywords'][0]['score'], 1 / 2.2)

    def test_namesakes_no_merge_and_mapping_requires_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'iterations/run'
            output.mkdir(parents=True)
            save(root / 'inputs/current-students.json', {'students': [{'author_name': 'Xiaoyu Wang'}]})
            save(root / 'inputs/graduated-students.json', {'students': []})
            rows = [{'paper_id': 'a', 'position': n, 'name': 'Xiaoyu Wang', 'person_key': 'A' + str(n),
                     'openalex_author_id': 'A' + str(n), 'orcid': None, 'institutions': [], 'roster_candidate': 'current'} for n in (1, 2)]
            save(output / '02-author-occurrences.json', {'rows': rows})
            mapping = root / 'mapping.json'
            save(mapping, {'schema': 'lab-atlas-person-mappings/v1', 'mappings': []})
            result = people(output, mapping)
            self.assertEqual(result['person_keys'], 2)
            self.assertEqual(result['confirmed_occurrences'], 0)
            self.assertTrue(all(p['group'] == 'other' for p in read(output / '02-persons.json')['rows']))
            save(mapping, {'schema': 'lab-atlas-person-mappings/v1', 'mappings': [
                {'person_id': 'lab-person', 'name': 'Xiaoyu Wang', 'group': 'current', 'occurrence_ids': ['a:1'], 'evidence': []}]})
            with self.assertRaises(AssertionError): people(output, mapping)


if __name__ == '__main__': unittest.main()
