"""Mechanical stage acceptance; asserts facts, not merely plausible explanations."""
import argparse
import collections
import json
import importlib.util
import re
import urllib.parse
from pathlib import Path
from pipeline import read, save, digest, summary, oid, ROOT, identity_projection


FACT_SOURCES = {'lab_homepage', 'lab_user_roster', 'openalex'}
DETAIL_FIELDS = {'abstract', 'database_keywords', 'database_topics', 'citations', 'references', 'citing'}


def provenance(output):
    """Verify the iteration's own frozen rules, source files and used responses."""
    output = Path(output)
    assert (output / 'protocol.json').is_file(), 'Missing frozen protocol.json; rerun this iteration'
    config = read(output / 'protocol.json')
    manifest = read(output / 'run-manifest.json')
    assert manifest['rules_sha256'] == digest(config), 'Frozen protocol hash mismatch'
    assert manifest['rules_version'] == config['rules_version'], 'Rules version mismatch'
    assert manifest['script_sha256'] == digest((output / 'pipeline.py').read_bytes()), 'Frozen collector hash mismatch'
    assert set(config['allowed_fact_sources']) == set(manifest['fact_sources']) == FACT_SOURCES, 'Forbidden fact source'
    assert [s['id'] for s in config['stages']] == ['homepage', 'identity', 'lab-details', 'external', 'features'], 'Unexpected stage contract'
    run_dir = output.parents[1]
    sources = read(run_dir / 'source-manifest.json')
    assert manifest['input_manifest_sha256'] == digest(sources), 'Frozen input manifest mismatch'
    paths = [r['path'] for r in sources['files']]
    required = {'inputs/homepage.html', 'inputs/current-students.json', 'inputs/graduated-students.json',
                'inputs/vocabulary.json', 'inputs/identity-audit.txt', 'inputs/keywords.txt'}
    assert required == set(paths) and len(paths) == len(set(paths)), 'Missing, duplicate or unexpected frozen source (legacy dependency prohibited)'
    for row in sources['files']:
        path = (run_dir / row['path']).resolve()
        assert (run_dir / 'inputs').resolve() in path.parents, 'Source outside frozen inputs (legacy dependency prohibited)'
        assert row['sha256'] == digest(path.read_bytes()), 'Frozen source hash mismatch: ' + row['path']
    used = {}
    loaded = {}

    def visit(value):
        if isinstance(value, dict):
            if 'url' in value and 'state' in value:
                url = value['url']
                parsed = urllib.parse.urlsplit(url)
                assert parsed.scheme == 'https' and parsed.netloc == 'api.openalex.org'
                assert re.fullmatch(r'/works(?:/W\d+)?', parsed.path), 'Forbidden fact endpoint'
                assert not parsed.fragment and not any(k.lower() in ('api_key', 'authorization') for k, _ in urllib.parse.parse_qsl(parsed.query))
                name = digest(url.encode()) + '.json'
                path = run_dir / 'responses' / name
                if not path.exists():
                    assert manifest['offline'] and value.get('reason') == 'response_not_in_frozen_run', 'Referenced response absent'
                else:
                    if name not in loaded:
                        loaded[name] = read(path)
                        assert loaded[name]['url'] == url and loaded[name]['sha256'] == digest(loaded[name].get('payload')), 'Response integrity mismatch'
                    envelope = loaded[name]
                    assert envelope['url'] == url, 'Response URL mismatch'
                    assert value == {k: v for k, v in envelope.items() if k != 'payload'}, 'Request event differs from frozen response'
                    if name not in used:
                        used[name] = digest(path.read_bytes())
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for name in ('02-identity.json', '03-lab-details.json', '04-external.json'):
        visit(read(output / name))
    return config, manifest, used


