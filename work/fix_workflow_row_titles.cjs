const fs=require('node:fs');const dir='outputs/paper-atlas/';
let s=fs.readFileSync(dir+'workflow-flow.js','utf8');
const band='<button class="flow-group-label" data-flow-group="${r.id}" data-info="${r.info}">${esc(r.label)}</button>';
if(!s.includes(band))throw Error('Group title markup missing');
s=s.replace(band,'<div class="flow-row-header"><button class="flow-group-label" data-flow-group="${r.id}" aria-pressed="false">${esc(r.label)}</button></div>');
s=s.replaceAll('class="flow-visible ${e.type}"','data-flow-trace="${e.id}" class="flow-visible ${e.type}"');
s=s.replace('class="flow-visible" marker-end','data-flow-trace="${e.id}" class="flow-visible" marker-end');
fs.writeFileSync(dir+'workflow-flow.js',s);
let css=fs.readFileSync(dir+'workflow.css','utf8');
css=css.replace(/\.flow-group-label\{[^}]*\}/,'.flow-row-header{position:absolute;inset:0 auto 0 0;width:142px;background:#f7f8fb;border-right:1px solid var(--line);z-index:3}.flow-group-label{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:112px;padding:2px 0;border:0;background:transparent;color:var(--text);font-size:13px;line-height:20px;text-align:left;font-weight:600}.flow-row-header:has(.flow-group-label[aria-pressed=true]){background:var(--soft)}');
fs.writeFileSync(dir+'workflow.css',css);
let js=fs.readFileSync(dir+'workflow.js','utf8');
const start=js.indexOf('function choose('),end=js.indexOf("$('clear').onclick",start);
if(start<0||end<0)throw Error('Selection block missing');
const block=`function choose(kind,id,persist=true){
 if(kind==='info'&&!information.has(id))return;
 if(kind==='group'&&!WORKFLOW_FLOW.rows.some(r=>r.id===id))return;
 const stage=data.stages.findIndex(s=>s.id===id);if(kind==='stage'&&stage<0)return;
 selection=kind==='all'?{kind:'all',id:null}:{kind,id};
 const matches=n=>kind==='group'?n.row===id:kind==='info'?n.info===id:kind==='stage'?n.stage===stage:true;
 const seeds=new Set([...flow.nodes.values()].filter(matches).map(n=>n.id));
 const relatedEdges=new Set([...flow.edges.values()].filter(e=>seeds.has(e.from)||seeds.has(e.to)).map(e=>e.id));
 const context=new Set(seeds);for(const key of relatedEdges){const e=flow.edges.get(key);context.add(e.from);context.add(e.to);}
 document.querySelectorAll('[data-flow-node]').forEach(b=>{const n=flow.nodes.get(b.dataset.flowNode);b.setAttribute('aria-pressed',String(kind!=='all'&&matches(n)));b.classList.toggle('dimmed',kind!=='all'&&!context.has(n.id));});
 document.querySelectorAll('[data-flow-trace]').forEach(p=>p.style.opacity=kind==='all'||relatedEdges.has(p.dataset.flowTrace)?'1':'.12');
 document.querySelectorAll('[data-flow-group]').forEach(b=>b.setAttribute('aria-pressed',String(kind==='group'&&b.dataset.flowGroup===id)));
 document.querySelectorAll('.stage-header').forEach(b=>b.setAttribute('aria-pressed',String(kind==='stage'&&b.dataset.stage===id)));
 $('clear').hidden=kind==='all';
 $('selection-caption').textContent=kind==='info'?information.get(id).name:kind==='group'?WORKFLOW_FLOW.rows.find(r=>r.id===id).label:kind==='stage'?data.stages[stage].label:'';
 if(persist){try{const p=new URLSearchParams();if(kind!=='all')p.set(kind,id);history.replaceState(null,'',location.pathname+location.search+(p.size?'#'+p.toString():''));}catch{}}
}
function restore(){const p=new URLSearchParams(location.hash.slice(1));choose('all',null,false);for(const kind of ['group','stage','info'])if(p.has(kind)){const id=kind==='stage'&&['candidates','match'].includes(p.get(kind))?'locate':p.get(kind);choose(kind,id,false);break;}}
$('lifecycle-board').onclick=e=>{const b=e.target.closest('[data-flow-group],[data-info],[data-stage]');if(b)choose(b.dataset.flowGroup?'group':b.dataset.info?'info':'stage',b.dataset.flowGroup||b.dataset.info||b.dataset.stage);};
`;
js=js.slice(0,start)+block+js.slice(end);
js=js.replace("e.target.closest('[data-stage],[data-info]')","e.target.closest('[data-flow-group],[data-stage],[data-info]')");
fs.writeFileSync(dir+'workflow.js',js);
let test=fs.readFileSync('work/check_workflow_flow.cjs','utf8');
const anchor="assert.equal(await page.locator('#inspector a[href=\"retrieval.html\"]').count(),1);";
if(!test.includes(anchor))throw Error('Test anchor missing');
test=test.replace(anchor,anchor+`
 // A row title selects its entire semantic group, including related traces.
 for(const row of d.rows){
  const title=page.locator(\`[data-flow-group="\${row.id}"]\`);await title.scrollIntoViewIfNeeded();await title.click();
  for(const n of [...d.nodes,...d.processes].filter(n=>n.row===row.id)){assert.equal(await page.locator(\`[data-flow-node="\${n.id}"]\`).getAttribute('aria-pressed'),'true',row.id+' group omitted '+n.id);assert(!(await page.locator(\`[data-flow-node="\${n.id}"]\`).getAttribute('class')).includes('dimmed'));}
  const centered=await title.evaluate(e=>{const b=e.getBoundingClientRect(),r=e.closest('.flow-row').getBoundingClientRect();return Math.abs(b.y+b.height/2-r.y-r.height/2)<1;});assert(centered,row.id+' group title off center');
  await page.locator('#clear').click();
 }
 await page.locator('main').evaluate(e=>e.scrollTop=0);
`);
fs.writeFileSync('work/check_workflow_flow.cjs',test);
