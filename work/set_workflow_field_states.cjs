const fs=require('node:fs');const dir='outputs/paper-atlas/';
let data=fs.readFileSync(dir+'workflow-flow-data.js','utf8');
data=data.replace("kind:stage===0?'source':'final'", "kind:stage===0?'source':'final',settled:stage!==0");
data=data.replace("  node(id+'-resolved','citations'", "  Object.assign(f.nodes.at(-1),{kind:'intermediate',settled:false});\n  node(id+'-resolved','citations'");
fs.writeFileSync(dir+'workflow-flow-data.js',data);
let render=fs.readFileSync(dir+'workflow-flow.js','utf8');render=render.replace('padding=[2,3].includes(index)?40:24','padding=[2,3].includes(index)?20:12');render=render.replace("n.kind==='final'?'life-settle'", "n.settled?'life-settle'");render=render.replace('data-flow-node="${n.id}" ${n.process?', 'data-flow-node="${n.id}" ${n.process?');fs.writeFileSync(dir+'workflow-flow.js',render);
let css=fs.readFileSync(dir+'workflow.css','utf8');css=css.replace('background:color-mix(in srgb,var(--track) 8%,white);font-weight:500}', 'background:var(--paper);font-weight:500}.flow-node.life-settle{background:color-mix(in srgb,var(--track) 8%,white)}');fs.writeFileSync(dir+'workflow.css',css);
