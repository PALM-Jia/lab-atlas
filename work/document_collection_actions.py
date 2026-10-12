# coding: utf-8
import json
from pathlib import Path
root=Path('outputs/paper-atlas')
text=(root/'README.md').read_text(encoding='utf-8-sig')
section=text.split('## 已执行的补救操作\n',1)[1].split('\n## 常见原因',1)[0]
actions=[]
for line in section.splitlines():
    if line and line.split('.',1)[0].isdigit():
        number,description=line.split('. ',1)
        actions.append({'sequence':int(number),'record':description})
(root/'collection-actions.json').write_text(json.dumps({'scope':'已执行操作及其结果；未执行路径在记录内明确区分','actions':actions},ensure_ascii=False,indent=2),encoding='utf8')
assert len(actions)==12
