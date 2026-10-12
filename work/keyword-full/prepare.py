"""Prepare frozen offline annotation inputs; never invoke an annotator or network."""
import argparse
import collections
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
MAX_PAPERS = 10
MAX_CHARS = 24000
ANNOTATION_MODELS = {"lab": "deepseek-flash", "external": "deepseek-flash"}
API_CONCURRENCY = 100
REVIEW_CONCURRENCY = 3
REVIEW_MODEL = "gpt-6.1-sol"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_title(title):
    # Control-only duplicate candidates. Never merge IDs or alter annotation text.
    return "".join(char for char in unicodedata.normalize("NFKC", title).casefold() if char.isalnum())


def distribution(values):
    counts = collections.Counter(json.dumps(value, ensure_ascii=False, sort_keys=True)
                                 if isinstance(value, (dict, list)) else value for value in values)
    return {str(key): count for key, count in sorted(counts.items(), key=lambda pair: str(pair[0]))}


def build_plan():
    source_paths = {
        "papers": WORK / "abstract-backfill/all-papers-with-abstracts.json",
        "vocabulary": WORK / "keyword-pilot/vocabulary-for-annotation.json",
        "pilot_schema": WORK / "keyword-pilot/annotation-output.schema.json",
        "pilot_instructions": WORK / "keyword-pilot/annotation-instructions.txt",
    }
    raw = {name: path.read_bytes() for name, path in source_paths.items()}
    papers = json.loads(raw["papers"].decode("utf-8-sig"))["papers"]
    vocabulary = json.loads(raw["vocabulary"].decode("utf-8-sig"))
    schema = copy.deepcopy(json.loads(raw["pilot_schema"].decode("utf-8-sig")))
    keyword_ids = [item["id"] for item in vocabulary["keywords"]]
    assert vocabulary["keyword_count"] == len(keyword_ids) == len(set(keyword_ids)) == 49
    assert len(papers) == 1673
    assert len({paper["id"] for paper in papers}) == len(papers)
    for paper in papers:
        assert isinstance(paper["id"], str) and re.fullmatch(r"[A-Za-z0-9_-]+", paper["id"])
        assert isinstance(paper["title"], str)
        assert paper["abstract"] is None or isinstance(paper["abstract"], str)
        assert isinstance(paper["lab"], bool)
    papers = sorted(papers, key=lambda paper: (not paper["lab"], paper["id"]))
    schema["required"] = ["paper_id", "annotations", "abstentions", "input_issues"]
    del schema["properties"]["sample_id"]
    schema["properties"]["paper_id"] = {"type": "string", "pattern": "^[A-Za-z0-9_-]+$"}
    schema["properties"]["input_issues"] = {
        "type": "array", "items": {"type": "string", "minLength": 1}
    }
    for field in ("annotations", "abstentions"):
        assert schema["properties"][field]["items"]["properties"]["keyword_id"]["enum"] == keyword_ids
        assert schema["properties"][field]["items"]["additionalProperties"] is False
    assert schema["additionalProperties"] is False

    controls = []
    batches = []
    current = []
    current_chars = 0
    current_lab = None
    title_groups = collections.defaultdict(list)
    oversized = []
    for paper in papers:
        chars = len(paper["title"]) + len(paper["abstract"] or "")
        if chars > MAX_CHARS:
            oversized.append({"paper_id": paper["id"], "title_abstract_chars": chars})
        if current and (paper["lab"] != current_lab or len(current) == MAX_PAPERS
                        or current_chars + chars > MAX_CHARS):
            batches.append(current)
            current, current_chars = [], 0
        current.append({"paper_id": paper["id"], "title": paper["title"], "abstract": paper["abstract"]})
        current_lab = paper["lab"]
        current_chars += chars
        key = normalized_title(paper["title"])
        if key:
            title_groups[key].append(paper["id"])
    if current:
        batches.append(current)
    if oversized:
        raise RuntimeError("Entries exceed the batch character limit: " + json.dumps(oversized))
    flattened = [item["paper_id"] for batch in batches for item in batch]
    assert flattened == [paper["id"] for paper in papers]
    assert len(set(flattened)) == len(papers)

    generated = {"vocabulary.json": raw["vocabulary"], "output.schema.json": encoded(schema)}
    for name in ("annotation-instructions.txt", "worker-task-template.txt", "review-instructions.txt",
                 "reviewer-task-template.txt", "review-output.schema.json", "EXECUTION-PLAN.txt"):
        generated[name] = (ROOT / name).read_bytes()
    batch_controls = []
    by_id = {paper["id"]: paper for paper in papers}
    for index, batch in enumerate(batches, 1):
        batch_name = f"batch-{index:03d}"
        relative_path = f"inputs/{batch_name}.json"
        batch_bytes = encoded({"papers": batch})
        generated[relative_path] = batch_bytes
        chars = sum(len(item["title"]) + len(item["abstract"] or "") for item in batch)
        assert len(batch) <= MAX_PAPERS and chars <= MAX_CHARS
        cohort = "lab" if by_id[batch[0]["paper_id"]]["lab"] else "external"
        assert all(by_id[item["paper_id"]]["lab"] == (cohort == "lab") for item in batch)
        annotation_model = ANNOTATION_MODELS[cohort]
        batch_controls.append({"batch_id": batch_name, "input_path": relative_path,
                               "cohort": cohort, "annotation_model": annotation_model,
                               "paper_count": len(batch), "title_abstract_chars": chars,
                               "sha256": sha256(batch_bytes)})
        for item in batch:
            original = by_id[item["paper_id"]]
            controls.append({"paper_id": item["paper_id"], "batch_id": batch_name,
                             "cohort": cohort, "annotation_model": annotation_model,
                             "input_sha256": sha256(encoded(item)),
                             "batch_sha256": sha256(batch_bytes),
                             "lab": original["lab"], "abstract_source": original["abstract_source"],
                             "quality": original["quality"], "status": original["status"],
                             "title_abstract_chars": len(item["title"]) + len(item["abstract"] or ""),
                             "result_path": f"results/{item['paper_id']}.json",
                             "review_path": f"reviews/{item['paper_id']}.json"})

    char_counts = [batch["title_abstract_chars"] for batch in batch_controls]
    duplicate_groups = [{"normalized_title": title, "paper_ids": ids}
                        for title, ids in sorted(title_groups.items()) if len(ids) > 1]
    preflight = {
        "mode": "prepared_not_started", "paper_count": len(papers),
        "valid_titles": sum(bool(p["title"].strip()) for p in papers),
        "valid_abstracts": sum(bool((p["abstract"] or "").strip()) for p in papers),
        "missing_abstracts": sum(not bool((p["abstract"] or "").strip()) for p in papers),
        "empty_title_ids": [p["id"] for p in papers if not p["title"].strip()],
        "lab_count": sum(p["lab"] for p in papers),
        "external_count": sum(not p["lab"] for p in papers),
        "quality_distribution": distribution(p["quality"] for p in papers),
        "status_distribution": distribution(p["status"] for p in papers),
        "abstract_source_distribution": distribution(p["abstract_source"] for p in papers),
        "oversized_entries": oversized,
        "maximum_paper_chars": max(c["title_abstract_chars"] for c in controls),
        "duplicate_title_normalization": "NFKC + casefold + isalnum only; candidates only, IDs retained",
        "duplicate_title_groups": duplicate_groups,
        "batch_count": len(batches), "batch_size_distribution": distribution(len(b) for b in batches),
        "cohort_batch_counts": distribution(b["cohort"] for b in batch_controls),
        "annotation_models": ANNOTATION_MODELS, "annotation_scope": "all",
        "annotation_model_name": "DeepSeek V4.1 Flash", "api_concurrency": API_CONCURRENCY,
        "review_concurrency": REVIEW_CONCURRENCY, "review_model": REVIEW_MODEL, "review_scope": "all",
        "batch_chars": {"min": min(char_counts), "max": max(char_counts),
                        "total": sum(char_counts), "mean": sum(char_counts) / len(char_counts),
                        "distribution": distribution((c // 4000) * 4000 for c in char_counts)},
    }
    manifest = {
        "mode": "prepared_not_started", "annotation_models": ANNOTATION_MODELS, "replicates": 1,
        "annotation_scope": "all", "annotation_transport": "deepseek_api",
        "annotation_model_name": "DeepSeek V4.1 Flash",
        "api_concurrency": API_CONCURRENCY, "review_concurrency": REVIEW_CONCURRENCY,
        "annotation_request_paper_count": 1, "annotation_requires_fresh_context": True,
        "thinking": {"type": "enabled"}, "reasoning_effort": "high", "max_tokens": 32768,
        "review_max_papers_per_worker": 40,
        "protocol_change": {"source": "user", "description": "All 1673 single-pass annotations use DeepSeek V4.1 Flash; all gpt-6.1-sol reviews retained."},
        "review_model": REVIEW_MODEL, "review_scope": "all", "review_replicates": 1,
        "review_requires_fresh_context": True, "parallel_workers": REVIEW_CONCURRENCY,
        "parallel_workers_scope": "native_review_workers_only; API annotations have separate concurrency",
        "worker_fork_turns": "none", "fresh_review_worker_per_dispatch": True,
        "reuse_pilot_results": False,
        "max_papers_per_batch": MAX_PAPERS, "max_title_abstract_chars_per_batch": MAX_CHARS,
        "result_path_template": "results/<paper_id>.json", "paper_count": len(papers),
        "review_path_template": "reviews/<paper_id>.json",
        "batch_count": len(batches), "batches": batch_controls, "papers": controls,
        "paper_hash_serialization": "UTF-8, ensure_ascii=False, indent=2, trailing LF (prepare.py encoded)",
    }
    generated["control/preflight.json"] = encoded(preflight)
    generated["control/manifest.json"] = encoded(manifest)
    fingerprints = {
        "mode": "prepared_not_started", "algorithm": "sha256",
        "source_files": {str(source_paths[name].relative_to(WORK)).replace('\\', '/'): sha256(data)
                         for name, data in raw.items()},
        "prepared_files": {path: sha256(data) for path, data in sorted(generated.items())},
    }
    generated["control/fingerprints.json"] = encoded(fingerprints)
    run_state = {
        "mode": "prepared_not_started", "annotation_started": False, "review_started": False,
        "annotation_models": ANNOTATION_MODELS, "annotation_scope": "all",
        "annotation_model_name": "DeepSeek V4.1 Flash", "api_concurrency": API_CONCURRENCY,
        "review_concurrency": REVIEW_CONCURRENCY, "review_model": REVIEW_MODEL, "review_scope": "all",
        "review_requires_fresh_context": True, "replicates": 1, "review_replicates": 1,
        "parallel_workers": REVIEW_CONCURRENCY,
        "parallel_workers_scope": "native_review_workers_only; API annotations have separate concurrency",
        "annotation_transport": "deepseek_api", "annotation_request_paper_count": 1,
        "annotation_requires_fresh_context": True, "review_max_papers_per_worker": 40,
        "thinking": {"type": "enabled"}, "reasoning_effort": "high", "max_tokens": 32768,
        "protocol_change": {"source": "user", "description": "Authorized pre-start switch to DeepSeek V4.1 Flash for all annotations."},
        "batches": [{"batch_id": b["batch_id"], "cohort": b["cohort"],
                     "annotation_model": b["annotation_model"], "status": "pending",
                     "agent_task": None, "dispatch_count": 0, "completed_ids": [], "blocked_ids": [],
                     "review_status": "pending", "review_agent_task": None, "review_dispatch_count": 0,
                     "review_completed_ids": [], "review_blocked_ids": []} for b in batch_controls],
    }
    return generated, preflight, run_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-protocol", action="store_true", help="Explicit authorized pre-start protocol refresh; immutable inputs must match.")
    args = parser.parse_args()
    for name in ("results", "reviews"):
        directory = ROOT / name
        if directory.exists() and any(directory.iterdir()):
            raise RuntimeError(f"Nonempty {name}: re-preparation is prohibited.")
    generated, preflight, run_state = build_plan()
    frozen = ROOT / "control/fingerprints.json"
    if args.refresh_protocol:
        if not frozen.is_file():
            raise RuntimeError("Protocol refresh requires an existing freeze")
        old = json.loads(frozen.read_text(encoding="utf-8-sig"))
        new = json.loads(generated["control/fingerprints.json"])
        if old["source_files"] != new["source_files"]:
            raise RuntimeError("Source files changed; protocol refresh prohibited")
        old_state = json.loads((ROOT / "control/run-state.json").read_text(encoding="utf-8-sig"))
        if old_state.get("annotation_started") or old_state.get("review_started"):
            raise RuntimeError("Run already started; protocol refresh prohibited")
        expected_inputs = {path for path in generated if path.startswith("inputs/")}
        actual_inputs = {path.relative_to(ROOT).as_posix() for path in (ROOT / "inputs").glob("*")}
        if expected_inputs != actual_inputs:
            raise RuntimeError("Input file set changed; protocol refresh prohibited")
        for relative, expected in generated.items():
            if relative.startswith("inputs/") or relative in ("vocabulary.json", "output.schema.json"):
                if (ROOT / relative).read_bytes() != expected or old["prepared_files"].get(relative) != sha256(expected):
                    raise RuntimeError("Immutable input changed: " + relative)
        for relative, data in generated.items():
            (ROOT / relative).write_bytes(data)
        (ROOT / "control/run-state.json").write_bytes(encoded(run_state))
        outcome = "authorized_pre_start_protocol_refresh"
    elif frozen.exists():
        # Compare the complete regenerated frozen file set before touching anything.
        expected_inputs = {path for path in generated if path.startswith("inputs/")}
        actual_inputs = {str(path.relative_to(ROOT)).replace('\\', '/') for path in (ROOT / "inputs").glob("*")}
        assert expected_inputs == actual_inputs, "Frozen input file set changed"
        for relative, expected in generated.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"Frozen file or source changed: {relative}; no files overwritten")
        outcome = "verified_existing_freeze"
    else:
        if any((ROOT / relative).exists() for relative in generated
               if relative not in ("annotation-instructions.txt", "worker-task-template.txt",
                                   "review-instructions.txt", "reviewer-task-template.txt", "review-output.schema.json", "EXECUTION-PLAN.txt")):
            raise RuntimeError("Existing unfrozen output files; refusing to overwrite")
        for relative, data in generated.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        outcome = "prepared_not_started"
    state_path = ROOT / "control/run-state.json"
    if state_path.exists():
        if state_path.read_bytes() != encoded(run_state):
            raise RuntimeError("Run state differs from untouched prepared state; no state overwritten")
    else:
        state_path.write_bytes(encoded(run_state))
    for name in ("results", "reviews"):
        (ROOT / name).mkdir(exist_ok=True)
    summary = {key: value for key, value in preflight.items()
               if key not in ("abstract_source_distribution", "duplicate_title_groups")}
    summary["duplicate_title_group_count"] = len(preflight["duplicate_title_groups"])
    summary["duplicate_title_paper_count"] = sum(len(group["paper_ids"]) for group in preflight["duplicate_title_groups"])
    summary["protocol_frozen"] = True
    print(json.dumps({"outcome": outcome, **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
