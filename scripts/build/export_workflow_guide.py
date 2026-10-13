#!/usr/bin/env python3
"""Build browser workflow projections from the adopted local JSON inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/workflow"
CONTRACT = INPUT / "contract.json"

DISPLAY_IDS = {
    "homepage": "import",
    "identity": "locate",
    "lab-details": "collect",
    "external": "external",
    "features": "features",
}


def projections() -> dict:
    """Read adopted inputs and return browser payloads without writing files."""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    stages = {}
    for stage in contract["stages"]:
        display_id = DISPLAY_IDS[stage["id"]]
        stages[display_id] = {
            "title": stage["title"],
            "tooltip": [
                "；".join(stage["inputs"]) + " → " + "；".join(stage["adopted_outputs"]),
                stage["handoff"],
            ],
            "description": "；".join(stage["adopted_outputs"]),
            "input": "；".join(stage["inputs"]),
            "added": "；".join(stage["adopted_outputs"]),
            "boundary": stage["handoff"],
            "mode": stage["mode"],
            "automation": stage["automation"],
            "unresolved": stage["unresolved"],
            "evidence": stage["evidence"],
        }
    payload = {
        "schema": contract["schema"],
        "fieldProvenance": "各阶段保留原始观察值、采用值、来源方法和未决状态。",
        "featureProvenance": "特征保留文本输入、标注审核、规则或模型版本及署名权重。",
        "stages": stages,
    }
    result = {"workflow-guide.js": ("WORKFLOW_GUIDE", payload)}
    titles = {DISPLAY_IDS[stage["id"]]: stage["title"] for stage in contract["stages"]}
    for source, target, variable in [
        ("map.json", "workflow-data.js", "WORKFLOW_MAP"),
        ("diagram.json", "workflow-flow-data.js", "WORKFLOW_FLOW"),
        ("explanations.json", "workflow-explanations.js", "WORKFLOW_EXPLANATIONS"),
    ]:
        projection = json.loads((INPUT / source).read_text(encoding="utf-8"))
        if source == "map.json":
            for number, stage in enumerate(projection["stages"], 1):
                stage["label"] = chr(0x2460 + number - 1) + " " + titles[stage["id"]]
        result[target] = (variable, projection)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/paper-atlas",
                        help="Directory for generated browser JavaScript")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    for target, (variable, payload) in projections().items():
        (output / target).write_text(
            "window." + variable + "=" + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
