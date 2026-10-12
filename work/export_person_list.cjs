const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const data=JSON.parse(fs.readFileSync('outputs/paper-atlas/data.json','utf8'));
const groupContext={window:{}};require('node:vm').runInNewContext(fs.readFileSync('outputs/paper-atlas/author-groups.js','utf8'),groupContext);
const groupConfig=groupContext.window.ATLAS_AUTHOR_GROUPS;
const displayName=name=>name==='Xiaoyu Wang — SEU'?'Xiaoyu Wang':name;
const category=name=>groupConfig.groups[groupConfig.assignments[name]||'other'].name;
const aliases={
  'Hui LIU':'Hui Liu','Mingkun Xie':'Ming-Kun Xie','Zhang, Xu':'Xu Zhang',
  'Jingq Wang':'Jing Wang','Yang Liu (4829)':'Yang Liu','Jiaochao Liu':'Jiachao Liu'
};
const sources={
  'Hui Liu':['https://cis.sfu.edu.hk/people-jianti.html','https://arxiv.org/abs/2511.21193'],
  'Ming-Kun Xie':['https://xiemk.github.io/'],
  'Xu Zhang':['https://xuz2019.github.io/publications/'],
  'Jing Wang':['https://wangjing4research.github.io/'],
  'Yang Liu':['https://arxiv.org/html/2604.28024v1','https://arxiv.org/html/2605.04827v1'],
  'Jiachao Liu':['https://heyang49.github.io/publications/','https://arxiv.org/pdf/2411.05842'],
  'Bo Han':['https://arxiv.org/html/2410.18388v2','https://arxiv.org/pdf/2605.07557','https://ojs.aaai.org/index.php/AAAI/article/download/39302/43263'],
  'Wei Gao':['https://gaowei262.github.io/pubs-full.html'],
  'Chongjie Si':['https://chongjiesi.site/'],
  'Ran Wang':['https://dblp.org/pid/12/6277-1.html','https://math.szu.edu.cn/en/info/1092/1290.htm','https://arxiv.org/html/2605.20965v1'],
  'Xiaoyu Wang — Monash':['https://academic.oup.com/bib/article/27/3/bbag329/8712665'],
  'Xiaoyu Wang — SEU':['https://ojs.aaai.org/index.php/AAAI/article/download/39302/43263','https://aclanthology.org/2026.acl-long.1265.pdf']
};
const notes={
  'Xiaoyu Wang — Monash':'Monash生物化学与分子生物学；ORCID 0000-0003-4444-6197；与东南作者分列。',
  'Xiaoyu Wang — SEU':'DiCaP：东南软件学院，wang_xy@seu.edu.cn；CuMA：东南计算机学院，结合单位与合作关系归一；其余3篇仅署名，归入实验室多标签合作组。',
  'Bo Han':'东南大学计算机学院，hanbo@seu.edu.cn；不与HKBU同名作者合并。',
  'Zhenbo Lu':'东南大学交通中心，luzhenbo@seu.edu.cn；不与Zhenyu Lu合并。',
  'Zhenyu Lu':'CVPR官方署名Zhenyu Lu；与交通作者Zhenbo Lu分列。'
};
const people=new Map(),pending=[];
const lab=data.nodes.filter(p=>p.lab);
for(const p of lab){
  for(const rawName of new Set(p.authors||[])){
    if(rawName==='Hao Chen'){
      pending.push({name:rawName,paper_id:p.id,title:p.title,links:p.links||[],reason:'两篇论文的同名作者尚无共同邮箱、ORCID或本人论文表可以核验，暂不合并。'});continue;
    }
    let name=aliases[rawName]||rawName;
    if(name==='Xiaoyu Wang')name=p.id==='lab-bf934091a903'?'Xiaoyu Wang — Monash':'Xiaoyu Wang — SEU';
    if(!people.has(name))people.set(name,{person_id:'person-'+crypto.createHash('sha256').update(name).digest('hex').slice(0,12),name,aliases:new Set(),paper_ids:new Set(),openalex_ids:new Set(),sources:sources[name]||[],identity_note:notes[name]||''});
    const person=people.get(name);person.aliases.add(rawName);person.paper_ids.add(p.id);
    for(const a of p.author_records||[])if(a.name===rawName&&a.id)person.openalex_ids.add(a.id);
  }
}
const rows=[...people.values()].map(p=>({...p,aliases:[...p.aliases],paper_ids:[...p.paper_ids],openalex_ids:[...p.openalex_ids]})).sort((a,b)=>b.paper_ids.length-a.paper_ids.length||a.name.localeCompare(b.name));
for(const name of Object.keys(groupConfig.assignments))assert(rows.some(p=>p.name===name)||['Li Yuan','Xujie Xiao','Yuzhe Zhou'].includes(name),'classification name exists or awaits paper import: '+name);
for(const p of rows)p.group=groupConfig.assignments[p.name]||'other';
for(const p of pending)p.group='other';
assert.equal(rows.length,201);assert.equal(pending.length,2);
assert.equal(rows.find(p=>p.name==='Yuheng Jia').paper_ids.length,138);
assert.equal(rows.find(p=>p.name==='Hui Liu').paper_ids.length,39);
assert.equal(rows.filter(p=>p.name.startsWith('Xiaoyu Wang')).length,2);
assert.equal(rows.find(p=>p.name==='Xiaoyu Wang — Monash').paper_ids.length,1);
assert.equal(rows.find(p=>p.name==='Xiaoyu Wang — SEU').paper_ids.length,5);
const expected=lab.reduce((s,p)=>s+new Set(p.authors).size,0),actual=rows.reduce((s,p)=>s+p.paper_ids.length,0)+pending.length;
assert.equal(actual,expected,'every author occurrence assigned exactly once');
const summary={lab_papers:lab.length,original_distinct_names:207,alias_groups_merged:6,homonym_groups_split:1,normalized_person_entries:rows.length,pending_name_groups:1,possible_total_people:[202,203],authors_unavailable_papers:lab.filter(p=>!p.authors.length).map(p=>({id:p.id,title:p.title}))};
fs.writeFileSync('outputs/author-person-identities.json',JSON.stringify({summary,alias_rules:aliases,scope:'已收集的实验室论文作者；数据库ID按具体论文中的出现记录映射，不作全库身份绑定。除有专门查证的冲突项外，结合本地署名与合作关系归一。',people:rows,pending},null,2)+'\n');
const header='人员归一分类名单\n范围：已收集的144篇实验室论文。201个归一人员条目；Hao Chen两条记录单独待确认，人数最终为202或203。\n6组姓名变体已合并；Xiaoyu Wang按Monash与SEU分列。分类按用户标注：已毕业作者14人（另有黄驰、何沐尚无对应署名）、在读名册30人（当前论文作者中18人），其余为其他。\n\n编号\t姓名／身份区分\t论文数\t原始姓名变体\t分类\t备注\n';
fs.writeFileSync('outputs/author-person-classification.txt',header+rows.map((p,i)=>[i+1,displayName(p.name),p.paper_ids.length,p.aliases.join(' / '),category(p.name),p.identity_note].join('\t')).join('\n')+'\n\n待确认：以下两条Hao Chen是否同一人\n'+pending.map((p,i)=>`H${i+1}\t${p.name}\t${p.title}\t分类：其他\t备注：`).join('\n')+'\n');
const networkPeople=rows.map(p=>({id:p.person_id,name:p.name,...(p.name==='Xiaoyu Wang — SEU'?{display_name:'Xiaoyu Wang'}:{}),identity_note:p.identity_note}));
const occurrences=[];
for(const p of rows)for(const paperId of p.paper_ids){const paper=lab.find(v=>v.id===paperId);for(const rawName of new Set(paper.authors))if(p.aliases.includes(rawName))occurrences.push({paper_id:paperId,name:rawName,person_id:p.person_id});}
for(const [i,p]of pending.entries()){
 const id='person-pending-'+p.paper_id;
 networkPeople.push({id,name:`Hao Chen（身份待确认 ${i+1}）`,identity_note:`署名 Hao Chen；${p.title}。两篇同名记录暂时分列，未认定为两个人。`});
 occurrences.push({paper_id:p.paper_id,name:p.name,person_id:id});
}
assert.equal(occurrences.length,expected);
fs.writeFileSync('outputs/paper-atlas/author-identities.js',"'use strict';\nwindow.ATLAS_AUTHOR_IDENTITIES="+JSON.stringify({people:networkPeople,occurrences})+';\n');
fs.writeFileSync('outputs/author-network-names.txt','作者网络默认名单（毕业学生弱化、在读学生显示、其他隐藏；2023–2027含年份未知、全方向；按论文数排序）\n姓名\t论文数\t分类\t备注\n'+networkPeople.filter(p=>p.name!=='Yuheng Jia'&&groupConfig.defaultAuthorModes[groupConfig.assignments[p.name]||'other']!=='hidden').map(p=>({...p,count:occurrences.filter(o=>o.person_id===p.id&&lab.some(paper=>paper.id===o.paper_id&&(paper.year==null||paper.year>=2023&&paper.year<=2027))).length})).filter(p=>p.count>0).sort((a,b)=>b.count-a.count||a.id.localeCompare(b.id)).slice(0,65).map(p=>[p.display_name||p.name,p.count,category(p.name),p.identity_note].join('\t')).join('\n')+'\n');
console.log(JSON.stringify({...summary,author_occurrences:actual},null,2));
