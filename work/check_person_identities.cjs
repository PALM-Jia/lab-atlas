const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const data=JSON.parse(fs.readFileSync('outputs/paper-atlas/data.json','utf8'));
const context={window:{}};
for(const file of ['author-identities.js','author-groups.js','author-identity-resolver.js'])vm.runInNewContext(fs.readFileSync('outputs/paper-atlas/'+file,'utf8'),context);
const people=new Map(),resolve=context.window.resolveAtlasPaperAuthors;
for(const paper of data.nodes.filter(p=>p.lab))for(const person of resolve(paper)){
 if(!people.has(person.id))people.set(person.id,{name:person.name,papers:new Set()});
 people.get(person.id).papers.add(paper.id);
}
assert.equal(people.size,203,'201 normalized plus2 unresolved appearances');
const find=name=>[...people.values()].filter(p=>p.name===name);
const groups=context.window.ATLAS_AUTHOR_GROUPS;
assert.equal(Object.values(groups.assignments).filter(g=>g==='graduated').length,14);
const graduated=JSON.parse(fs.readFileSync('outputs/paper-atlas/graduated-students.json','utf8'));
assert.equal(graduated.students.length,13);assert.equal(new Set(graduated.students.map(s=>s.name)).size,13);
for(const s of graduated.students.filter(s=>s.author_name))assert.equal(groups.assignments[s.author_name],'graduated');
for(const name of graduated.previously_confirmed_retained)assert.equal(groups.assignments[name],'graduated');
for(const name of ['Wenlong Lyu','Zhuoming Li','Zhixin Li'])assert.equal(groups.assignments[name],'current');
const roster=JSON.parse(fs.readFileSync('outputs/paper-atlas/current-students.json','utf8')).students;
assert.equal(roster.length,30);assert.equal(new Set(roster.map(s=>s.name)).size,30);
assert.equal(Object.values(groups.assignments).filter(g=>g==='current').length,21);
for(const s of roster.filter(s=>s.author_name))assert.equal(groups.assignments[s.author_name],'current');
for(const name of Object.keys(groups.assignments)){
 const count=find(name==='Xiaoyu Wang — SEU'?'Xiaoyu Wang':name).length;
 assert(count===1||['Li Yuan','Xujie Xiao','Yuzhe Zhou','Jingwei Fang'].includes(name)&&count===0,'classification matches one existing author or a roster member awaiting papers');
}
for(const name of ['Junfeng Fang','Xu Zhang','Haiyun Guo','Hanyang Li','Yuhang Li'])assert.notEqual(groups.assignments[name],'current');
assert.equal(resolve(data.nodes.find(p=>p.id==='lab-bf934091a903')) .find(p=>p.name==='Xiaoyu Wang — Monash').group,'other');
assert.equal(find('Hui Liu').length,1);assert.equal(find('Hui Liu')[0].papers.size,39);
assert.equal(find('Junhui Hou')[0].papers.size,50);assert.equal(find('Xu Zhang')[0].papers.size,5);
assert.equal(find('Jing Wang')[0].papers.size,10);assert.equal(find('Jiachao Liu')[0].papers.size,2);
assert.equal(find('Yang Liu')[0].papers.size,2);
assert.equal(find('Xiaoyu Wang — Monash')[0].papers.size,1);assert.equal(find('Xiaoyu Wang')[0].papers.size,5);
assert.equal([...people.values()].filter(p=>p.name.startsWith('Hao Chen（')).length,2);
assert.equal(resolve({id:'unseen',authors:['Hui Liu']})[0].id,'unresolved-unseen-Hui Liu','new occurrences need identity audit');
assert.equal(resolve({id:'unseen',authors:['Hui Liu','Hui Liu']}).length,1,'duplicate署名 deduplicated');
const allRows=fs.readFileSync('outputs/author-person-classification.txt','utf8');assert(allRows.includes('Xiaoyu Wang — Monash')&&allRows.includes('H1\tHao Chen'));
console.log('PASS: occurrence-based person identity, aliases, fragmented IDs, homonyms, pending identities, duplicate signatures and classification export.');
