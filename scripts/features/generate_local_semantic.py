"""Refresh only semantic features/edges, preserving all other collected fields."""

import collections, copy, datetime, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / "data/atlas"
REPORTS = ROOT / "work/reports"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_features import generate_embeddings, semantic_edges


def summary(rows):
    good = sum(r["status"] == "success" for r in rows)
    total = len(rows)
    return {
        "total": total,
        "success": good,
        "explained_failure": total - good,
        "success_rate": round(good / total * 100, 4) if total else 0,
        "failure_rate": round((total - good) / total * 100, 4) if total else 0,
        "accounted_rate": 100 if total else 0,
        "unexplained": 0,
        "reasons": dict(collections.Counter(r["reason"] for r in rows)),
        "items": rows,
    }


def save(name, value, pretty=False):
    p = ATLAS / name
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix(p.suffix + ".partial")
    temp.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        ),
        encoding="utf8",
    )
    temp.replace(p)


def synchronize_vectors(graph, rows, retrieval, network):
    """Copy only vector fields and semantic metadata; never rebuild adopted evidence."""
    retrieval, network = copy.deepcopy(retrieval), copy.deepcopy(network)
    papers = {p["id"]: p for p in graph["nodes"]}
    reports = {r["id"]: r for r in rows}
    semantic = graph["meta"]["semantic"]
    for row in retrieval["papers"] + retrieval.get("external", []):
        paper = papers[row["id"]]
        report = reports[row["id"]]
        ready = (
            paper.get("semantic_status") == "available"
            and report["status"] == "success"
        )
        info = copy.deepcopy(report.get("input"))
        label = (
            "标题＋摘要" if info and "abstract" in info.get("fields", []) else "仅标题"
        )
        dimensions = semantic["dimensions"]
        reason = "本地 SPECTER2 输入：" + label + "。"
        if info and info.get("truncated"):
            reason += "超过模型长度的部分已截断。"
        if not ready:
            reason = (
                report.get("failure_summary")
                or report.get("reason")
                or "本地向量未生成。"
            )
        vector = {
            "value": "SPECTER2 · %s维 · %s" % (dimensions, label) if ready else None,
            "state": "ready" if ready else "missing",
            "sources": [
                {
                    "name": "本地 SPECTER2",
                    "url": "https://huggingface.co/allenai/specter2",
                }
            ],
            "explanation": reason,
            "model": semantic["model"],
            "dimensions": dimensions if ready else None,
            "input": info,
            "base": semantic.get("base"),
            "adapter": semantic.get("adapter"),
            "baseRevision": semantic.get("base_revision"),
            "adapterRevision": semantic.get("adapter_revision"),
            "paperId": paper.get("semantic_paper_id"),
            "identifier": None,
            "routes": [] if ready else copy.deepcopy(report.get("failure_sources", [])),
            "assessment": (
                ""
                if ready
                else report.get("failure_assessment", {}).get("judgment", "")
            ),
            "next": (
                ""
                if ready
                else report.get("failure_assessment", {}).get("next_action", "")
            ),
        }
        row["fields"]["vector"] = vector
        if row["id"] in network.get("papers", {}):
            network["papers"][row["id"]]["fields"]["vector"] = copy.deepcopy(vector)
    retrieval.setdefault("meta", {})["semantic"] = copy.deepcopy(semantic)
    network.setdefault("meta", {})["semantic"] = copy.deepcopy(semantic)
    return retrieval, network


def run():
    REPORTS.mkdir(parents=True, exist_ok=True)
    d = json.loads((ATLAS / "data.json").read_text(encoding="utf8"))
    rows, model = generate_embeddings(d["nodes"])
    edges = semantic_edges(d["nodes"])
    d["edges"] = [e for e in d["edges"] if e["kind"] != "semantic"] + edges
    d["meta"]["semantic"] = {
        **model,
        "updated": datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).isoformat(timespec="seconds"),
    }
    d["meta"]["stats"]["vectors"] = model["ready"]
    for key in ["edges", "full_edges"]:
        d["meta"]["stats"][key]["semantic"] = len(edges)
    for p in d["nodes"]:
        p.pop("embedding", None)
    report = summary(rows)
    save(
        "semantic-generation.json",
        {"model": d["meta"]["semantic"], "coverage": report},
        True,
    )
    acceptance = json.loads((ATLAS / "acceptance.json").read_text(encoding="utf8"))
    history = REPORTS / "semantic-api-history.json"
    if not history.exists():
        history.write_text(
            json.dumps(
                {
                    k: acceptance["steps"][k]
                    for k in ["08_content_vector", "07_readiness_semantic"]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf8",
        )
    acceptance["steps"]["08_content_vector"] = report
    acceptance["steps"]["07_readiness_semantic"] = summary(
        [
            {
                **r,
                "reason": (
                    "relation_input_ready" if r["status"] == "success" else r["reason"]
                ),
            }
            for r in rows
            if next(p["lab"] for p in d["nodes"] if p["id"] == r["id"])
        ]
    )
    acceptance["meta"] = d["meta"]
    save("acceptance.json", acceptance, True)
    coverage = json.loads((ATLAS / "coverage.json").read_text(encoding="utf8"))
    coverage["meta"] = d["meta"]
    save("coverage.json", coverage, True)
    retrieval = json.loads((ATLAS / "retrieval-data.json").read_text(encoding="utf8"))
    network = json.loads((ATLAS / "network-evidence.json").read_text(encoding="utf8"))
    retrieval, network = synchronize_vectors(d, rows, retrieval, network)
    save("retrieval-data.json", retrieval)
    save("network-evidence.json", network)
    save("data.json", d)
    print(
        json.dumps(
            {
                "model": model,
                "edges": len(edges),
                "lab_success": acceptance["steps"]["07_readiness_semantic"]["success"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    run()
