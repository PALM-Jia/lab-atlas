"""Offline static release from adopted data. --check never writes files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from export_workflow_guide import projections as workflow_projections

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'outputs/paper-atlas'
PROJECTIONS = {
    'data/atlas/data.json': ('data.js', 'ATLAS_DATA'),
    'data/atlas/citation-history.json': ('citation-history.js', 'ATLAS_CITATION_HISTORY'),
    'data/atlas/retrieval-data.json': ('retrieval-data.js', 'ATLAS_RETRIEVAL'),
    'data/atlas/paper-keywords.json': ('paper-keywords.js', 'ATLAS_PAPER_KEYWORDS'),
    'data/atlas/paper-fields.json': ('paper-fields.js', 'ATLAS_PAPER_FIELDS'),
    'data/atlas/network-evidence.json': ('network-evidence.js', 'ATLAS_NETWORK_EVIDENCE'),
    'data/people/author-identities.json': ('author-identities.js', 'ATLAS_AUTHOR_IDENTITIES'),
    'data/people/author-groups.json': ('author-groups.js', 'ATLAS_AUTHOR_GROUPS'),
    'data/people/author-affiliations.json': ('author-affiliations.js', 'ATLAS_AUTHOR_AFFILIATIONS'),
}
PAGES = ('index.html', 'retrieval.html', 'workflow.html', 'workflow-map.html', 'keyword-missing.html')
WORKFLOW = ('workflow-guide.js', 'workflow-data.js', 'workflow-flow-data.js', 'workflow-explanations.js')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def dependencies():
    found = set(PAGES)
    for page in PAGES:
        source = (SITE/page).read_text(encoding='utf-8')
        for ref in re.findall(r'(?:src|href)=[\"\']([^\"\']+)[\"\']', source):
            if re.match(r'(?:https?:|mailto:|#)', ref):
                continue
            ref = ref.split('?',1)[0].split('#',1)[0]
            if ref:
                found.add(str(Path(ref).as_posix()))
    return sorted(found)

def assignment(path, variable):
    text = path.read_text(encoding='utf-8')
    start = text.index('window.'+variable+'=') + len('window.'+variable+'=')
    return json.JSONDecoder().raw_decode(text[start:])[0]


def citation_history(graph, retrieval):
    """Derive annual observations only from adopted citing lists and citation edges."""
    nodes = {p['id']: p for p in graph['nodes']}
    lab = {p['id']: p for p in retrieval['papers']}
    bibliography = retrieval['bibliography']
    snapshot = retrieval['meta'].get('citationsSnapshot') or retrieval['meta'].get('snapshot')
    incoming = {pid: set() for pid in nodes}
    for edge in graph['edges']:
        if edge['kind'] == 'citation' and edge['target'] in incoming:
            source = nodes.get(edge['source'])
            target = nodes[edge['target']]
            if source and (source.get('lab') or target.get('lab')):
                incoming[edge['target']].add(edge['source'])
    result = {}
    for pid, node in nodes.items():
        field = lab[pid]['fields'].get('citing', {}) if pid in lab else {}
        scope = 'database_citing_list' if pid in lab else 'observed_neighborhood'
        collected = set(field.get('ids', [])) if pid in lab else incoming[pid]
        total = field.get('total') if pid in lab else None
        available = field.get('state') in ('ready', 'empty', 'partial') if pid in lab else True
        if not available:
            total = None
        complete = available and total is not None and len(collected) == total
        status = ('complete' if complete else 'partial' if available else 'missing') if pid in lab else 'neighborhood'
        annual = {}
        unknown = 0
        for citing_id in sorted(collected):
            # Citing ids in the adopted database lists refer to bibliography records,
            # including citing papers omitted from the rendered graph neighborhood.
            record = bibliography.get(citing_id) if pid in lab else nodes.get(citing_id)
            year = record.get('year') if record else None
            if isinstance(year, int) and not isinstance(year, bool) and year > 0:
                annual[year] = annual.get(year, 0) + 1
            else:
                unknown += 1
        cumulative = 0
        rows = []
        for year, count in sorted(annual.items()):
            cumulative += count
            rows.append({'year': year, 'count': count, 'cumulative': cumulative})
        result[pid] = {'annual': rows, 'unknownYearCount': unknown,
                       'observedCount': len(collected) if available else None,
                       'databaseTotal': total, 'scope': scope, 'status': status,
                       'state': field.get('state', 'observed') if pid in lab else 'observed',
                       'complete': bool(complete), 'sources': field.get('sources', []) if pid in lab else [{'name': 'OpenAlex', 'description': 'Adopted direct citation edges touching laboratory papers'}],
                       'snapshot': snapshot}
    return {'meta': {'schemaVersion': 1, 'snapshot': snapshot,
                     'source': 'adopted retrieval-data bibliography/citing lists and data citation edges',
                     'semantics': 'Retrospective publication-year citation observations; unknown years excluded from dated cumulative counts. External counts cover only the observed laboratory neighborhood.'},
            'papers': result}

def check(out):
    for ref in dependencies():
        assert (out/ref).is_file(), 'Missing release dependency: '+ref
    for source, (target, variable) in PROJECTIONS.items():
        assert read(ROOT/source) == assignment(out/target,variable), 'Projection differs: '+target
    graph = read(ROOT/'data/atlas/data.json')
    ids = {p['id'] for p in graph['nodes']}
    assert len(ids) == len(graph['nodes'])
    assert all(e['source'] in ids and e['target'] in ids for e in graph['edges'])
    retrieval = read(ROOT/'data/atlas/retrieval-data.json')
    assert read(ROOT/'data/atlas/citation-history.json') == citation_history(graph, retrieval), 'Citation history differs from adopted evidence'
    assert ids == {p['id'] for p in retrieval['papers']+retrieval['external']}
    assert ids == set(read(ROOT/'data/atlas/paper-keywords.json')['papers'])
    assert ids == set(read(ROOT/'data/atlas/paper-fields.json')['papers'])
    contract = read(ROOT/'data/workflow/contract.json')
    assert [s['id'] for s in contract['stages']] == ['homepage','identity','lab-details','external','features']
    for target, (variable, expected) in workflow_projections().items():
        assert assignment(out/target, variable) == expected, 'Projection differs: '+target
    print('Offline check passed: %s nodes, %s edges, %s release files' % (len(ids),len(graph['edges']),len(dependencies())))

def build(out):
    out.mkdir(parents=True, exist_ok=True)
    history_path=ROOT/'data/atlas/citation-history.json'
    history=citation_history(read(ROOT/'data/atlas/data.json'),read(ROOT/'data/atlas/retrieval-data.json'))
    if not history_path.is_file() or read(history_path) != history:
        history_path.write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    generated = {target for target,_ in PROJECTIONS.values()} | set(WORKFLOW)
    for ref in dependencies():
        if ref in generated:
            continue
        target=out/ref
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.resolve() != (SITE/ref).resolve():
            shutil.copy2(str(SITE/ref),str(target))
    for source,(target,variable) in PROJECTIONS.items():
        payload=json.dumps(read(ROOT/source),ensure_ascii=False,separators=(',',':'))
        (out/target).write_text('window.'+variable+'='+payload+';\n',encoding='utf-8')
    subprocess.run([sys.executable,str(Path(__file__).with_name('export_workflow_guide.py')),'--output',str(out)],cwd=str(ROOT),check=True)
    check(out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=SITE)
    parser.add_argument('--check',action='store_true',help='Read-only data/projection validation')
    parser.add_argument('--refresh',action='store_true',help='Reapply adopted keywords and field mapping locally before build')
    args=parser.parse_args()
    if args.check:
        assert not args.refresh, '--check and --refresh are mutually exclusive'
        check(args.output)
    else:
        if args.refresh:
            subprocess.run([sys.executable,str(ROOT/'scripts/features/apply-reviewed-keywords.py')],cwd=str(ROOT),check=True)
        build(args.output)

if __name__=='__main__': main()
