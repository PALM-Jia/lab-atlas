"""One resumable entry point. Default offline; never changes network UI inputs."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from pipeline import ROOT, read, save, digest, initialize, now
from validate import check
from derived import people, keywords, profiles, validate_derived

HERE = Path(__file__).resolve().parent
ACTIVE_RUN = None
COLLECTED = [
    "protocol.json",
    "pipeline.py",
    "run-manifest.json",
    "01-homepage.json",
    "02-identity.json",
    "02-author-occurrences.json",
    "02-review-queue.json",
    "03-lab-details.json",
    "03-identity-review-queue.json",
    "04-external.json",
    "04-relations.json",
    "04-graph-selection.json",
    "05-feature-inputs.json",
    "05-keyword-tasks.jsonl",
]


def files_hash(paths):
    result = {}
    for path in paths:
        path = Path(path)
        if path.is_dir():
            result.update(files_hash(sorted(p for p in path.rglob("*") if p.is_file())))
        else:
            result[str(path)] = digest(path.read_bytes()) if path.exists() else None
    return result


class Steps:
    def __init__(self, path):
        self.path = path
        self.state = (
            read(path) if path.exists() else {"schema": "lab-atlas-run/v1", "steps": {}}
        )

    def run(self, name, inputs, outputs, action, always=False):
        fingerprint = digest(files_hash(inputs))
        old = self.state["steps"].get(name, {})
        if (
            not always
            and old.get("input_sha256") == fingerprint
            and old.get("state") == "complete"
            and old.get("outputs") == files_hash(outputs)
        ):
            print(name + ": reused", flush=True)
            return False
        record = {
            "state": "running",
            "input_sha256": fingerprint,
            "inputs": files_hash(inputs),
            "started_at": now(),
        }
        self.state["steps"][name] = record
        save(self.path, self.state)
        print(name + ": running", flush=True)
        try:
            result = action()
            assert all(p.exists() for p in outputs), (
                "Step did not produce all outputs: " + name
            )
            record.update(
                state="complete",
                finished_at=now(),
                outputs=files_hash(outputs),
                result=result,
            )
        except Exception as error:
            record.update(state="failed", finished_at=now(), reason=str(error))
            save(self.path, self.state)
            raise
        save(self.path, self.state)
        return True


def command(python, script, *args):
    subprocess.run(
        [str(python), "-B", str(script), *map(str, args)], cwd=str(ROOT), check=True
    )


def vector_files(output):
    if not (output / "05-vectors.json").exists():
        return []
    return [
        output / "vectors" / (p["vector_key"] + ".json")
        for p in read(output / "05-vectors.json")["rows"]
        if p["status"] == "success"
    ]


def verify_vectors(output):
    sys.path.insert(0, str(ROOT / "scripts/features"))
    from semantic_features import input_text, read_vector, MODEL

    inputs = {p["id"]: p for p in read(output / "05-feature-inputs.json")["papers"]}
    rows = read(output / "05-vectors.json")["rows"]
    assert len(rows) == len(inputs) and {p["id"] for p in rows} == set(
        inputs
    ), "Vector scope mismatch"
    for row in rows:
        _, info, key = input_text(inputs[row["id"]])
        assert (
            row["status"] == "success" and row["vector_key"] == key
        ), "Vector input mismatch"
        value = read_vector(output / "vectors", key)
        assert (
            value
            and value["input"]["sha256"] == info["sha256"]
            and row["input"] == value["input"]
        ), "Invalid vector record"
    assert all(
        read(output / "05-vectors.json")["model"][k] == v for k, v in MODEL.items()
    ), "Vector model mismatch"
    return {"ready": len(rows), "total": len(inputs)}


def seed_vectors(output, seed):
    # Keys encode model and exact title/abstract. The feature generator validates
    # each cached record again; this never imports an old text or old vector space.
    if seed.exists():
        (output / "vectors").mkdir(exist_ok=True)
        for path in seed.glob("*.json"):
            destination = output / "vectors" / path.name
            if not destination.exists():
                shutil.copy2(path, destination)


def reviews(output):
    identities = read(output / "02-review-queue.json")["papers"]
    drift = read(output / "03-identity-review-queue.json")["papers"]
    persons = read(output / "02-person-review-queue.json")
    warnings = read(output / "02-person-review-warnings.json")
    counts = {
        "work_identity": len(identities),
        "detail_identity_drift": len(drift),
        "person_occurrences": len(persons["rows"]),
        "person_warnings": len(warnings["rows"]),
        "keyword_papers": read(output / "05-keywords.json")["summary"]["states"].get(
            "not_generated", 0
        ),
    }
    save(
        output / "review-queues.json",
        {
            "ai_executed": False,
            "counts": counts,
            "identity": {
                "prompt": "inputs/identity-audit.txt",
                "input_sha256": digest(identities),
                "items": identities,
            },
            "drift": drift,
            "personnel": persons,
            "person_warnings": warnings,
            "keywords": "05-keyword-pending.jsonl",
            "policy": "Queues do not block fact freezing; unresolved tasks remain explicit. No AI calls, paid requests or UI adoption in this runner.",
        },
    )
    return counts


def publish_snapshot(output, run_dir):
    from freeze import run as freeze

    destination = ROOT / "data/two-source/snapshot"
    marker = digest(
        files_hash(
            [
                output / "automation-acceptance.json",
                output / "02-persons.json",
                output / "05-keywords.json",
            ]
        )
    )[:16]
    candidate = run_dir / "frozen" / ("automation-" + marker)
    if not candidate.exists():
        candidate.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=str(candidate.parent), prefix="freeze-candidate-"
        ) as temp:
            freeze(output, Path(temp))
            Path(temp).rename(candidate)
    manifest = read(candidate / "manifest.json")
    for item in manifest["files"]:
        assert (
            digest((candidate / item["path"]).read_bytes()) == item["sha256"]
        ), "Frozen candidate changed"
    if (
        destination.exists()
        and (destination / "manifest.json").read_bytes()
        == (candidate / "manifest.json").read_bytes()
    ):
        assert all(
            digest((destination / item["path"]).read_bytes()) == item["sha256"]
            for item in manifest["files"]
        ), "Adopted snapshot changed"
        return {
            "snapshot": str(destination.relative_to(ROOT)),
            "network_ui_switched": False,
            "reused": True,
        }
    # Preserve each previous independent snapshot. Network/retrieval data is never touched.
    replacement = ROOT / "data/two-source" / ("snapshot-next-" + marker)
    assert not replacement.exists(), "Unfinished promotion exists; inspect " + str(
        replacement
    )
    shutil.copytree(candidate, replacement)
    if destination.exists():
        history = (
            run_dir
            / "frozen"
            / ("previous-" + digest((destination / "manifest.json").read_bytes())[:16])
        )
        if history.exists():
            history = (
                run_dir
                / "frozen"
                / (
                    "previous-"
                    + digest((destination / "manifest.json").read_bytes())[:16]
                    + "-"
                    + marker
                )
            )
        assert not history.exists(), "Snapshot history collision"
        destination.rename(history)
    replacement.rename(destination)
    return {
        "snapshot": str(destination.relative_to(ROOT)),
        "network_ui_switched": False,
    }


def main():
    global ACTIVE_RUN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default="work/two-source/current")
    parser.add_argument(
        "--online",
        action="store_true",
        help="Allow OpenAlex requests absent from this run cache",
    )
    parser.add_argument(
        "--semantic-python", default="work/semantic-runtime/Scripts/python.exe"
    )
    parser.add_argument(
        "--keyword-results",
        help="Optional saved fixed-task JSONL; no model requests are made",
    )
    parser.add_argument(
        "--no-freeze",
        action="store_true",
        help="Validate candidate without promoting independent snapshot",
    )
    args = parser.parse_args()
    run_dir = (ROOT / args.run).resolve()
    allowed = (ROOT / "work/two-source").resolve()
    assert allowed in run_dir.parents, "Run must be a child of work/two-source"
    ACTIVE_RUN = run_dir
    save(
        run_dir / "automation-status.json",
        {"state": "running", "started_at": now(), "network_ui_switched": False},
    )
    initialize(run_dir)
    collector_inputs = [
        HERE / "pipeline.py",
        ROOT / "data/two-source/protocol.json",
        run_dir / "inputs",
        run_dir / "source-manifest.json",
    ]
    # The response pool is part of the collection dependency. Added/changed
    # responses invalidate collection even when homepage and rules are unchanged.
    collection_key = digest(files_hash(collector_inputs))[:16]
    output = run_dir / "iterations" / ("automation-" + collection_key)
    output.mkdir(parents=True, exist_ok=True)
    steps = Steps(output / "execution.json")
    steps.state["output"] = str(output.relative_to(ROOT))
    steps.state["network_ui_switched"] = False

    def collect():
        command(
            sys.executable,
            HERE / "pipeline.py",
            "--run",
            args.run,
            "--iteration",
            output.name,
            "--broad",
            *([] if args.online else ["--offline"])
        )
        coverage = check(output)
        # Online collection can add responses. Store the final pool fingerprint.
        return coverage

    collector_inputs.append(run_dir / "responses")
    steps.run("collection", collector_inputs, [output / n for n in COLLECTED], collect)
    # New responses produced above are valid inputs on the next invocation.
    steps.state["steps"]["collection"]["inputs"] = files_hash(collector_inputs)
    steps.state["steps"]["collection"]["input_sha256"] = digest(
        steps.state["steps"]["collection"]["inputs"]
    )
    save(steps.path, steps.state)
    check(output)
    mapping = ROOT / "data/two-source/person-mappings.json"
    steps.run(
        "persons",
        [
            HERE / "derived.py",
            HERE / "persons.py",
            output / "02-author-occurrences.json",
            mapping,
            run_dir / "inputs/current-students.json",
            run_dir / "inputs/graduated-students.json",
            ROOT / "data/two-source/prompts/person-audit.txt",
        ],
        [
            output / "02-persons.json",
            output / "02-person-review-queue.json",
            output / "02-person-review-warnings.json",
        ],
        lambda: people(output, mapping),
    )

    def vectors():
        seed_vectors(output, ROOT / "data/two-source/snapshot/vectors")
        command(
            ROOT / args.semantic_python, HERE / "features.py", output.relative_to(ROOT)
        )
        return verify_vectors(output)

    # Dense vector records are verified each run; their exact checksums are also
    # part of the vector step's output manifest after the first generation.
    steps.run(
        "vectors",
        [
            output / "05-feature-inputs.json",
            HERE / "features.py",
            ROOT / "scripts/features/semantic_features.py",
        ],
        [output / "05-vectors.json"] + vector_files(output),
        vectors,
    )
    steps.state["steps"]["vectors"]["outputs"] = files_hash(
        [output / "05-vectors.json"] + vector_files(output)
    )
    save(steps.path, steps.state)
    verify_vectors(output)
    legacy = ROOT / "_legacy/v1.0/data/keywords"
    results = ROOT / args.keyword_results if args.keyword_results else None
    assert (
        results is None or results.is_file()
    ), "Keyword result file does not exist: " + str(results)
    keyword_inputs = [
        HERE / "derived.py",
        output / "05-feature-inputs.json",
        output / "05-vectors.json",
        run_dir / "inputs/vocabulary.json",
        run_dir / "inputs/keywords.txt",
        *[legacy / n for n in ("inputs.json", "accepted.json", "vocabulary.json")],
        *([results] if results else []),
    ]
    steps.run(
        "keywords",
        keyword_inputs,
        [
            output / n
            for n in (
                "05-keywords.json",
                "05-keyword-pending.jsonl",
                "05-features.json",
                "05-feature-status.json",
            )
        ],
        lambda: keywords(output, legacy, results),
    )
    steps.run(
        "author-profiles",
        [
            HERE / "derived.py",
            output / "02-persons.json",
            output / "05-keywords.json",
            output / "05-feature-inputs.json",
        ],
        [output / "05-author-profiles.json"],
        lambda: profiles(output),
    )

    def accept():
        # Mandatory recomputation, including on a fully cached run.
        derived = validate_derived(output, mapping, legacy, results)
        coverage = check(output)
        queues = reviews(output)
        save(
            output / "automation-acceptance.json",
            {
                "checks_passed": True,
                "facts": coverage,
                "derived": derived,
                "vectors": verify_vectors(output),
                "pending": queues,
                "all_inputs_accounted": True,
                "completion": (
                    "validated_with_explicit_pending_tasks"
                    if any(queues.values())
                    else "complete"
                ),
                "code_sha256": files_hash(
                    [
                        HERE / n
                        for n in (
                            "run.py",
                            "derived.py",
                            "persons.py",
                            "model_jobs.py",
                            "validate.py",
                            "features.py",
                            "freeze.py",
                            "report.py",
                        )
                    ]
                    + [ROOT / "scripts/features/semantic_features.py"]
                ),
                "input_sha256": files_hash(
                    [mapping, ROOT / "data/two-source/prompts/person-audit.txt"]
                ),
                "derived_outputs_sha256": files_hash(
                    [
                        output / n
                        for n in (
                            "02-persons.json",
                            "02-person-review-queue.json",
                            "02-person-review-warnings.json",
                            "05-keywords.json",
                            "05-keyword-pending.jsonl",
                            "05-author-profiles.json",
                            "05-vectors.json",
                            "05-features.json",
                            "05-feature-status.json",
                            "review-queues.json",
                        )
                    ]
                    + vector_files(output)
                ),
            },
        )
        return queues

    steps.run(
        "acceptance",
        [],
        [output / "automation-acceptance.json", output / "review-queues.json"],
        accept,
        always=True,
    )
    queues = steps.state["steps"]["acceptance"]["result"]
    from report import run as report

    legacy_reports = ROOT / "_legacy/v1.0/data/atlas"
    steps.run(
        "comparison",
        [
            output / "automation-acceptance.json",
            HERE / "report.py",
            legacy_reports / "data.json",
            legacy_reports / "retrieval-data.json",
        ],
        [output / "comparison/comparison.json", output / "comparison/report.md"],
        lambda: report(output, output / "comparison"),
    )
    steps.state.update(
        pending=queues,
        acceptance="passed_with_pending" if any(queues.values()) else "passed",
    )
    save(steps.path, steps.state)
    if not args.no_freeze:
        steps.run(
            "freeze",
            [output / "automation-acceptance.json", HERE / "freeze.py"],
            [ROOT / "data/two-source/snapshot/manifest.json"],
            lambda: publish_snapshot(output, run_dir),
            always=True,
        )
        for filename in ("comparison.json", "report.md"):
            shutil.copy2(
                output / "comparison" / filename,
                ROOT / "data/two-source/results" / filename,
            )
    save(
        run_dir / "automation-status.json",
        {
            "state": "complete",
            "output": str(output.relative_to(ROOT)),
            "acceptance": steps.state["acceptance"],
            "pending": queues,
            "frozen": not args.no_freeze,
            "network_ui_switched": False,
            "steps": steps.state["steps"],
        },
    )
    print(
        "Validated run:",
        str(output.relative_to(ROOT)),
        "\nPending:",
        queues,
        "\nNetwork UI unchanged.",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if ACTIVE_RUN:
            save(
                ACTIVE_RUN / "automation-status.json",
                {"state": "failed", "reason": str(error), "network_ui_switched": False},
            )
        raise