def check(output):
    output = Path(output)
    config, manifest, used_responses = provenance(output)
    spec = importlib.util.spec_from_file_location('frozen_two_source_collector', output / 'pipeline.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    homepage = read(output / '01-homepage.json')
    identities = read(output / '02-identity.json')['papers']
    details = read(output / '03-lab-details.json')['papers']
    drift_queue = read(output / '03-identity-review-queue.json')['papers']
    drift_ids = {r['id'] for r in details if r.get('identity_drift')}
    assert drift_ids == {r['id'] for r in drift_queue} and len(drift_ids) == len(drift_queue), 'Identity drift missing review disposition'
    external = read(output / '04-external.json')
    relations = read(output / '04-relations.json')['rows']
    selection = read(output / '04-graph-selection.json')['ids']
    inputs = read(output / '05-feature-inputs.json')['papers']
    ids = {p['id'] for p in homepage['papers']}
    assert ids == set(manifest['paper_ids']) and len(ids) == len(manifest['paper_ids']), 'Iteration paper scope mismatch'
    parsed = frozen.parse_homepage((output.parents[1] / 'inputs/homepage.html').read_text(encoding='utf-8'), config['homepage_url'])
    assert homepage['papers'] == [p for p in parsed['papers'] if p['id'] in ids], 'Homepage output differs from frozen HTML parser'
    assert ids == {p['id'] for p in identities} == {p['id'] for p in details}
    assert len(ids) == len(identities) == len(details), 'Duplicate lab entries'
    assert summary(identities)['unexplained'] == 0
    for row in identities:
        assert row['attempts'], 'Identity decision without saved query evidence'
        observed = []
        for a in row['attempts']:
            assert a['url'].startswith('https://api.openalex.org/works?')
            assert 'api_key' not in a['url']
            response = output.parents[1] / 'responses' / (digest(a['url'].encode()) + '.json')
            if response.exists():
                payload = read(response).get('payload') or {}
                observed.extend(identity_projection(w) for w in payload.get('results', []))
        for c in row['candidates']:
            assert set(c['work']) == set(config['identity']['fields_kept_from_search'])
            assert c['work'] in observed, 'Candidate absent from this iteration query evidence'
            assert c['metrics'] == frozen.metrics(row['homepage'], c['work'], config['identity']), 'Candidate metrics differ from frozen rules'
        selected, expected_state, expected_reason, _ = frozen.choose(row['homepage'], [c['work'] for c in row['candidates']], config['identity'])
        if row['state'] != 'query_failed':
            assert (row['state'], row['reason']) == (expected_state, expected_reason), 'Identity decision differs from frozen rules'
        else:
            assert not row['candidates'] and all(a['state'] != 'ready' for a in row['attempts'])
        assert set(row['adopted_sources'].values()) <= {'openalex', 'lab_homepage'}
        if row['state'] == 'ready':
            candidate = next(c for c in row['candidates'] if c['work']['id'] == row['adopted']['openalex'])
            assert candidate['metrics']['accepted']
            assert selected and selected['id'] == row['adopted']['openalex']
            assert row['adopted']['title'] == selected['title']
            assert row['adopted']['authors'] == ([a['author']['display_name'] for a in selected.get('authorships') or []] or row['homepage']['authors'])
        else:
            assert row['adopted']['openalex'] is None
            assert row['attempts'], 'Unresolved paper without any search route'
    fields = {}
    assert all(set(row['fields']) == DETAIL_FIELDS for row in details), 'Missing or unexpected stage 3 fields'
    for key in sorted(DETAIL_FIELDS):
        fields[key] = summary([row['fields'][key] for row in details])
        assert fields[key]['unexplained'] == 0
    for row in details:
        assert all(f.get('source') in ('openalex', None) for f in row['fields'].values()), 'Forbidden detail source'
        ref = row['fields']['references']
        assert ref.get('source') in ('openalex', None)
        citing = row['fields']['citing']
        if citing.get('ids') is not None:
            assert len(citing['ids']) == len(set(citing['ids'])) == citing['collected']
            assert citing['collected'] <= config['requests']['citing_max_records']
            assert not citing['complete'] or citing['collected'] == citing['query_total']
        if row['bibliography']:
            expected = next(p['adopted'] for p in identities if p['id'] == row['id'])
            assert row['bibliography']['openalex'] == expected['openalex']
            event = row['fields']['abstract']['request']
            path = output.parents[1] / 'responses' / (digest(event['url'].encode()) + '.json')
            work = read(path)['payload']
            assert row['bibliography'] == frozen.bibliography(work), 'Bibliography differs from exact-ID response'
            for key, value in [('abstract', frozen.abstract(work)), ('database_keywords', work.get('keywords')), ('database_topics', work.get('topics')),
                               ('references', [oid(x) for x in work['referenced_works']] if 'referenced_works' in work else None)]:
                assert row['fields'][key]['value'] == value, 'Detail value differs from its source: ' + key
            citations = row['fields']['citations']
            expected_count = citing.get('query_total') if isinstance(citing.get('query_total'), int) else work.get('cited_by_count')
            assert citations['value'] == expected_count, 'Adopted citation count differs from rule'
    requested = {r['id'] for r in external['records']}
    assert len(requested) == len(external['records']), 'Duplicate requested external IDs'
    assert all(not r['record'] or r['record'].get('source') == 'openalex' for r in external['records'])
    known_lab = {oid(p['adopted']['openalex']) for p in identities if p['adopted']['openalex']}
    expected_ids = set()
    expected_relations = set()
    for row in details:
        for kind, values in [('reference', row['fields']['references'].get('value') or []), ('citing', row['fields']['citing'].get('ids') or [])]:
            expected_ids.update(set(values) - known_lab)
            expected_relations.update((row['id'], i, kind) for i in values)
    assert requested == expected_ids, 'External lookup must cover all known one-hop identifiers'
    assert expected_relations == {(r['lab_id'], r['work_id'], r['direction']) for r in relations}
    assert len(relations) == len(expected_relations), 'Duplicate relations'
    lab_map = {oid(p['adopted']['openalex']): p['id'] for p in identities if p['adopted']['openalex']}
    external_map = {r['id']: r for r in external['records']}
    for relation in relations:
        work_id = relation['work_id']
        record = external_map.get(work_id, {}).get('record')
        canonical = record['id'] if record else work_id
        assert relation['endpoint_id'] == lab_map.get(canonical, canonical), 'Incorrect canonical relation endpoint'
        assert relation['endpoint_state'] == ('ready' if canonical in lab_map else external_map[work_id]['state']), 'Incorrect relation endpoint state'
    assert len(selection) == len(set(selection)) <= config['external']['graph_budget']
    successful = {r['record']['id'] for r in external['records'] if r['record']}
    assert set(selection) <= successful
    assert not set(selection) & known_lab, 'Laboratory work selected as external node'
    connections = collections.defaultdict(set)
    for relation in relations:
        if relation['endpoint_state'] == 'ready' and relation['endpoint_id'] not in lab_map.values():
            connections[relation['endpoint_id']].add(relation['lab_id'])
    eligible = {i for i in successful-known_lab if len(connections[i]) >= config['external'].get('graph_min_lab_neighbors',1)}
    expected_selection = sorted(eligible,key=lambda i:(-len(connections[i]),i))[:config['external']['graph_budget']]
    assert selection == expected_selection, 'Graph selection differs from distinct lab-neighbor minimum and budget rule'
    assert summary(external['records'])['unexplained'] == 0
    assert ids | set(selection) == {p['id'] for p in inputs}
    assert len(inputs) == len(ids) + len(selection)
    for paper in inputs:
        assert paper['input_sha256'] == digest({k: paper[k] for k in ('id', 'title', 'abstract')})
    run_dir = output.parents[1]
    vocabulary_hash = digest(read(run_dir / 'inputs/vocabulary.json'))
    prompt_hash = digest((run_dir / 'inputs/keywords.txt').read_text(encoding='utf-8').encode())
    assert read(output / '05-feature-inputs.json')['vocabulary_sha256'] == vocabulary_hash
    tasks = [json.loads(line) for line in (output / '05-keyword-tasks.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    input_map = {p['id']: p for p in inputs}
    assert len(tasks) == len(inputs) and {t['paper_id'] for t in tasks} == set(input_map), 'Keyword task scope mismatch'
    for task in tasks:
        paper = input_map[task['paper_id']]
        assert task['input_sha256'] == paper['input_sha256'] and task['title'] == paper['title'] and task['abstract'] == paper['abstract']
        assert task['vocabulary_sha256'] == vocabulary_hash and task['prompt_sha256'] == prompt_hash, 'Keyword generation contract mismatch'
    author_rows = read(output / '02-author-occurrences.json')['rows']
    assert len(author_rows) == sum(len(p['adopted']['authors']) for p in identities)
    expected_authors = {(p['id'], i + 1, name) for p in identities for i, name in enumerate(p['adopted']['authors'])}
    assert expected_authors == {(r['paper_id'], r['position'], r['name']) for r in author_rows}, 'Author occurrence scope mismatch'
    for row in author_rows:
        assert row['person_key'] == (row['openalex_author_id'] or 'occurrence:' + row['paper_id'] + ':' + str(row['position'])), 'Name-only person merge'
    coverage = {'homepage': {'papers': len(ids), 'unparsed': len(homepage['excluded'])},
                'identity': summary(identities), 'identity_drift_pending': len(drift_ids),
                'final_confirmed_identity': sum(p['state'] == 'ready' and p['id'] not in drift_ids for p in identities),
                'details': fields, 'external': summary(external['records']),
                'graph_external': len(selection), 'feature_inputs': len(inputs),
                'external_degree_eligible': len(eligible),
                'external_excluded_by_degree': len(successful-known_lab)-len(eligible),
                'author_occurrences': summary(author_rows),
                'author_group_pending': sum(r['group_state'] == 'needs_roster_identity_confirmation' for r in author_rows)}
    save(output / 'acceptance.json', {'checks_passed': True, 'rules_sha256': manifest['rules_sha256'],
                                    'verified_responses': used_responses, 'coverage': coverage})
    print('Verified: identity rules, source boundaries, one-hop completeness, list accounting, graph selection, text fingerprints, author occurrence accounting.')
    return coverage


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    args = parser.parse_args()
    check(ROOT / args.output)
