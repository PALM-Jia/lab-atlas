#!/usr/bin/env python3
"""Build browser workflow projections from the adopted local JSON inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/workflow"
PROTOCOL = ROOT / 'data/two-source/protocol.json'

DISPLAY_IDS = {
    "homepage": "import",
    "identity": "locate",
    "lab-details": "collect",
    "external": "external",
    "features": "features",
}


def workflow_contract() -> dict:
    """Reader-facing contract is a projection of the executable collection protocol."""
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    return {
        'schema': protocol['schema'], 'rules_version': protocol['rules_version'],
        'purpose': protocol['page']['purpose'], 'generated_from': 'data/two-source/protocol.json',
        'stages': [{**stage, **protocol['page']['stages'][stage['id']]} for stage in protocol['stages']],
        'field_semantics': protocol['page']['field_semantics'],
    }


def execution_status(protocol):
    snapshot = ROOT/'data/two-source/snapshot'
    coverage = json.loads((snapshot/'acceptance.json').read_text(encoding='utf-8'))['coverage']
    features = json.loads((snapshot/'05-feature-status.json').read_text(encoding='utf-8'))
    identity = coverage['identity']
    external = coverage['external']
    abstract = coverage['details']['abstract']
    persons_path = snapshot/'02-persons.json'
    person_pending = json.loads(persons_path.read_text(encoding='utf-8'))['summary']['pending_occurrences'] if persons_path.exists() else coverage['author_group_pending']
    values = {
        'lab': coverage['homepage']['papers'], 'unparsed': coverage['homepage']['unparsed'],
        'identity': identity['success'], 'unmatched': identity['states'].get('unmatched',0), 'ambiguous': identity['states'].get('ambiguous',0),
        'abstract': abstract['states'].get('ready',0), 'external': external['success'], 'external_total': external['total'],
        'external_missing': external['total']-external['success'], 'vectors': features['vectors'].get('success',0),
        'graph_external': coverage['graph_external'],
        'feature_total': features['papers'], 'keyword_pending': features['keyword_tasks']['states'].get('not_generated',0),
        'keyword_ready': features['keyword_tasks']['success'],
        'roster_pending': coverage['author_group_pending'],
        'person_pending': person_pending,
    }
    return [{**row,'result':row['result'].format(**values)} for row in protocol['page']['execution']]


def projections() -> dict:
    """Read adopted inputs and return browser payloads without writing files."""
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    contract = workflow_contract()
    stages = {}
    for stage in contract["stages"]:
        display_id = DISPLAY_IDS[stage["id"]]
        stages[display_id] = {
            "title": stage["title"],
            "tooltip": [
                stage['description'],
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
        'notice': protocol['page']['notice'],
    }
    result = {"workflow-guide.js": ("WORKFLOW_GUIDE", payload)}
    titles = {DISPLAY_IDS[stage["id"]]: stage["title"] for stage in contract["stages"]}
    for source, target, variable in [
        ("map.json", "workflow-data.js", "WORKFLOW_MAP"),
        ("diagram.json", "workflow-flow-data.js", "WORKFLOW_FLOW"),
    ]:
        projection = json.loads((INPUT / source).read_text(encoding="utf-8"))
        if source == "map.json":
            for number, stage in enumerate(projection["stages"], 1):
                stage["label"] = chr(0x2460 + number - 1) + " " + titles[stage["id"]]
                stage['mode'] = stages[stage['id']]['mode'] + ' · ' + stages[stage['id']]['automation']
        if source == 'diagram.json':
            descriptions = protocol['page']['diagram_descriptions']
            for row in projection['rows']:
                row['description'] = descriptions['rows'][row['id']]
            for node in projection['nodes']:
                node['description'] = descriptions['nodes'][node['id']]
            for process in projection['processes']:
                process.update(descriptions['processes'][process['id']])
            nodes = {n['id']: n for n in projection['nodes'] + projection['processes']}
            for edge in projection['edges']:
                edge['description'] = descriptions['edges'].get(edge['from']+'>'+edge['to'], nodes[edge['to']]['description'])
        result[target] = (variable, projection)
    result['workflow-explanations.js'] = ('WORKFLOW_EXPLANATIONS', protocol['page']['explanations'])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/paper-atlas",
                        help="Directory for generated browser JavaScript")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    (INPUT/'contract.json').write_bytes((json.dumps(workflow_contract(),ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    for target, (variable, payload) in projections().items():
        (output / target).write_text(
            "window." + variable + "=" + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
