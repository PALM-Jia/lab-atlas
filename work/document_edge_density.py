# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/README.md');s=p.read_text(encoding='utf-8');s+='''

网络连线按当前可见图的平均度数自适应淡化：平均度数为 2 × 连线数 / 节点数，≤ 5 时维持原不透明度，> 5 时乘以 5 / 平均度数。论文、作者和三维时间网络共用这一规则；选中连线保持原高亮强度，无关连线继续随密度降低。每次筛选或切换关联重新计算。
''';p.write_text(s,encoding='utf-8')
