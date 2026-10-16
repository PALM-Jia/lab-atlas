"""Freeze an accepted two-source fact snapshot without switching any UI inputs."""

import argparse
import shutil
from pathlib import Path
from pipeline import ROOT, read, save, digest
from validate import check


def run(output, destination):
    output, destination = Path(output), Path(destination)
    acceptance = check(output)
    if (output / "automation-acceptance.json").exists():
        automated = read(output / "automation-acceptance.json")
        assert automated["checks_passed"]
        for section in ("code_sha256", "input_sha256", "derived_outputs_sha256"):
            for filename, sha in automated[section].items():
                assert digest(Path(filename).read_bytes()) == sha, (
                    "Automation dependency changed after acceptance: " + filename
                )
    identities = read(output / "02-identity.json")["papers"]
    details = {r["id"]: r for r in read(output / "03-lab-details.json")["papers"]}
    papers = []
    for row in identities:
        papers.append(
            {
                "id": row["id"],
                "homepage": row["homepage"],
                "identity_state": row["state"],
                "identity_reason": row["reason"],
                "adopted": row["adopted"],
                "adopted_sources": row["adopted_sources"],
                "decision_sha256": row["decision_sha256"],
                "fields": details[row["id"]]["fields"],
            }
        )
    save(destination / "papers.json", {"papers": papers})
    external = read(output / "04-external.json")
    save(
        destination / "external.json",
        {"records": external["records"], "summary": external["summary"]},
    )
    for name in (
        "01-homepage.json",
        "02-author-occurrences.json",
        "04-relations.json",
        "04-graph-selection.json",
        "05-feature-inputs.json",
        "05-feature-status.json",
        "acceptance.json",
        "run-manifest.json",
        "05-vectors.json",
        "05-features.json",
    ):
        if (output / name).exists():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output / name, destination / name)
    for name in (
        "protocol.json",
        "pipeline.py",
        "05-keyword-tasks.jsonl",
        "03-identity-review-queue.json",
    ):
        if (output / name).exists():
            shutil.copy2(output / name, destination / name)
    for name in (
        "02-persons.json",
        "02-person-review-queue.json",
        "02-person-review-warnings.json",
        "05-keywords.json",
        "05-keyword-pending.jsonl",
        "05-author-profiles.json",
        "review-queues.json",
        "automation-acceptance.json",
    ):
        if (output / name).exists():
            shutil.copy2(output / name, destination / name)
    for name in ("05-model-keyword-results.jsonl", "05-model-keyword-status.json"):
        if (output / name).exists():
            shutil.copy2(output / name, destination / name)
    # Preserve the fixed-task request/response envelopes, without credentials.
    ai_dir = output.parents[1] / "ai"
    if ai_dir.exists():
        shutil.copytree(ai_dir, destination / "model-jobs", dirs_exist_ok=True)
    if (output / "automation-acceptance.json").exists():
        assert read(output / "automation-acceptance.json")["checks_passed"]
        for filename, sha in read(output / "automation-acceptance.json")[
            "code_sha256"
        ].items():
            source = Path(filename)
            assert (
                digest(source.read_bytes()) == sha
            ), "Automation code changed after acceptance"
        (destination / "automation-code").mkdir(exist_ok=True)
        for filename in read(output / "automation-acceptance.json")["code_sha256"]:
            shutil.copy2(
                filename, destination / "automation-code" / Path(filename).name
            )
    if (output / "vectors").exists():
        keys = {
            r["vector_key"]
            for r in read(output / "05-vectors.json")["rows"]
            if r["status"] == "success"
        }
        (destination / "vectors").mkdir(parents=True, exist_ok=True)
        for key in sorted(keys):
            shutil.copy2(
                output / "vectors" / (key + ".json"),
                destination / "vectors" / (key + ".json"),
            )
    run_dir = output.parents[1]
    shutil.copytree(run_dir / "inputs", destination / "inputs", dirs_exist_ok=True)
    if (output / "automation-acceptance.json").exists():
        for filename, sha in read(output / "automation-acceptance.json")[
            "input_sha256"
        ].items():
            source = Path(filename)
            assert (
                digest(source.read_bytes()) == sha
            ), "Automation input changed after acceptance"
            shutil.copy2(source, destination / "inputs" / source.name)
    save(
        destination / "manifest.json",
        {
            "coverage": acceptance,
            "adoption": "independent snapshot; old visualization not switched",
            "files": [
                {
                    "path": p.relative_to(destination).as_posix(),
                    "sha256": digest(p.read_bytes()),
                }
                for p in sorted(destination.rglob("*"))
                if p.is_file() and p.name != "manifest.json"
            ],
            "raw_requests_path": (run_dir / "responses").relative_to(ROOT).as_posix(),
            "raw_requests": [
                {"file": name, "sha256": sha}
                for name, sha in sorted(
                    read(output / "acceptance.json")["verified_responses"].items()
                )
            ],
        },
    )
    print("Independent snapshot frozen:", str(destination), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--destination", default="data/two-source/snapshot")
    args = parser.parse_args()
    run(ROOT / args.output, ROOT / args.destination)
