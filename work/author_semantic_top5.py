from pathlib import Path
root=Path('outputs/paper-atlas')
p=root/'author-relations.js';s=p.read_text(encoding='utf8')
s=s.replace('所有可比较作者对均保留，不设相似度阈值。','每位作者选取相似度最高的 5 位，任一方选中即保留，不设分数阈值。')
s=s.replace("edge.evidence.threshold_rule=mode==='semantic'?'none':", "edge.evidence.threshold_rule=mode==='semantic'?'top_k_union':")
s=s.replace("const result=eligible;", """let result=eligible;
    if(mode==='semantic'){
      const selectedBy=new Map();
      for(const author of uniqueAuthors){
        const incident=eligible.filter(e=>e.source===author.id||e.target===author.id)
          .sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5);
        for(const edge of incident){if(!selectedBy.has(edge.id))selectedBy.set(edge.id,[]);selectedBy.get(edge.id).push(author.id);}
      }
      result=eligible.filter(e=>selectedBy.has(e.id));
      for(const edge of result){edge.evidence.top_k=5;edge.evidence.selected_by=selectedBy.get(edge.id);}
    }""")
s=s.replace("result.stats={threshold,valid_pairs:scores.length,eligible_pairs:eligible.length};", "result.stats={threshold,valid_pairs:scores.length,eligible_pairs:eligible.length,selected_pairs:result.length,...(mode==='semantic'?{top_k:5}: {})};")
p.write_text(s,encoding='utf8')
p=root/'app.js';s=p.read_text(encoding='utf8').replace('保留所有可比较的作者连线；相似度越高，边越明显、吸引力越强。','每位作者选取最相近的 5 位，任一方选中即连线，不设分数阈值。相似度越高，边越明显、吸引力越强。');p.write_text(s,encoding='utf8')
p=root/'README.md';s=p.read_text(encoding='utf8').replace('作者语义关系不设阈值，保留所有有有效不同论文对的作者边，包括零分和负分。','作者语义关系不设分数阈值。每位作者按原始相似度选取前 5 位，任一端选中即保留；候选不足 5 位时全保留。同分按边 ID 稳定排序。因此被多位作者选中的节点最终度数可超过 5。').replace('论文、作者及时间脉络均不按每节点的连接数量裁剪。','论文与时间脉络不按每节点的连接数量裁剪；作者语义关系使用每人 top-5 的并集。');p.write_text(s,encoding='utf8')
p=Path('work/check_author_semantic_current.cjs');s=p.read_text(encoding='utf8').replace("assert.equal(cy.edges().length,cy.nodes().length*(cy.nodes().length-1)/2,'all currently comparable author pairs retained');", "assert(cy.nodes().every(n=>n.degree()>=5),'default authors retain their five closest candidates');\nassert(cy.edges().length<=cy.nodes().length*5,'only union of per-author top five');").replace("assert.equal(d.evidence.threshold_rule,'none');", "assert.equal(d.evidence.threshold_rule,'top_k_union');assert.equal(d.evidence.top_k,5);");p.write_text(s,encoding='utf8')
p=Path('work/check_author_relations.cjs');s=p.read_text(encoding='utf8').replace("assert.equal(e.evidence.threshold_rule,'none')", "assert.equal(e.evidence.threshold_rule,'top_k_union')").replace("assert.equal(result.length,result.stats.eligible_pairs,'no qualifying pair is pruned');", "assert.equal(result.length,mode==='semantic'?result.stats.selected_pairs:result.stats.eligible_pairs,'reported selected pairs match');");p.write_text(s,encoding='utf8')
p=Path('work/capture_author_all.cjs');s=p.read_text(encoding='utf8').replace("includes('保留所有')", "includes('任一方选中')").replace('author-semantic-all','author-semantic-top5');p.write_text(s,encoding='utf8')
