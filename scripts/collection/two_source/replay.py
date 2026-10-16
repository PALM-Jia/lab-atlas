"""Replay a frozen collector and protocol, not whatever rules happen to be current."""
import argparse
import importlib.util
import sys
from pathlib import Path
from pipeline import ROOT, digest, read
from validate import provenance


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('frozen_output')
    parser.add_argument('--iteration',default='frozen-replay')
    args=parser.parse_args()
    original=ROOT/args.frozen_output
    config,manifest,_=provenance(original)
    run_dir=original.parents[1]
    assert (run_dir/'iterations'/args.iteration).resolve()!=original.resolve(),'Replay must not overwrite the frozen iteration'
    # Older collectors read the prompt from the project configuration path.
    # Refuse a changed prompt rather than silently changing old feature tasks.
    for name in ('keywords.txt','identity-audit.txt'):
        assert digest((ROOT/'data/two-source/prompts'/name).read_bytes())==digest((run_dir/'inputs'/name).read_bytes()),'Restore the frozen prompt before replay: '+name
    spec=importlib.util.spec_from_file_location('two_source_frozen_replay',original/'pipeline.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT=ROOT
    module.CONFIG=original/'protocol.json'
    sys.argv=[str(original/'pipeline.py'),'--run',str(run_dir.relative_to(ROOT)),'--iteration',args.iteration,'--offline']
    if manifest['broad']:sys.argv.append('--broad')
    sys.argv.extend(['--ids',','.join(manifest['paper_ids'])])
    module.main()
    replay=run_dir/'iterations'/args.iteration
    names=['01-homepage.json','02-identity.json','02-author-occurrences.json','02-review-queue.json','03-lab-details.json',
           '03-identity-review-queue.json','04-external.json','04-relations.json','04-graph-selection.json','05-feature-inputs.json','05-keyword-tasks.jsonl']
    for name in names:
        assert digest((original/name).read_bytes())==digest((replay/name).read_bytes()),'Replay mismatch: '+name
    print('Frozen collector replay is byte-identical for all 11 stage outputs; no network or legacy data read.',flush=True)


if __name__=='__main__':
    main()
