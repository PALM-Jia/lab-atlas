/* Geometry only: horizontal stage crossings; all turns stay inside endpoint stages. */
window.WorkflowLayout={build(data){
 const left=178,firstY=130,pitch=104,padding=48,gap=48,portRun=24,cornerRadius=8;
 const textWidth=(text,size)=>[...text].reduce((sum,c)=>sum+(c.charCodeAt(0)<128?size*.6:size),0);
 const nodeWidth=n=>Math.max(96,Math.ceil(textWidth(n.label,12)+24));
 const lifeWidth=label=>Math.max(74,Math.ceil(textWidth(label,11)+28));
 const artifacts=new Map(data.artifacts.map(n=>[n.id,n])),ranks=new Map(),visiting=new Set();
 const rank=n=>{
  if(ranks.has(n.id))return ranks.get(n.id);
  if(visiting.has(n.id))throw new Error('Cyclic stage dependency: '+n.id);
  visiting.add(n.id);
  const parents=data.dependencies.filter(e=>e.to===n.id).map(e=>artifacts.get(e.from));
  if(parents.some(p=>p.stage>n.stage))throw new Error('Dependency crosses an earlier stage: '+n.id);
  const value=Math.max(0,...parents.filter(p=>p.stage===n.stage).map(p=>rank(p)+1));
  visiting.delete(n.id);ranks.set(n.id,value);return value;
 };
 data.artifacts.forEach(rank);
 const subcolumns=data.stages.map((_,stage)=>{
  const nodes=data.artifacts.filter(n=>n.stage===stage),count=Math.max(0,...nodes.map(rank))+1;
  return Array.from({length:count},(_,r)=>Math.max(96,...nodes.filter(n=>rank(n)===r).map(nodeWidth)));
 });
 const groupWidth=widths=>widths.reduce((sum,w)=>sum+w,0)+gap*(widths.length-1);
 const columnWidths=subcolumns.map((widths,i)=>Math.max(208,groupWidth(widths)+padding*2,Math.ceil(textWidth(data.stages[i].label,14)+32)));
 for(const info of data.information)for(const lane of info.lifecycles||[info]){
  const endWidth=lane.end?lifeWidth(lane.end[0]):132,local=(lane.branches||[]).filter(b=>b.stage===lane.settle);
  columnWidths[lane.settle]=Math.max(columnWidths[lane.settle],local.length?Math.max(...local.map(b=>lifeWidth(b.label)))+endWidth+56:endWidth+24);
 }
 let cursor=left;
 const columns=columnWidths.map(width=>{const col={left:cursor,width,center:cursor+width/2};cursor+=width;return col;});
 const info=new Map(data.information.map(i=>[i.id,i])),rows=new Map(data.tracks.map((t,i)=>[t.id,i]));
 const offsets={candidates:-22,identity:22,homeTitle:22,title:22,abstract:22,keywords:-22,topics:22,publication:-22,homePublication:-22,counts:22,references:-22,citingRecords:22,citationMap:-22,citingMap:22,directions:-22,vector:22,externalDirections:-22,externalVector:22,keywordProfile:-22,directionProfile:22};
 const point=n=>{
  const widths=subcolumns[n.stage],r=ranks.get(n.id),col=columns[n.stage];
  const x=col.left+(col.width-groupWidth(widths))/2+widths.slice(0,r).reduce((sum,w)=>sum+w+gap,0)+widths[r]/2;
  return {x,y:firstY+rows.get(n.track||info.get(n.info).track)*pitch+(offsets[n.id]||0)};
 };
 const width=cursor+12,height=firstY+pitch*(data.tracks.length-1)+70;
 const boxes=data.artifacts.map(n=>{const p=point(n);return {id:n.id,left:p.x-nodeWidth(n)/2-4,right:p.x+nodeWidth(n)/2+4,top:p.y-20,bottom:p.y+20};});
 const unique=values=>[...new Set(values)].sort((a,b)=>a-b);
 const clear=(a,b)=>!boxes.some(r=>a.x===b.x?a.x>r.left&&a.x<r.right&&Math.max(a.y,b.y)>r.top&&Math.min(a.y,b.y)<r.bottom:a.y>r.top&&a.y<r.bottom&&Math.max(a.x,b.x)>r.left&&Math.min(a.x,b.x)<r.right);
 const routes=new Map();
 const vertices=e=>{
  if(routes.has(e.id))return routes.get(e.id);
  const from=artifacts.get(e.from),to=artifacts.get(e.to),a=point(from),b=point(to),source={x:a.x+nodeWidth(from)/2,y:a.y},target={x:b.x-nodeWidth(to)/2,y:b.y};
  if(source.x>=target.x)throw new Error('Dependency must advance right: '+e.id);
  if(source.y===target.y&&clear(source,target)){routes.set(e.id,[]);return [];}
  const start={x:source.x+portRun,y:source.y},finish={x:target.x-portRun,y:target.y};
  // The extra 24 px at boundaries also contains the rounded connector's 8 px radius.
  const turnAllowed=x=>[from.stage,to.stage].some(stage=>x>=columns[stage].left+24&&x<=columns[stage].left+columns[stage].width-24);
  const xs=unique([start.x,finish.x,...columns.flatMap(c=>[c.left+24,c.left+c.width-24]),...boxes.flatMap(r=>[r.left-16,r.right+16])]).filter(x=>x>=start.x&&x<=finish.x);
  const ys=unique([start.y,finish.y,82,height-24,...data.artifacts.flatMap(n=>{const p=point(n);return [p.y-28,p.y+28];})]);
  const nx=xs.length,index=(x,y)=>y*nx+x,coords=id=>({x:xs[id%nx],y:ys[Math.floor(id/nx)]});
  const first=index(xs.indexOf(start.x),ys.indexOf(start.y)),last=index(xs.indexOf(finish.x),ys.indexOf(finish.y));
  const distance=new Map([[first,0]]),previous=new Map(),open=[first],closed=new Set();
  const heuristic=id=>{const p=coords(id);return Math.abs(p.x-finish.x)+Math.abs(p.y-finish.y);};
  while(open.length){
   let best=0;for(let i=1;i<open.length;i++)if(distance.get(open[i])+heuristic(open[i])<distance.get(open[best])+heuristic(open[best]))best=i;
   const current=open.splice(best,1)[0];if(current===last)break;if(closed.has(current))continue;closed.add(current);
   const x=current%nx,y=Math.floor(current/nx),p=coords(current);
   for(const [dx,dy] of [[1,0],[0,1],[0,-1]]){
    if(dy&&!turnAllowed(p.x))continue;
    const xx=x+dx,yy=y+dy;if(xx<0||xx>=nx||yy<0||yy>=ys.length)continue;
    const next=index(xx,yy),q=coords(next);if(closed.has(next)||!clear(p,q))continue;
    const cost=distance.get(current)+Math.abs(p.x-q.x)+Math.abs(p.y-q.y)+(dy?2:0);
    if(cost<(distance.get(next)??Infinity)){distance.set(next,cost);previous.set(next,current);open.push(next);}
   }
  }
  if(!distance.has(last))throw new Error('No clear endpoint-stage route: '+e.id);
  const route=[];for(let n=last;n!==undefined;n=previous.get(n))route.unshift(coords(n));
  const path=[source,...route,target],simple=[];
  for(const p of path){if(simple.length&&simple[simple.length-1].x===p.x&&simple[simple.length-1].y===p.y)continue;while(simple.length>1){const u=simple[simple.length-2],v=simple[simple.length-1];if(u.x===v.x&&v.x===p.x||u.y===v.y&&v.y===p.y)simple.pop();else break;}simple.push(p);}
  const result=simple.slice(1,-1);routes.set(e.id,result);return result;
 };
 return {left,columns,firstY,pitch,point,nodeWidth,lifeWidth,vertices,width,height,portRun,cornerRadius};
}};

