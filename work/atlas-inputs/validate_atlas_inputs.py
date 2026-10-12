#!/usr/bin/env python3
"""Validate the Lab Atlas input contract and write a small, auditable manifest.

This validator intentionally reads a fixed list of JSON/JS files.  It does not
walk the checkout, inspect credentials, or touch generated runtime files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


AUTHORITATIVE_INPUTS = (
    "outputs/paper-atlas/data.json",
    "outputs/paper-atlas/retrieval-data.json",
    "outputs/paper-atlas/paper-keywords.json",
    "outputs/paper-atlas/paper-fields.json",
    "outputs/paper-atlas/network-evidence.js",
)

WORKFLOW_CONTRACT = "work/atlas-inputs/workflow-contract.json"
WORKFLOW_GUIDE = "outputs/paper-atlas/workflow-guide.js"

# These are browser/runtime projections of the authoritative payloads.  They
# are listed for provenance, but are never parsed to establish counts.
DERIVED_PROJECTIONS = (
    "outputs/paper-atlas/data.js",
    "outputs/paper-atlas/retrieval-data.js",
    "outputs/paper-atlas/paper-keywords.js",
    "outputs/paper-atlas/paper-fields.js",
    "outputs/paper-atlas/research-fields.js",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot parse JSON {path}: {exc}") from exc


def read_network_evidence(path: Path) -> dict[str, Any]:
    """Decode the JSON object assigned to window.ATLAS_NETWORK_EVIDENCE."""
    try:
        text = path.read_text(encoding="utf-8")
        marker = "window.ATLAS_NETWORK_EVIDENCE="
        start = text.index(marker) + len(marker)
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot parse network evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError("network evidence assignment is not an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    record: dict[str, Any] = {"path": relative, "exists": path.is_file()}
    if path.is_file():
        record.update({"bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return record


def check(checks: list[dict[str, Any]], name: str, actual: Any, expected: Any, ok: bool | None = None) -> None:
    def serializable(value: Any) -> Any:
        if isinstance(value, set):
            return sorted(value, key=lambda item: str(item))
        if isinstance(value, dict):
            return {str(key): serializable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [serializable(item) for item in value]
        return value

    checks.append({
        "name": name,
        "actual": serializable(actual),
        "expected": serializable(expected),
        "passed": (actual == expected) if ok is None else ok,
    })


def check_ids(checks: list[dict[str, Any]], name: str, actual: set[Any], expected: set[Any]) -> None:
    """Record an ID-set comparison without embedding thousands of IDs."""
    missing = expected - actual
    extra = actual - expected
    checks.append({
        "name": name,
        "actual_count": len(actual),
        "expected_count": len(expected),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "missing_sample": sorted(missing, key=str)[:5],
        "extra_sample": sorted(extra, key=str)[:5],
        "passed": not missing and not extra,
    })


def run(root: Path, manifest_path: Path) -> tuple[dict[str, Any], bool]:
    checks: list[dict[str, Any]] = []
    files = {
        rel: root / rel for rel in (*AUTHORITATIVE_INPUTS, *DERIVED_PROJECTIONS)
    }
    for rel, path in files.items():
        check(checks, f"path exists: {rel}", path.is_file(), True)
    contract_path = root / WORKFLOW_CONTRACT
    check(checks, f"path exists: {WORKFLOW_CONTRACT}", contract_path.is_file(), True)
    if contract_path.is_file():
        contract = read_json(contract_path)
        stages = contract.get("stages", [])
        stage_ids = [stage.get("id") for stage in stages]
        required_stage_ids = ["homepage", "identity", "lab-details", "external", "features"]
        check(checks, "workflow contract schema", contract.get("schema"), "lab-atlas-workflow-contract/v1")
        check(checks, "workflow contract stage order", stage_ids, required_stage_ids)
        check(checks, "workflow contract stage count", len(stages), 5)
        for stage in stages:
            fields_present = all(stage.get(key) for key in ("inputs", "adopted_outputs", "evidence", "unresolved", "handoff"))
            check(checks, f"workflow contract fields: {stage.get('id')}", fields_present, True)
        semantics = contract.get("field_semantics", {})
        check(checks, "workflow contract field semantics", sorted(semantics), sorted((
            "controlled_keywords", "cited_by_count", "citing_query_total",
            "database_keywords", "citing_records", "references",
        )))
        guide_path = root / WORKFLOW_GUIDE
        guide_text = guide_path.read_text(encoding="utf-8") if guide_path.is_file() else ""
        check(checks, "workflow guide exists", guide_path.is_file(), True)
        check(checks, "workflow guide schema", contract.get("schema") in guide_text, True)
        for stage in stages:
            check(checks, f"workflow guide title: {stage.get('id')}", stage.get("title") in guide_text, True)

    # Only parse authoritative files that exist.  This keeps failure output
    # useful when a checkout is incomplete while still making the run fail.
    required = [root / rel for rel in AUTHORITATIVE_INPUTS]
    if not all(path.is_file() for path in required):
        raise ValidationError("one or more authoritative input files are missing")

    data = read_json(root / AUTHORITATIVE_INPUTS[0])
    retrieval = read_json(root / AUTHORITATIVE_INPUTS[1])
    keywords = read_json(root / AUTHORITATIVE_INPUTS[2])
    fields = read_json(root / AUTHORITATIVE_INPUTS[3])
    network = read_network_evidence(root / AUTHORITATIVE_INPUTS[4])

    nodes = data.get("nodes", [])
    lab_nodes = [node for node in nodes if node.get("lab") is True]
    external_nodes = [node for node in nodes if node.get("lab") is not True]
    node_ids = {node.get("id") for node in nodes}
    lab_ids = {node.get("id") for node in lab_nodes}

    check(checks, "atlas nodes", len(nodes), 1673)
    check(checks, "atlas lab nodes", len(lab_nodes), 144)
    check(checks, "atlas external nodes", len(external_nodes), 1529)
    check(checks, "atlas node partition", len(lab_nodes) + len(external_nodes), len(nodes))

    retrieval_papers = retrieval.get("papers", [])
    retrieval_external = retrieval.get("external", [])
    check(checks, "retrieval lab papers", len(retrieval_papers), 144)
    check(checks, "retrieval external papers", len(retrieval_external), 1529)
    check(checks, "retrieval total", len(retrieval_papers) + len(retrieval_external), 1673)
    check_ids(checks, "retrieval lab IDs match atlas", {item.get("id") for item in retrieval_papers}, lab_ids)
    check_ids(checks, "retrieval external IDs match atlas", {item.get("id") for item in retrieval_external}, node_ids - lab_ids)

    keyword_papers = keywords.get("papers", {})
    keyword_statuses = keywords.get("statuses", {})
    vocabulary = keywords.get("vocabulary", [])
    vocabulary_ids = {item.get("id") for item in vocabulary if isinstance(item, dict)}
    check(checks, "keyword papers", len(keyword_papers), 1673)
    check(checks, "keyword statuses", len(keyword_statuses), 1673)
    check_ids(checks, "keyword IDs match atlas", set(keyword_papers), node_ids)
    check(checks, "keyword vocabulary", len(vocabulary), 49)
    check(checks, "keyword vocabulary IDs unique", len(vocabulary_ids), 49)
    check(checks, "keyword IDF vocabulary", set(keywords.get("idf", {})), vocabulary_ids)

    field_papers = fields.get("papers", {})
    check(checks, "field papers", len(field_papers), 1673)
    check_ids(checks, "field IDs match atlas", set(field_papers), node_ids)
    check(checks, "field vocabulary", len(fields.get("fields", [])), 6)

    evidence_papers = network.get("papers", {})
    evidence_ids = set(evidence_papers)
    check_ids(checks, "network evidence lab IDs", evidence_ids, lab_ids)
    check(checks, "network evidence lab count", len(evidence_ids), 144)
    coverage = network.get("coverage", {})
    check(checks, "network evidence coverage total", coverage.get("total"), 144)

    passed = all(item["passed"] for item in checks)
    manifest = {
        "schema": "lab-atlas-input-manifest/v1",
        "project": "Lab Atlas",
        "authoritative_inputs": [file_record(root, rel) for rel in AUTHORITATIVE_INPUTS],
        "derived_projections": [file_record(root, rel) for rel in DERIVED_PROJECTIONS],
        "workflow_contract": file_record(root, WORKFLOW_CONTRACT),
        "validation": {"passed": passed, "checks": checks},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest, passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="Lab Atlas checkout root (default: repository root)")
    parser.add_argument("--manifest", type=Path, default=None, help="Manifest output path (default: work/atlas-inputs/manifest.json)")
    args = parser.parse_args(argv)
    script_root = Path(__file__).resolve().parents[2]
    root = (args.root or script_root).resolve()
    manifest_path = (args.manifest or root / "work/atlas-inputs/manifest.json").resolve()
    try:
        manifest, passed = run(root, manifest_path)
    except ValidationError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"manifest: {manifest_path}")
    print(f"checks: {sum(item['passed'] for item in manifest['validation']['checks'])}/{len(manifest['validation']['checks'])} passed")
    print(f"status: {'passed' if passed else 'failed'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
