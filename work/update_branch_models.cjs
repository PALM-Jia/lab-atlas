const fs=require('fs');global.window=global;require('../outputs/paper-atlas/workflow-data.js');const d=WORKFLOW_MAP,s=WORKFLOW_STAGES;
const info=id=>d.information.find(x=>x.id===id);
const branch=(stage,label,description)=>({stage,label,description});
info('identity').lifecycles[0].branches=[branch(0,'主页线索','主页标题、作者和链接中的 DOI、arXiv ID 是定位起点。'),branch(1,'候选身份','各来源候选保留独立标识和版本线索，②核对后固定对应关系。')];
info('identity').lifecycles[1].branches=[branch(2,'引用标识','从实验室论文参考与施引查询中取得另一端论文的标识。'),branch(3,'数据库记录','按标识查得外部论文记录，④核对后确定身份与版本对应。')];
for(const [id,home,candidate] of [['title','主页标题','候选标题'],['authors','主页署名','候选署名'],['publication','主页发表信息','候选发表信息']]){
 const row=info(id);row.lifecycles[0].branches=[branch(0,home,'保留主页原值与出处，作为实验室论文核心字段的一条独立来源。'),branch(1,candidate,'各候选来源值先独立保存，②结合身份和版本证据核对采用；新差异返回②。')];
 row.lifecycles[1].branches=[branch(3,'外部来源记录','④读取并核对外部论文自身的来源值，固定其核心字段；不与实验室条目合并。')];
}
info('authors').lifecycles[1].end=['外部人员署名','④核对外部论文自身的人员身份和署名顺序；实验室分类仅依据已确认名册，不为外部作者推断分类。'];
for(const [id,name] of [['abstract','摘要'],['counts','被引次数'],['keywords','关键词'],['topics','数据库主题']]){
 const row=info(id);row.lifecycles=[{scope:'实验室论文',sources:[2],settle:4,branches:[branch(2,'实验室来源值',`③取得已确认实验室记录的${name}及来源；已缓存字段直接复用。各来源值分别保留，⑤决定采用值。`)],end:[`实验室${name}`,`⑤采用实验室论文的${name}；缺失和来源差异随字段记录。`]},{scope:'外部文献',sources:[3],settle:4,branches:[branch(3,'外部来源值',`④取得外部论文自身的${name}原值及来源，⑤单独采用。`)],end:[`外部${name}`,`⑤采用外部论文自身的${name}，不用于替代实验室字段。`]}];
}
info('references').lifecycles=[{scope:'实验室相关关系',sources:[2],settle:4,branches:[branch(2,'参考方向记录','查询实验室论文引用了哪些论文，保留 A 引用 B 的方向与来源。'),branch(2,'施引方向记录','查询哪些论文引用了实验室论文，同样转换为 A 引用 B 的方向。')],end:['统一引用关系','⑤使用②④确认的论文身份归一两端、合并重复关系。两支汇合为关系集合，保留各自出处；不是二选一采用。']}];
const stringify=xs=>xs.map(x=>' '+JSON.stringify(x)).join(',\n');fs.writeFileSync('outputs/paper-atlas/workflow-data.js','window.WORKFLOW_STAGES = [\n'+stringify(s)+'\n];\nwindow.WORKFLOW_MAP = {\n'+['stages','tracks','information','artifacts','dependencies'].map(key=>' '+key+': [\n'+stringify(d[key])+'\n ]').join(',\n')+'\n};\n','utf8');
console.log(d.information.filter(i=>i.lifecycles).map(i=>i.id+': '+i.lifecycles.map(l=>l.branches.length+' branches -> '+l.settle).join(' / ')).join('\n'));
