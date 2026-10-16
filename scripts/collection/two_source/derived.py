"""Deterministic, evidence-bounded annotation reuse, personnel and profiles."""

import collections
import json
import re
import unicodedata
from pathlib import Path
from pipeline import ROOT, read, save, digest, summary, author_norm


def formatted(text):
    return (
        re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or ""))
        .strip()
        .casefold()
    )


def anchor(text, quote):
    """Return a literal span, allowing only NFKC/case/whitespace differences."""
    if not quote or not quote.strip():
        return None
    if quote in text:
        return quote
    chars, positions = [], []
    for i, char in enumerate(text):
        for c in unicodedata.normalize("NFKC", char).casefold():
            if c.isspace():
                c = " "
                if chars and chars[-1] == " ":
                    positions[-1] = (positions[-1][0], i + 1)
                    continue
            chars.append(c)
            positions.append((i, i + 1))
    needle = formatted(quote)
    start = "".join(chars).find(needle)
    if start < 0:
        return None
    result = text[positions[start][0] : positions[start + len(needle) - 1][1]]
    return result if formatted(result) == needle else None


def annotation(paper, value, allowed, reanchor=False):
    ids = value.get("keyword_ids", [])
    assert (
        isinstance(ids, list) and len(ids) == len(set(ids)) and set(ids) <= allowed
    ), "unknown_or_duplicate_keyword"
    evidence = []
    for item in value.get("evidence", []):
        assert item["keyword_id"] in ids and item["field"] in (
            "title",
            "abstract",
        ), "invalid_evidence_field"
        quote = item["quote"]
        assert isinstance(quote, str) and quote.strip(), "empty_evidence"
        quote = anchor(paper[item["field"]], quote) if reanchor else quote
        assert quote and quote in paper[item["field"]], "quote_not_in_current_input"
        evidence.append(
            {"keyword_id": item["keyword_id"], "field": item["field"], "quote": quote}
        )
    assert {e["keyword_id"] for e in evidence} == set(ids), "keyword_without_evidence"
    return {"keyword_ids": ids, "evidence": evidence}


def reuse_one(paper, old_input, accepted, vocabulary_equal, allowed):
    if not vocabulary_equal:
        return None, "vocabulary_changed"
    if old_input is None:
        return None, "no_previous_input"
    if accepted is None:
        return None, "previous_annotation_not_accepted"
    exact = all(
        (paper.get(k) or "") == (old_input.get(k) or "") for k in ("title", "abstract")
    )
    equal = all(
        formatted(paper.get(k)) == formatted(old_input.get(k))
        for k in ("title", "abstract")
    )
    if not equal:
        return None, "title_or_abstract_changed"
    value = {
        "keyword_ids": [a["keyword_id"] for a in accepted["annotations"]],
        "evidence": [
            {
                "keyword_id": a["keyword_id"],
                "field": a["evidence_field"],
                "quote": a["exact_quote"],
            }
            for a in accepted["annotations"]
        ],
    }
    try:
        return annotation(paper, value, allowed, reanchor=not exact), (
            "exact_input_reuse" if exact else "format_only_reanchored"
        )
    except (AssertionError, KeyError, TypeError) as error:
        return None, "previous_evidence_invalid:" + str(error)


