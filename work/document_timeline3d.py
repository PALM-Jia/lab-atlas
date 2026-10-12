# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/README.md');s=p.read_text(encoding='utf-8').replace('author-relations.js、cytoscape.min.js','author-relations.js、timeline-3d.js、cytoscape.min.js').replace('时间脉络保持年份和主题坐标。','时间脉络使用三维时间坐标与原有论文关联布局。')
s+='''

## 三维时间脉络

时间脉络采用真实三维坐标和透视投影。X 轴线性表示发表年份，Y/Z 轴分别采用预计算论文关联布局的两个坐标（全数据归一化）；颜色仍表示研究方向。年份未知条目放在单独一带。时间轴范围随当前可见论文的已知年份更新，平移、旋转和缩放保持原值。

拖拽旋转，Shift 拖拽或右键拖拽平移，滚轮缩放；适应画布重新设置视角。悬停预览、点击论文或连线查看详情，论文索引与筛选同步。切回二维视图保留各自视角。

使用原生 Canvas，无新增外部依赖或网络请求。仅在交互、筛选或尺寸变化时绘制，拖动限频 30 次/秒；三维视图不运行逐帧力导向计算。
''';p.write_text(s,encoding='utf-8')
