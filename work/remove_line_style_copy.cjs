const fs=require('node:fs');const p='outputs/paper-atlas/workflow-flow-data.js';let s=fs.readFileSync(p,'utf8');s=s.replace('标题必需，摘要可选；图中虚线标明输入关系。','标题必需，摘要可选。');fs.writeFileSync(p,s);