def keywords(output, legacy, results=None):
    """Only this derived step may read legacy keyword annotations, never old facts."""
    papers = read(output / "05-feature-inputs.json")["papers"]
    vocabulary = read(output.parents[1] / "inputs/vocabulary.json")
    allowed = {k["id"] for k in vocabulary["keywords"]}
    previous = {p["paper_id"]: p for p in read(legacy / "inputs.json")}
    accepted = {p["paper_id"]: p for p in read(legacy / "accepted.json")["papers"]}
    equal = digest(vocabulary) == digest(read(legacy / "vocabulary.json"))
    imported = {}
    if results and results.exists():
        for line in results.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                assert row["paper_id"] not in imported, "Duplicate keyword result"
                imported[row["paper_id"]] = row
        assert set(imported) <= {
            p["id"] for p in papers
        }, "Keyword results outside current scope"
    prompt = (output.parents[1] / "inputs/keywords.txt").read_bytes()
    rows, pending = [], []
    for p in papers:
        value, reason = reuse_one(
            p, previous.get(p["id"]), accepted.get(p["id"]), equal, allowed
        )
        if p["id"] in imported:
            entry = imported[p["id"]]
            assert entry["input_sha256"] == p["input_sha256"], "Stale keyword input"
            assert entry["vocabulary_sha256"] == digest(vocabulary) and entry[
                "prompt_sha256"
            ] == digest(prompt), "Stale keyword contract"
            assert (
                entry.get("model")
                and isinstance(entry.get("settings"), dict)
                and "raw_response" in entry
            ), "Missing model provenance"
            assert entry["response_sha256"] == digest(
                entry["raw_response"]
            ), "Raw response hash mismatch"
            raw = (
                json.loads(entry["raw_response"])
                if isinstance(entry["raw_response"], str)
                else entry["raw_response"]
            )
            assert all(
                raw[k] == entry[k]
                for k in ("paper_id", "input_sha256", "keyword_ids", "evidence")
            ), "Annotation differs from saved model response"
            value, reason = (
                annotation(p, entry, allowed),
                "imported_fixed_task_response",
            )
        row = {
            "paper_id": p["id"],
            "input_sha256": p["input_sha256"],
            "state": "ready" if value else "not_generated",
            "reason": reason,
            **(value or {"keyword_ids": [], "evidence": []}),
        }
        if p["id"] in imported:
            row["response_provenance"] = imported[p["id"]]
        rows.append(row)
        if not value:
            pending.append(
                {
                    "paper_id": p["id"],
                    "title": p["title"],
                    "abstract": p["abstract"],
                    "input_sha256": p["input_sha256"],
                    "prompt_sha256": digest(prompt),
                    "vocabulary_sha256": digest(vocabulary),
                    "reason": reason,
                }
            )
    save(
        output / "05-keywords.json",
        {
            "papers": rows,
            "summary": summary(rows),
            "legacy_inputs": [
                {
                    "path": str(legacy / name),
                    "sha256": digest((legacy / name).read_bytes()),
                }
                for name in ("inputs.json", "accepted.json", "vocabulary.json")
            ],
        },
    )
    (output / "05-keyword-pending.jsonl").write_bytes(
        ("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pending)).encode(
            "utf-8"
        )
    )
    state = read(output / "05-feature-status.json")
    state["keyword_tasks"] = summary(rows)
    vectors = read(output / "05-vectors.json")
    state["vectors"] = summary(
        [
            {
                "state": "ready" if p["status"] == "success" else "missing",
                "reason": p["reason"],
            }
            for p in vectors["rows"]
        ]
    )
    save(output / "05-feature-status.json", state)
    by_id = {r["paper_id"]: r for r in rows}
    vector_map = {p["id"]: p for p in vectors["rows"]}
    save(
        output / "05-features.json",
        {
            "model": {
                k: v
                for k, v in vectors["model"].items()
                if k
                not in ("papers", "ready", "title_only", "lab_ready", "lab_title_only")
            },
            "papers": [
                {
                    "id": p["id"],
                    "input_sha256": p["input_sha256"],
                    "vector_key": vector_map[p["id"]]["vector_key"],
                    "keyword_state": by_id[p["id"]]["state"],
                    "keyword_reason": by_id[p["id"]]["reason"],
                }
                for p in papers
            ],
        },
    )
    return summary(rows)


def people(output, mappings):
    from persons import run

    return run(output, mappings)


