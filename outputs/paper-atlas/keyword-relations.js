/* Binary accepted-vocabulary paper labels; sparse IDF-weighted Jaccard neighbors. */
(function(root){
  'use strict';
  function buildPaperKeywordRelations({papers=[],keywordData=root.ATLAS_PAPER_KEYWORDS||{}}={}){
    const vocabulary=new Map((keywordData.vocabulary||[]).map(k=>[k.id,k]));
    const unique=[...new Map(papers.map(p=>[p.id,p])).values()].sort((a,b)=>a.id.localeCompare(b.id));
    const profiles=new Map(),inverted=new Map(),candidates=new Map();
    const idf=id=>Number.isFinite(keywordData.idf?.[id])&&keywordData.idf[id]>0?keywordData.idf[id]:1;
    for(const paper of unique){
      if(!['annotated','empty'].includes(keywordData.statuses?.[paper.id]))continue;
      const labels=new Map((keywordData.statuses[paper.id]==='annotated'?keywordData.papers?.[paper.id]||[]:[])
        .filter(k=>vocabulary.has(k.id)).map(k=>[k.id,{...k,...vocabulary.get(k.id)}]));
      profiles.set(paper.id,{paper,labels,total:[...labels.keys()].reduce((s,id)=>s+idf(id),0)});
      for(const id of labels.keys()){
        if(!inverted.has(id))inverted.set(id,[]);
        inverted.get(id).push(paper.id);
      }
    }
    // Enumerate only pairs sharing a label. External-only pairs never enter the candidate set.
    const addPair=(term,first,second)=>{
      const [source,target]=[first,second].sort((a,b)=>a.localeCompare(b));
      const key=JSON.stringify([source,target]);
      if(!candidates.has(key))candidates.set(key,{source,target,shared:[]});
      candidates.get(key).shared.push(term);
    };
    for(const [term,ids] of inverted){
      const lab=ids.filter(id=>profiles.get(id).paper.lab),external=ids.filter(id=>!profiles.get(id).paper.lab);
      for(let i=0;i<lab.length;i++){
        for(let j=i+1;j<lab.length;j++)addPair(term,lab[i],lab[j]);
        for(const id of external)addPair(term,lab[i],id);
      }
    }
    const edges=[];
    for(const pair of candidates.values()){
      const a=profiles.get(pair.source),b=profiles.get(pair.target);
      const numerator=pair.shared.reduce((s,id)=>s+idf(id),0),denominator=a.total+b.total-numerator;
      if(!numerator||!denominator)continue;
      const shared=pair.shared.map(id=>({id,name:vocabulary.get(id).name,dimension:vocabulary.get(id).dimension,
        idf:idf(id),contribution:idf(id),source_evidence:[{paper_id:pair.source,...a.labels.get(id)}],
        target_evidence:[{paper_id:pair.target,...b.labels.get(id)}]})).sort((x,y)=>y.contribution-x.contribution||x.id.localeCompare(y.id));
      edges.push({id:'keyword:'+pair.source+':'+pair.target,source:pair.source,target:pair.target,kind:'keyword',score:Math.min(1,numerator/denominator),
        papers:[pair.source,pair.target],evidence:{aggregation:'paper_keyword_jaccard',shared_keywords:shared,keyword_names:shared.map(k=>k.name),numerator,denominator,
          text:'词表标签按是否出现计数，以 IDF 加权计算 Jaccard 相似度；每篇论文选择最强 5 条，取两端选择的并集。'}});
    }
    const select=root.selectAtlasTopEdges||(typeof require==='function'?require('./paper-density.js').selectTopEdges:null);
    const result=select(edges,5);
    result.stats={threshold:null,top_k:5,valid_pairs:candidates.size,positive_pairs:edges.length,eligible_pairs:edges.length,selected_pairs:result.length,profiled_papers:profiles.size};
    result.profiles=[...profiles].map(([paper_id,p])=>({paper_id,status:keywordData.statuses[paper_id],keywords:[...p.labels.values()],idf_sum:p.total}));
    return result;
  }
  root.buildPaperKeywordRelations=buildPaperKeywordRelations;
  if(typeof module!=='undefined'&&module.exports)module.exports=buildPaperKeywordRelations;
})(typeof window!=='undefined'?window:globalThis);
