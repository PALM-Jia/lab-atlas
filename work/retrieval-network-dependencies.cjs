module.exports=({p,source,topics,vectorRow,semantic={}})=>{
 const state=p.semantic_status==='available'?'ready':'missing';
 const local=p.semantic_source==='本地 SPECTER2'||p.semantic_model==='specter2_proximity';
 const input=p.semantic_input||null;
 const inputLabel=input?.fields?.includes('abstract')?'标题＋摘要':'仅标题';
 const dimensions=semantic.dimensions||768;
 const limited=vectorRow?.reason==='no_supported_public_identifier';
 const limitation='未查询：缺少 DOI/arXiv 查询标识。';
 const reason=state==='ready'?(local?`已在本地生成并校验${dimensions}维SPECTER2向量；输入：${inputLabel}${input?.truncated?'；超过模型长度的输入已截断':''}。`:'已取得并校验768维SPECTER2向量'):limited?limitation:vectorRow?.failure_summary||({'no_supported_public_identifier':'未查询：缺少 DOI/arXiv 查询标识。','semantic_scholar_no_record':'按所用标识查询返回 null。','vector_missing_or_invalid':'记录返回，但向量为空或未通过维度与数值校验'}[vectorRow?.reason]||'向量查询未完成');
 return {
  topics:{value:(p.api_topics||[]).map(t=>({id:t.id,name:t.display_name,score:t.score})),state:p.api_topics?.length?'ready':p.openalex?'empty':'missing',sources:[source('OpenAlex',p.openalex)],explanation:p.api_topics?.length?'OpenAlex自动研究主题；用于研究主题重合连线。':p.openalex?'OpenAlex记录的主题字段为空。':'未确认OpenAlex记录，主题未取得。'},
  directions:{value:(p.tags||[]).map(id=>({id,name:topics.find(t=>t.id===id)?.name||id})),state:p.tags?.length?'ready':'missing',sources:[source(p.tag_source||'标题与摘要规则推断','')],explanation:(p.tag_source||'标题与摘要规则推断')+(p.tags?.length===1&&p.tags[0]==='other'?'；未命中专门方向规则，归入其他方向':'')+'；用于研究方向筛选和作者方向画像。',input:{title:!!p.title,abstract:!!p.abstract},matches:p.direction_matches||[]},
  vector:{value:state==='ready'?`SPECTER2 · ${dimensions}维${local?' · '+inputLabel:''}`:null,state,
   sources:[source(local?'本地 SPECTER2':p.semantic_source||'Semantic Scholar',local?'https://huggingface.co/allenai/specter2':p.semantic_paper_id?'https://www.semanticscholar.org/paper/'+p.semantic_paper_id:'https://api.semanticscholar.org/graph/v1/paper/batch')],
   explanation:reason,model:p.semantic_model||'specter_v2',dimensions:state==='ready'?dimensions:null,input,
   base:local?semantic.base||null:null,adapter:local?semantic.adapter||null:null,baseRevision:local?semantic.base_revision||null:null,adapterRevision:local?semantic.adapter_revision||null:null,
   paperId:p.semantic_paper_id||null,identifier:local?null:vectorRow?.identifier||null,
   routes:state==='ready'?[]:(vectorRow?.failure_sources||[]).map(r=>({...r,result:limited?limitation:r.result,url:r.url||(vectorRow?.identifier?'https://api.semanticscholar.org/graph/v1/paper/batch?fields=paperId,title,authors,abstract,year,externalIds,embedding.specter_v2':'')})),
   assessment:state==='ready'?'':vectorRow?.failure_assessment?.judgment||'',next:state==='ready'?'':vectorRow?.failure_assessment?.next_action||''}
 };
};
