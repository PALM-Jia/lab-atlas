const fs=require('node:fs'),p='outputs/paper-atlas/workflow.css';let s=fs.readFileSync(p,'utf8');
const before='#inspector{max-width:1000px;margin-top:18px}.explanation-prose{padding:0;margin:0}';
if(!s.includes(before))throw Error('Prose layout anchor missing');
s=s.replace(before,'#inspector{width:100%;max-width:1048px;margin:18px auto 0}.explanation-prose{padding:0 24px;margin:0}');
s=s.replace('.explanation-section{padding:14px 0}}','.explanation-prose{padding:0 16px}.explanation-section{padding:14px 0}}');
fs.writeFileSync(p,s);
