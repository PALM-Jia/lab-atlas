(() => {
'use strict';
const data=window.WORKFLOW_MAP, stages=window.WORKFLOW_STAGES;
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tracks=new Map(data.tracks.map((t,i)=>[t.id,{...t,index:i}]));
const nodes=new Map(data.nodes.map(n=>[n.id,n]));
const edges=new Map(data.edges.map(e=>[e.id,e]));
const layout=window.WorkflowLayout.build(data);
$('map-board').style.height=layout.height+'px';$('map-board').style.minWidth=layout.width+'px';
const graph=new joint.dia.Graph({}, {cellNamespace:joint.shapes});
const paper=new joint.dia.Paper({el:$('paper'),model:graph,width:layout.width,height:layout.height,interactive:false,async:false,cellViewNamespace:joint.shapes,background:{color:'#fff'}});
const Stop=joint.dia.Element.define('atlas.Stop',{
 size:{width:136,height:54},
 attrs:{root:{tabindex:0,role:'button'},hit:{x:0,y:0,width:136,height:54,fill:'transparent'},halo:{cx:68,cy:27,r:12,fill:'none',strokeWidth:2,opacity:0},ring:{cx:68,cy:27,r:9,fill:'white',strokeWidth:1.4,opacity:0},body:{cx:68,cy:27,r:5.5,fill:'white',strokeWidth:2.3},label:{x:68,y:8,textAnchor:'middle',fontSize:12.5,fontWeight:500,fill:'#364256',stroke:'white',strokeWidth:5,paintOrder:'stroke',pointerEvents:'none'}}
},{markup:[{tagName:'rect',selector:'hit'},{tagName:'circle',selector:'halo'},{tagName:'circle',selector:'ring'},{tagName:'circle',selector:'body'},{tagName:'text',selector:'label'}]});
const elements=new Map(), links=new Map();
let selection={kind:'all',id:null},activeNodes=null,activeEdges=null,hovered=null;
paper.freeze();
for(let i=0;i<data.stages.length;i++){
 graph.addCell(new joint.shapes.standard.Rectangle({position:{x:layout.left+i*layout.columnWidth,y:77},size:{width:layout.columnWidth,height:layout.height-78},attrs:{root:{pointerEvents:'none','aria-hidden':true},body:{fill:data.stages[i].fixed?'#f7f5fc':i%2?'#fcfcfe':'#fff',stroke:'none'},label:{text:''}},z:-3}));
}
for(const t of tracks.values()){
 const y=layout.firstY+t.index*layout.pitch;
 graph.addCell(new joint.shapes.standard.Link({source:{x:layout.left+2,y},target:{x:layout.width-16,y},attrs:{root:{pointerEvents:'none','aria-hidden':true},line:{stroke:'#edf0f4',strokeWidth:1,targetMarker:{type:'path',d:''}},wrapper:{display:'none'}},z:-2}));
}
for(const n of data.nodes){
 const pos=layout.point(n),color=tracks.get(n.track).color;
 const el=new Stop({id:n.id,position:{x:pos.x-68,y:pos.y-27},attrs:{root:{'aria-label':n.label,'aria-pressed':'false'},body:{stroke:color},ring:{stroke:color,opacity:n.kind==='fixed'?1:0},halo:{stroke:color},label:{text:n.label,y:n.id==='vector'?51:8}},z:2});elements.set(n.id,el);graph.addCell(el);
}
for(const e of data.edges){
 const a=nodes.get(e.from),b=nodes.get(e.to),color=tracks.get(a.track).color;
 const link=new joint.shapes.standard.Link({id:e.id,source:layout.point(a),target:layout.point(b),vertices:layout.vertices(e),connector:{name:'rounded',args:{radius:8}},attrs:{root:{tabindex:-1,role:'button','aria-label':a.label+' → '+b.label},line:{stroke:color,strokeWidth:e.kind==='dependency'?1.5:2.8,strokeOpacity:e.kind==='dependency'?.4:.85,targetMarker:{type:'path',d:''}},wrapper:{strokeWidth:12,cursor:'pointer'}},z:e.kind==='dependency'?0:1});links.set(e.id,link);graph.addCell(link);
}
paper.unfreeze();
$('stage-headings').innerHTML=data.stages.map((s,i)=>`<button class="stage-header${s.fixed?' checkpoint':''}" data-stage="${s.id}" style="left:${layout.left+i*layout.columnWidth}px;width:${layout.columnWidth}px" aria-pressed="false"><strong>${esc(s.label)}</strong><small>${esc(s.mode)}</small></button>`).join('');
$('lane-headings').innerHTML=data.tracks.map(t=>`<button class="lane-header" data-track="${t.id}" style="top:${layout.firstY+tracks.get(t.id).index*layout.pitch}px;--track:${t.color}" aria-pressed="false">${esc(t.label)}</button>`).join('');
function emphasis(){
 for(const [id,el] of elements){
  const active=!activeNodes||activeNodes.has(id),chosen=selection.kind==='node'&&selection.id===id,color=tracks.get(nodes.get(id).track).color;
  el.attr({label:{opacity:active?1:.24},body:{opacity:active?1:.24,fill:chosen?color:'white'},ring:{opacity:nodes.get(id).kind==='fixed'?(active?1:.2):0},halo:{opacity:hovered===id?.48:chosen?.32:activeNodes&&active?.12:0},root:{'aria-pressed':String(chosen)}});
 }
 for(const [id,el] of links){
  const e=edges.get(id),active=!activeEdges||activeEdges.has(id),chosen=selection.kind==='edge'&&selection.id===id;
  el.attr({line:{strokeOpacity:active?(e.kind==='dependency'?.65:.9):.08,strokeWidth:chosen?4:active?(e.kind==='dependency'?2:3):1.4,targetMarker:{type:'path',d:chosen?'M 6 -3 0 0 6 3 z':''}}});
 }
 document.querySelectorAll('[data-stage]').forEach(b=>b.setAttribute('aria-pressed',String(selection.kind==='stage'&&selection.id===b.dataset.stage)));
 document.querySelectorAll('[data-track]').forEach(b=>b.setAttribute('aria-pressed',String(selection.kind==='track'&&selection.id===b.dataset.track)));
}
function focusNeighborhood(ids){activeNodes=new Set(ids);activeEdges=new Set(data.edges.filter(e=>ids.has(e.from)||ids.has(e.to)).map(e=>e.id));for(const id of activeEdges){const e=edges.get(id);activeNodes.add(e.from);activeNodes.add(e.to);}}
const grid=items=>`<dl class="detail-grid">${items.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`;
// Build the reference once; graph selection only locates existing content.
const stageCards=stages.map(s=>`<article id="explain-stage-${s.id}" class="explanation-card"><div class="detail-top"><h2>${esc(s.n+' '+s.title)}</h2><small>${s.mode==='remote'?'外部查询':'本地处理'} · ${s.ai?'自动 / AI 按需':'自动'}</small></div>${grid([['输入',s.input],['增加',s.added],['固定',s.fixed]])}<div class="source-line"><b>来源</b> ${esc(s.source)} <span>·</span> ${esc(s.method)}</div><p class="boundary-note">${esc(s.note)}</p></article>`).join('');
const trackCards=data.tracks.map(t=>`<article id="explain-track-${t.id}" class="explanation-card"><h2 style="color:${t.color}">${esc(t.label)}</h2><p class="detail-summary">${esc(t.fields)}</p>${grid([['收集',t.collect],['固定',t.fixed],['使用',t.used]])}</article>`).join('');
const edgeCards=data.tracks.map(t=>`<section class="edge-group"><h2 style="color:${t.color}">${esc(t.label)}</h2>${data.edges.filter(e=>nodes.get(e.from).track===t.id).map(e=>{const a=nodes.get(e.from),b=nodes.get(e.to);return `<article id="explain-edge-${e.id}" class="edge-row"><div><button data-node="${a.id}">${esc(a.label)}</button><span class="arrow">→</span><button data-node="${b.id}">${esc(b.label)}</button></div><p>${esc(e.explanation)}</p></article>`;}).join('')}</section>`).join('');
$('inspector').innerHTML=`<div class="explanation-toolbar"><div class="tabs" role="tablist" aria-label="说明视角">${[['stages','阶段说明'],['tracks','信息流'],['edges','连线依据']].map(([id,title],i)=>`<button id="explain-tab-${id}" role="tab" data-doc-tab="${id}" aria-controls="explain-panel-${id}" aria-selected="${i===0}" tabindex="${i===0?0:-1}">${title}</button>`).join('')}</div><button class="quiet" id="back-to-map">流程图 ↑</button></div><div id="explain-panel-stages" role="tabpanel" aria-labelledby="explain-tab-stages">${stageCards}</div><div id="explain-panel-tracks" role="tabpanel" aria-labelledby="explain-tab-tracks" hidden>${trackCards}</div><div id="explain-panel-edges" role="tabpanel" aria-labelledby="explain-tab-edges" hidden>${edgeCards}</div>`;
let docTab='stages';
function showDocs(tab){
 docTab=tab;
 for(const name of ['stages','tracks','edges']){const active=name===tab;const button=$('explain-tab-'+name);button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;button.classList.toggle('active',active);$('explain-panel-'+name).hidden=!active;}
}
function locate(tab,id,scroll=true){
 showDocs(tab);
 if(scroll){const target=$(id);if(target)target.scrollIntoView({block:'start',behavior:'instant'});}
}
function stageTarget(id){const stage=data.stages.find(s=>s.id===id);return stage?stage.details[0]:id;}
function locateChoice(kind,id,scroll){
 if(kind==='stage'||kind==='detail')locate('stages','explain-stage-'+stageTarget(id),scroll);
 if(kind==='track')locate('tracks','explain-track-'+id,scroll);
 if(kind==='node')locate('stages','explain-stage-'+stageTarget(nodes.get(id).detail),scroll);
 if(kind==='edge')locate('edges','explain-edge-'+id,scroll);
}
showDocs('stages');
function remember(kind,id){try{history.replaceState(null,'',kind==='all'?location.pathname:('#'+kind+'='+encodeURIComponent(id)));}catch{}}
function choose(kind,id,save=true,scroll=true){
 if(kind==='detail'){
  const index=data.stages.findIndex(s=>s.details.includes(id));if(index<0)return;
  selection={kind:'stage',id:data.stages[index].id};focusNeighborhood(new Set(data.nodes.filter(n=>n.stage===index).map(n=>n.id)));
 }else if(kind==='stage'){
  const index=data.stages.findIndex(s=>s.id===id);if(index<0)return;
  selection={kind,id};focusNeighborhood(new Set(data.nodes.filter(n=>n.stage===index).map(n=>n.id)));
 }else if(kind==='track'){
  if(!tracks.has(id))return;selection={kind,id};focusNeighborhood(new Set(data.nodes.filter(n=>n.track===id).map(n=>n.id)));
 }else if(kind==='node'){
  if(!nodes.has(id))return;selection={kind,id};focusNeighborhood(new Set([id]));
 }else if(kind==='edge'){
  if(!edges.has(id))return;selection={kind,id};const e=edges.get(id);activeNodes=new Set([e.from,e.to]);activeEdges=new Set([id]);
 }else{kind='all';selection={kind,id:null};activeNodes=null;activeEdges=null;hovered=null;}
 emphasis();if(kind!=='all')locateChoice(kind,id,scroll);if(save)remember(kind,id);
}
$('stage-headings').onclick=e=>{const b=e.target.closest('[data-stage]');if(b)choose('stage',b.dataset.stage);};
$('lane-headings').onclick=e=>{const b=e.target.closest('[data-track]');if(b)choose('track',b.dataset.track);};
$('inspector').addEventListener('click',e=>{const edge=e.target.closest('[data-edge]'),node=e.target.closest('[data-node]');if(edge)choose('edge',edge.dataset.edge);if(node)choose('node',node.dataset.node);});
$('clear').onclick=()=>choose('all');
$('back-to-map').onclick=()=>{$('map-scroll').scrollIntoView({block:'start',behavior:'instant'});};
$('inspector').querySelectorAll('[data-doc-tab]').forEach(b=>b.onclick=()=>{showDocs(b.dataset.docTab);$('inspector').scrollIntoView({block:'start',behavior:'instant'});});
$('inspector').querySelector('[role=tablist]').addEventListener('keydown',e=>{
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();
 const names=['stages','tracks','edges'],i=names.indexOf(docTab);
 const next=e.key==='Home'?0:e.key==='End'?2:(i+(e.key==='ArrowRight'?1:-1)+3)%3;
 showDocs(names[next]);$('explain-tab-'+names[next]).focus();
});
// A capture handler clears on other content, before the diagram handles its own click.
document.addEventListener('click',e=>{
 if(!(e.target instanceof Element))return;
 if(e.target.closest('[data-stage],[data-track],[data-node],[data-edge]'))return;
 const cell=e.target.closest('[model-id]'),id=cell?.getAttribute('model-id');
 if(id&&(nodes.has(id)||edges.has(id)))return;
 if(selection.kind!=='all')choose('all');
},true);
paper.on('element:pointerclick',v=>{if(nodes.has(v.model.id))choose('node',v.model.id);});
paper.on('link:pointerclick',v=>{if(edges.has(v.model.id))choose('edge',v.model.id);});
paper.on('element:mouseenter',v=>{if(nodes.has(v.model.id)){hovered=v.model.id;emphasis();}});
paper.on('element:mouseleave',()=>{hovered=null;emphasis();});
$('paper').addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const el=e.target.closest('[model-id]');if(el&&nodes.has(el.getAttribute('model-id'))){e.preventDefault();choose('node',el.getAttribute('model-id'));}});
$('stage-headings').addEventListener('keydown',e=>{
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
 const buttons=[...$('stage-headings').querySelectorAll('button')],index=buttons.indexOf(e.target);if(index<0)return;e.preventDefault();
 const next=e.key==='Home'?0:e.key==='End'?buttons.length-1:(index+(e.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;
 buttons[next].focus();choose('stage',buttons[next].dataset.stage);
});
document.addEventListener('keydown',e=>{if(e.key==='Escape')choose('all');});
function restore(){const match=location.hash.match(/^#(stage|track|node|edge|detail)=(.+)$/);if(match){let id;try{id=decodeURIComponent(match[2]);}catch{return choose('all',null,false);}choose('all',null,false,false);choose(match[1],id,false,false);}else choose('all',null,false);}
window.addEventListener('hashchange',restore);restore();
})();


