const fs=require('node:fs');const p='outputs/paper-atlas/workflow-flow.js';let s=fs.readFileSync(p,'utf8');
s=s.replace('const columns=map.stages.map((stage,index)=>{', 'let previousRightPadding=0;\n const columns=map.stages.map((stage,index)=>{');
s=s.replace('const routeGutter=[1,2,3].includes(index)?FLOW_PORT_RUN+16:0;', 'const routeGutter=[1,2,3].includes(index)?Math.max(FLOW_PORT_RUN+16,FLOW_PORT_RUN*2-previousRightPadding):0;');
s=s.replace('const c={left:cursor,width,center:cursor+width/2,points};cursor+=width;return c;', 'const c={left:cursor,width,center:cursor+width/2,points};previousRightPadding=cursor+width-(points.at(-1)+sizes.at(-1)/2);cursor+=width;return c;');
fs.writeFileSync(p,s);
