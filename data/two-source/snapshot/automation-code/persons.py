"""Deterministic person resolution from this run's authorships and lab inputs."""
import collections
import re
from pipeline import ROOT, read, save, digest, author_norm


def valid_orcid(value):
    value = (value or '').rstrip('/').split('/')[-1].upper()
    if not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', value): return None
    digits = value.replace('-', '')
    total = 0
    for digit in digits[:-1]: total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return value if digits[-1] == ('X' if check == 10 else str(check)) else None


def resolve(rows, titles, roster, mappings, rules):
    items = [{**r, 'occurrence_id': r['paper_id'] + ':' + str(r['position'])} for r in rows]
    by_id = {p['occurrence_id']: p for p in items}
    assert len(by_id) == len(items), 'Duplicate authorship occurrence'
    names = {k: author_norm(p['name']) for k, p in by_id.items()}
    aliases = {author_norm(k): v for k, v in rules['homonyms'].items()}
    disabled = {author_norm(n) for n in rules['name_only_link_disabled']}
    orcids = {k: valid_orcid(p.get('orcid')) for k, p in by_id.items()}
    institutes = {k: {author_norm(i.get('display_name') or i.get('name')) for i in p.get('institutions', [])} for k, p in by_id.items()}
    lab_titles = {author_norm(n): ts for n, ts in rules['explicit_lab_titles'].items()}

    def partition(key):
        rule = aliases.get(names[key])
        if not rule: return None
        if any(author_norm(i) in institutes[key] for i in rule['other_institutions']): return 'other'
        if any(author_norm(i) in institutes[key] for i in rule['lab_institutions']): return 'lab'
        if any(titles.get(by_id[key]['paper_id'], '').casefold().startswith(t.casefold()) for t in lab_titles.get(names[key], [])): return 'lab'
        return 'unknown'

    partition_keys = {k: partition(k) for k in by_id}
    parent = {k: k for k in by_id}
    members = {k: {k} for k in by_id}
    links, rejected = [], []
    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    def compatible(a, b, ignore_orcid=False):
        keys = members[find(a)] | members[find(b)]
        if len({names[k] for k in keys}) != 1: return False
        partitions = {partition_keys[k] for k in keys} - {None, 'unknown'}
        if partitions == {'lab', 'other'}: return False
        return ignore_orcid or len({orcids[k] for k in keys if orcids[k]}) <= 1
    def join(a, b, rule, evidence, ignore_orcid=False):
        a, b = find(a), find(b)
        if a == b: return False
        if not compatible(a, b, ignore_orcid):
            rejected.append({'left': a, 'right': b, 'rule': rule, 'reason': 'conflicting_name_or_identifier_or_lab_constraint'})
            return False
        if b < a: a, b = b, a
        parent[b] = a
        members[a].update(members.pop(b))
        links.append({'left': a, 'right': b, 'rule': rule, 'evidence': evidence})
        return True

    explicit = {}
    for m in mappings['mappings']:
        assert m.get('person_id') and m.get('evidence') and m['group'] in ('current', 'graduated', 'other')
        if m['group'] != 'other': assert roster.get(author_norm(m['name'])) == m['group'], 'Mapping contradicts roster'
        allowed = {author_norm(n) for n in [m['name']] + m.get('aliases', [])}
        for k in m['occurrence_ids']:
            assert k in by_id and k not in explicit and names[k] in allowed, 'Invalid explicit occurrence mapping'
            explicit[k] = m
        for k in m['occurrence_ids'][1:]:
            join(m['occurrence_ids'][0], k, 'explicit_lab_mapping', m['evidence'], ignore_orcid=True)
    # Source identifiers are automatic evidence, but contradictory ORCID/name
    # metadata never disappear under a single opaque author ID.
    for kind, get in [('same_openalex_author_id', lambda k: by_id[k].get('openalex_author_id')), ('same_verified_orcid', lambda k: orcids[k])]:
        buckets = collections.defaultdict(list)
        for k in by_id:
            value = get(k)
            if value: buckets[(names[k], value)].append(k)
        for (_, value), keys in sorted(buckets.items()):
            for k in keys[1:]: join(keys[0], k, kind, {'identifier': value})

    # Coauthor evidence is fixed from names in the collected bylines, never
    # recursively inferred from keyword/topic/semantic similarity.
    paper_names = collections.defaultdict(set)
    name_papers = collections.defaultdict(set)
    for k, p in by_id.items():
        paper_names[p['paper_id']].add(names[k])
        name_papers[names[k]].add(p['paper_id'])
    def component_evidence(root):
        keys = members[root]
        coauthors, institutions = set(), set()
        for k in keys:
            coauthors.update(paper_names[by_id[k]['paper_id']] - {names[k]})
            institutions.update(institutes[k])
        return coauthors, institutions
    for _ in range(rules['maximum_rounds']):
        changed = False
        buckets = collections.defaultdict(list)
        for r in sorted(members): buckets[names[r]].append(r)
        for name, roots in sorted(buckets.items()):
            if name in disabled or len(roots) < 2: continue
            # Larger evidenced components serve as anchors. Unique best score
            # prevents a no-ID occurrence from bridging two equally plausible people.
            ordered = sorted(roots, key=lambda r: (-len(members[r]), r))
            for b in ordered[1:]:
                if b not in members: continue
                bc, bi = component_evidence(b)
                candidates = []
                for a in ordered:
                    if a == b or a not in members or not compatible(a, b): continue
                    if names[a] in aliases and any(partition_keys[k] == 'unknown' for k in members[a] | members[b]): continue
                    ac, ai = component_evidence(a)
                    common = sorted(ac & bc)
                    rare = [n for n in common if len(name_papers[n]) <= rules['maximum_corroborator_papers'] and n not in aliases and n not in disabled]
                    if len(common) < rules['minimum_common_coauthors'] or not rare: continue
                    if not (ai & bi or name in roster or partition_keys[b] == 'lab'): continue
                    score = (len(rare), len(common), len(ai & bi), len(members[a]))
                    candidates.append((score, a, common, sorted(ai & bi)))
                candidates.sort(reverse=True)
                if candidates and (len(candidates) == 1 or candidates[0][0] > candidates[1][0]):
                    _, a, common, institutions = candidates[0]
                    changed |= join(a, b, 'unique_coauthor_and_context_anchor', {'shared_coauthors': common, 'shared_institutions': institutions})
        if not changed: break

    components_by_name = collections.defaultdict(list)
    for root in members: components_by_name[names[root]].append(root)
    result, queue, warnings = [], [], []
    person_components = {}
    for root, keys in sorted(members.items()):
        key_list = sorted(keys)
        explicit_claims = [explicit[k] for k in keys if k in explicit]
        assert len({m['person_id'] for m in explicit_claims}) <= 1, 'Conflicting explicit persons'
        ids = sorted({by_id[k]['openalex_author_id'] for k in keys if by_id[k].get('openalex_author_id')})
        ors = sorted({orcids[k] for k in keys if orcids[k]})
        person_id = explicit_claims[0]['person_id'] if explicit_claims else ('orcid:' + ors[0] if ors else ids[0] if ids else 'occurrence:' + key_list[0])
        # Separate source-ID fragments with conflicting ORCIDs keep distinct keys.
        if not ors and ids and any(r != root and any(by_id[k].get('openalex_author_id') in ids for k in members[r]) for r in members):
            person_id = 'fragment:' + digest(key_list)[:16]
        if person_id in person_components:
            # A conflicting ORCID can occur under different names. A refused
            # graph merge must never accidentally reappear as an identical key.
            person_id += ':fragment:' + digest(key_list)[:16]
        person_components[person_id] = root
        component_links = [l for l in links if find(l['left']) == root]
        name = names[root]
        partitions = {partition_keys[k] for k in keys} - {None, 'unknown'}
        is_lab = partitions == {'lab'} or (name not in aliases and any(author_norm('Southeast University') in institutes[k] for k in keys))
        coauthors, _ = component_evidence(root)
        corroborated = len(coauthors) >= rules['minimum_common_coauthors'] and any(len(name_papers[n]) <= rules['maximum_corroborator_papers'] for n in coauthors)
        group = explicit_claims[0]['group'] if explicit_claims else roster[name] if name in roster and is_lab and corroborated else 'other'
        reasons, blocking, warning_reasons = [], [], []
        if len(components_by_name[name]) > 1 and name not in aliases:
            reasons.append('same_name_distinct_evidence_components')
            warning_reasons.append('same_name_distinct_evidence_components')
        if not ids and not ors and not explicit_claims and not any(l['rule'] == 'unique_coauthor_and_context_anchor' for l in component_links):
            reasons.append('no_identifier_or_coauthor_anchor'); blocking.append('no_identifier_or_coauthor_anchor')
        if name in roster and group == 'other' and partitions != {'other'}:
            reasons.append('roster_assignment_not_supported'); warning_reasons.append('roster_assignment_not_supported')
        if name in disabled and len(components_by_name[name]) > 1:
            reasons.append('user_identity_uncertain'); blocking.append('user_identity_uncertain')
        if name in aliases and not partitions:
            reasons.append('known_homonym_context_missing'); blocking.append('known_homonym_context_missing')
        if name in aliases and partitions and any(r != root and any(partition_keys[k] in partitions for k in members[r]) for r in components_by_name[name]):
            reasons.append('multiple_components_in_same_homonym_partition'); blocking.append('multiple_components_in_same_homonym_partition')
        for k in key_list:
            p = by_id[k]
            row = {**p, 'resolved_person_id': person_id, 'group': group,
                   'resolution': 'confirmed_mapping' if explicit_claims else 'automatic_evidence_component',
                   'mapping_evidence': component_links,
                   'personnel_state': 'ambiguous' if blocking else 'warning' if warning_reasons else 'ready'}
            result.append(row)
            if blocking: queue.append({'occurrence_id': k, 'person_id': person_id, 'name': p['name'], 'reasons': reasons,
                                     'openalex_author_id': p.get('openalex_author_id'), 'orcid': p.get('orcid'),
                                     'roster_candidate': p.get('roster_candidate'), 'institutions': p.get('institutions', [])})
            elif warning_reasons: warnings.append({'occurrence_id': k, 'person_id': person_id, 'name': p['name'], 'reasons': warning_reasons,
                                      'openalex_author_id': p.get('openalex_author_id'), 'orcid': p.get('orcid'),
                                      'roster_candidate': p.get('roster_candidate'), 'institutions': p.get('institutions', [])})
    result.sort(key=lambda p: next(i for i, old in enumerate(items) if old['occurrence_id'] == p['occurrence_id']))
    return result, queue, warnings, links, rejected


