/* Normalize current field evidence without changing graph inputs. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../outputs/paper-atlas');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const context={window:{}};
for(const file of ['author-identities.js','author-groups.js','author-identity-resolver.js','paper-keywords.js'])vm.runInNewContext(fs.readFileSync(path.join(root,file),'utf8'),context);
const W=context.window,data=read('data.json'),audit=read('acceptance.json'),citation=read('citation-comparison.json');
const keywordMissing=new Map(read('keyword-missing.json').missing.map(r=>[r.id,r]));
const keywordReviews=new Map(read('keyword-status-review.json').items.map(r=>[r.id,r]));
const publicMetadata=read('public-paper-metadata.json');
const homepagePapers=new Map(read('lab-papers.json').map(p=>[p.id,p]));
const citingSets=JSON.parse(fs.readFileSync(path.resolve(__dirname,'citing-sets.json'),'utf8'));
const comparisons=new Map(citation.rows.map(r=>[r.id,r]));
const sourceNames={'实验室列表':'实验室主页','OpenAlex':'OpenAlex'};
const source=(name,url)=>({name:sourceNames[name]||name,url:url||''});
function metadataSource(p,field){
  const value=p.metadata_sources?.[field]||p.source;
  if(/^https?:/.test(value||''))return source('公开论文页',value);
  return source(value||'实验室主页',value==='OpenAlex'?p.openalex:data.meta.source);
}
const statuses={ready:'已取得值',partial:'部分详情缺失',empty:'来源返回空',missing:'无可用值',review:'身份待核对',derived:'论文聚合',unlinked:'尚未关联论文'};
const reasons={
 'HTTP 404':'接口返回 HTTP 404，未返回对应记录',
 'HTTP 429':'接口 HTTP 429，重试后仍限流',
 'No verified DOI; Crossref DOI lookup unavailable':'无已确认 DOI，无法按 DOI 查询 Crossref',
 'DOI registered with DataCite; Crossref works endpoint HTTP 404':'DOI 注册于 DataCite；Crossref 记录接口返回 HTTP 404',
 'Semantic Scholar returned null for identifier':'按标识符查询返回 null',
 'Bulk title search returned no identity-validated record':'标题搜索无身份校验通过的记录',
 'Candidate failed title/author identity validation':'候选未通过标题／作者校验',
 'Unresolved State/TRB versus Speed/TITS version identity; candidate count not adopted':'State/TRB 与 Speed/TITS 版本对应未确认',
 'public_page_verified_no_openalex_match':'公开论文页已核对，未匹配 OpenAlex 记录',
 'official_listing_no_openalex_match':'会议正式列表已核对，未匹配 OpenAlex 记录',
 'title_only_no_independent_locator':'主页只有标题，缺少独立定位信息',
 'possible_renamed_paper_without_version_identity':'疑似改名，版本对应关系未确认',
 'spelling_variant_no_verified_match':'拼写变体未确认对应记录',
 'expanded_search_no_verified_record':'扩大查询无身份校验通过的记录',
 'no_public_locator_for_future_year':'未来年份条目缺少公开定位链接',
 'public_candidate_page_access_blocked':'公开候选页面获取受阻',
 'title_variant_collides_with_another_lab_paper':'题名变体与另一实验室论文的版本身份冲突',
 'database_returned_empty':'数据库返回空字段',
 'no_verified_database_id':'尚无校验通过的数据库身份',
 'authors_not_available':'尚未取得作者名单',
 'year_not_available':'尚未取得年份',
 'database_not_matched':'尚未匹配数据库记录'
};
const explain=reason=>reasons[reason]||reason||'尚未完成采集';
const field=(value,state,sources,extra={})=>({value,state,sources,...extra});
const needed=new Set(data.nodes.filter(p=>p.lab).flatMap(p=>[...(p.references||[]),...(citingSets[p.id]||[])]));
const bibliography=require('./retrieval-bibliography.cjs')({nodes:data.nodes,needed,cache:path.resolve(__dirname,'api-cache')});
const auditMaps=Object.fromEntries(Object.entries(audit.steps).map(([k,v])=>[k,new Map(v.items?.map(i=>[i.id,i])||[])]));
function issue(p,key,label){
 const r=auditMaps[key]?.get(p.id);if(!r||r.status!=='failure')return null;
 return {field:label,reason:r.failure_summary||explain(r.reason),routes:r.failure_sources?.map(s=>({url:s.url,name:s.provider||s.source,result:s.result}))||[],assessment:r.failure_assessment?.judgment||'',next:r.next_action||r.failure_assessment?.next_action||''};
}
const directionRules=read('../../work/direction-rules.json');
const addDependencies=p=>{p.direction_matches=(p.tags||[]).flatMap(id=>{const pattern=directionRules[id];if(!pattern||id==='other')return [];const re=new RegExp(pattern.replaceAll('(?i)',''),'ig');return ['title','abstract'].flatMap(input=>[...(p[input]||'').matchAll(re)].slice(0,6).map(m=>({id,input,text:m[0]})));});return require('./retrieval-network-dependencies.cjs')({p,source,topics:data.topics,vectorRow:auditMaps['08_content_vector']?.get(p.id),semantic:data.meta.semantic||{}});};
const papers=data.nodes.filter(p=>p.lab).map(p=>{
 const comparison=comparisons.get(p.id),keywords=W.ATLAS_PAPER_KEYWORDS.papers[p.id]||[],refs=p.references||[];
 const resolved=W.resolveAtlasPaperAuthors(p);
 const parsed=refs.filter(id=>bibliography[id]).length;
 const kMissing=keywordMissing.get(p.id),review=keywordReviews.get(p.id);
 const official=kMissing?.sources?.find(s=>s.result?.includes('正式')&&/proceedings|aclanthology|ojs\.aaai|openaccess.thecvf|neurips/.test(s.url||''));
 const venueKind=['preprint','预印本'].includes(p.publication_status)?'预印本':official?'正式条目已核对':p.match_status==='matched'&&p.publication_status!=='列表标注的发表条目'?'数据库发表记录':'主页标注';
 const venueSources=[metadataSource(p,'year')];if(official)venueSources.push(source('会议／期刊官方页',official.url));
 const fields={
  title:field(p.title,'ready',[source('实验室主页',data.meta.source),...(p.openalex?[source('OpenAlex',p.openalex)]:[])],{original:p.list_title||p.title}),
  authors:field(resolved.map(a=>({id:a.id,name:a.name,raw:p.authors.find(n=>W.ATLAS_AUTHOR_IDENTITIES.occurrences.some(o=>o.paper_id===p.id&&o.name===n&&o.person_id===a.id))||a.name,excluded:a.excluded_from_network})),p.authors.length?'ready':'missing',[metadataSource(p,'authors')]),
  venue:field({name:p.venue||'',year:p.year,kind:venueKind},p.venue&&Number.isFinite(p.year)?'ready':p.venue||Number.isFinite(p.year)?'partial':'missing',venueSources,{originalVenue:p.list_venue||'',originalYear:p.list_year}),
  references:field(refs,refs.length?(parsed===refs.length?'ready':'partial'):p.reference_status==='database_observed'?'empty':'missing',[source('OpenAlex',p.openalex||'https://api.openalex.org/works')],{parsed,total:refs.length}),
  keywords:field(keywords.map(k=>({id:k.id,name:k.name})),keywords.length?'ready':p.openalex?'empty':'missing',[source('OpenAlex',p.openalex||'https://api.openalex.org/works')]),
  identity:field({doi:p.doi||'',openalex:p.openalex||'',semantic_scholar:comparison?.semantic_scholar.status==='success'?comparison.semantic_scholar.identifier:''},p.match_status==='ambiguous'?'review':p.openalex||comparison?.semantic_scholar.status==='success'?'ready':'missing',[])
 };
 for(const [key,label]of [['openalex','OpenAlex'],['semantic_scholar','Semantic Scholar'],['crossref','Crossref']]){
  const r=comparison?.[key]||{status:'missing',reason:'尚未采集'};
  fields[key]=field(r.count??null,r.status==='success'?'ready':/校验|Candidate|identity|版本/.test(r.reason||'')?'review':'missing',[source(label,r.url||r.route?.startsWith('http')&&r.route||'')],{reason:r.status==='success'?'':explain(r.reason),route:r.route||r.url||'',snapshot:key==='openalex'?data.meta.updated:citation.collected_at,previous:r.previous_attempt,agency:r.agency_check});
 }
 const issues=[issue(p,'02_match','OpenAlex 身份'),issue(p,'04_authors','作者'),issue(p,'04_year','年份'),issue(p,'04_references','参考文献')].filter(Boolean);
 if(refs.length>parsed)issues.push({field:'参考文献详情',reason:`OpenAlex 已返回 ${refs.length} 个参考文献 ID；当前汇总已匹配其中 ${parsed} 条的标题，剩余 ${refs.length-parsed} 条仅保留 ID。`,routes:[{name:'OpenAlex',url:p.openalex,result:'参考文献 ID 列表已取得'}],next:''});
 if(kMissing)issues.push({field:'关键词',reason:kMissing.assessment||kMissing.detail||explain(kMissing.reason),routes:(kMissing.sources||[]).map(s=>({name:s.source,url:s.url,result:s.result})),next:kMissing.next_action||''});
 for(const key of ['semantic_scholar','crossref'])if(fields[key].state!=='ready')issues.push({field:key==='crossref'?'Crossref 被引数':'Semantic Scholar 被引数',reason:fields[key].reason,routes:[{name:fields[key].sources[0].name,url:fields[key].route,result:fields[key].reason}],previous:fields[key].previous,agency:fields[key].agency});
 require('./retrieval-evidence.cjs')({p,fields,comparison,homepageRecord:homepagePapers.get(p.id),publicRecord:publicMetadata[p.id],source,homepage:data.meta.source,snapshot:data.meta.updated});
 fields.citing.ids=citingSets[p.id]||[];
 fields.citing.parsed=fields.citing.ids.filter(id=>bibliography[id]).length;
 fields.citing.explanation=Number.isFinite(fields.citing.total)?`OpenAlex 报告 ${fields.citing.total} 篇施引文献；已收集 ${fields.citing.ids.length} 个标识符，当前汇总已匹配详情 ${fields.citing.parsed} 篇。`:'未取得施引名单；具体查询路径见请求记录。';
 Object.assign(fields,addDependencies(p));
 const providers=[...new Set(Object.values(fields).flatMap(f=>[...f.sources,...(f.observations||[]).flatMap(o=>o.sources)].map(s=>s.name)))];
 return{id:p.id,title:p.title,fields,issues,providers,links:[...new Set([p.openalex,p.doi,...(p.links||[]),...(publicMetadata[p.id]?.links||[])].filter(Boolean))],publicationReview:review||null};
});
const paperMap=new Map(papers.map(p=>[p.id,p]));
// Bibliographic lists use adopted lab metadata; source alternatives remain in fields.
for(const p of papers){const r=bibliography[p.id];for(const key of ['title','authors','venue','year','citations'])if(p.fields[key].adoptedValue!=null)r[key]=p.fields[key].adoptedValue;}
const originalPeople=JSON.parse(fs.readFileSync(path.resolve(root,'../author-person-identities.json'),'utf8'));
const oldPeople=new Map(originalPeople.people.map(p=>[p.person_id,p]));
const authors=W.ATLAS_AUTHOR_IDENTITIES.people.filter(p=>!W.ATLAS_AUTHOR_GROUPS.excludedPersonIds.includes(p.id)).map(person=>{
 const ids=[...new Set(W.ATLAS_AUTHOR_IDENTITIES.occurrences.filter(o=>o.person_id===person.id).map(o=>o.paper_id))];
 const old=oldPeople.get(person.id),weights=new Map(),kwPapers=new Map();let total=0;
 for(const id of ids){const p=paperMap.get(id);if(!p?.fields.keywords.value.length)continue;const weight=p.fields.authors.value[0]?.id===person.id?1:.2;total+=weight;for(const k of p.fields.keywords.value){weights.set(k.id,{name:k.name,score:(weights.get(k.id)?.score||0)+weight});if(!kwPapers.has(k.id))kwPapers.set(k.id,[]);kwPapers.get(k.id).push(id);}}
 const keywords=[...weights].map(([id,k])=>({id,name:k.name,weight:k.score/total,papers:kwPapers.get(id)})).sort((a,b)=>b.weight-a.weight||a.name.localeCompare(b.name));
 return{id:person.id,name:person.display_name||person.name,identityName:person.name,aliases:old?.aliases||[person.name],group:W.ATLAS_AUTHOR_GROUPS.assignments[person.name]||'other',papers:ids,keywords,state:person.id.includes('pending')?'review':'ready',identityLabel:person.id.includes('pending')?'同名身份待确认':old?.sources?.length?'有身份核查来源':'按署名归一',identityNote:person.identity_note||'',sources:(old?.sources||[]).map(url=>source('身份核查来源',url)),chinese:''};
});
for(const [file,group]of [['current-students.json','current'],['graduated-students.json','graduated']]){
 const roster=read(file);
 for(const entry of roster.students){let person=authors.find(a=>a.identityName===entry.author_name||a.chinese===entry.name);
  if(person){person.chinese=entry.name;person.rosterSource=roster.source;}
  else authors.push({id:'roster-'+group+'-'+entry.name,name:entry.author_name||entry.name,identityName:entry.author_name||'',chinese:entry.name,aliases:[],group,papers:[],keywords:[],state:'unlinked',identityLabel:entry.author_name?'尚未关联论文':'中文姓名尚未对应署名',identityNote:'',sources:[],rosterSource:roster.source});
 }
}
const coverage={total:papers.length,authors:papers.filter(p=>p.fields.authors.state==='ready').length,venue:papers.filter(p=>p.fields.venue.state==='ready').length,references:papers.filter(p=>p.fields.references.value.length).length,referenceIDs:papers.reduce((n,p)=>n+p.fields.references.total,0),referenceTitles:papers.reduce((n,p)=>n+p.fields.references.parsed,0),keywords:papers.filter(p=>p.fields.keywords.state==='ready').length};
coverage.citingTotal=papers.reduce((n,p)=>n+(p.fields.citing.total||0),0);
coverage.citingIDs=papers.reduce((n,p)=>n+p.fields.citing.ids.length,0);
coverage.citingTitles=papers.reduce((n,p)=>n+p.fields.citing.parsed,0);
for(const key of ['openalex','semantic_scholar','crossref'])coverage[key]=papers.filter(p=>p.fields[key].state==='ready').length;
const external=data.nodes.filter(p=>!p.lab).map(p=>{
 const row=bibliography[p.id]||bibliography[p.openalex?.split('/').pop()]||{},metaSource=source('OpenAlex',p.openalex),dep=addDependencies(p);
 const simple=(value)=>field(value,value==null||value===''||Array.isArray(value)&&!value.length?'missing':'ready',[metaSource],{observations:value==null||value===''||Array.isArray(value)&&!value.length?[]:[{value,adopted:true,sources:[metaSource]}],adoptedValue:value});
 return {id:p.id,title:p.title,providers:[...new Set([...(p.openalex?['OpenAlex']:[]),...dep.vector.sources.map(s=>s.name)])],links:[p.openalex,p.doi,...(p.links||[])].filter(Boolean),issues:[],fields:{
  title:simple(p.title),authors:{...simple(p.authors||[]),value:(p.authors||[]).map(name=>({name,raw:name,excluded:true}))},year:simple(p.year),venue:{...simple(p.venue||row.venue||''),value:{name:p.venue||row.venue||''}},abstract:simple(p.abstract||''),
  references:field(p.references||[],p.references?.length?'ready':p.reference_status==='database_observed'?'empty':'missing',[metaSource],{total:p.references?.length||0,parsed:(p.references||[]).filter(id=>bibliography[id]).length,explanation:'外部论文参考文献记录；不建立外部论文之间的引用边。'}),
  citing:field(null,'missing',[],{ids:[],total:null,parsed:0,explanation:'未为外部文献采集施引名单。'}),
  citations:field(p.citations,Number.isFinite(p.citations)?'ready':'missing',[metaSource],{observations:Number.isFinite(p.citations)?[{value:p.citations,adopted:true,sources:[metaSource]}]:[],adoptedValue:p.citations,attempts:[]}),
  keywords:field([],'missing',[],{explanation:'本流程未为外部文献导出关键词。'}),identity:field({openalex:p.openalex||'',doi:p.doi||'',semantic_scholar:p.semantic_paper_id||''},p.openalex?'ready':'missing',[]),...dep}};
});
const dashboard={meta:{snapshot:data.meta.updated,citationsSnapshot:citation.collected_at,scope:'全部年份的实验室论文',coverage,authorCount:authors.length,groups:W.ATLAS_AUTHOR_GROUPS.groups,statuses},papers,authors,external,bibliography};
fs.writeFileSync(path.join(root,'retrieval-data.json'),JSON.stringify(dashboard,null,2)+'\n');
fs.writeFileSync(path.join(root,'retrieval-data.js'),'window.ATLAS_RETRIEVAL='+JSON.stringify(dashboard)+';\n');
const networkEvidence={coverage,bibliography,papers:Object.fromEntries(papers.map(p=>[p.id,{title:p.title,links:p.links,fields:Object.fromEntries(['title','authors','venue','year','abstract','keywords','references','citing','citations'].map(key=>[key,p.fields[key]]))}]))};
fs.writeFileSync(path.join(root,'network-evidence.js'),'window.ATLAS_NETWORK_EVIDENCE='+JSON.stringify(networkEvidence)+';\n');
console.log('Dashboard:',coverage,'authors',authors.length);
