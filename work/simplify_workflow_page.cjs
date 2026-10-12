const fs=require('node:fs');const dir='outputs/paper-atlas/';
let html=fs.readFileSync(dir+'workflow.html','utf8');
for(const src of ['vendor/joint-4.3.3.js','workflow-layout.js'])html=html.replace(`<script defer src="${src}"></script>`,'');
html=html.replace(/<div class="intro">.*?<\/div><\/div>/,'<div class="intro"><h1>从论文清单到关系与特征</h1></div>');
html=html.replace('id="panel-lifecycle" role="tabpanel" aria-labelledby="view-lifecycle"','id="panel-lifecycle" aria-label="采集与定稿"');
html=html.replace(/<section id="panel-dependencies"[\s\S]*?<\/section>\s*/,'');
fs.writeFileSync(dir+'workflow.html',html);
const old=fs.readFileSync(dir+'workflow.js','utf8').replace(/\r\n/g,'\n');
let tips=old.slice(old.indexOf('// One viewport-level tooltip'),old.indexOf('// Explanatory prose'));
tips=tips.replace(/const tipSelector=.*?;/,"const tipSelector='[data-flow-group],[data-flow-node],[data-flow-edge],[data-stage]';");
tips=tips.replace(/ if\(target.dataset.lifeBranch\)[\s\S]*?return '';\n}/," return '';\n}");
const head=`(() => {
'use strict';
const data=window.WORKFLOW_MAP,guide=window.WORKFLOW_GUIDE,$=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const information=new Map(data.information.map(i=>[i.id,i]));
let selection={kind:'all',id:null};
const flow=renderWorkflowFlow(WORKFLOW_FLOW,data,guide);
$('lifecycle-board').style.width=flow.width+'px';$('lifecycle-board').style.height=flow.height+'px';
$('lifecycle-board').innerHTML=flow.html;
`;
const tail=`
// Supplemental explanations stay visible regardless of selection.
$('inspector').innerHTML='<div class="explanation-prose">'+window.WORKFLOW_EXPLANATIONS.map(section=>\`<article id="explain-\${esc(section.id)}" class="explanation-section"><h2>\${esc(section.title)}</h2>\${section.paragraphs.map(p=>\`<p>\${esc(p)}</p>\`).join('')}</article>\`).join('')+'</div>';
function choose(kind,id,persist=true){
 if(kind==='info'&&!information.has(id))return;
 if(kind==='stage'&&!data.stages.some(s=>s.id===id))return;
 selection=kind==='all'?{kind:'all',id:null}:{kind,id};
 document.querySelectorAll('[data-info]').forEach(b=>{const active=kind==='info'&&b.dataset.info===id;b.setAttribute('aria-pressed',String(active));b.classList.toggle('dimmed',kind==='info'&&!active);});
 document.querySelectorAll('[data-stage]').forEach(b=>b.setAttribute('aria-pressed',String(kind==='stage'&&b.dataset.stage===id)));
 $('selection-caption').textContent=kind==='info'?information.get(id).name:kind==='stage'?data.stages.find(s=>s.id===id).label:'';
 if(persist){try{const p=new URLSearchParams();if(kind!=='all')p.set(kind,id);history.replaceState(null,'',location.pathname+location.search+(p.size?'#'+p.toString():''));}catch{}}
}
function restore(){const p=new URLSearchParams(location.hash.slice(1));choose('all',null,false);for(const kind of ['stage','info'])if(p.has(kind)){const id=kind==='stage'&&['candidates','match'].includes(p.get(kind))?'locate':p.get(kind);choose(kind,id,false);break;}}
$('lifecycle-board').onclick=e=>{const b=e.target.closest('[data-info],[data-stage]');if(b)choose(b.dataset.info?'info':'stage',b.dataset.info||b.dataset.stage);};
$('clear').onclick=()=>choose('all');
document.addEventListener('click',e=>{if(!(e.target instanceof Element)||e.target.closest('[data-stage],[data-info]'))return;if(selection.kind!=='all')choose('all');},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape')choose('all');});
window.addEventListener('hashchange',restore);restore();
})();
`;
fs.writeFileSync(dir+'workflow.js',head+tips+tail);
const sections=[
 {id:'queries',title:'两次检索各自解决什么问题',paragraphs:[
 '第一次用主页的标题、署名和发表情况，同时在 OpenAlex 与 Semantic Scholar 寻找候选；遇到改名、预印本与正式版等疑问，再查论文原始发布页。结合这些证据确定论文身份、版本及三项基本信息。明确对应由规则处理，复杂歧义才交给 AI 辅助核对。',
 '第二次用确认的数据库标识精确查询，以 OpenAlex 为主，Semantic Scholar 按字段补缺，原始发布页按需补充。摘要、关键词、数据库主题、被引数与两份引用记录在这里采集；第一次搜索附带返回的这些详情不沿用。若详情查询暴露身份或版本冲突，返回身份核对阶段处理。']},
 {id:'adoption',title:'来源差异与信息取舍',paragraphs:[
 '同一工作可能有多个标题、版本和数据库标识。版本联系明确时优先采用正式版，并保留别名与版本对应。NeurIPS 与 Neural Information Processing Systems 这类等价名称统一；主页标“预印”、数据库写年份这类实际差异则保留来源表述及采用理由。作者同名结合单位、合作关系等证据区分，人员分类以实验室确认的名单为准。',
 '来源原值、采用值、采集时间和判断依据随具体字段保存。字段为空、请求失败和分页未完成分别记录；“确定”也可以是明确记录缺失及原因。实际到位情况见检索汇总。']},
 {id:'citations',title:'被引数与引用记录',paragraphs:[
 '“A 引用 B”在 A 的条目中是一篇引用文献，在 B 的条目中是一条被引记录。两种查询方向分别保存收集情况。数据库报告的被引总数、实际取得的被引条目数、其中已匹配详情的条目数，是三个不同的量，分别受数据库覆盖与统计时间、分页与请求结果、外部详情采集影响。']},
 {id:'external',title:'外部文献的采集范围',paragraphs:[
 '从引用文献与被引记录中提取外部标识，合并去重后采集外部论文。取得的信息用于核对身份与版本、补充条目详情，输出外部文献信息及两份补全后的记录。同一外部论文可供多条关系共用，采集止于这一层。',
 '未匹配的条目保留原标识和失败原因。跨来源去重可能改变记录条目数，被引数仍采用来源统计；缺少摘要或向量时，已有引用关系也会保留。']},
 {id:'features',title:'关键词、主题与文本特征',paragraphs:[
 '论文关键词是来源提供的词项，数据库主题是 OpenAlex 分类体系中的概念，研究方向标签则按论文文本规则生成。它们分别保存，分数含义不同。每篇论文的文本特征使用自己的标题与可用摘要，外部论文也一样；标题是基本输入，摘要补充方法、任务与结论。',
 '图中的语义向量描述拟采用的本地生成路径，当前网络使用 Semantic Scholar 提供的向量。本地模型可接受仅标题输入；DOI、arXiv ID 等用于查询记录与已有向量。生成结果保存实际输入、规则和模型版本，以便区分是否使用了摘要，并支持重算。']},
 {id:'profiles',title:'作者画像的依据',paragraphs:[
 '关键词画像与研究方向画像分别聚合该作者署名的实验室论文。一作权重为 1，其他署名为 0.2；Yuheng Jia 一作时，第二作者按一作计入。每个词项或研究方向保留支撑论文，缺少某项输入的论文不贡献相应画像。外部文献不纳入作者画像。画像反映这些论文的加权分布。']}
];
fs.writeFileSync(dir+'workflow-explanations.js','// Supplemental prose complements the single processing diagram.\nwindow.WORKFLOW_EXPLANATIONS = '+JSON.stringify(sections,null,2)+';\n');
let css=fs.readFileSync(dir+'workflow.css','utf8');
css=css.replace(/#dependency-board\{[^}]*\}#paper\{[^}]*\}#dependency-headings,#dependency-tracks\{[^}]*\}\.dependency-track\{[^}]*\}\.dependency-track:hover\{[^}]*\}\.joint-element\[data-type="atlas.Artifact"\],\.joint-link\{[^}]*\}\.joint-element:focus-visible \[joint-selector=body\]\{[^}]*\}/g,'');
css=css.replace(/\.explanation-toolbar[^{}]*\{[^}]*\}/g,'').replace(/#dependency-headings[^{}]*\{[^}]*\}/g,'');
css=css.replace('.atlas-header,.explanation-toolbar,.map-actions','.atlas-header,.map-actions').replace(/#inspector \[role=tabpanel\]\[hidden\]\{[^}]*\}/g,'');
fs.writeFileSync(dir+'workflow.css',css);
