from pathlib import Path
root=Path('outputs/paper-atlas')
p=root/'index.html';s=p.read_text(encoding='utf8');s=s.replace('<option value="topic">研究主题重合</option>','').replace('<option value="coauthor">共同署名</option>','<option value="coauthor">共同署名</option><option value="semantic">标题与摘要相似</option>');p.write_text(s,encoding='utf8')
p=root/'app.js';s=p.read_text(encoding='utf8')
s=s.replace("const kinds =", "const semanticPaperEdges=D.edges.filter(e=>e.kind==='semantic'&&nodeMap.get(e.source)?.lab&&nodeMap.get(e.target)?.lab);\n  const kinds =",1)
s=s.replace("semantic:'标题与摘要相似',topic:'研究主题重合'", "semantic:'标题与摘要相似',author_semantic:'标题与摘要相似'")
s=s.replace('edge[kind="author_keyword"], edge[kind="author_topic"]','edge[kind="author_keyword"], edge[kind="author_topic"], edge[kind="author_semantic"]')
s=s.replace('authors:top,papers,mode:state.authorRelation','authors:top,papers,paperEdges:semanticPaperEdges,mode:state.authorRelation')
s='\n'.join(line for line in s.split('\n') if "topic:'两篇论文有相同的 OpenAlex" not in line)
s=s.replace("const authorDescriptions={", "const authorDescriptions={\n      semantic:'比较两位作者当前筛选内的全部不同论文对，将标题与摘要的向量相似度按署名权重取平均。共同署名的同一篇论文不与自身比较；无摘要的论文仅用标题。得分达到当前作者对得分的中位数时连线。',")
s=s.replace("keywords:'author_keyword'}", "keywords:'author_keyword',semantic:'author_semantic'}")
s=s.replace("author&&state.authorRelation==='keywords'?`<p>连线阈值", "author&&['keywords','semantic'].includes(state.authorRelation)?`<p>连线阈值")
s=s.replace('（当前正得分的中位数）。','（当前有效得分的中位数）。')
s=s.replace("['coauthor','topic','keywords'].includes(incoming.get('authorRelation'))", "['coauthor','topic','keywords','semantic'].includes(incoming.get('authorRelation'))")
s=s.replace("if(['citation','author','semantic','topic'].includes(incoming.get('relation')))state.relation=incoming.get('relation');", "if(['citation','author','semantic'].includes(incoming.get('relation')))state.relation=incoming.get('relation');\n    else if(incoming.get('relation')==='topic')state.relation='semantic';")
s=s.replace("if(!profile)return '';", """if(!profile)return '';
    if(profile.semantic)return `<div class="detail-section author-profile"><h3>${showAuthor?esc(profile.author_name)+' · ':''}语义依据论文</h3>${profile.paper_contributions.map(p=>`<div>${evidencePaper(p.paper_id)}<span class="detail-meta">${(p.share*100).toFixed(1)}%${p.title_only?' · 仅标题':''}</span></div>`).join('')}</div>`;""")
s=s.replace("+(profile?.keywords?authorProfileMarkup(profile,false):'')", "+(profile?.keywords||profile?.semantic?authorProfileMarkup(profile,false):'')")
s=s.replace("(pair.source_weight===1?'一作':'后续署名')+' / '+(pair.target_weight===1?'一作':'后续署名')", "'权重 '+pair.source_weight+' / '+pair.target_weight")
p.write_text(s,encoding='utf8')
p=root/'author-relations.js';s=p.read_text(encoding='utf8')
s=s.replace("const edges = [];", """const semanticProfiles=new Map(uniqueAuthors.map(author=>{
      const ids=profiles.get(author.id).ids.filter(id=>papers.find(p=>p.id===id)?.semantic_status==='available'||[...semantic.values()].some(e=>e.source===id||e.target===id));
      const total=ids.reduce((sum,id)=>sum+(author.paperWeights?.[id]===1?1:.2),0);
      return [author.id,{author_id:author.id,author_name:author.name,semantic:true,total_papers:profiles.get(author.id).ids.length,profiled_papers:ids.length,
        paper_contributions:ids.map(id=>({paper_id:id,weight:author.paperWeights?.[id]===1?1:.2,share:(author.paperWeights?.[id]===1?1:.2)/total,title_only:!paperMap.get(id).abstract}))}];
    }));
    const edges = [];""")
s=s.replace("model: 'specter_v2', aggregation:", "model: 'specter2_proximity', profiles:[semanticProfiles.get(a.id),semanticProfiles.get(b.id)], aggregation:")
s=s.replace("result.profiles=uniqueAuthors.map(author=>{", "result.profiles=uniqueAuthors.map(author=>{\n      if(mode==='semantic')return semanticProfiles.get(author.id);")
p.write_text(s,encoding='utf8')
p=Path('work/check_local_semantic_integration.cjs');s=p.read_text(encoding='utf8').replace("'#author-relation option[value=\"semantic\"]').count(),0", "'#author-relation option[value=\"semantic\"]').count(),1");p.write_text(s,encoding='utf8')
p=Path('work/check_author_relations.cjs');s=p.read_text(encoding='utf8').replace("const paperEdges=mode==='semantic'?authorSemantic.edges:data.edges;", "const paperEdges=data.edges;");p.write_text(s,encoding='utf8')
