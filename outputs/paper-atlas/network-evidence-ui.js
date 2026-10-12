'use strict';
window.createNetworkEvidenceUI=function({evidence,nodeMap,oaMap,topicMap,fieldMap=new Map(),researchFields={papers:{}},esc,safeURL}){
 const E=evidence||{papers:{},bibliography:{}};
 function researchFieldMarkup(p){
  const record=researchFields.papers[p.id],primary=fieldMap.get(record?.primary);
  const proof=id=>(record?.evidence||[]).filter(e=>e.field_id===id).map(e=>`${({keyword:'关键词',title:'标题',abstract:'摘要'})[e.kind]||'依据'}：${e.text}`).join('\n');
  const main=primary?`<span class="pill" style="color:${esc(primary.color)};border-color:${esc(primary.color)}" title="${esc(proof(primary.id))}">${esc(primary.name)}</span>`:'<span class="pill" style="color:#969aa4" title="未确定主研究领域">未分领域</span>';
  const secondary=(record?.secondary||[]).filter(id=>id!==record.primary&&fieldMap.has(id)).slice(0,2).map(id=>`<span class="pill" style="color:#9299a3" title="${esc('副领域\n'+proof(id))}">${esc(fieldMap.get(id).name)}</span>`).join('');
  return `<div class="pills research-fields" aria-label="研究领域" style="margin-top:8px">${main}${secondary}</div>`;
 }
 function metadata(p){
  const f=E.papers[p.id]?.fields;
  return {f,title:f?.title.adoptedValue||p.title,year:f?.year.adoptedValue??p.year,venue:f?.venue.adoptedValue||p.venue||p.publication_status||'会议／期刊未取得',authors:f?.authors.adoptedValue||p.authors,count:f?.citations.adoptedValue??p.citations,abstract:f?.abstract.adoptedValue||p.abstract};
 }
 function preview(p){
  const {title,year,authors,count}=metadata(p);
  const primary=fieldMap.get(researchFields.papers[p.id]?.primary);
  return `<div class="preview-title">${esc(title)}</div><div class="preview-meta">${p.lab?'实验室论文':'外部文献'} · ${esc(year??'年份未取得')} · <b title="用于节点大小">${Number.isFinite(count)?`被引 ${count} 次`:'被引次数未取得'}</b><br>${esc(authors.slice(0,3).join(', ')||'作者未取得')}${authors.length>3?' 等':''}<br><span style="color:${esc(primary?.color||'#969aa4')}">${esc(primary?.name||'未分领域')}</span></div>`;
 }
 function sourceLabel(url){
  let host;try{host=new URL(url).hostname;}catch{return '论文来源';}
  const is=domain=>host===domain||host.endsWith('.'+domain);
  return is('openalex.org')?'OpenAlex 记录':is('semanticscholar.org')?'Semantic Scholar 记录':is('crossref.org')?'Crossref 记录':is('github.com')?'项目／代码':is('doi.org')?'DOI 记录':host==='jyh-learning.github.io'?'实验室主页':'论文来源';
 }
 function find(id){
  const key=String(id).replace('https://openalex.org/','');
  const known=nodeMap.get(key)||oaMap.get(key);if(known)return known;
  const r=E.bibliography[key];
  return r?{...r,lab:false,tags:[],references:[],abstract:'',links:[r.url].filter(Boolean),openalex:r.recordUrl||(/openalex/.test(r.url)?r.url:null),match_status:'database'}:null;
 }
 const link=(id,edge)=>{
  const p=find(id);
  return p?`<button class="neighbor"${edge?` data-edge="${esc(edge)}"`:''} data-paper="${esc(p.id)}">${esc(p.title)}</button>`:`<div class="detail-note">${esc(id)} · 标题未取得</div>`;
 };
 function render(p,related){
  const {f,title,year,venue,authors,count,abstract}=metadata(p);
  const keywords=p.keyword_status?(p.keywords||[]):(f?.keywords.value||[]);
  const keywordTitle=k=>[k.evidence_field==='title'?'标题依据':k.evidence_field==='abstract'?'摘要依据':'',k.exact_quote,k.reason_zh].filter(Boolean).join('\n');
  const keywordMarkup=keywords.length?`<div class="pills">${keywords.map(k=>`<span class="pill adopted" title="${esc(keywordTitle(k))}">${esc(k.name)}</span>`).join('')}</div>`:`<p class="detail-note">${p.keyword_status==='excluded'?'关键词标注未采用':p.keyword_status==='empty'?'未匹配词表中的关键词':'关键词未取得'}</p>`;
  const citationSummary=Number.isFinite(count)?`<b class="adopted-value" title="用于节点大小">被引 ${count} 次</b>`:'被引次数未取得';
  const urls=[...new Set([...(E.papers[p.id]?.links||p.links||[]),p.openalex].filter(safeURL))];
  return `<div class="detail-meta" style="margin-top:22px">${p.lab?'● 实验室论文':'○ 外部文献'} · ${esc(year??'年份未取得')} · ${citationSummary}</div><h2 class="detail-title">${esc(title)}</h2><div class="detail-meta">${esc(venue)}<br>${esc(authors.join(', ')||'作者未取得')}</div>${researchFieldMarkup(p)}${related.length?`<section class="detail-section paper-relations"><h3>关联论文</h3>${related.map(row=>`<div class="evidence-record">${link(row.paper_id,row.edge_id)}<div class="pills"><button type="button" class="pill" data-edge="${esc(row.edge_id)}">${esc(row.summary)}</button>${row.labels.map(label=>`<span class="pill">${esc(label)}</span>`).join('')}</div></div>`).join('')}</section>`:''}<details class="detail-section paper-text-fold"><summary>关键词</summary>${keywordMarkup}</details><details class="detail-section paper-text-fold"><summary>摘要</summary>${abstract?`<div class="abstract">${esc(abstract)}</div>`:'<p class="detail-note">摘要未取得</p>'}</details><section class="detail-section"><h3>来源</h3><a class="detail-link" href="retrieval.html?${p.lab?'':'view=external&'}paper=${encodeURIComponent(p.id)}">检索汇总 ↗</a>${urls.map(url=>`<a class="detail-link" href="${esc(url)}" target="_blank" rel="noopener">${sourceLabel(url)} ↗</a>`).join('')}</section>`;
 }
 return {find,link,render,preview,sourceLabel};
};
