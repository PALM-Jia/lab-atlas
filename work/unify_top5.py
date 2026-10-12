from pathlib import Path
root=Path('outputs/paper-atlas')
p=root/'author-relations.js';s=p.read_text(encoding='utf8')
s=s.replace("if (!databaseTopic&&score < 0.6) continue;", "if (!common.length) continue;")
s=s.replace("+' 阈值为当前有效作者对得分的中位数。'", "+' 每位作者选取最强 5 条，取两端选择的并集。'").replace('画像余弦相似度 ≥ 0.6。','画像余弦相似度，每位作者选取最强 5 条，取两端选择的并集。')
a=s.index('    const scores=edges.map');b=s.index('    result.profiles=',a)
s=s[:a]+"""    const select=root.selectAtlasTopEdges||(typeof require==='function'?require('./paper-density.js').selectTopEdges:null);
    const result=select(edges,5);
    result.stats={threshold:null,top_k:5,valid_pairs:edges.length,eligible_pairs:edges.length,selected_pairs:result.length};
"""+s[b:];p.write_text(s,encoding='utf8')
p=root/'author-keywords.js';s=p.read_text(encoding='utf8');a=s.index('    const scores=edges.map');b=s.index('    result.profiles=',a)
s=s[:a]+"""    const select=root.selectAtlasTopEdges||(typeof require==='function'?require('./paper-density.js').selectTopEdges:null);
    const result=select(edges,5);
    result.stats={threshold:null,top_k:5,valid_pairs:validPairs,positive_pairs:edges.length,eligible_pairs:edges.length,selected_pairs:result.length};
"""+s[b:];p.write_text(s,encoding='utf8')
p=root/'app.js';s=p.read_text(encoding='utf8')
s=s.replace("? [...links.values()].filter(e=>ids.has(e.source)&&ids.has(e.target))", "? window.selectAtlasTopEdges([...links.values()].filter(e=>ids.has(e.source)&&ids.has(e.target)),5)")
s=s.replace("state.relation==='semantic'?window.coverSemanticPapers(visible,graphData,4):window.limitPaperEdges(visible,graphData,4)", "window.limitPaperEdges(visible,graphData,5)")
s=s.replace('优先让至少 95% 有向量且有足够候选的实验室论文保留两条连接，再将平均连接数控制在约 4。','')
s=s.replace('每位作者选取最相近的 5 位，任一方选中即连线，不设分数阈值。','')
s=s.replace('比较两位作者的方向分布，余弦相似度达到 60.0% 时连线。','比较两位作者的方向分布，余弦相似度越高越接近。')
s='\n'.join(line for line in s.split('\n') if "const threshold=author&&state.authorRelation==='keywords'" not in line)
a=s.index("    $('relation-explanation').innerHTML=");b=s.index('\n',a)
s=s[:a]+"""    const selectionRule=`<p>每${author?'位作者':'篇论文'}选取最强的 5 条关联，任一端选中即保留；不足 5 条时全部保留。${!author&&state.relation==='citation'?'直接引用的边同分，按固定顺序选取。':''}</p>`;
    $('relation-explanation').innerHTML=`<h3>${esc(kinds[kind])}</h3><p>${esc(description)}</p>${weightExplanation}${selectionRule}${keywordCoverage}`;"""+s[b:]
p.write_text(s,encoding='utf8')
p=root/'index.html';s=p.read_text(encoding='utf8');tag='<script defer src="paper-density.js"></script>';s=s.replace(tag,'').replace('<script defer src="author-keywords.js">',tag+'<script defer src="author-keywords.js">');p.write_text(s,encoding='utf8')
p=root/'README.md';s=p.read_text(encoding='utf8');s+='\n\n当前网络显示统一采用 top-5：作者、论文、时间脉络的全部可选关联规则均在当前筛选内按原始分数为每个节点选取前 5 条边，取两端选择的并集。不再使用分数阈值、正分中位数、平均度数 4 或 95% 覆盖补边。存在共同署名、共同关键词或共同方向才形成对应候选；没有依据时不补边。直接引用同分按边 ID 稳定排序，保留引用方向。同分排序不代表引用重要性。完整候选数据保留，筛选只改变当前显示。\n';p.write_text(s,encoding='utf8')
