from pathlib import Path
p=Path('outputs/paper-atlas/app.js');s=p.read_text(encoding='utf8')
s=s.replace('内容相近 ${(e.score*100).toFixed(1)+\'%\'} · ${v.pair_count} 对论文；下列为主要依据。', '论文相似度加权平均 ${(e.score*100).toFixed(1)+\'%\'} · ${v.pair_count} 对论文')
s=s.replace("$('detail-content').insertAdjacentHTML('beforeend',(e.evidence?.profiles||[]).map", "if(e.kind!=='author_semantic')$('detail-content').insertAdjacentHTML('beforeend',(e.evidence?.profiles||[]).map")
needle="    }\n  }\n  function authorDetail(n)"
s=s.replace(needle,"      if(e.kind==='author_semantic')$('detail-content').insertAdjacentHTML('beforeend',(e.evidence?.profiles||[]).map(p=>authorProfileMarkup(p)).join(''));\n"+needle)
p.write_text(s,encoding='utf8')
p=Path('work/check_author_relations.cjs');s=p.read_text(encoding='utf8').replace('/内容相近 78.9% · 4 对论文/', '/论文相似度加权平均 78.9% · 4 对论文/');p.write_text(s,encoding='utf8')
p=Path('outputs/paper-atlas/README.md');s=p.read_text(encoding='utf8');s=s.replace('作者网络当前仅提供共同署名、研究方向标签、共同论文关键词。两种 OpenAlex 数据库主题和 SPECTER2 作者关联准则已从页面移除，旧链接参数回退至共同署名；论文地图的内容相似准则保留。下文中被移除准则的计算说明为历史实现记录。','作者网络提供共同署名、标题与摘要相似、研究方向分布相似、论文关键词分布相似。论文及时间视图提供直接引用、共同作者、标题与摘要相似；研究主题重合已移除，旧 topic 关系参数转为 semantic。研究方向仍可用于分类筛选。')
start=s.index('SEU 的 Xiaoyu Wang 显示为 Xiaoyu Wang');end=s.index('\n',start)
s=s[:start]+'SEU 的 Xiaoyu Wang 显示为 Xiaoyu Wang，内部人员 ID、身份归属与分类保持原值，Monash 同名作者仍分列。作者的“标题与摘要相似”直接使用 data.js 中全部实验室论文对的本地 SPECTER2 分数（144 篇），不使用旧 author-semantic.js，也不使用论文图经阈值筛选后的连线。当前筛选内，两位作者所有不同论文对的相似度按双方署名权重乘积取加权平均；默认一作 1、其他署名 0.2。共同署名论文不与自身比较。作者对得分中位数为阈值，不限每位作者的边数。右栏优先展示贡献最大的 3 对论文，再列各作者的论文贡献权重及仅标题输入标记。切换年份、搜索和署名三态会重算作者关系。'+s[end:];p.write_text(s,encoding='utf8')
p=Path('outputs/paper-atlas/workflow-explanations.js');s=p.read_text(encoding='utf8');needle='研究方向画像则先在每篇论文的多个标签间均分贡献，再汇总为作者的研究方向占比。';s=s.replace(needle,needle+'作者的标题与摘要相似关系使用当前筛选内全部不同论文对的语义相似度，按双方署名贡献加权平均；共同署名的同一篇论文不与自身比较。');p.write_text(s,encoding='utf8')
