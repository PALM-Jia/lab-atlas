const fs=require('fs');const dir='outputs/paper-atlas/';
for(const file of ['workflow-flow-data.js','workflow-data.js','workflow-guide.js','workflow-explanations.js']){let s=fs.readFileSync(dir+file,'utf8').replaceAll('作者信息','作者名字');fs.writeFileSync(dir+file,s);}
let s=fs.readFileSync(dir+'workflow-flow-data.js','utf8');s=s.replace("info:'profiles',height:112", "info:'profiles',height:156").replace("id:'features',stage:4,slot:0", "id:'features',stage:4,slot:1").replace("id:'profile',stage:4,slot:2,row:'profiles',offset:54", "id:'profile',stage:4,slot:1,row:'profiles',offset:78");
s=s.replace("['keyword-profile','profiles',30", "['keyword-profile','profiles',54").replace("['direction-profile','profiles',78", "['direction-profile','profiles',102").replace("node(id,row,4,process==='profile'?3:1", "node(id,row,4,2");
const begin=s.indexOf(" edge('lab-title','features'");if(begin<0)throw Error('Old long inputs not found');
s=s.slice(0,begin)+` const inputs=[
  ['feature-title','paperfeatures',30,'论文标题','title',['lab-title','external-info'],'features','使用该论文已核对的标题，作为方向标签和语义向量的必需文本输入。'],
  ['feature-abstract','paperfeatures',78,'摘要','abstract',['lab-abstract','external-info'],'features','该论文摘要可用时与标题一同输入；没有摘要时仅使用标题。'],
  ['profile-authors','profiles',30,'作者名字','authors',['lab-authors'],'profile','使用按署名顺序排列、已完成同名区分的作者名字，确定画像归属和署名贡献权重。'],
  ['profile-keywords','profiles',78,'论文关键词','keywords',['lab-keywords'],'profile','按署名贡献权重聚合论文关键词及分数，形成关键词画像。'],
  ['profile-directions','profiles',126,'方向标签','directions',['directions'],'profile','按署名贡献权重聚合实验室论文方向标签，形成方向画像。']
 ];
 for(const [id,row,offset,label,info,sourceIds,process,description] of inputs){
  node(id,row,4,0,offset,label,info,description);
  Object.assign(f.nodes.at(-1),{kind:'reference',sourceIds});
  edge(id,process,'query',description);
 }
})(window.WORKFLOW_FLOW);
`;
s=s.replaceAll('参考、被引记录','引用文献、被引记录');fs.writeFileSync(dir+'workflow-flow-data.js',s);
let r=fs.readFileSync(dir+'workflow-flow.js','utf8').replace('left=142,gap=56,padding=32','left=142,gap=40,padding=24').replace('const stageGap=index===4?96:gap;','const stageGap=gap;');r=r.replace(/^ const notes=.*\r?\n/m,'').replace('${lines}${notes}${labels}','${lines}${labels}');fs.writeFileSync(dir+'workflow-flow.js',r);
let css=fs.readFileSync(dir+'workflow.css','utf8').replace(/\n\.flow-edge-note\{[^}]+\}\r?\n?/g,'\n');fs.writeFileSync(dir+'workflow.css',css);
let layout=fs.readFileSync(dir+'workflow-layout.js','utf8').replace('padding=48,gap=64','padding=40,gap=48').replace('Math.max(240,groupWidth','Math.max(208,groupWidth');fs.writeFileSync(dir+'workflow-layout.js',layout);
let test=fs.readFileSync('work/check_workflow_flow.cjs','utf8').replace("['external-info','lab-abstract','lab-title']", "['feature-abstract','feature-title']").replace("['directions','lab-authors','lab-keywords']", "['profile-authors','profile-directions','profile-keywords']");test=test.replace(" assert.equal(d.processes.find(p=>p.id==='external')",` for(const e of d.edges.filter(e=>['features','profile'].includes(e.to))){const n=d.nodes.find(n=>n.id===e.from);assert.equal(n.stage,4);assert(n.sourceIds.length);for(const source of n.sourceIds)assert(d.nodes.some(n=>n.id===source));}
 assert(!d.edges.some(e=>e.note));
 assert.equal(d.processes.find(p=>p.id==='external')`);fs.writeFileSync('work/check_workflow_flow.cjs',test);
