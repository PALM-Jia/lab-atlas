const fs=require('fs'),p='outputs/paper-atlas/workflow-layout.js';let s=fs.readFileSync(p,'utf8');const marker=s.indexOf('// Source branches'),tail=s.slice(marker);let head=s.slice(0,marker);
const needle=' return {left,columns,firstY,pitch,point,nodeWidth,lifeWidth,vertices,width,height};';
const replacement=` // Equal relationship types may share a clear vertical trunk, while retaining separate endpoints.
 const buses=new Map(),groups=new Map();
 for(const e of data.dependencies){
  const keys=['from|'+e.from+'|'+e.type+'|'+artifacts.get(e.to).stage,'to|'+e.to+'|'+e.type+'|'+artifacts.get(e.from).stage];
  for(const key of keys){if(!groups.has(key))groups.set(key,[]);groups.get(key).push(e);}
 }
 const busPath=(e,x)=>{
  const a=artifacts.get(e.from),b=artifacts.get(e.to),p=point(a),q=point(b);
  const start={x:p.x+nodeWidth(a)/2+10,y:p.y},finish={x:q.x-nodeWidth(b)/2-10,y:q.y};
  if(x<start.x||x>finish.x||start.y===finish.y)return null;
  const route=[start,{x,y:start.y},{x,y:finish.y},finish];
  if(route.slice(1).some((p,i)=>!clear(route[i],p)))return null;
  return [{x,y:start.y},{x,y:finish.y}];
 };
 const candidates=[];
 for(const [key,edges] of groups){
  if(edges.length<2)continue;
  const xs=unique([...columns.map(c=>c.left),...boxes.flatMap(r=>[r.left-6,r.right+6])]);
  let best=null;
  for(const x of xs){
   const routes=edges.map(e=>({edge:e,path:busPath(e,x)})).filter(r=>r.path);
   if(routes.length<2)continue;
   const length=routes.reduce((sum,r)=>sum+Math.abs(r.path[1].y-r.path[0].y),0);
   if(!best||routes.length>best.routes.length||routes.length===best.routes.length&&(key.startsWith('from|')?x<best.x:x>best.x))best={x,routes,length};
  }
  if(best)candidates.push(best);
 }
 candidates.sort((a,b)=>b.routes.length-a.routes.length||a.length-b.length);
 for(const candidate of candidates){
  const available=candidate.routes.filter(r=>!buses.has(r.edge.id));
  if(available.length>=2)for(const r of available)buses.set(r.edge.id,r.path);
 }
 return {left,columns,firstY,pitch,point,nodeWidth,lifeWidth,vertices:e=>buses.get(e.id)||vertices(e),width,height};`;
if(!head.includes(needle))throw new Error('Return block missing');head=head.replace(needle,replacement);fs.writeFileSync(p,head+tail,'utf8');
const js='outputs/paper-atlas/workflow.js';let source=fs.readFileSync(js,'utf8');if((source.match(/radius:6/g)||[]).length!==1)throw new Error('Unexpected radius count');fs.writeFileSync(js,source.replace('radius:6','radius:9'),'utf8');
