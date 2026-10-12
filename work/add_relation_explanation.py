# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/app.js');s=p.read_text(encoding='utf-8');marker='  function renderList() {'
s=s.replace(marker,'''  function explainRelation(){
    const descriptions={
      citation:'依据 OpenAlex 参考文献记录，箭头由引用论文指向被引用论文。',
      coupling:'两篇论文引用相同文献。强度 = 共同参考数 ÷ √(两篇参考数乘积)；共同参考至少 2 篇，强度 ≥ 0.06。',
      cocitation:'采集到的其他论文同时引用这两篇论文。强度 = 共同施引数 ÷ √(两篇已采集施引数乘积)。每篇种子最多采集 600 篇施引文献。',
      author:'两篇实验室论文共享作者 ID；缺少 ID 时按署名姓名匹配。强度为共同作者数，排除 Yuheng Jia。',
      institution:'两篇实验室论文共享 OpenAlex 发表署名机构 ID，强度为共同机构数。',
      semantic:'比较 Semantic Scholar SPECTER2 论文向量，余弦相似度 ≥ 0.8 时连线。',
      topic:'优先比较 OpenAlex 主题 ID；没有共同数据库主题时，实验室论文按标题和摘要的方向标签关联。强度 = 共享主题数 ÷ 合并主题数。',
      series:'按人工确认的研究系列连线。目前未录入系列标注。'
    };
    const authorDescriptions={
      coauthor:'作者共同署名同一篇实验室论文时连线，强度为共同署名论文数。',
      topic:'每篇论文的明确方向标签均分权重，再按作者有标签的论文平均形成画像。比较画像余弦相似度，≥ 0.6 时连线；“其他”标签不参与。',
      'database-topic':'每篇论文的 OpenAlex 主题分数归一化，再按作者有数据库主题的论文平均形成画像。画像余弦相似度 ≥ 0.6 时连线。',
      semantic:'取两位作者不同论文间已展示的 SPECTER2 连接相似度最大值，≥ 0.8 时连线。连线详情列出最多 3 对论文。'
    };
    const author=state.view==='authors';
    const kind=author?({coauthor:'author',topic:'author_topic','database-topic':'author_database_topic',semantic:'author_semantic'}[state.authorRelation]):state.relation;
    const description=author?authorDescriptions[state.authorRelation]:descriptions[state.relation];
    const pruning=author?(state.authorRelation==='coauthor'?'共同署名连接全部展示。':'每位作者选取最强 4 条连接，取两端选择的并集。'):(state.relation==='citation'?'直接引用连接全部展示。':'每个节点选取最强 4 条连接，取两端选择的并集。');
    $('relation-explanation').innerHTML=`<h3>${esc(kinds[kind])}</h3><p>${esc(description)}</p>${author?'<p>按当前筛选的实验室论文计算，展示参与论文数最多的 65 位作者。</p>':''}<p class="relation-stats">${esc(pruning)}当前 ${cy.nodes().length} 个节点，${graphData.length} 条连接。</p>`;
  }
''' +marker)
s=s.replace("    renderList();\n    if(state.selected) focus", "    explainRelation();\n    renderList();\n    if(state.selected) focus")
p.write_text(s,encoding='utf-8')
