"""Local features from the isolated text snapshot, using existing pinned model weights."""

import argparse
import sys
from pathlib import Path
from pipeline import ROOT, read, save, digest, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    output = ROOT / args.output
    papers = read(output / "05-feature-inputs.json")["papers"]
    for p in papers:
        assert p["input_sha256"] == digest(
            {k: p[k] for k in ("id", "title", "abstract")}
        )
    sys.path.insert(0, str(ROOT / "scripts/features"))
    from semantic_features import generate_embeddings, valid_vector, MODEL

    rows, model = generate_embeddings(papers, cache=output / "vectors", threads=8)
    for paper in papers:
        assert valid_vector(paper.get("embedding")), paper["id"]
    save(output / "05-vectors.json", {"model": model, "rows": rows})
    state = read(output / "05-feature-status.json")
    state["vectors"] = summary(
        [
            {
                "state": "ready" if r["status"] == "success" else "missing",
                "reason": r["reason"],
            }
            for r in rows
        ]
    )
    save(output / "05-feature-status.json", state)
    # Feature outputs contain compact content addresses, not a second dense vector copy.
    save(
        output / "05-features.json",
        {
            "model": MODEL,
            "papers": [
                {
                    "id": p["id"],
                    "input_sha256": p["input_sha256"],
                    "vector_key": p["semantic_vector_key"],
                    "keyword_state": "not_generated",
                    "keyword_reason": "independent_annotation_step_not_executed",
                }
                for p in papers
            ],
        },
    )
    print("Local vector coverage:", state["vectors"], flush=True)


if __name__ == "__main__":
    main()
