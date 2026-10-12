const fs=require('fs');const p='outputs/paper-atlas/workflow-flow.js';let s=fs.readFileSync(p,'utf8');const tail=s.slice(s.indexOf('function compactFieldPoints'));
const head=`// Milestones and stage-local routing; computational inputs use the companion view.
window.renderWorkflowFlow=function(data,map,guide){
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const measure=label=>Math.max(84,...label.split('\\n').map(line=>[...line].reduce((s,c)=>s+(/[\\u0000-\\u007f]/.test(c)?7:12),0)+24));
 const left=142,gap=56,padding=32;let cursor=left,y=92;
 const all=[...data.nodes,...data.processes.map(n=>({...n,process:true}))];
 const rows=data.rows.map(row=>{const r={...row,top:y};y+=r.height;return r;});
 const rowMap=new Map(rows.map(r=>[r.id,r]));
 const colors=new Map(map.tracks.map(t=>[t.id,t.color])),info=new Map(map.information.map(i=>[i.id,i]));
 const columns=map.stages.map((stage,index)=>{
  const local=all.filter(n=>n.stage===index),count=Math.max(0,...local.map(n=>n.slot))+1;
  const sizes=Array.from({length:count},(_,slot)=>Math.max(84,...local.filter(n=>n.slot===slot).map(n=>measure(n.label))));
  const width=Math.max(170,sizes.reduce((s,w)=>s+w,0)+gap*(count-1)+padding*2),points=[];
  let x=cursor+padding;for(const w of sizes){points.push(x+w/2);x+=w+gap;}
  const c={left:cursor,width,center:cursor+width/2,points};cursor+=width;return c;
 });
 const items=all.map(n=>({...n,x:columns[n.stage].points[n.slot],y:rowMap.get(n.row).top+n.offset,width:measure(n.label),height:n.label.split('\\n').length*20+8,color:n.process?'#6b6585':colors.get(info.get(n.info).track)}));
 const registry=new Map(items.map(n=>[n.id,n])),width=cursor+12,height=y+8;
 const edges=data.edges.map((e,index)=>({...e,id:'flow-edge-'+index,fromNode:registry.get(e.from),toNode:registry.get(e.to)}));
 const paths=routeFields(items,columns,width,height);
 const routed=new Map(edges.map(e=>[e.id,paths(e)]));
 bundleFieldRoutes(edges,routed,items,columns);
 const headers=map.stages.map((s,i)=>\`<button data-stage="\${s.id}" class="stage-header\${s.fixed?' checkpoint':''}" style="left:\${columns[i].left}px;width:\${columns[i].width}px" aria-pressed="false"><strong>\${esc(s.label)}</strong><small>\${esc(s.mode)}</small></button>\`).join('');
 const bands=rows.map(r=>\`<div class="flow-row" style="top:\${r.top}px;height:\${r.height}px;--track:\${colors.get(info.get(r.info).track)}"><button class="flow-group-label" data-flow-group="\${r.id}" data-info="\${r.info}">\${esc(r.label)}</button></div>\`).join('');
 const grid=columns.map(c=>\`<span class="flow-column" style="left:\${c.left}px;width:\${c.width}px;top:76px;height:\${height-76}px"></span>\`).join('');
 const visible=edges.map(e=>{const points=routed.get(e.id),branch=fieldBranch(points),shared=e.fromNode.process&&e.type==='value',color=e.type==='query'?'#9396a8':shared?'#9693a5':e.toNode.color;return \`<path d="\${roundedFieldPath(points)}" class="flow-visible \${e.type}" \${shared?'':\`marker-end="url(#flow-arrow)"\`} style="stroke:\${color}"/>\${shared?\`<path d="\${roundedFieldPath(branch)}" class="flow-visible" marker-end="url(#flow-arrow)" style="stroke:\${e.toNode.color}"/>\`:''}\`;}).join('');
 const lines=\`<svg class="flow-paths" width="\${width}" height="\${height}"><defs><marker id="flow-arrow" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 6 3 L 0 6 Z" fill="context-stroke"/></marker></defs><g class="flow-ink">\${visible}</g>\${edges.map(e=>\`<path data-flow-edge="\${e.id}" d="\${roundedFieldPath(routed.get(e.id))}" class="flow-hit"/>\`).join('')}</svg>\`;
 const labels=items.map(n=>\`<button class="flow-node \${n.process?'flow-process':n.kind==='final'?'life-settle':'life-event'}" data-flow-node="\${n.id}" \${n.process?\`data-stage="\${map.stages[n.stage].id}"\`:\`data-info="\${n.info}"\`} style="left:\${n.x}px;top:\${n.y-n.height/2}px;width:\${n.width}px;height:\${n.height}px;--track:\${n.color}">\${esc(n.label)}</button>\`).join('');
 return {html:\`\${bands}\${grid}\${lines}\${labels}<div class="lifecycle-header">\${headers}</div>\`,width,height,columns,routes:routed,nodes:registry,edges:new Map(edges.map(e=>[e.id,e]))};
};
function routeFields(items,columns,width,height){
 const boxes=items.map(n=>({id:n.id,left:n.x-n.width/2-4,right:n.x+n.width/2+4,top:n.y-n.height/2-6,bottom:n.y+n.height/2+6}));
 const unique=v=>[...new Set(v)].sort((a,b)=>a-b);
 const clear=(a,b)=>!boxes.some(r=>a.x===b.x?a.x>r.left&&a.x<r.right&&Math.max(a.y,b.y)>r.top&&Math.min(a.y,b.y)<r.bottom:a.y>r.top&&a.y<r.bottom&&Math.max(a.x,b.x)>r.left&&Math.min(a.x,b.x)<r.right);
 return e=>{
  const a=e.fromNode,b=e.toNode,source={x:a.x+a.width/2,y:a.y},target={x:b.x-b.width/2,y:b.y};
  if(target.x<=source.x)throw Error('Non-forward edge: '+e.from+' -> '+e.to);
  if(source.y===target.y&&clear(source,target))return [source,target];
  const start={x:source.x+12,y:source.y},finish={x:target.x-12,y:target.y};
  const endpointColumns=[...new Set([a.stage,b.stage])].map(i=>columns[i]);
  const allowed=x=>endpointColumns.some(c=>x>=c.left+16&&x<=c.left+c.width-16);
  const xs=unique([start.x,finish.x,...endpointColumns.flatMap(c=>[c.left+20,c.left+c.width-20]),...boxes.flatMap(r=>[r.left-12,r.right+12])]).filter(x=>x>=start.x&&x<=finish.x&&allowed(x));
  const ys=unique([start.y,finish.y,82,height-14,...boxes.flatMap(r=>[r.top-10,r.bottom+10])]);
  const nx=xs.length,index=(x,y)=>y*nx+x,coords=i=>({x:xs[i%nx],y:ys[Math.floor(i/nx)]});
  const first=index(xs.indexOf(start.x),ys.indexOf(start.y)),last=index(xs.indexOf(finish.x),ys.indexOf(finish.y));
  const distance=new Map([[first,0]]),previous=new Map(),open=[first],closed=new Set();
  const heuristic=i=>{const p=coords(i);return Math.abs(p.x-finish.x)+Math.abs(p.y-finish.y);};
  while(open.length){
   let best=0;for(let i=1;i<open.length;i++)if(distance.get(open[i])+heuristic(open[i])<distance.get(open[best])+heuristic(open[best]))best=i;
   const current=open.splice(best,1)[0];if(current===last)break;if(closed.has(current))continue;closed.add(current);
   const x=current%nx,y=Math.floor(current/nx),p=coords(current);
   for(const [dx,dy] of [[1,0],[0,1],[0,-1]]){const xx=x+dx,yy=y+dy;if(xx<0||xx>=nx||yy<0||yy>=ys.length)continue;const next=index(xx,yy),q=coords(next);if(closed.has(next)||!clear(p,q))continue;const cost=distance.get(current)+Math.abs(p.x-q.x)+Math.abs(p.y-q.y)+2;if(cost<(distance.get(next)??Infinity)){distance.set(next,cost);previous.set(next,current);open.push(next);}}
  }
  if(!distance.has(last))throw Error('No stage-local route: '+e.id);
  const route=[];for(let n=last;n!==undefined;n=previous.get(n))route.unshift(coords(n));
  return compactFieldPoints([source,...route,target]);
 };
}
`;
let rest=tail.replace('function bundleFieldRoutes(edges,routes,nodes){','function bundleFieldRoutes(edges,routes,nodes,columns){');
rest=rest.replace('t=n.y-18,b=n.y+18','t=n.y-n.height/2-4,b=n.y+n.height/2+4');
rest=rest.replace("let applied=false;for(const bus of [hi,(lo+hi)/2,lo])", "const phase=columns[group[0].toNode.stage],buses=[hi,(lo+hi)/2,lo].filter(x=>x>=phase.left+16&&x<=phase.left+phase.width-16);let applied=false;for(const bus of buses)");
fs.writeFileSync(p,head+rest);
let html=fs.readFileSync('outputs/paper-atlas/workflow.html','utf8').replace('从论文清单到关联网络','从论文清单到关系与特征').replace('>采集与核对<','>采集与定稿<').replace('信息生命周期表，可横向滚动','采集与定稿图，可横向滚动').replace('①建立清单 → ②定位与核对 → ③确定实验室信息 → ④采集外部与补全记录 → ⑤生成特征。','①建立主页清单 → ②多源检索与一致化 → ③按标识精确采集 → ④采集外部与补全关系 → ⑤生成特征与作者画像。');fs.writeFileSync('outputs/paper-atlas/workflow.html',html);
let js=fs.readFileSync('outputs/paper-atlas/workflow.js','utf8').replace("'[data-flow-node],[data-flow-edge]", "'[data-flow-group],[data-flow-node],[data-flow-edge]").replace('function tipContent(target){','function tipContent(target){\n if(target.dataset.flowGroup)return paragraphs([WORKFLOW_FLOW.rows.find(r=>r.id===target.dataset.flowGroup).description]);');fs.writeFileSync('outputs/paper-atlas/workflow.js',js);
fs.appendFileSync('outputs/paper-atlas/workflow.css','\n/* Semantic groups keep individual fields visible without repeated row headers. */\n.flow-group-label{position:absolute;left:12px;top:16px;width:118px;padding:0;border:0;background:transparent;color:var(--track);font-size:13px;text-align:left;font-weight:600;cursor:pointer;z-index:3}.flow-group-label:hover{text-decoration:underline;text-underline-offset:3px}.flow-node{white-space:pre;line-height:20px}.flow-row:nth-child(even){background:#fcfcfe}.flow-row{border-bottom:1px solid #e7eaf0}\n');
