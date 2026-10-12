from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path('outputs/paper-atlas')
# Sync explanatory limits from the same data snapshot used by the graph.
import json, re
payload=(root/'data.js').read_text(encoding='utf8')
limits=json.loads(payload.split('=',1)[1].strip().rstrip(';'))['meta']['limits']
prose_path=root/'workflow-explanations.js'
prose=prose_path.read_text(encoding='utf8')
prose=re.sub(r'每篇实验室论文最多采集 \d+ 条被引记录', f"每篇实验室论文最多采集 {limits['citing_per_seed']} 条被引记录", prose)
prose=re.sub(r'外部网络节点上限为 \d+', f"外部网络节点上限为 {limits['external_nodes']}", prose)
prose_path.write_text(prose,encoding='utf8')
with ZipFile('outputs/paper-atlas.zip','w',ZIP_DEFLATED) as archive:
    for p in root.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.partial'): archive.write(p,p.relative_to(root.parent))
print('Site package updated')
