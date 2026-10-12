const fs=require('fs'),p='outputs/paper-atlas/workflow-layout.js';let s=fs.readFileSync(p,'utf8');const end=s.indexOf('// Source branches');const build=`/* Coordinates and orthogonal routing only; no input semantics live here. */
window.WorkflowLayout={build(data){
 const left=178,columnWidth=166,firstY=130,pitch=96;
 const info=new Map(data.information.map(i=>[i.id,i]));
 const rows=new Map(data.tracks.map((t,i)=>[t.id,i]));
 const offsets={candidates:-22,identity:22,homeTitle:-22,sourceTitle:-22,sourceAbstract:22,title:22,abstract:22,sourceAuthors:-22,authors:22,directions:-22,vector:22,sourcePublication:-22,sourceCounts:22,publication:22,counts:22,sourceKeywords:-22,sourceTopics:22,keywords:-22,topics:22,keywordProfile:-22,directionProfile:22};
 const point=n=>({x:left+columnWidth*(n.stage+.5),y:firstY+rows.get(n.track||info.get(n.info).track)*pitch+(offsets[n.id]||0)});
 const artifacts=new Map(data.artifacts.map(n=>[n.id,n]));
 const width=left+columnWidth*data.stages.length+24,height=firstY+pitch*(data.tracks.length-1)+62;
 const boxes=data.artifacts.map(n=>{const p=point(n);return {id:n.id,left:p.x-70,right:p.x+70,top:p.y-20,bottom:p.y+20};});
 const unique=values=>[...new Set(values)].sort((a,b)=>a-b);
 const clear=(a,b)=>!boxes.some(r=>a.x===b.x?a.x>r.left&&a.x<r.right&&Math.max(a.y,b.y)>r.top&&Math.min(a.y,b.y)<r.bottom:a.y>r.top&&a.y<r.bottom&&Math.max(a.x,b.x)>r.left&&Math.min(a.x,b.x)<r.right);
 // Use column gutters and the gaps above/below nodes, rather than crossing occupied rows.
 const vertices=e=>{
  const a=point(artifacts.get(e.from)),b=point(artifacts.get(e.to)),same=a.x===b.x;
  const source={x:a.x+(same?0:66),y:a.y+(same?16:0)},target={x:b.x-(same?0:66),y:b.y-(same?16:0)};
  if((source.x===target.x||source.y===target.y)&&clear(source,target))return [];
  const start={x:a.x+(same?0:74),y:a.y+(same?22:0)},finish={x:b.x-(same?0:74),y:b.y-(same?22:0)};
  const xs=unique([start.x,finish.x,...Array.from({length:data.stages.length+1},(_,i)=>left+i*columnWidth)]);
  const ys=unique([start.y,finish.y,80,height-20,...data.artifacts.flatMap(n=>{const p=point(n);return [p.y-22,p.y+22];})]);
  const nx=xs.length,index=(x,y)=>y*nx+x,coords=id=>({x:xs[id%nx],y:ys[Math.floor(id/nx)]});
  const first=index(xs.indexOf(start.x),ys.indexOf(start.y)),last=index(xs.indexOf(finish.x),ys.indexOf(finish.y));
  const distance=new Map([[first,0]]),previous=new Map(),open=[first],closed=new Set();
  const heuristic=id=>{const p=coords(id);return Math.abs(p.x-finish.x)+Math.abs(p.y-finish.y);};
  while(open.length){
   let best=0;for(let i=1;i<open.length;i++)if(distance.get(open[i])+heuristic(open[i])<distance.get(open[best])+heuristic(open[best]))best=i;
   const current=open.splice(best,1)[0];if(current===last)break;if(closed.has(current))continue;closed.add(current);
   const x=current%nx,y=Math.floor(current/nx),p=coords(current);
   for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
    const xx=x+dx,yy=y+dy;if(xx<0||xx>=nx||yy<0||yy>=ys.length)continue;
    const next=index(xx,yy),q=coords(next);if(closed.has(next)||!clear(p,q))continue;
    const cost=distance.get(current)+Math.abs(p.x-q.x)+Math.abs(p.y-q.y);
    if(cost<(distance.get(next)??Infinity)){distance.set(next,cost);previous.set(next,current);open.push(next);}
   }
  }
  if(!distance.has(last))throw new Error('No clear dependency route: '+e.id);
  const route=[];for(let n=last;n!==undefined;n=previous.get(n))route.unshift(coords(n));
  const path=[source,...route,target],simple=[];
  for(const p of path){if(simple.length&&simple[simple.length-1].x===p.x&&simple[simple.length-1].y===p.y)continue;while(simple.length>1){const u=simple[simple.length-2],v=simple[simple.length-1];if(u.x===v.x&&v.x===p.x||u.y===v.y&&v.y===p.y)simple.pop();else break;}simple.push(p);}
  return simple.slice(1,-1);
 };
 return {left,columnWidth,firstY,pitch,point,vertices,width,height};
}};

`;
fs.writeFileSync(p,build+s.slice(end),'utf8');
global.window=global;require('../outputs/paper-atlas/workflow-data.js');require('../'+p);const g=WorkflowLayout.build(WORKFLOW_MAP);let bends=0;for(const e of WORKFLOW_MAP.dependencies)bends+=g.vertices(e).length;console.log(JSON.stringify({edges:WORKFLOW_MAP.dependencies.length,bends}));
