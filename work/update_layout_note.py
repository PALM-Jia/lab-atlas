# coding: utf-8
from pathlib import Path
import json
root=Path('outputs/paper-atlas')
old='坐标由引用与共同参考文献关系迭代计算。'
new='初始坐标由引用与共同参考文献计算；动态排布按当前关系与连接强度调整。'
p=root/'pipeline.py';p.write_text(p.read_text(encoding='utf8').replace(old,new),encoding='utf8')
p=root/'data.json';d=json.loads(p.read_text(encoding='utf8'));d['meta']['notes']=[t.replace(old,new)for t in d['meta']['notes']]
s=json.dumps(d,ensure_ascii=False,separators=(',',':'));p.write_text(s,encoding='utf8');(root/'data.js').write_text('window.ATLAS_DATA = '+s+';\n',encoding='utf8')
