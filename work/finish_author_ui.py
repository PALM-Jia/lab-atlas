# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/app.js')
s=p.read_text(encoding='utf-8')
s=s.replace('${e.papers?e.papers.map',"${e.papers&&!e.kind.startsWith('author_')?e.papers.map")
s=s.replace("const pairs=e.evidence?.paper_pairs||[];", """const profiles=e.evidence?.profiles||[];
      if(profiles.length)$('detail-content').insertAdjacentHTML('beforeend',`<div class="detail-section"><h3>主题数据覆盖</h3>${profiles.map(p=>`<p class="detail-meta">${esc(p.author_name)}：${p.profiled_papers} / ${p.total_papers} 篇论文参与主题画像</p>`).join('')}</div>`);
      const shared=e.evidence?.shared_papers||[];
      if(shared.length)$('detail-content').insertAdjacentHTML('beforeend',`<div class="detail-section"><h3>共同署名的主题依据</h3>${shared.map(id=>`<button class="neighbor" data-paper="${esc(id)}">${esc(nodeMap.get(id)?.title)}</button>`).join('')}</div>`);
      const pairs=e.evidence?.paper_pairs||[];""")
p.write_text(s,encoding='utf-8')
p=Path('work/check_frontend_viewport.cjs')
s=p.read_text(encoding='utf-8').replace("append(){},replaceChildren(){}", "append(){},insertAdjacentHTML(pos,html){this.innerHTML+=html;},replaceChildren(){}")
p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/README.md')
s=p.read_text(encoding='utf-8').replace('作者合作和时间脉络','作者网络和时间脉络').replace('作者合作节点权重','作者节点权重').replace('node-shadows.js、dynamic-layout.js、cytoscape.min.js','node-shadows.js、dynamic-layout.js、author-relations.js、cytoscape.min.js')
s+='''

## 作者关联

作者网络提供共同署名、研究方向相近、数据库主题相近、论文内容相近四种选择。计算范围是当前筛选中的实验室论文，展示参与论文最多的 65 位作者。

研究方向采用六类明确规则标签（排除“其他”）：每篇标签均分，再平均成作者画像。数据库主题采用 OpenAlex 主题 ID 和 score：每篇分数归一化，再对有主题的论文取平均，详情列出画像覆盖论文数。两者均取画像余弦相似度 ≥ 0.6。

论文内容使用已有 SPECTER2 论文连接，取两位作者不同论文之间相似度最大值，阈值 0.8；详情列出最多三对证据论文。同一篇共同署名论文不计为跨论文证据。

三种相近关系按每位作者最强四条连接的并集展示。切换关系更新动态排布，保留缩放和平移。连线详情列出共享主题、共同署名的主题依据和代表论文对。
'''
p.write_text(s,encoding='utf-8')
