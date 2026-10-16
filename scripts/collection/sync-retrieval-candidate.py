"""Synchronize only the local candidate; adoption remains a separate review step."""

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "work" / "retrieval-candidate"


def load(name):
    path = ROOT / "scripts" / "features" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    graph = read(ROOT / "data" / "atlas" / "data.json")
    dashboard = read(CANDIDATE / "retrieval-data.json")
    counts = load("sync-keyword-retrieval.py").synchronize(graph, dashboard)
    dashboard = load("refresh-retrieval-copy.py").refresh(dashboard)
    network = read(CANDIDATE / "network-evidence.json")
    for paper in dashboard["papers"]:
        fields = network["papers"][paper["id"]]["fields"]
        for key in ("keywords", "research_task"):
            fields[key] = copy.deepcopy(paper["fields"][key])
        fields.pop("directions", None)
        for key in tuple(fields):
            if key in paper["fields"]:
                fields[key] = copy.deepcopy(paper["fields"][key])
    network["coverage"]["keywords"] = dashboard["meta"]["coverage"]["keywords"]
    network["keywordAnnotations"] = dict(counts)
    for name, value in [
        ("retrieval-data.json", dashboard),
        ("network-evidence.json", network),
    ]:
        (CANDIDATE / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {"candidate": str(CANDIDATE), "statuses": dict(counts)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
