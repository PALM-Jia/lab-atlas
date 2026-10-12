"""Ensure both graph builders exclude external-only citations, retaining both lab directions."""
import copy
import ast
import collections
import hashlib
import math
import re
import unicodedata
from types import SimpleNamespace
from pathlib import Path

root = Path(__file__).resolve().parent.parent / 'outputs/paper-atlas'
def load_functions(filename, functions, assignments, namespace):
    tree = ast.parse((root / filename).read_text(encoding='utf8'))
    tree.body = [node for node in tree.body if
                 isinstance(node, ast.FunctionDef) and node.name in functions or
                 isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in assignments for t in node.targets)]
    exec(compile(tree, str(root / filename), 'exec'), namespace)
    return SimpleNamespace(**namespace)
collect = load_functions('collect.py', {'norm', 'tags_for', 'build_graph'}, {'TOPICS'},
                         dict(math=math, re=re, unicodedata=unicodedata, hashlib=hashlib))
pipeline = load_functions('pipeline.py', {'graph'}, {'KINDS'}, dict(base=collect, math=math, collections=collections))

def paper(pid, lab, references):
    return {'id': pid, 'openalex': 'https://openalex.org/' + pid,
            'lab': lab, 'title': 'Clustering', 'authors': [], 'references': references}
nodes = [paper('Wlab', True, ['Wext1']),
         paper('Wext1', False, ['Wlab', 'Wext2']),
         paper('Wext2', False, ['Wext1'])]
expected = {('Wlab', 'Wext1'), ('Wext1', 'Wlab')}
for name, build in [('collect', lambda rows: collect.build_graph(rows, None, {})),
                    ('pipeline', lambda rows: pipeline.graph(rows, {}))]:
    result = build(copy.deepcopy(nodes))
    edges = result[0] if name == 'pipeline' else result
    assert {(e['source'], e['target']) for e in edges if e['kind'] == 'citation'} == expected, name
    if name == 'pipeline':
        assert {(e['source'], e['target']) for e in result[1] if e['kind'] == 'citation'} == expected
print('PASS: both offline builders prohibit external-only citations in full and displayed graphs.')
