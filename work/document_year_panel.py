# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/README.md');s=p.read_text(encoding='utf-8').replace('滑条范围涵盖实验室与外部文献的已知年份','滑条固定为 2010–2027，2010 左端表示 −∞ 并包含 2010 年及更早论文').replace('X 轴线性表示发表年份','X 轴在 2010–2027 区间线性表示发表年份，2010 年及更早论文归入左端 −∞ 桶（详情保留实际年份）');s+='''

右侧面板常驻当前关联说明：随论文和作者关联选项更新，列出数据来源、计算方式、阈值、连接裁剪方式和当前节点/连线数；选择节点或连线后仍保留说明。
''';p.write_text(s,encoding='utf-8')
