"""Offline mechanical validation. Never calls models or modifies raw results."""

import argparse
import copy
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def read_json(path):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("duplicate JSON key: " + key)
            obj[key] = value
        return obj

    return json.loads(
        path.read_text(encoding="utf-8-sig"),
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError("invalid number: " + x)
        ),
    )


def schema_errors(value, schema, path="$", root=None):
    """The frozen output schema uses this deliberately small JSON Schema subset."""
    root = root or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            return [path + ": unsupported external schema reference"]
        target = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return schema_errors(value, target, path, root)
    errors = []
    kinds = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int,
        "number": lambda x: type(x) in (int, float),
        "boolean": lambda x: type(x) is bool,
        "null": lambda x: x is None,
    }
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(kinds[k](value) for k in types):
            return [path + ": wrong type"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(path + ": not in enum")
    if "const" in schema and value != schema["const"]:
        errors.append(path + ": const mismatch")
    for component in schema.get("allOf", []):
        errors.extend(schema_errors(value, component, path, root))
    for union in ("anyOf", "oneOf"):
        if union in schema:
            successes = sum(
                not schema_errors(value, part, path, root) for part in schema[union]
            )
            if not successes or (union == "oneOf" and successes != 1):
                errors.append(path + ": " + union + " mismatch")
    if "if" in schema:
        branch = (
            "then" if not schema_errors(value, schema["if"], path, root) else "else"
        )
        errors.extend(schema_errors(value, schema.get(branch, {}), path, root))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(path + ": missing " + key)
        for key, item in value.items():
            if key in props:
                errors.extend(schema_errors(item, props[key], path + "." + key, root))
            elif schema.get("additionalProperties") is False:
                errors.append(path + ": extra field " + key)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(path + ": too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(path + ": too many items")
        if schema.get("uniqueItems") and len(
            {json.dumps(x, sort_keys=True) for x in value}
        ) != len(value):
            errors.append(path + ": duplicate items")
        for index, item in enumerate(value):
            if "items" in schema:
                errors.extend(
                    schema_errors(item, schema["items"], f"{path}[{index}]", root)
                )
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(path + ": too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(path + ": pattern mismatch")
    return errors


def validate_record(record, paper, keywords, schema):
    errors = schema_errors(record, schema)
    if errors:
        return errors
    selected, abstained = [], []
    for field, target in [("annotations", selected), ("abstentions", abstained)]:
        for index, item in enumerate(record[field]):
            kid = item["keyword_id"]
            if kid not in keywords:
                errors.append(f"{field}[{index}]: unknown keyword {kid}")
            target.append(kid)
            if not item["reason_zh"].strip():
                errors.append(f"{field}[{index}]: blank reason_zh")
            if field == "annotations":
                quote = item["exact_quote"]
                source = paper.get(item["evidence_field"])
                if not quote.strip():
                    errors.append(f"annotations[{index}]: blank exact_quote")
                if not isinstance(source, str) or not source or quote not in source:
                    errors.append(
                        f"annotations[{index}]: exact_quote is not a continuous substring of evidence_field"
                    )
                if (
                    paper.get("evidence_scope") == "title_only"
                    and item["evidence_field"] != "title"
                ):
                    errors.append(
                        f"annotations[{index}]: title-only input cannot cite abstract"
                    )
    for field, ids in [("annotations", selected), ("abstentions", abstained)]:
        for kid, count in Counter(ids).items():
            if count > 1:
                errors.append(field + ": duplicate keyword " + kid)
    for kid in set(selected) & set(abstained):
        errors.append("selected and abstained overlap: " + kid)
    for kid in selected:
        parent = keywords.get(kid, {}).get("parent_id")
        visited = {kid}
        while parent:
            if parent in visited:
                errors.append("vocabulary parent cycle: " + kid)
                break
            visited.add(parent)
            if parent in selected:
                errors.append("selected ancestor and descendant: " + parent + "/" + kid)
            parent = keywords.get(parent, {}).get("parent_id")
    if any(not x.strip() for x in record["input_issues"]):
        errors.append("input_issues: blank issue")
    return errors


def validate_review(record, raw, paper, keywords, output_schema, review_schema):
    """Return errors and an in-memory candidate; never rewrite immutable evidence."""
    errors = schema_errors(record, review_schema)
    if errors:
        return errors, None
    if record["paper_id"] != paper["paper_id"]:
        errors.append("review paper_id does not match input")
    for index, issue in enumerate(record["issues"]):
        if not issue["reason_zh"].strip():
            errors.append(f"issues[{index}]: blank reason_zh")
        field, quote = issue["evidence_field"], issue["exact_quote"]
        if field is None:
            if quote != "":
                errors.append(f"issues[{index}]: quote without evidence_field")
        else:
            source = paper.get(field)
            if not quote.strip() or not isinstance(source, str) or quote not in source:
                errors.append(
                    f"issues[{index}]: quote is not a nonempty continuous source substring"
                )
        if issue["keyword_id"] is not None and issue["keyword_id"] not in keywords:
            errors.append(f"issues[{index}]: unknown keyword")
    if record["verdict"] == "pass":
        if record["issues"] or record["patch"] is not None:
            errors.append("pass requires no issues and null patch")
        return errors, copy.deepcopy(raw) if not errors else None
    if record["verdict"] == "needs_review":
        return errors, None
    patch = record["patch"]
    removes = patch["remove_ids"]
    upserts = patch["upsert_annotations"]
    upsert_ids = [x["keyword_id"] for x in upserts]
    original = {x["keyword_id"]: x for x in raw["annotations"]}
    addressed = {
        issue["keyword_id"]
        for issue in record["issues"]
        if issue["keyword_id"] is not None
    }
    if len(upsert_ids) != len(set(upsert_ids)):
        errors.append("patch: duplicate upsert keyword")
    if set(removes) & set(upsert_ids):
        errors.append("patch: remove and upsert overlap")
    for kid in removes:
        if kid not in original:
            errors.append("patch removes absent keyword: " + kid)
        if kid not in addressed:
            errors.append("patch remove lacks corresponding issue: " + kid)
    for item in upserts:
        kid = item["keyword_id"]
        if kid not in addressed:
            errors.append("patch upsert lacks corresponding issue: " + kid)
        if original.get(kid) == item:
            errors.append("patch upsert rewrites an unchanged annotation: " + kid)
    old_abstentions = {x["keyword_id"]: x for x in raw["abstentions"]}
    new_abstentions = {x["keyword_id"]: x for x in patch["abstentions"]}
    for kid in set(old_abstentions) | set(new_abstentions):
        if (
            old_abstentions.get(kid) != new_abstentions.get(kid)
            and kid not in addressed
        ):
            errors.append("patch abstention change lacks corresponding issue: " + kid)
    if patch["input_issues"] != raw["input_issues"]:
        input_support = [x for x in record["issues"] if x["kind"] == "input_problem"]
        if not input_support:
            errors.append("patch input_issues change lacks input_problem issue")
        # Removing previously flagged text requires positive evidence from the frozen input.
        if set(raw["input_issues"]) - set(patch["input_issues"]) and not any(
            x["exact_quote"].strip() for x in input_support
        ):
            errors.append("patch removes input_issues without source evidence")
    candidate = copy.deepcopy(raw)
    annotations = {
        kid: copy.deepcopy(item) for kid, item in original.items() if kid not in removes
    }
    annotations.update({x["keyword_id"]: copy.deepcopy(x) for x in upserts})
    candidate["annotations"] = list(annotations.values())
    candidate["abstentions"] = copy.deepcopy(patch["abstentions"])
    candidate["input_issues"] = copy.deepcopy(patch["input_issues"])
    if (
        annotations == original
        and new_abstentions == old_abstentions
        and Counter(candidate["input_issues"]) == Counter(raw["input_issues"])
    ):
        errors.append("revise requires a real change")
    errors.extend(
        "patched result: " + error
        for error in validate_record(candidate, paper, keywords, output_schema)
    )
    return errors, candidate if not errors else None


def validate_reviews(root, papers, records, statuses, keywords, output_schema):
    review_schema = read_json(root / "review-output.schema.json")
    paths = sorted((root / "reviews").rglob("*.json"))
    found, bad_known, file_errors = defaultdict(list), defaultdict(list), []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            review = read_json(path)
            if not isinstance(review, dict) or not isinstance(
                review.get("paper_id"), str
            ):
                raise ValueError("missing or wrong-type review paper_id")
            pid = review["paper_id"]
            found[pid].append((relative, review))
            if relative != "reviews/" + pid + ".json":
                raise ValueError("review path does not match paper_id")
        except (ValueError, OSError) as exc:
            file_errors.append({"file": relative, "error": str(exc)})
            if path.stem in papers and relative == "reviews/" + path.stem + ".json":
                bad_known[path.stem].append(str(exc))
    review_statuses, candidates = [], {}
    raw_states = {x["paper_id"]: x["status"] for x in statuses}
    for pid, paper in papers.items():
        items = found.get(pid, [])
        errors = list(bad_known.get(pid, []))
        state = "review_pending"
        if items or errors:
            if raw_states[pid] not in (
                "valid_empty",
                "valid_nonempty",
                "flag_for_review",
            ):
                errors.append("review has no mechanically valid first-round result")
            if len(items) > 1:
                errors.append("duplicate review paper_id")
            candidate = None
            if len(items) == 1 and not errors:
                name, record = items[0]
                if name != "reviews/" + pid + ".json":
                    errors.append("review path does not match paper_id")
                else:
                    more, candidate = validate_review(
                        record,
                        records[pid][0][1],
                        paper,
                        keywords,
                        output_schema,
                        review_schema,
                    )
                    errors.extend(more)
            if errors:
                state = "review_invalid"
            elif items[0][1]["verdict"] == "needs_review" or (
                candidate and candidate["input_issues"]
            ):
                state = "review_needs_review"
            else:
                state = (
                    "review_pass"
                    if items[0][1]["verdict"] == "pass"
                    else "review_revised"
                )
                candidates[pid] = candidate
        review_statuses.append(
            {
                "paper_id": pid,
                "status": state,
                "files": [name for name, _ in items],
                "errors": errors,
            }
        )
    counts = {
        state: sum(x["status"] == state for x in review_statuses)
        for state in (
            "review_pending",
            "review_pass",
            "review_revised",
            "review_needs_review",
            "review_invalid",
        )
    }
    unknown = sorted(set(found) - set(papers))
    complete = (
        bool(papers) and len(candidates) == len(papers) and not (unknown or file_errors)
    )
    return {
        "review_file_count": len(paths),
        "review_counts": counts,
        "review_papers": review_statuses,
        "review_file_errors": file_errors,
        "unknown_review_ids": unknown,
        "review_complete": complete,
    }, candidates


def validate(root):
    root = Path(root)
    setup_errors, file_errors, records = [], [], defaultdict(list)
    schema = read_json(root / "output.schema.json")
    vocabulary = read_json(root / "vocabulary.json")
    keywords = {k["id"]: k for k in vocabulary["keywords"]}
    if len(keywords) != 49 or len(vocabulary["keywords"]) != 49:
        setup_errors.append("frozen vocabulary must contain exactly 49 unique keywords")
    papers = {}
    for path in sorted((root / "inputs").glob("batch-*.json")):
        for paper in read_json(path)["papers"]:
            pid = paper["paper_id"]
            if pid in papers:
                setup_errors.append("duplicate input paper_id: " + pid)
            papers[pid] = paper
    fingerprint = check_fingerprints(root)
    setup_errors.extend(fingerprint["errors"])
    paths = sorted((root / "results").rglob("*.json"))
    unreadable_known = defaultdict(list)

    def file_failure(relative, error, **details):
        file_errors.append(dict(file=relative, error=error, **details))
        known_id = Path(relative).stem
        if known_id in papers and relative == "results/" + known_id + ".json":
            unreadable_known[known_id].append(relative + ": " + error)

    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            payload = read_json(path)
            if isinstance(payload, dict) and "paper_id" in payload:
                entries = [payload]
            else:
                raise ValueError("result must be one paper record")
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict) or not isinstance(
                    entry.get("paper_id"), str
                ):
                    file_failure(
                        relative, "missing or wrong-type paper_id", index=index
                    )
                    continue
                records[entry["paper_id"]].append((relative, entry))
                if relative != "results/" + entry["paper_id"] + ".json":
                    file_failure(
                        relative,
                        "result path does not match paper_id",
                        paper_id=entry["paper_id"],
                    )
        except (ValueError, OSError) as exc:
            file_failure(relative, str(exc))
    statuses, invalid, missing, review = [], [], [], []
    for pid, paper in papers.items():
        found = records.get(pid, [])
        errors = list(unreadable_known.get(pid, []))
        if not found:
            if errors:
                state = "invalid"
                invalid.append(pid)
            else:
                state = "pending"
                missing.append(pid)
        else:
            if len(found) > 1:
                errors.append("duplicate result paper_id")
            for name, record in found:
                if name != "results/" + pid + ".json":
                    errors.append(name + ": result path does not match paper_id")
                errors.extend(
                    name + ": " + e
                    for e in validate_record(record, paper, keywords, schema)
                )
            if errors:
                state = "invalid"
                invalid.append(pid)
            elif found[0][1]["input_issues"]:
                state = "flag_for_review"
                review.append(pid)
            else:
                state = (
                    "valid_nonempty" if found[0][1]["annotations"] else "valid_empty"
                )
        names = [name for name, _ in found]
        if pid in unreadable_known:
            names.append("results/" + pid + ".json")
        statuses.append(
            {
                "paper_id": pid,
                "status": state,
                "files": sorted(set(names)),
                "errors": errors,
            }
        )
    extra = sorted(set(records) - set(papers))
    counts = {
        state: sum(s["status"] == state for s in statuses)
        for state in (
            "pending",
            "valid_nonempty",
            "valid_empty",
            "flag_for_review",
            "invalid",
        )
    }
    complete = bool(papers) and not (
        missing or invalid or review or extra or file_errors or setup_errors
    )
    run_state = (
        "prepared_not_started"
        if not paths
        else ("completed_valid" if complete else "incomplete_or_requires_review")
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": run_state,
        "mechanical_validation_only": True,
        "quality_scoring_performed": False,
        "input_count": len(papers),
        "result_file_count": len(paths),
        "counts": dict(counts),
        "complete": complete,
        "freeze": fingerprint,
        "setup_errors": setup_errors,
        "file_errors": file_errors,
        "unknown_result_ids": extra,
        "papers": statuses,
        "retry": {
            "invalid_ids": invalid,
            "missing_ids": missing,
            "paper_ids": invalid + missing,
        },
        "flag_for_review_ids": review,
    }
    review_report, candidates = validate_reviews(
        root, papers, records, statuses, keywords, schema
    )
    report.update(review_report)
    report["review_complete"] = report["review_complete"] and not (
        setup_errors or file_errors or extra or missing or invalid
    )
    report["semantic_verdicts_from_reviewers"] = True
    selected, abstained = Counter(), Counter()
    for candidate in candidates.values():
        selected.update(x["keyword_id"] for x in candidate["annotations"])
        abstained.update(x["keyword_id"] for x in candidate["abstentions"])
    report["accepted_candidate_count"] = len(candidates)
    report["keyword_counts"] = [
        {
            "keyword_id": kid,
            "selected_count": selected[kid],
            "abstention_count": abstained[kid],
        }
        for kid in keywords
    ]
    return report


def check_fingerprints(root):
    """Verify every frozen file plus complete coverage of inputs and protocol."""
    path = root / "control" / "fingerprints.json"
    if not path.exists():
        return {"checked": [], "errors": ["freeze manifest is missing"]}
    frozen = read_json(path)
    fingerprints = dict(frozen.get("prepared_files", {}))
    errors, checked = [], []
    required = {
        p.relative_to(root).as_posix() for p in (root / "inputs").glob("batch-*.json")
    }
    required.update(
        [
            "vocabulary.json",
            "output.schema.json",
            "annotation-instructions.txt",
            "worker-task-template.txt",
            "control/manifest.json",
            "review-output.schema.json",
            "review-instructions.txt",
            "reviewer-task-template.txt",
        ]
    )
    for name in sorted(required - set(fingerprints)):
        errors.append("freeze fingerprint missing: " + name)
    for name in sorted(fingerprints):
        path = root / name
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != fingerprints[name]
        ):
            errors.append("freeze fingerprint mismatch: " + name)
        checked.append(name)
    for name, expected in frozen.get("source_files", {}).items():
        path = root.parent / name
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            errors.append("source freeze fingerprint mismatch: " + name)
        checked.append("../" + name)
    return {"checked": checked, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work" / "keyword-full",
    )
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--require-reviewed", action="store_true")
    args = parser.parse_args()
    try:
        report = validate(args.root)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report = {
            "state": "setup_invalid",
            "complete": False,
            "setup_errors": [str(exc)],
        }
    destination = args.root / "control" / "validation-report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "state",
                    "complete",
                    "counts",
                    "review_complete",
                    "review_counts",
                    "setup_errors",
                )
                if k in report
            },
            ensure_ascii=False,
        )
    )
    invalid = (
        report.get("setup_errors")
        or report.get("file_errors")
        or report.get("unknown_result_ids")
        or report.get("retry", {}).get("invalid_ids")
    )
    return (
        1
        if invalid
        or (args.require_complete and not report["complete"])
        or (args.require_reviewed and not report.get("review_complete"))
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
