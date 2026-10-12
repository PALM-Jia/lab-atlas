(() => {
'use strict';
const data=window.WORKFLOW_MAP,guide=window.WORKFLOW_GUIDE,$=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const information=new Map(data.information.map(i=>[i.id,i]));
let selection={kind:'all',id:null};
const flow=renderWorkflowFlow(WORKFLOW_FLOW,data,guide);
$('lifecycle-board').style.width=flow.width+'px';$('lifecycle-board').style.height=flow.height+'px';
$('lifecycle-board').innerHTML=flow.html;
// One viewport-level tooltip works outside the horizontally clipped charts.
const tooltip=document.createElement('div');tooltip.id='workflow-tooltip';tooltip.className='workflow-tooltip';tooltip.role='tooltip';tooltip.hidden=true;document.body.append(tooltip);
const tipSelector='[data-flow-group],[data-flow-node],[data-flow-edge],[data-stage]';
let tipTarget=null;
const paragraphs=items=>items.filter(Boolean).slice(0,2).map(text=>`<p>${esc(text)}</p>`).join('');
function tipContent(target){
 if(target.dataset.flowGroup)return paragraphs([WORKFLOW_FLOW.rows.find(r=>r.id===target.dataset.flowGroup).description]);
 if(target.dataset.flowNode)return paragraphs([flow.nodes.get(target.dataset.flowNode).description]);
 if(target.dataset.flowEdge)return paragraphs([flow.edges.get(target.dataset.flowEdge).description]);
 if(target.dataset.stage){const d=guide.stages[target.dataset.stage];return paragraphs(d.tooltip||[d.description,d.boundary]);}
 return '';
}
function hideTip(){if(tipTarget){tipTarget.removeAttribute('aria-describedby');tipTarget=null;}tooltip.hidden=true;}
function showTip(target){const html=tipContent(target);if(!html){hideTip();return;}if(tipTarget===target&&!tooltip.hidden)return;hideTip();tipTarget=target;target.setAttribute('aria-describedby',tooltip.id);tooltip.innerHTML=html;tooltip.hidden=false;const r=target.getBoundingClientRect(),w=tooltip.offsetWidth,h=tooltip.offsetHeight;const left=Math.max(12,Math.min(r.left,innerWidth-w-12)),top=r.bottom+8+h<=innerHeight-12?r.bottom+8:Math.max(12,r.top-h-8);tooltip.style.left=left+'px';tooltip.style.top=top+'px';}
for(const event of ['pointerover','pointermove','focusin'])document.addEventListener(event,e=>{const target=e.target instanceof Element?e.target.closest(tipSelector):null;if(target)showTip(target);});
document.addEventListener('pointerout',e=>{if(tipTarget&&e.target instanceof Element&&e.target.closest(tipSelector)===tipTarget&&(!(e.relatedTarget instanceof Element)||e.relatedTarget.closest(tipSelector)!==tipTarget))hideTip();});
document.addEventListener('focusout',hideTip);document.addEventListener('scroll',hideTip,true);window.addEventListener('resize',hideTip);document.addEventListener('keydown',e=>{if(e.key==='Escape')hideTip();});

// Supplemental explanations stay visible regardless of selection.
$('inspector').innerHTML='<div class="explanation-prose">'+window.WORKFLOW_EXPLANATIONS.map(section=>`<article id="explain-${esc(section.id)}" class="explanation-section"><h2>${esc(section.title)}</h2>${section.paragraphs.map(p=>`<p>${esc(p).replace('【检索汇总】','<a href="retrieval.html">检索汇总</a>')}</p>`).join('')}</article>`).join('')+'</div>';
function choose(kind,id,persist=true){
 if(kind==='info'&&!information.has(id))return;
 if(kind==='action'&&!flow.nodes.get(id)?.process)return;
 if(kind==='edge'&&!flow.edges.has(id))return;
 if(kind==='group'&&!WORKFLOW_FLOW.rows.some(r=>r.id===id))return;
 const stage=data.stages.findIndex(s=>s.id===id);if(kind==='stage'&&stage<0)return;
 selection=kind==='all'?{kind:'all',id:null}:{kind,id};
 const edge=kind==='edge'?flow.edges.get(id):null;
 const matches=n=>kind==='group'?n.row===id:kind==='info'?n.info===id:kind==='stage'?n.stage===stage:kind==='action'?n.id===id:kind==='edge'?[edge.from,edge.to].includes(n.id):true;
 const seeds=new Set([...flow.nodes.values()].filter(matches).map(n=>n.id));
 const relatedEdges=kind==='edge'?new Set([id]):new Set([...flow.edges.values()].filter(e=>seeds.has(e.from)||seeds.has(e.to)).map(e=>e.id));
 const context=new Set(seeds);for(const key of relatedEdges){const e=flow.edges.get(key);context.add(e.from);context.add(e.to);}
 document.querySelectorAll('[data-flow-node]').forEach(b=>{const n=flow.nodes.get(b.dataset.flowNode);b.setAttribute('aria-pressed',String(kind!=='all'&&matches(n)));b.classList.toggle('dimmed',kind!=='all'&&!context.has(n.id));});
 document.querySelectorAll('[data-flow-trace]').forEach(p=>{p.style.opacity=kind==='all'||relatedEdges.has(p.dataset.flowTrace)?'1':'.12';p.style.strokeWidth=kind==='edge'&&p.dataset.flowTrace===id?'2.5':'1.5';});
 document.querySelectorAll('[data-flow-edge]').forEach(p=>p.setAttribute('aria-pressed',String(kind==='edge'&&p.dataset.flowEdge===id)));
 document.querySelectorAll('[data-flow-group]').forEach(b=>b.setAttribute('aria-pressed',String(kind==='group'&&b.dataset.flowGroup===id)));
 document.querySelectorAll('.stage-header').forEach(b=>b.setAttribute('aria-pressed',String(kind==='stage'&&b.dataset.stage===id)));
 $('clear').hidden=kind==='all';
 $('selection-caption').textContent=kind==='info'?information.get(id).name:kind==='group'?WORKFLOW_FLOW.rows.find(r=>r.id===id).label:kind==='stage'?data.stages[stage].label:kind==='action'?flow.nodes.get(id).label:kind==='edge'?flow.nodes.get(edge.from).label+' → '+flow.nodes.get(edge.to).label:'';
 if(persist){try{const p=new URLSearchParams();if(kind!=='all')p.set(kind,id);history.replaceState(null,'',location.pathname+location.search+(p.size?'#'+p.toString():''));}catch{}}
}
function restore(){const p=new URLSearchParams(location.hash.slice(1));choose('all',null,false);for(const kind of ['group','stage','info','action','edge'])if(p.has(kind)){const id=kind==='stage'&&['candidates','match'].includes(p.get(kind))?'locate':p.get(kind);choose(kind,id,false);break;}}
$('lifecycle-board').onclick=e=>{
 const b=e.target.closest('[data-flow-group],[data-flow-node],[data-stage],[data-flow-edge]');if(!b)return;
 if(b.dataset.flowGroup)choose('group',b.dataset.flowGroup);
 else if(b.dataset.flowNode){const n=flow.nodes.get(b.dataset.flowNode);choose(n.process?'action':'info',n.process?n.id:n.info);}
 else if(b.dataset.stage)choose('stage',b.dataset.stage);
 else choose('edge',b.dataset.flowEdge);
};
$('lifecycle-board').addEventListener('keydown',e=>{if(!['Enter',' '].includes(e.key))return;const b=e.target.closest('[data-flow-edge]');if(b){e.preventDefault();choose('edge',b.dataset.flowEdge);}});
$('clear').onclick=()=>choose('all');
document.addEventListener('click',e=>{if(!(e.target instanceof Element)||e.target.closest('[data-flow-group],[data-flow-node],[data-stage],[data-flow-edge]'))return;if(selection.kind!=='all')choose('all');},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape')choose('all');});
window.addEventListener('hashchange',restore);restore();
})();
