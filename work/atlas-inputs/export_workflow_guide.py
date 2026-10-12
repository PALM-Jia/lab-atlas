#!/usr/bin/env python3
"""Project the workflow contract into the small guide consumed by workflow.html."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "work/atlas-inputs/workflow-contract.json"
OUTPUT = ROOT / "outputs/paper-atlas/workflow-guide.js"

DISPLAY_IDS = {
    "homepage": "import",
    "identity": "locate",
    "lab-details": "collect",
    "external": "external",
    "features": "features",
}


def main() -> None:
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
    OUTPUT.write_text(
        "window.WORKFLOW_GUIDE=" + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
