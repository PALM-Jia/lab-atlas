const fs=require('node:fs');const p='outputs/paper-atlas/workflow-flow.js';let s=fs.readFileSync(p,'utf8');
s=s.replace('const stageGap=gap,padding=[2,3].includes(index)?20:12;', 'const stageGap=gap,padding=[2,3].includes(index)?20:12;\n  // Entering a bent cross-stage edge needs the 24 px port run plus a 16 px gutter.\n  const leftPadding=[2,3].includes(index)?FLOW_PORT_RUN+16:padding;');
s=s.replace('stageGap*(count-1)+padding*2)', 'stageGap*(count-1)+leftPadding+padding)');
s=s.replace('let x=cursor+padding;', 'let x=cursor+leftPadding;');
fs.writeFileSync(p,s);