// Source branches are independent roots; every path stops at its own verification result.
window.WorkflowLayout.lifecycle=function(info,geometry,guide){
 const lanes=info.lifecycles||[info];let height=0;
 const width=geometry.lifeWidth;
 const separateInTime=lanes.length===2&&lanes[0].settle<Math.min(...(lanes[1].branches||[]).map(b=>b.stage));
 const result=lanes.map((lane,k)=>{
  const offset=separateInTime?0:height,branches=lane.branches||[],end=lane.end||guide.end;
  const sameStage=branches.some(b=>b.stage===lane.settle);
  const endWidth=width(end[0]),endX=sameStage?geometry.columns[lane.settle].left+geometry.columns[lane.settle].width-12-endWidth/2:geometry.columns[lane.settle].center,endY=offset+23;
  const nodes=branches.map((b,n)=>{
   const lower=b.stage===lane.settle||n>0;
   const y=offset+23+(lower?36*Math.max(1,n):0);
   const w=width(b.label),x=b.stage===lane.settle?geometry.columns[b.stage].left+12+w/2:geometry.columns[b.stage].center;
   const start=x+w/2,finish=endX-endWidth/2;
   let path;
   const bend=Math.min(32,Math.max(8,(finish-start)/3));
   path=y===endY?`M ${start} ${y} H ${finish}`:`M ${start} ${y} H ${finish-bend*2} C ${finish-bend} ${y} ${finish-bend} ${endY} ${finish} ${endY}`;
   return {...b,index:n,x,y,width:w,path};
  });
  const laneHeight=Math.max(46,...nodes.map(n=>n.y-offset+23));
  height=Math.max(height,offset+laneHeight);
  return {index:k,scope:lane.scope||info.name,settle:lane.settle,end,endX,endY,endWidth,nodes,top:offset,height:laneHeight};
 });
 return {lanes:result,height};
};
