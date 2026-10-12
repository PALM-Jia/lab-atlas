/* Author affinities inferred from the currently filtered laboratory papers. */
(function (root) {
  'use strict';
  const sortedUnique = values => [...new Set(values)].sort();
  function buildAuthorRelations({authors = [], papers = [], paperEdges = [], mode = 'topic', keywordData = root.ATLAS_PAPER_KEYWORDS||{}} = {}) {
    if(mode==='keywords')return (root.buildAuthorKeywordRelations||(typeof require==='function'?require('./author-keywords.js'):null))({authors,papers,keywordData});
    const paperMap = new Map(papers.map(p => [p.id, p]));
    const maximumTopic=mode==='database-topic-max';
    const databaseTopic = mode === 'database-topic'||maximumTopic;
    const vocabulary=new Map((keywordData.vocabulary||[]).map(k=>[k.id,k]));
    const names = new Map([...vocabulary].map(([id,k])=>[id,k.name]));
    const uniqueAuthors = [...new Map(authors.map(a => [a.id, a])).values()]
      .sort((a, b) => a.id.localeCompare(b.id));
    const profiles = new Map();
    for (const author of uniqueAuthors) {
      const ids = sortedUnique(author.papers || []).filter(id => paperMap.has(id));
      const weights = new Map(), tagged = [], paperTopics = new Map(), contributions=[], termEvidence=new Map();
      let totalContribution=0;
      for (const id of ids) {
        const perPaper = new Map();
        if (databaseTopic) {
          for (const topic of paperMap.get(id).api_topics || []) {
            if (!topic.id || !Number.isFinite(topic.score) || topic.score <= 0) continue;
            perPaper.set(topic.id, Math.max(perPaper.get(topic.id) || 0, topic.score));
            names.set(topic.id, topic.display_name || topic.id);
          }
        } else {
          if(!['annotated','empty'].includes(keywordData.statuses?.[id]))continue;
          if(keywordData.statuses[id]==='annotated')for(const label of new Map((keywordData.papers?.[id]||[]).filter(k=>vocabulary.get(k.id)?.dimension==='research_task').map(k=>[k.id,k])).values()){
            perPaper.set(label.id,1);
            if(!termEvidence.has(label.id))termEvidence.set(label.id,[]);
            termEvidence.get(label.id).push({paper_id:id,...label,...vocabulary.get(label.id)});
          }
        }
        const total = [...perPaper.values()].reduce((sum, value) => sum + value, 0);
        if (!total&&databaseTopic) continue;
        tagged.push(id);
        paperTopics.set(id, new Set(perPaper.keys()));
        const contribution=author.paperWeights?.[id]===1?1:.2;
        totalContribution+=contribution;
        contributions.push({paper_id:id,weight:contribution,first_author:author.firstAuthorPapers?author.firstAuthorPapers.includes(id):contribution===1});
        for (const [tag, value] of perPaper) weights.set(tag, (weights.get(tag) || 0) + value / total*contribution);
      }
      for (const [tag, value] of weights) weights.set(tag, value / totalContribution);
      profiles.set(author.id, {ids, tagged, weights, paperTopics,contributions,totalContribution,termEvidence});
    }
    const semantic = new Map();
    if (mode === 'semantic') for (const edge of paperEdges) {
      if (edge.kind !== 'semantic' || edge.source === edge.target ||
          !paperMap.has(edge.source) || !paperMap.has(edge.target) ||
          !Number.isFinite(edge.score)) continue;
      const key = [edge.source, edge.target].sort().join('\u0000');
      if (!semantic.has(key) || semantic.get(key).score < edge.score) semantic.set(key, edge);
    }
    const semanticIds=new Set([...semantic.values()].flatMap(e=>[e.source,e.target]));
    const semanticProfiles=new Map((mode==='semantic'?uniqueAuthors:[]).map(author=>{
      const ids=profiles.get(author.id).ids.filter(id=>paperMap.get(id)?.semantic_status==='available'||semanticIds.has(id));
      const total=ids.reduce((sum,id)=>sum+(author.paperWeights?.[id]===1?1:.2),0);
      return [author.id,{author_id:author.id,author_name:author.name,semantic:true,total_papers:profiles.get(author.id).ids.length,profiled_papers:ids.length,
        paper_contributions:ids.map(id=>({paper_id:id,weight:author.paperWeights?.[id]===1?1:.2,share:(author.paperWeights?.[id]===1?1:.2)/total,title_only:!paperMap.get(id).abstract}))}];
    }));
    const edges = [];
    for (let i = 0; i < uniqueAuthors.length; i++) for (let j = i + 1; j < uniqueAuthors.length; j++) {
      const a = uniqueAuthors[i], b = uniqueAuthors[j];
      const pa = profiles.get(a.id), pb = profiles.get(b.id);
      let score, evidence, relatedPapers;
      if (mode === 'topic' || databaseTopic) {
        const common = [...pa.weights.keys()].filter(t => pb.weights.has(t)).sort();
        const norm = profile => Math.sqrt([...profile.weights.values()].reduce((s, v) => s + v * v, 0));
        const denominator = norm(pa) * norm(pb);
        if (!denominator) continue;
        score = maximumTopic?Math.max(0,...common.map(t=>pa.weights.get(t)*pb.weights.get(t))):Math.min(1, common.reduce((s, t) => s + pa.weights.get(t) * pb.weights.get(t), 0) / denominator);
        if (!common.length) continue;
        const winningTopics=maximumTopic?common.filter(t=>Math.abs(pa.weights.get(t)*pb.weights.get(t)-score)<1e-12):common;
        const pairs = [];
        for (const source of pa.tagged) for (const target of pb.tagged) {
          if (source === target) continue;
          const tags = winningTopics.filter(t => pa.paperTopics.get(source).has(t) && pb.paperTopics.get(target).has(t));
          if (tags.length) pairs.push({source, target, topic_names: tags.map(t => names.get(t))});
        }
        const sharedPapers = pa.tagged.filter(id => pb.tagged.includes(id) && common.some(t => pa.paperTopics.get(id).has(t)));
        const profile = (author, data) => ({author_id: author.id, author_name: author.name,
          paper_count: data.ids.length, tagged_paper_count: data.tagged.length,
          total_papers: data.ids.length, profiled_papers: data.tagged.length,
          first_author_papers:data.contributions.filter(p=>p.first_author).length,
          contribution_weight:data.totalContribution,paper_contributions:data.contributions,
          topics: [...data.weights.entries()].map(([id, weight]) => ({id, name: names.get(id), dimension:vocabulary.get(id)?.dimension,weight,evidence:data.termEvidence.get(id)||[]})),
          papers: data.tagged});
        evidence = {
          text: databaseTopic ? '每篇 OpenAlex 主题 score 归一化，按第一作者权重1、其他署名权重0.2形成画像；'+(maximumTopic?'相似度为最大主题权重乘积 maxₖ(Ta[k] × Tb[k])。':'相似度为画像余弦。')+' 每位作者选取最强 5 条，取两端选择的并集。' : '每篇论文的词表研究任务标签均分，按第一作者权重1、其他署名权重0.2形成画像；有效空标注计入分母，排除论文不计入。画像余弦相似度，每位作者选取最强 5 条，取两端选择的并集。',
          shared_topics:common.map(id=>({id,name:names.get(id),dimension:vocabulary.get(id)?.dimension,source_weight:pa.weights.get(id),target_weight:pb.weights.get(id),product:pa.weights.get(id)*pb.weights.get(id),source_evidence:pa.termEvidence.get(id)||[],target_evidence:pb.termEvidence.get(id)||[]})).sort((a,b)=>b.product-a.product||a.id.localeCompare(b.id)),
          cosine_parts:{dot:common.reduce((sum,t)=>sum+pa.weights.get(t)*pb.weights.get(t),0),source_norm:norm(pa),target_norm:norm(pb)},
          aggregation:maximumTopic?'maximum_topic_product':'profile_cosine',
          sharedtopic_sources: [databaseTopic ? 'openalex_topics' : 'vocabulary_research_task'], topic_names: winningTopics.map(t => names.get(t)),
          profiles: [profile(a, pa), profile(b, pb)], shared_papers: sharedPapers,
          paper_pairs: pairs.slice(0, 3)
        };
        relatedPapers = sortedUnique([...pairs.slice(0, 3).flatMap(p => [p.source, p.target]), ...sharedPapers]);
      } else if (mode === 'semantic') {
        const pairs = [];
        for (const source of pa.ids) for (const target of pb.ids) {
          if (source === target) continue;
          const key = [source, target].sort().join('\u0000'), edge = semantic.get(key);
          if (!edge) continue;
          const sourceWeight=a.paperWeights?.[source]===1?1:.2,targetWeight=b.paperWeights?.[target]===1?1:.2;
          pairs.push({source, target, score: edge.score,source_weight:sourceWeight,target_weight:targetWeight,weight:sourceWeight*targetWeight});
        }
        if (!pairs.length) continue;
        const totalWeight=pairs.reduce((s,p)=>s+p.weight,0);
        score=pairs.reduce((s,p)=>s+p.score*p.weight,0)/totalWeight;
        pairs.sort((x, y) => y.score*y.weight-x.score*x.weight || x.source.localeCompare(y.source) || x.target.localeCompare(y.target));
        evidence = {text: '全部有效跨论文对余弦相似度取加权平均；第一作者权重1、其他署名权重0.2，论文对权重为两者乘积。同一论文与自身排除，不提前按相似度筛选论文对；每位作者选取相似度最高的 5 位，任一方选中即保留，不设分数阈值。',
          model: 'specter2_proximity', profiles:[semanticProfiles.get(a.id),semanticProfiles.get(b.id)], aggregation: 'weighted_mean',weighted_sum:score*totalWeight,pair_count:pairs.length,total_pair_weight:totalWeight,paper_pairs: pairs.slice(0, 3)};
        relatedPapers = sortedUnique(evidence.paper_pairs.flatMap(p => [p.source, p.target]));
      } else continue;
      const kind = maximumTopic?'author_database_topic_max':databaseTopic ? 'author_database_topic' : mode === 'topic' ? 'author_topic' : 'author_semantic';
      edges.push({id: kind + ':' + a.id + ':' + b.id, source: a.id, target: b.id,
        kind, score, tentative: true, papers: relatedPapers, evidence});
    }
    const select=root.selectAtlasTopEdges||(typeof require==='function'?require('./paper-density.js').selectTopEdges:null);
    const result=select(edges,5);
    result.stats={threshold:null,top_k:5,valid_pairs:edges.length,eligible_pairs:edges.length,selected_pairs:result.length};
    result.profiles=uniqueAuthors.map(author=>{
      if(mode==='semantic')return semanticProfiles.get(author.id);
      const p=profiles.get(author.id);
      return {author_id:author.id,author_name:author.name,total_papers:p.ids.length,profiled_papers:p.tagged.length,
        contribution_weight:p.totalContribution,paper_contributions:p.contributions,topics:[...p.weights].map(([id,weight])=>({id,name:names.get(id),dimension:vocabulary.get(id)?.dimension,weight,evidence:p.termEvidence.get(id)||[]})).sort((a,b)=>b.weight-a.weight||a.id.localeCompare(b.id))};
    });
    return result;
  }
  root.buildAuthorRelations = buildAuthorRelations;
  if (typeof module !== 'undefined' && module.exports) module.exports = buildAuthorRelations;
})(typeof window !== 'undefined' ? window : globalThis);
