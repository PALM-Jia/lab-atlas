"""Build replaceable accepted artifacts from validated immutable raw and reviews."""
import argparse
from collections import Counter
import json
from pathlib import Path
import validate as validator


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def assemble(root):
    root = Path(root)
    report = validator.validate(root)
    write_json(root / 'control' / 'validation-report.json', report)
    if report['setup_errors']:
        raise ValueError('frozen preparation failed validation; no accepted outputs written')
    schema = validator.read_json(root / 'output.schema.json')
    review_schema = validator.read_json(root / 'review-output.schema.json')
    keywords = {x['id']: x for x in validator.read_json(root / 'vocabulary.json')['keywords']}
    papers = {p['paper_id']: p for path in sorted((root / 'inputs').glob('batch-*.json'))
              for p in validator.read_json(path)['papers']}
    accepted, coverage, abstention = [], Counter(), Counter()
    statuses = {x['paper_id']: x['status'] for x in report['review_papers']}
    for pid, paper in papers.items():
        destination = root / 'accepted' / (pid + '.json')
        if statuses[pid] not in ('review_pass', 'review_revised'):
            # This is a replaceable derived artifact, never a raw result or review.
            if destination.exists():
                destination.unlink()
            continue
        raw = validator.read_json(root / 'results' / (pid + '.json'))
        review = validator.read_json(root / 'reviews' / (pid + '.json'))
        errors = validator.validate_record(raw, paper, keywords, schema)
        more, candidate = validator.validate_review(review, raw, paper, keywords, schema, review_schema)
        if errors or more or candidate is None or candidate['input_issues']:
            raise ValueError('raw or review changed during assembly: ' + pid)
        write_json(destination, candidate)
        accepted.append(candidate)
        coverage.update(x['keyword_id'] for x in candidate['annotations'])
        abstention.update(x['keyword_id'] for x in candidate['abstentions'])
    aggregate = {'generated_at': report['generated_at'], 'input_count': report['input_count'],
                 'accepted_count': len(accepted), 'review_complete': report['review_complete'],
                 'review_finished': report['review_counts']['review_pending'] == 0 and report['review_counts']['review_invalid'] == 0,
                 'review_counts': report['review_counts'], 'mechanical_counts': report['counts'],
                 'unaccepted_ids': [pid for pid in papers if statuses[pid] not in ('review_pass', 'review_revised')],
                 'keyword_counts': [{'keyword_id': kid, 'selected_count': coverage[kid],
                                     'abstention_count': abstention[kid]} for kid in keywords],
                 'papers': accepted}
    if sum(aggregate['review_counts'].values()) != aggregate['input_count']:
        raise ValueError('review status counts are not mutually exclusive and exhaustive')
    write_json(root / 'accepted' / 'aggregate.json', aggregate)
    return aggregate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2] / 'work' / 'keyword-full')
    parser.add_argument('--require-reviewed', action='store_true')
    args = parser.parse_args()
    try:
        summary = assemble(args.root)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(str(exc))
        return 1
    print(json.dumps({k: summary[k] for k in ('input_count', 'accepted_count', 'review_complete', 'review_counts')}, ensure_ascii=False))
    return 1 if args.require_reviewed and not summary['review_complete'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
