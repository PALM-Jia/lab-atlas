"""Validate local vocabulary artifacts; no dependencies, network, or semantic claims.

Run: python validate-vocabulary.py
Prints JSON to stdout. Exit 0 means structural/exact-text checks pass, not that
the concepts, evidence roles, or paper candidates have been semantically proved.
Offsets use Python Unicode code points, zero-based, with exclusive end offsets.
"""

import collections
import hashlib
import json
from pathlib import Path
import sys


def validate(base):
    def read(name):
        return json.loads((base / name).read_text(encoding="utf-8-sig"))

    papers = read("lab-papers.json")
    vocabulary = read("vocabulary.json")
    coverage = read("coverage-review.json")
    manifest = read("source-manifest.json")
    homepage = (base / "homepage-context.md").read_text(encoding="utf-8-sig")
    markdown = (base / "vocabulary.md").read_text(encoding="utf-8-sig")
    keywords = vocabulary["keywords"]
    records = coverage["papers"]
    errors, warnings, locations = [], [], []

    def check(ok, message):
        if not ok:
            errors.append(message)

    paper_by_id = {p["id"]: p for p in papers}
    keyword_by_id = {k["id"]: k for k in keywords}
    record_ids = [r["paper_id"] for r in records]
    invalid_abstracts = {"lab-d99ee9ba4a13"}
    title_only = {p["id"] for p in papers if not p.get("abstract")} | invalid_abstracts
    dimensions = collections.Counter(k["primary_dimension"] for k in keywords)
    allowed_dimensions = {"research_task", "method", "application_object", "research_setting"}
    check(len(papers) == len(paper_by_id) == 144, "Corpus must have 144 unique papers")
    check(len(title_only) == 31, "Expected 31 papers requiring title-only evidence")
    check(len(keywords) == len(keyword_by_id), "Duplicate keyword IDs")
    check(len(records) == len(set(record_ids)) == 144, "Coverage must have 144 unique rows")
    check(set(record_ids) == set(paper_by_id), "Coverage paper IDs differ from corpus")
    check(set(dimensions) <= allowed_dimensions, "Unknown primary dimension")
    if not 45 <= len(keywords) <= 55:
        warnings.append("Keyword count is outside 45-55; semantic justification is required")

    hashes = {}
    for name, key in [("lab-papers.json", "lab_papers_sha256"),
                      ("homepage-context.md", "homepage_context_sha256")]:
        hashes[name] = hashlib.sha256((base / name).read_bytes()).hexdigest()
        check(hashes[name] == manifest["integrity"][key], f"Source hash mismatch: {name}")
    for name in ["vocabulary.json", "coverage-review.json", "vocabulary.md"]:
        hashes[name] = hashlib.sha256((base / name).read_bytes()).hexdigest()

    for keyword in keywords:
        kid = keyword["id"]
        for field in ["canonical_en", "canonical_zh", "definition_zh"]:
            check(bool(keyword.get(field, "").strip()), f"{kid}: empty {field}")
            check(keyword.get(field, "") in markdown, f"{kid}: {field} absent from Markdown")
        check(isinstance(keyword.get("aliases"), list), f"{kid}: aliases must be a list")
        parent = keyword.get("parent_id")
        if parent is not None:
            check(parent in keyword_by_id, f"{kid}: unknown parent {parent}")
            if parent in keyword_by_id:
                check(keyword["primary_dimension"] == keyword_by_id[parent]["primary_dimension"],
                      f"{kid}: parent crosses dimensions")
        seen, current = {kid}, parent
        while current in keyword_by_id:
            if current in seen:
                errors.append(f"{kid}: parent cycle")
                break
            seen.add(current)
            current = keyword_by_id[current].get("parent_id")
        evidence = keyword.get("evidence", [])
        check(any(e.get("source_type") == "paper" for e in evidence), f"{kid}: no paper evidence")
        for index, item in enumerate(evidence):
            label = f"{kid}.evidence[{index}]"
            source_id, field = item.get("source_id"), item.get("field")
            check(bool(item.get("role_reason_zh", "").strip()), f"{label}: empty role explanation")
            if item.get("source_type") == "paper":
                check(source_id in paper_by_id, f"{label}: unknown paper {source_id}")
                check(field in {"title", "abstract"}, f"{label}: invalid paper field {field}")
                if source_id not in paper_by_id or field not in {"title", "abstract"}:
                    continue
                check(not (source_id in title_only and field == "abstract"),
                      f"{label}: title-only paper uses abstract")
                source = paper_by_id[source_id].get(field) or ""
            elif item.get("source_type") == "homepage":
                check(source_id == "https://jyh-learning.github.io/", f"{label}: unknown homepage")
                check(field == "research_description", f"{label}: unknown homepage field")
                source = homepage
            else:
                errors.append(f"{label}: unsupported source type")
                continue
            quote = item.get("exact_quote")
            check(isinstance(quote, str) and bool(quote), f"{label}: empty quote")
            if not isinstance(quote, str) or not quote:
                continue
            start = source.find(quote)
            check(start >= 0, f"{label}: quote is not an exact source substring")
            if start >= 0:
                locations.append({"keyword_id": kid, "evidence_index": index,
                                  "source_id": source_id, "field": field,
                                  "start": start, "end": start + len(quote),
                                  "occurrences": source.count(quote)})

    for record in records:
        pid = record["paper_id"]
        if pid not in paper_by_id:
            continue
        check(record.get("title") == paper_by_id[pid]["title"], f"{pid}: changed title")
        check(record.get("reviewed") is True, f"{pid}: not marked reviewed")
        expected_fields = ["title"] if pid in title_only else ["title", "abstract"]
        check(record.get("reviewed_fields") == expected_fields, f"{pid}: wrong reviewed fields")
        expected_basis = "title_only" if pid in title_only else "title_and_abstract"
        check(record.get("evidence_basis") == expected_basis, f"{pid}: wrong evidence basis")
        candidates = record.get("candidate_keyword_ids", [])
        check(isinstance(candidates, list), f"{pid}: candidates must be a list")
        check(len(candidates) == len(set(candidates)), f"{pid}: duplicate candidates")
        check(set(candidates) <= set(keyword_by_id), f"{pid}: unknown candidate IDs")
        if not candidates:
            check(bool(record.get("uncovered_reason")), f"{pid}: empty candidates without reason")

    covered = sum(bool(r.get("candidate_keyword_ids")) for r in records)
    metadata = vocabulary["metadata"]
    check(metadata.get("keyword_count") == len(keywords), "Wrong declared keyword count")
    check(metadata.get("dimension_counts") == dict(dimensions), "Wrong declared dimension counts")
    expected_corpus = {"paper_count": 144, "nonempty_abstract_count": 114,
                       "substantive_abstract_count": 113, "title_only_count": 31}
    for key, value in expected_corpus.items():
        check(metadata.get("corpus", {}).get(key) == value, f"Wrong declared corpus {key}")
    for key, value in [("paper_count", 144), ("reviewed_count", 144),
                       ("papers_with_candidates", covered), ("papers_without_candidates", 144-covered)]:
        check(coverage.get(key) == value, f"Wrong coverage {key}")

    return {"validation_scope": "programmatic_structure_and_exact_text_only",
            "passed": not errors, "errors": errors, "warnings": warnings,
            "counts": {"papers": len(papers), "keywords": len(keywords),
                       "dimensions": dict(dimensions), "substantive_abstracts": 113,
                       "title_only": len(title_only), "evidence_items": len(locations),
                       "coverage_rows": len(records), "papers_with_candidates": covered,
                       "papers_without_candidates": len(records)-covered},
            "sha256": hashes, "quote_offsets": locations,
            "not_proved": ["semantic synonymy", "strict semantic parent containment",
                           "evidence role and definition fit", "candidate correctness or completeness",
                           "publisher abstract completeness"]}


if __name__ == "__main__":
    result = validate(Path(__file__).resolve().parent)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)