def profiles(output):
    persons = read(output / "02-persons.json")["rows"]
    queue = (
        read(output / "02-person-review-queue.json")["rows"]
        if (output / "02-person-review-queue.json").exists()
        else []
    )
    pending_occurrences = {p["occurrence_id"] for p in queue}
    keywords_by_id = {
        p["paper_id"]: p for p in read(output / "05-keywords.json")["papers"]
    }
    papers = {
        p["id"]: p
        for p in read(output / "05-feature-inputs.json")["papers"]
        if p["lab"]
    }
    groups = collections.defaultdict(list)
    for p in persons:
        groups[p["resolved_person_id"]].append(p)
    result = []
    for person_id, occurrences in sorted(groups.items()):
        # One contribution per person per paper, including duplicated source bylines.
        weights = {}
        for p in occurrences:
            byline = papers[p["paper_id"]]["authors"]
            first = p["position"] == 1 or (
                p["position"] == 2
                and author_norm(byline[0]) == author_norm("Yuheng Jia")
            )
            weights[p["paper_id"]] = max(
                weights.get(p["paper_id"], 0), 1.0 if first else 0.2
            )
        ready = {
            i: w for i, w in weights.items() if keywords_by_id[i]["state"] == "ready"
        }
        denominator = sum(ready.values())
        scores = collections.Counter()
        for paper_id, weight in ready.items():
            for keyword in keywords_by_id[paper_id]["keyword_ids"]:
                scores[keyword] += weight
        pending_identity = any(
            p.get("occurrence_id") in pending_occurrences
            or p["resolution"] == "independent_occurrence"
            for p in occurrences
        )
        identity_state = (
            "unresolved"
            if pending_identity
            else (
                "confirmed_mapping"
                if all(p["resolution"] == "confirmed_mapping" for p in occurrences)
                else "database_identifier"
            )
        )
        result.append(
            {
                "person_id": person_id,
                "name": occurrences[0]["name"],
                "group": occurrences[0]["group"],
                "identity_state": identity_state,
                "state": (
                    "ready"
                    if len(ready) == len(weights) and not pending_identity
                    else "partial"
                ),
                "reason": (
                    "identity_or_keyword_tasks_pending"
                    if len(ready) != len(weights) or pending_identity
                    else "all_dependencies_ready"
                ),
                "papers": weights,
                "keyword_papers": len(ready),
                "total_papers": len(weights),
                "keywords": (
                    [
                        {"keyword_id": k, "score": v / denominator}
                        for k, v in sorted(scores.items(), key=lambda x: (-x[1], x[0]))
                    ]
                    if denominator
                    else []
                ),
            }
        )
    save(
        output / "05-author-profiles.json",
        {
            "profiles": result,
            "summary": summary(result),
            "denominator": "Sum of author weights over papers with completed annotations; pending papers excluded, accepted empty included.",
            "weights": {
                "first": 1,
                "others": 0.2,
                "advisor_first_student_second": True,
            },
            "scope": "full frozen lab corpus; UI filters must recompute from per-paper contributions",
        },
    )
    return summary(result)


def validate_derived(output, mappings=None, legacy=None, results=None):
    """Recompute outputs independently from frozen dependencies to detect tampering."""
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory(
        dir=str(output.parent), prefix="derived-check-"
    ) as name:
        target = Path(name)
        for filename in (
            "02-author-occurrences.json",
            "05-feature-inputs.json",
            "05-feature-status.json",
            "05-vectors.json",
        ):
            shutil.copy2(output / filename, target / filename)
        people(target, mappings or ROOT / "data/two-source/person-mappings.json")
        keywords(target, legacy or ROOT / "_legacy/v1.0/data/keywords", results)
        profiles(target)
        for name in (
            "02-persons.json",
            "02-person-review-queue.json",
            "02-person-review-warnings.json",
            "05-keywords.json",
            "05-features.json",
            "05-author-profiles.json",
        ):
            assert read(target / name) == read(output / name), (
                "Derived recomputation mismatch: " + name
            )
    papers = {p["id"]: p for p in read(output / "05-feature-inputs.json")["papers"]}
    allowed = {
        p["id"] for p in read(output.parents[1] / "inputs/vocabulary.json")["keywords"]
    }
    rows = read(output / "05-keywords.json")["papers"]
    assert len(rows) == len(papers) and {p["paper_id"] for p in rows} == set(papers)
    for p in rows:
        assert (
            p["input_sha256"] == papers[p["paper_id"]]["input_sha256"] and p["reason"]
        )
        if p["state"] == "ready":
            annotation(papers[p["paper_id"]], p, allowed)
        else:
            assert p["state"] == "not_generated" and not p["keyword_ids"]
    people_rows = read(output / "02-persons.json")["rows"]
    original = read(output / "02-author-occurrences.json")["rows"]
    assert len(people_rows) == len(original)
    for p, old in zip(people_rows, original):
        assert p["paper_id"] == old["paper_id"] and p["position"] == old["position"]
        if p["resolution"] != "confirmed_mapping":
            assert p["resolution"] == "automatic_evidence_component" and p.get(
                "personnel_state"
            ) in ("ready", "warning", "ambiguous"), "Unrecorded personnel merge"
    return {
        "keywords": summary(rows),
        "persons": read(output / "02-persons.json")["summary"],
        "profiles": read(output / "05-author-profiles.json")["summary"],
    }
