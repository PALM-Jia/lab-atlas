#!/usr/bin/env python3
"""Build/check the static Lab Atlas without making network requests.

Default mode is read-only.  ``--refresh`` explicitly runs the existing local
keyword synchronisation pipeline, then validates all page projections again.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "paper-atlas"
INPUT_VALIDATOR = ROOT / "work" / "atlas-inputs" / "validate_atlas_inputs.py"
PAGES = ("index.html", "retrieval.html", "workflow.html")
ARCHIVE_CANDIDATES = (
    "papers.html", "papers.js", "papers.css", "acceptance-report.html",
    "citation-comparison.html", "citation-comparison.json",
    "citation-comparison.csv", "scholar-dblp-probe.html",
    "scholar-dblp-probe.json", "author-semantic.js", "citation-counts.js",
)


def page_dependencies() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    pattern = re.compile(r"(?:src|href)=[\"']([^\"']+)[\"']")
    for page in PAGES:
        source = (OUT / page).read_text(encoding="utf-8")
        local = []
        for ref in pattern.findall(source):
            if ref.startswith(("http://", "https://", "#", "mailto:")):
                continue
            candidate = ref.split("?", 1)[0].split("#", 1)[0]
            if candidate and candidate not in local:
                local.append(candidate)
        result[page] = local
    return result


def write_release_manifest(deps: dict[str, list[str]]) -> Path:
    manifest = {
        "schema": "lab-atlas-release-manifest/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_pages": list(PAGES),
        "page_dependencies": deps,
        "compatibility_pages": ["workflow-map.html", "keyword-missing.html"],
        "archive_candidates": list(ARCHIVE_CANDIDATES),
        "notes": [
            "The three primary pages must remain usable from file://.",
            "Archive candidates are not deleted by this command.",
        ],
    }
    path = ROOT / "work" / "atlas-inputs" / "release-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def validate_pages() -> tuple[dict[str, list[str]], list[str]]:
    deps = page_dependencies()
    missing = []
    for page, refs in deps.items():
        if not (OUT / page).is_file():
            missing.append(f"page:{page}")
        for ref in refs:
            if not (OUT / ref).is_file():
                missing.append(f"{page}:{ref}")
    write_release_manifest(deps)
    return deps, missing


def run_validator() -> None:
    completed = subprocess.run(
        [sys.executable, str(INPUT_VALIDATOR)], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def check() -> int:
    if not INPUT_VALIDATOR.is_file():
        print(f"missing validator: {INPUT_VALIDATOR}", file=sys.stderr)
        return 2
    deps, missing = validate_pages()
    run_validator()
    print(f"primary pages: {len(PAGES)}")
    print(f"loaded local files: {sum(len(refs) for refs in deps.values())}")
    if missing:
        print("missing page dependencies:", *missing, sep="\n  ", file=sys.stderr)
        return 1
    print("status: passed (read-only offline check)")
    return 0


def refresh() -> int:
    print("preflight: read-only validation")
    if check():
        return 1
    command = [sys.executable, str(ROOT / "work" / "apply-reviewed-keywords.py")]
    print("refresh: running local keyword/field/retrieval synchronisation")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        return completed.returncode
    print("postflight: validation")
    return check()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="explicitly rewrite local generated data")
    args = parser.parse_args()
    return refresh() if args.refresh else check()


if __name__ == "__main__":
    raise SystemExit(main())
