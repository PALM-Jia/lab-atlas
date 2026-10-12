const fs=require('fs');global.window=global;require('../outputs/paper-atlas/workflow-data.js');const d=WORKFLOW_MAP;
const stages=[
 {id:'import',n:'①',group:'import',title:'建立清单',mode:'remote',summary:'读取主页论文条目与原始字段。',description:'以实验室主页为论文清单依据，为每个条目建立稳定编号，保存标题、署名、发表情况与链接原值。',input:'实验室论文主页。',added:'实验室条目、标题、署名、年份与发表情况、原始链接。',fixed:'实验室条目范围、稳定编号和主页原值。',source:'实验室主页。',method:'自动解析。',note:'各字段附带出处与采集时间；获取失败记录在具体请求上。'},
 {id:'locate',n:'②',group:'retrieval',title:'定位与核对',mode:'remote',checkpoint:true,ai:true,summary:'固定实验室身份、标题、人员署名和发表情况。',description:'用主页标识与核心字段查找候选，对照版本和人员证据，必要时补查；完成身份判断与核心字段采用。',input:'主页标题、署名、发表情况、链接及确认名册。',added:'来源 ID、版本关系、其他来源核心字段和顺带返回的字段缓存。',fixed:'实验室身份对应、标题、人员署名、名册分类与年份发表情况；未确定项保存原因。',source:'OpenAlex 主查、Semantic Scholar 按需补查、原始发布页查证。',method:'明确标识与已有规则自动处理；复杂身份、版本或同名人员问题由 AI 比较来源证据。',note:'顺带返回的摘要等缓存保留，③直接复用。新核心差异返回②核对；第三方值不直接覆盖主页原值。'},
 {id:'collect',n:'③',group:'retrieval',title:'采集并确定实验室信息',mode:'remote',checkpoint:true,ai:true,summary:'确定实验室其余字段，分别保存参考记录与施引记录。',description:'按确认的来源 ID 或发布页复用缓存并补缺，在同阶段比较来源、确定采用值，记录每项缺失或获取不全的具体状态。',input:'②确认的论文记录、固定核心字段及其余字段缓存。',added:'摘要、关键词、主题、来源被引数、参考记录、施引记录及获取状态。',fixed:'实验室采用摘要、关键词、主题、被引次数，以及本次取得的参考和施引记录；未取全的列表保留当前条目与状态。',source:'OpenAlex 主采集，Semantic Scholar 和原始发布页按字段缺口补充。',method:'自动读取、缓存、重试和来源规则采用；少量实质分歧由 AI 比较已有证据。',note:'数据库被引总数、取得的施引条目数、其中匹配详情的条目数分别统计。采用被引数来自来源统计，不由已取得施引列表长度代替。'},
 {id:'external',n:'④',group:'retrieval',title:'采集外部并补全引用记录',mode:'remote',checkpoint:true,summary:'核定外部论文信息，分别补充两份引用记录的端点详情。',description:'用③参考和施引记录中的标识确定外部检索范围；查找并核对外部身份，采用其字段，归一记录端点并去重。',input:'③已取得的参考记录、施引记录及其标识。',added:'外部论文身份、版本、标题、署名、发表情况、摘要、关键词、主题和被引数，以及记录端点匹配结果。',fixed:'外部论文信息与获取状态、补充后的参考记录和施引记录；匹配不到的原条目仍保留。',source:'OpenAlex 批量读取；已有其他来源标识按可确认的 DOI 等对应。',method:'自动按标识查询、核对、采用与去重；未确定身份保留具体原因。',note:'补全指为已经取得的引用条目补充身份与详情，不代表名单全部取得。④不因施引名单长度或详情匹配量修改③的数据库被引总数，也不递归采集外部引用。'},
 {id:'features',n:'⑤',group:'features',title:'生成特征',mode:'local',summary:'生成方向标签、语义向量与作者画像。',description:'从已核定的标题和可用摘要生成方向标签及文本向量；按人员署名汇总论文关键词与方向画像。',input:'②实验室核心字段、③实验室其余字段、④外部信息，以及固定规则和模型。',added:'研究方向标签、语义向量、作者关键词画像和方向画像。',fixed:'特征结果、输入与规则或模型版本，以及支撑论文。',source:'本地计算，无文献查询。',method:'固定规则、固定模型和署名贡献权重自动计算。',note:'标题必需、摘要可选；现有网络向量来自 Semantic Scholar，本流程包含本地计算路径。一作权重 1，其他署名 0.2；Yuheng Jia 一作时按第二作者计一作。网络连线、详情和检索汇总直接使用上述结果，不另设采集阶段。'}
];
d.stages=stages.map(s=>({id:s.id,label:s.n+' '+s.title,mode:s.id==='import'?'外部查询 · 自动':s.id==='locate'?'查询＋核对 · AI 按需':s.id==='collect'?'采集＋采用 · AI 按需':s.id==='external'?'查询＋核对 · 自动':'本地处理 · 自动',details:[s.id],...(s.checkpoint?{fixed:true}:{})}));
d.tracks=d.tracks.filter(t=>t.id!=='output');
const track=(id,x)=>Object.assign(d.tracks.find(t=>t.id===id),x);
track('identity',{used:'③读取确认的实验室记录；④核对外部记录。无法确定数据库身份时仍保留经核对的主页核心字段。',stages:['locate','external']});
track('text',{collect:'①保留主页标题，②核定实验室标题；③补充并采用实验室摘要；④核定外部标题与摘要。',fixed:'实验室标题在②、摘要在③确定；外部标题与摘要在④确定。',used:'⑤从标题和可用摘要生成方向标签与语义向量。',stages:['locate','collect','external','features']});
track('authors',{used:'⑤按②已确认的实验室人员署名聚合画像，一作权重 1、其他署名 0.2。',stages:['locate','external','features']});
track('keywords',{collect:'③复用缓存并补充实验室关键词和主题；④读取外部字段。',fixed:'实验室关键词与主题在③采用，外部值在④分别采用。',stages:['collect','external','features']});
track('publication',{fixed:'实验室年份发表在②固定，被引次数在③采用；外部发表与被引数在④核定。',used:'保存来源统计时点；数据库被引数与取得施引条目数、已匹配详情数分别展示。',stages:['locate','collect','external']});
track('citations',{collect:'③分别保存参考记录和施引记录；④按两份记录采集外部论文信息。',fixed:'③固定已取得的条目及获取状态；④分别补充端点身份详情、归一和去重。',used:'参考与施引是 A 引用 B 的两种查询方向；详情未齐不删除已取得记录，不建立外部—外部引用边。',stages:['collect','external']});
for(const i of d.information){
 if(['abstract','counts','keywords','topics'].includes(i.id)){
  i.sources=[2];i.settle=2;
  for(const lane of i.lifecycles||[]){const lab=lane.scope==='实验室论文';lane.sources=[lab?2:3];lane.settle=lab?2:3;lane.end[1]=(lab?'③核定实验室':'④核定外部')+i.name+'及获取状态；保留各来源原值和采用理由。';for(const b of lane.branches||[])b.description=(lab?'③读取已确认的实验室记录并复用②缓存':'④读取外部论文自身记录')+'，在本阶段确定采用值与缺失状态。';}
  i.description=(i.id==='counts'?'来源在指定统计时点报告的被引总数；':'')+'实验室值在③采集并采用，外部值在④独立核定；缺失和来源分歧随字段保存。';
 }
 if(['directions','vector','profiles'].includes(i.id)){i.sources=[4];i.settle=4;i.description=i.description.replaceAll('⑥','⑤');}
 if(['title','authors','publication'].includes(i.id)){i.scope=i.scope.replace('③与⑤','③与④');for(const lane of i.lifecycles||[])lane.end[1]=lane.end[1].replace('新差异返回②','新差异返回②');}
}
const ref=d.information.find(i=>i.id==='references');Object.assign(ref,{sources:[2,3],settle:3,description:'③分别保存已取得的参考记录与施引记录及其收集状态。④用外部论文信息分别补充端点身份与详情、合并重复条目。',scope:'两份记录均按 A 引用 B 的方向解释；补全详情不表示名单全量取得，也不修改来源报告的被引总数。',lifecycles:[{scope:'参考记录',sources:[2,3],settle:3,branches:[{stage:2,label:'参考记录',description:'③取得实验室论文所引用的条目及获取状态。'}],end:['补全参考记录','④按外部身份补充已有参考条目的端点详情并去重，保留未匹配项。']},{scope:'施引记录',sources:[2,3],settle:3,branches:[{stage:2,label:'施引记录',description:'③取得引用实验室论文的条目及获取状态。'}],end:['补全施引记录','④补充已有施引条目的端点详情并去重，保留未匹配项，不重算数据库被引数。']}]});
const removed=new Set(['paperEdges','authorEdges','topicEdges','appearance','citationEdges','summary']);d.artifacts=d.artifacts.filter(a=>!removed.has(a.id));
for(const a of d.artifacts){if(['abstract','counts','keywords','topics'].includes(a.id))a.stage=2;if(['directions','vector','keywordProfile','directionProfile'].includes(a.id))a.stage=4;if(a.id==='citationMap')a.stage=3;a.detail=d.stages[a.stage].id;}
const art=(id,x)=>Object.assign(d.artifacts.find(a=>a.id===id),x);
art('references',{label:'参考记录',definition:'③取得的实验室论文参考条目、来源标识、方向与收集状态；列表可能获取不全。'});
art('citationMap',{label:'补全参考记录',definition:'④补充已取得参考条目的身份与详情，归一端点并去重；匹配失败的条目和原因仍保留。'});
art('external',{definition:'④根据③参考与施引记录查找外部论文，核定其身份、标题、署名、发表情况和其余字段；获取不全时保存现有值和状态。'});
art('abstract',{label:'实验室摘要',definition:'③核定的实验室摘要及其来源；没有摘要保留缺失。'});
art('counts',{label:'采用被引数',definition:'③采用的实验室论文数据库被引总数及来源时点；④不依据不完整施引名单或详情匹配数修改它。'});
art('keywords',{label:'实验室关键词',definition:'③采用的实验室关键词与分数，附来源与缺失状态。'});
art('topics',{label:'实验室主题',definition:'③采用的实验室 OpenAlex 主题与分数，附来源与缺失状态。'});
d.artifacts.push({id:'citingRecords',info:'references',stage:2,label:'施引记录',detail:'collect',definition:'③取得的施引条目、来源标识和获取状态；实际条目数与数据库报告的被引总数分别记录。'},{id:'citingMap',info:'references',stage:3,label:'补全施引记录',detail:'external',definition:'④补充已有施引条目的身份与详情，归一去重并保留未匹配项；不改写来源被引总数。'});
d.dependencies=d.dependencies.filter(e=>!removed.has(e.from)&&!removed.has(e.to)&&!(e.from==='external'&&['abstract','counts','keywords','topics'].includes(e.to)));
function edge(from,to,type,explanation){d.dependencies.push({id:from+'--'+to,from,to,type,explanation});}
for(const e of d.dependencies){e.explanation=e.explanation.replaceAll('⑤','③').replaceAll('⑥','⑤');if(e.from==='references'&&e.to==='external'){e.type='optional';e.explanation='从已取得的参考条目提取另一端标识，加入外部检索范围；施引方向独立贡献其条目。';}if(e.from==='references'&&e.to==='citationMap')e.explanation='对③已取得的参考记录补充端点身份详情并去重，保留原始条目及获取状态。';if(e.from==='external'&&e.to==='citationMap')e.explanation='可匹配的外部身份与详情填入参考条目；未匹配项仍保留。';}
edge('identity','citingRecords','required','按②确认的实验室来源 ID 获取施引条目，并保存实际取得范围与失败状态。');
edge('citingRecords','external','optional','从已取得的施引条目提取论文标识，和参考方向共同确定外部检索范围。');
edge('citingRecords','citingMap','required','④以③已取得的施引记录为基础补充端点详情、归一和去重。');
edge('external','citingMap','optional','把外部身份和详情补入已取得的施引条目，保留未匹配项，不改数据库被引总数。');
const line=xs=>xs.map(x=>' '+JSON.stringify(x)).join(',\n');fs.writeFileSync('outputs/paper-atlas/workflow-data.js','window.WORKFLOW_STAGES = [\n'+line(stages)+'\n];\nwindow.WORKFLOW_MAP = {\n'+['stages','tracks','information','artifacts','dependencies'].map(k=>' '+k+': [\n'+line(d[k])+'\n ]').join(',\n')+'\n};\n','utf8');
const ids=new Set(d.artifacts.map(a=>a.id));console.log(JSON.stringify({stages:d.stages.length,artifacts:d.artifacts.length,edges:d.dependencies.length,badEdges:d.dependencies.filter(e=>!ids.has(e.from)||!ids.has(e.to)),backward:d.dependencies.filter(e=>d.artifacts.find(a=>a.id===e.from).stage>d.artifacts.find(a=>a.id===e.to).stage)}));
