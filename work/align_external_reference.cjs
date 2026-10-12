const fs=require('node:fs');
const p='outputs/paper-atlas/workflow-flow-data.js';let s=fs.readFileSync(p,'utf8');
const before="{id:'external',stage:3,slot:0,row:'citations',offset:30,";
if(!s.includes(before))throw Error('External action anchor missing');
s=s.replace(before,"{id:'external',stage:3,slot:0,row:'citations',offset:82,");fs.writeFileSync(p,s);
const test='work/check_workflow_flow.cjs';let t=fs.readFileSync(test,'utf8');
t=t.replace("assert.equal(d.processes.find(p=>p.id==='external').offset,d.nodes.find(n=>n.id==='lab-counts').offset);","assert.equal(d.processes.find(p=>p.id==='external').offset,d.nodes.find(n=>n.id==='reference-list').offset);");fs.writeFileSync(test,t);
