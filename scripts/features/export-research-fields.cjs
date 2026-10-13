/* Export deterministic display fields without changing keywords or graph evidence. */
const fs=require('fs'),path=require('path'),{fields,classify}=require('./research-fields.js');
const ROOT=path.resolve(__dirname,'../..');
const out=path.join(ROOT,'data/atlas');
const graph=JSON.parse(fs.readFileSync(path.join(out,'data.json'),'utf8'));
const assignmentPath=path.join(out,'lab-field-assignments.json');
const assignments=fs.existsSync(assignmentPath)?JSON.parse(fs.readFileSync(assignmentPath,'utf8')):{};
const papers=Object.fromEntries(graph.nodes.map(p=>[p.id,p.lab&&assignments[p.id]?assignments[p.id]:classify(p)]));
const stats={all:{},lab:{}};
for(const p of graph.nodes){const id=papers[p.id].primary||'unclassified';stats.all[id]=(stats.all[id]||0)+1;if(p.lab)stats.lab[id]=(stats.lab[id]||0)+1;}
const data={fields,papers,stats,schema:'six-v1',method:'实验室论文按标题与可用摘要逐篇确定主领域；外部文献按标题与关键词映射。通用方法和监督设定不单独决定领域。'};
const destination=path.join(out,'paper-fields.json');
if(!fs.existsSync(destination)||JSON.stringify(JSON.parse(fs.readFileSync(destination,'utf8')))!==JSON.stringify(data))fs.writeFileSync(destination,JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify(stats));
