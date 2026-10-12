/* Stable, coarse display fields derived from task keywords and title evidence. */
(function(root){
 'use strict';
 const fields=[
  {id:'clustering',name:'聚类与表示学习',color:'#6877ce'},
  {id:'labels',name:'标签学习',color:'#d99850'},
  {id:'foundation',name:'大模型与多模态',color:'#54a3a0'},
  {id:'vision',name:'视觉感知与图像处理',color:'#679aba'},
  {id:'recovery',name:'数据补全与恢复',color:'#839c56'},
  {id:'trust',name:'鲁棒与可信学习',color:'#bd6c8c'}
 ];
 const anchors={
  clustering:{'deep-clustering':4,'ensemble-clustering':4,'subspace-clustering':4,'dimensionality-reduction':4},
  labels:{'multi-label-learning':4,'label-distribution-learning':4,'label-enhancement':4,'partial-label-learning':4,'noisy-label-learning':4,'label-correlation-modeling':1},
  foundation:{'large-language-models':3,'vision-language-models':3,'large-vision-language-models':3,'model-merging':4,'value-preference-alignment':4,'multimodal-retrieval':4,'latent-reasoning':2},
  vision:{'image-segmentation':4,'person-reidentification':4,'hyperspectral-images':2,'underwater-images':2,'zero-shot-learning':2,'open-vocabulary-recognition':3},
  recovery:{'data-imputation-recovery':4,'traffic-data':2},
  trust:{'adversarial-robustness':4,'confidence-calibration':3,'hallucination-mitigation':3,'noisy-label-learning':2}
 };
 // General-purpose methods/settings do not supply primary-field votes.
 // In particular: low rank, graph regularization, semi/weak supervision,
 // pseudo-labeling, contrastive learning and distillation are not field anchors.
 const titleRules={
  clustering:{weight:6,pattern:/\b(?:cluster(?:ing|s)?|representation learning|dimensionality reduction|spectral embedding)\b/i},
  labels:{weight:6,pattern:/\b(?:multi[\s-]?label(?:led)?|partial[\s-]?label|label distribution|label enhancement|label disambiguation|noisy[\s-]?label|label correlation|semi[\s-]?supervised learning|weakly[\s-]?supervised (?:learning|classification)|multiple instance learning|long[\s-]?tailed (?:learning|classification))\b/i},
  foundation:{weight:5,pattern:/\b(?:large language models?|large vision[\s-]language models?|vision[\s-]language|multi[\s-]?modal|language-assisted|model merg(?:ing|e)|preference align(?:ment)?|retrieval augmented generation|llms?|lvlms?)\b/i},
  vision:{weight:5,pattern:/\b(?:image (?:segmentation|classification|restoration|quality|processing|enhancement)|saliency|salient(?: object)?|superpixels?|person re[\s-]?identification|hyperspectral|underwater|zero-shot (?:learning|recognition)|open-vocabulary)\b/i},
  recovery:{weight:6,pattern:/\b(?:data (?:imputation|completion|recovery)|matrix completion|tensor completion|(?:matrix|tensor) recovery|traffic (?:data|speed|state|flow)|missing data|incomplete data)\b/i},
  trust:{weight:4,pattern:/\b(?:adversarial|calibrat(?:ion|ed)|hallucinations?|uncertainty|trustworthy|fairness|differential privacy|certified robustness)\b/i}
 };
 const specificity=['clustering','labels','recovery','vision','foundation','trust'];
 function classify(paper){
  const evidence=[],scores=new Map();
  for(const field of fields){
   let keywordScore=0,titleScore=0;
   for(const k of paper.keywords||[]){
    const weight=anchors[field.id][k.id];if(!weight)continue;
    const score=weight+(k.evidence_field==='title'?1:0);
    keywordScore=Math.max(keywordScore,score);
    evidence.push({field_id:field.id,keyword_id:k.id,kind:'keyword',text:k.name,score});
   }
   const rule=titleRules[field.id],match=String(paper.title||'').normalize('NFKC').replace(/[‐‑–—]/g,'-').match(rule.pattern);
   if(match){titleScore=rule.weight;evidence.push({field_id:field.id,keyword_id:null,kind:'title',text:match[0],score:titleScore});}
   scores.set(field.id,keywordScore+titleScore);
  }
  // Take the strongest anchor, not the sum of tags: a larger vocabulary does
  // not inflate a field's score. Title evidence favors the stated paper task.
  const ranked=fields.map(f=>({id:f.id,score:scores.get(f.id)})).filter(f=>f.score>=2)
   .sort((a,b)=>b.score-a.score||specificity.indexOf(a.id)-specificity.indexOf(b.id));
  return {primary:ranked[0]?.id||null,secondary:ranked.slice(1).map(f=>f.id),scores:Object.fromEntries(scores),evidence,source:'title_and_keywords'};
 }
 root.classifyAtlasResearchField=classify;
 if(typeof module!=='undefined'&&module.exports)module.exports={fields,classify};
})(typeof window!=='undefined'?window:globalThis);