def run(output, mapping_path):
    rows = read(output / '02-author-occurrences.json')['rows']
    inputs = output.parents[1] / 'inputs'
    roster = {}
    for group, filename in [('current', 'current-students'), ('graduated', 'graduated-students')]:
        data = read(inputs / (filename + '.json'))
        for p in data['students']:
            if p.get('author_name'): roster[author_norm(p['author_name'].split(' — ')[0])] = group
        for name in data.get('previously_confirmed_retained', []): roster.setdefault(author_norm(name), group)
    feature_file = output / '05-feature-inputs.json'
    titles = {p['id']: p['title'] for p in read(feature_file)['papers']} if feature_file.exists() else {}
    rules = read(ROOT / 'data/two-source/person-rules.json')
    mappings = read(mapping_path)
    result, queue, warnings, links, rejected = resolve(rows, titles, roster, mappings, rules)
    save(output / '02-persons.json', {'rows': result, 'mappings_sha256': digest(mappings), 'rules_sha256': digest(rules),
         'links': links, 'rejected_links': rejected,
         'summary': {'occurrences': len(rows), 'person_keys': len({p['resolved_person_id'] for p in result}),
                     'confirmed_occurrences': sum(p['personnel_state'] == 'ready' for p in result),
                     'explicit_mapping_occurrences': sum(p['resolution'] == 'confirmed_mapping' for p in result),
                     'pending_occurrences': len(queue), 'warning_occurrences': len(warnings)}})
    save(output / '02-person-review-queue.json', {'ai_executed': False, 'rows': queue, 'input_sha256': digest(queue),
         'prompt_sha256': digest((ROOT / 'data/two-source/prompts/person-audit.txt').read_bytes())})
    save(output / '02-person-review-warnings.json', {'rows': warnings, 'input_sha256': digest(warnings),
         'policy': 'Warnings have an identifier-level basis but a same-name family or roster classification caveat; they do not block per-identifier profiles or trigger automatic person merging.'})
    return read(output / '02-persons.json')['summary']
