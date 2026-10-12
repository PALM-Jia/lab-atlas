(() => {
'use strict';
const data=window.WORKFLOW_MAP, stages=window.WORKFLOW_STAGES;
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const trackMap=new Map(data.tracks.map((t,i)=>[t.id,{...t,index:i}]));
const nodeMap=new Map(data.nodes.map(n=>[n.id,n]));
const position=n=>({x:195+n.stage*151,y:124+trackMap.get(n.track).index*82+n.offset});
const graph=new joint.dia.Graph({}, {cellNamespace:joint.shapes});
const paper=new joint.dia.Paper({el:$('paper'),model:graph,width:1350,height:596,gridSize:1,interactive:false,async:false,cellViewNamespace:joint.shapes,background:{color:'#ffffff'}});
const Stop=joint.dia.Element.define('atlas.Stop',{size:{width:136,height:54},attrs:{root:{tabindex:0,role:'button'},hit:{x:0,y:0,width:136,height:54,fill:'transparent'},halo:{cx:68,cy:27,r:12,fill:'none',strokeWidth:2,opacity:0},ring:{cx:68,cy:27,r:9,fill:'white',strokeWidth:1.4,opacity:0},body:{cx:68,cy:27,r:5.5,fill:'white',strokeWidth:2.3},label:{x:68,y:8,textAnchor:'middle',fontSize:12.5,fontWeight:500,fill:'#364256',stroke:'white',strokeWidth:5,paintOrder:'stroke',pointerEvents:'none'}}},{markup:[{tagName:'rect',selector:'hit'},{tagName:'circle',selector:'halo'},{tagName:'circle',selector:'ring'},{tagName:'circle',selector:'body'},{tagName:'text',selector:'label'}]});
const elements=new Map(), links=[];
paper.freeze();
for(let i=0;i<8;i++){
 const rect=new joint.shapes.standard.Rectangle({position:{x:120+i*151,y:77},size:{width:151,height:518},attrs:{body:{fill:i===2||i===5?'#f7f5fc':i%2?'#fcfcfe':'#ffffff',stroke:'none'},label:{text:''}},z:-3});graph.addCell(rect);
}
for(const t of data.tracks){const y=124+trackMap.get(t.id).index*82;const guide=new joint.shapes.standard.Link({source:{x:122,y},target:{x:1334,y},attrs:{line:{stroke:'#edf0f4',strokeWidth:1,targetMarker:{type:'path',d:''}}},z:-2});graph.addCell(guide);}
for(const n of data.nodes){const pos=position(n), color=trackMap.get(n.track).color;const el=new Stop({id:n.id,position:{x:pos.x-68,y:pos.y-27},attrs:{root:{'aria-label':n.label},body:{stroke:color},ring:{stroke:color,opacity:n.kind==='fixed'?1:0},halo:{stroke:color},label:{text:n.label,y:n.id==='vector'?51:8}},z:2});elements.set(n.id,el);graph.addCell(el);}
for(const e of data.edges){
 const a=nodeMap.get(e.from),b=nodeMap.get(e.to),s=position(a),t=position(b),color=trackMap.get(a.track).color;
 let vertices=[];
 if(e.kind==='bypass'){const dy=a.track==='text'?31:29;vertices=[{x:s.x+23,y:s.y},{x:s.x+23,y:s.y+dy},{x:t.x-25,y:s.y+dy},{x:t.x-25,y:t.y}];}
 else if(s.y!==t.y){const x=s.x===t.x?s.x-68:(s.x+t.x)/2;vertices=[{x,y:s.y},{x,y:t.y}];}
 const link=new joint.shapes.standard.Link({source:s,target:t,vertices,connector:{name:'rounded',args:{radius:8}},attrs:{line:{stroke:color,strokeWidth:e.kind==='dependency'?1.5:2.8,strokeOpacity:e.kind==='dependency'?.36:.8,strokeDasharray:e.kind==='optional'?'5 5':'none',targetMarker:{type:'path',d:''}},wrapper:{strokeWidth:14,cursor:'pointer'}},z:e.kind==='dependency'?0:1});graph.addCell(link);links.push({model:link,edge:e,color});
}
paper.unfreeze();
$('stage-headings').innerHTML=data.stages.map((s,i)=>`<button class="stage-header${s.fixed?' checkpoint':''}" data-stage-index="${i}" style="left:${120+i*151}px;width:151px" aria-pressed="false"><strong>${esc(s.label)}</strong><small>${esc(s.mode)}</small></button>`).join('');
$('lane-headings').innerHTML=data.tracks.map(t=>`<button class="lane-header" data-track="${t.id}" style="top:${124+trackMap.get(t.id).index*82}px;--track:${t.color}" aria-pressed="false">${esc(t.label)}</button>`).join('');
let selectedStage=null, selectedTrack=null;
function emphasize(nodeIds=null,edgeSet=null){
 for(const [id,el]of elements){const active=!nodeIds||nodeIds.has(id);el.attr('label/opacity',active?1:.24);el.attr('body/opacity',active?1:.24);el.attr('ring/opacity',nodeMap.get(id).kind==='fixed'?(active?1:.2):0);el.attr('halo/opacity',nodeIds&&active?.18:0);}
 for(const {model,edge} of links){const active=!nodeIds||(edgeSet?edgeSet.has(edge):(nodeIds.has(edge.from)&&nodeIds.has(edge.to)));model.attr('line/strokeOpacity',active?(edge.kind==='dependency'?.65:.9):.07);model.attr('line/strokeWidth',active?(edge.kind==='dependency'?2:3.2):1.4);}
}
function markControls(){document.querySelectorAll('[data-stage-index]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.stageIndex)===selectedStage)));document.querySelectorAll('[data-track]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.track===selectedTrack)));}
function stageDetail(id,choices){const s=stages.find(s=>s.id===id);if(!s)return;const options=choices||[id];$('inspector').innerHTML=`${options.length>1?`<div class="detail-tabs">${options.map(key=>{const v=stages.find(s=>s.id===key);return `<button data-detail="${key}" class="${key===id?'active':''}">${esc(v.n+' '+v.title)}</button>`;}).join('')}</div>`:''}<div class="detail-top"><h2>${esc(s.n+' '+s.title)}</h2><small>${s.mode==='remote'?'外部查询':'本地处理'} · ${s.ai?'自动 / AI 按需':'自动'}</small></div><dl class="detail-grid">${[['输入',s.input],['增加',s.added],['固定',s.fixed]].map(([k,v])=>`<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl><details><summary>来源、执行方式与边界</summary><p>${esc(s.source)}</p><p>${esc(s.method)}</p><p>${esc(s.note)}</p></details>`;$('inspector').querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>stageDetail(b.dataset.detail,options));}
function selectStage(index){selectedStage=index;selectedTrack=null;const ids=new Set(data.nodes.filter(n=>n.stage===index).map(n=>n.id));const edgeSet=new Set(data.edges.filter(e=>ids.has(e.from)||ids.has(e.to)));for(const e of edgeSet){ids.add(e.from);ids.add(e.to);}emphasize(ids,edgeSet);markControls();stageDetail(data.stages[index].details[0],data.stages[index].details);}
function selectTrack(id){selectedTrack=id;selectedStage=null;const t=trackMap.get(id),ids=new Set(data.nodes.filter(n=>n.track===id).map(n=>n.id));const relevant=new Set(data.edges.filter(e=>ids.has(e.from)||ids.has(e.to)));for(const e of relevant){ids.add(e.from);ids.add(e.to);}emphasize(ids,relevant);markControls();$('inspector').innerHTML=`<div class="detail-top"><h2>${esc(t.label)}</h2></div><p class="detail-summary">${esc(t.description)}</p><div class="detail-tabs">${t.stages.map(id=>{const s=stages.find(x=>x.id===id);return `<button data-open-stage="${id}">${esc(s.n+' '+s.title)}</button>`;}).join('')}</div><p class="note">同色横线追踪同类信息；跨轨连线表示输入依赖。主页原值可以直接进入⑥，不必先匹配数据库。</p>`;$('inspector').querySelectorAll('[data-open-stage]').forEach(b=>b.onclick=()=>stageDetail(b.dataset.openStage));}
function selectNode(id){const n=nodeMap.get(id);selectedStage=n.stage;selectedTrack=null;const ids=new Set([id]), edges=new Set();
 for(const e of data.edges)if(e.from===id||e.to===id){edges.add(e);ids.add(e.from);ids.add(e.to);}emphasize(ids,edges);markControls();const d=data.stages.find(s=>s.id===n.detail);stageDetail(d?d.details[0]:n.detail,d?.details);}
function reset(){selectedStage=null;selectedTrack=null;emphasize();markControls();$('inspector').innerHTML='<div class="detail-top"><h2>信息的扩充与收束</h2></div><dl class="detail-grid"><div><dt>①—⑤ · 收集</dt><dd>OpenAlex 主采集；Semantic Scholar 补缺；按需访问原始发布页。⑤从引用名单扩充外部文献。</dd></div><div><dt>③、⑥ · 固定</dt><dd>③确认论文与版本对应；⑥确定采用字段与人员身份。主页原值和各来源证据继续保留。</dd></div><div><dt>⑦—⑧ · 使用</dt><dd>从采用字段生成特征和关联。检索汇总直接读取来源证据与采用值。</dd></div></dl><p class="note" style="margin-top:10px">同色横线追踪同类信息；跨轨连线表示输入依赖。选择阶段、节点或信息轨道可查看说明。</p>';}
$('stage-headings').onclick=e=>{const b=e.target.closest('[data-stage-index]');if(b)selectStage(Number(b.dataset.stageIndex));};$('lane-headings').onclick=e=>{const b=e.target.closest('[data-track]');if(b)selectTrack(b.dataset.track);};$('clear').onclick=reset;
paper.on('element:pointerclick',view=>{if(nodeMap.has(view.model.id))selectNode(view.model.id);});
paper.on('link:pointerclick',view=>{const entry=links.find(l=>l.model===view.model);if(entry)selectTrack(nodeMap.get(entry.edge.from).track);});
paper.on('element:mouseenter',view=>{if(nodeMap.has(view.model.id))view.model.attr('halo/opacity',.4);});paper.on('element:mouseleave',view=>{if(nodeMap.has(view.model.id))view.model.attr('halo/opacity',0);});
$('paper').addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const el=e.target.closest('[model-id]');if(el&&nodeMap.has(el.getAttribute('model-id'))){e.preventDefault();selectNode(el.getAttribute('model-id'));}});
reset();
})();
