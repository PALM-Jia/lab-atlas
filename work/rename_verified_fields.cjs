const fs=require('fs');const dir='outputs/paper-atlas/';const names=[['标题（核对后）','论文标题'],['署名（核对后）','作者信息'],['发表情况（核对后）','论文录用情况']];
for(const file of ['workflow-flow-data.js','workflow-data.js','workflow-guide.js','workflow-explanations.js']){let s=fs.readFileSync(dir+file,'utf8');for(const [a,b] of names)s=s.replaceAll(a,b);fs.writeFileSync(dir+file,s);}
