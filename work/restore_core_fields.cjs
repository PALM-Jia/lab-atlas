const fs=require('fs'),vm=require('vm');
const dir='outputs/paper-atlas/';let flow=fs.readFileSync(dir+'workflow-flow-data.js','utf8');
flow=flow.replace("info:'identity',height:164", "info:'identity',height:212").replace("row:'basic',offset:50,label:'多源检索与核对'", "row:'basic',offset:78,label:'多源检索与核对'");
const start=flow.indexOf(" node('home-basic'"),end=flow.indexOf(" edge('locate','identity'",start);
if(start<0||end<0)throw Error('Core block not found');
flow=flow.slice(0,start)+` const core=[
  ['title',30,'主页标题','最终标题','结合署名和版本关系核对标题变体，确定采用标题，保留其他标题与来源。'],
  ['authors',78,'主页署名','最终署名','核对作者顺序与人员身份，保留采用署名、来源原值及同名区分依据。'],
  ['publication',126,'主页发表情况','最终发表情况','结合版本证据核对年份、会议期刊与预印状态，统一等价名称并保留真实差异。']
 ];
 for(const [id,offset,home,final,detail] of core){
  node('home-'+id,'basic',0,0,offset,home,id,'实验室主页的原始字段，保留出处与采集时间；与其他两项基本信息共同提供身份核对线索。');
  node('lab-'+id,'basic',1,1,offset,final,id,'②多源核对后确定。'+detail);
  edge('home-'+id,'locate','query','标题、署名、发表情况共同参与同一次身份与版本核对；每项仍独立保存。');
  edge('locate','lab-'+id,'value',detail);
 }
 node('identity','basic',1,1,182,'确认标识与版本','identity','与实验室条目对应的 OpenAlex ID、Semantic Scholar paperId、DOI、arXiv ID 或原始发布页，以及确认的版本关系。关联核对所用的基本信息证据；③按这些定位结果查询。');
`+flow.slice(end);
fs.writeFileSync(dir+'workflow-flow-data.js',flow);
const ctx={window:{}};vm.createContext(ctx);for(const name of ['workflow-data','workflow-guide'])vm.runInContext(fs.readFileSync(dir+name+'.js','utf8'),ctx);
const titles={import:'读取主页清单',locate:'核对身份与版本',collect:'采集论文详情',external:'补全引用记录',features:'生成特征与画像'};
const modes={import:'外部读取 · 自动',locate:'多源查询 · 自动，AI 按需',collect:'按标识查询 · 自动',external:'外部查询 · 自动',features:'本地计算 · 自动'};
const {WORKFLOW_MAP:m,WORKFLOW_STAGES:s,WORKFLOW_GUIDE:g}=ctx.window;
for(const stage of s)stage.title=titles[stage.id];
for(let i=0;i<m.stages.length;i++){const stage=m.stages[i];stage.label=s[i].n+' '+titles[stage.id];stage.mode=modes[stage.id];g.stages[stage.id].title=titles[stage.id];}
fs.writeFileSync(dir+'workflow-data.js','window.WORKFLOW_STAGES = '+JSON.stringify(s,null,2)+';\nwindow.WORKFLOW_MAP = '+JSON.stringify(m,null,2)+';\n');
fs.writeFileSync(dir+'workflow-guide.js','window.WORKFLOW_GUIDE = '+JSON.stringify(g,null,2)+';\n');
let html=fs.readFileSync(dir+'workflow.html','utf8').replace(/<noscript>[\s\S]*?<\/noscript>/,'<noscript>'+m.stages.map(s=>s.label).join(' → ')+'。</noscript>');fs.writeFileSync(dir+'workflow.html',html);
