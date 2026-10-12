const assert=require('node:assert/strict');
global.window=global;
require('../outputs/paper-atlas/workflow-data.js');
require('../outputs/paper-atlas/workflow-layout.js');
const data=WORKFLOW_MAP,geometry=WorkflowLayout.build(data),nodes=new Map(data.artifacts.map(n=>[n.id,n]));
const collisions=[],portErrors=[],diagonalSegments=[],backwardSegments=[],nonAdvancingEdges=[],started=Date.now();
assert.equal(typeof geometry.nodeWidth,'function','Geometry must expose per-node widths.');
for(const edge of data.dependencies){
 const source=nodes.get(edge.from),target=nodes.get(edge.to),a=geometry.point(source),b=geometry.point(target);
 const path=[{x:a.x+geometry.nodeWidth(source)/2,y:a.y},...geometry.vertices(edge),{x:b.x-geometry.nodeWidth(target)/2,y:b.y}];
 if(path[0].x>=path[path.length-1].x)nonAdvancingEdges.push(edge.id);
 const points=path.filter((p,i)=>i===0||p.x!==path[i-1].x||p.y!==path[i-1].y);
 const first=points[0],next=points[1],last=points[points.length-1],previous=points[points.length-2];
 if(!next||next.y!==first.y||next.x<=first.x)portErrors.push({edge:edge.id,port:'source',first,next});
 if(!previous||previous.y!==last.y||previous.x>=last.x)portErrors.push({edge:edge.id,port:'target',previous,last});
 for(let i=1;i<points.length;i++){
  const p=points[i-1],q=points[i];
  if(q.x<p.x)backwardSegments.push({edge:edge.id,p,q});
  if(p.x!==q.x&&p.y!==q.y){diagonalSegments.push({edge:edge.id,p,q});continue;}
  for(const node of data.artifacts){
   if(node.id===edge.from||node.id===edge.to)continue;
   const r=geometry.point(node),half=geometry.nodeWidth(node)/2;
   const intersects=p.x===q.x
    ?p.x>r.x-half&&p.x<r.x+half&&Math.max(p.y,q.y)>r.y-16&&Math.min(p.y,q.y)<r.y+16
    :p.y>r.y-16&&p.y<r.y+16&&Math.max(p.x,q.x)>r.x-half&&Math.min(p.x,q.x)<r.x+half;
   if(intersects)collisions.push({edge:edge.id,node:node.id,segment:i});
  }
 }
}
console.log(JSON.stringify({edges:data.dependencies.length,collisions,portErrors,diagonalSegments,backwardSegments,nonAdvancingEdges,elapsedMs:Date.now()-started},null,2));
assert.deepEqual(diagonalSegments,[],'Dependency segments must be orthogonal.');
assert.deepEqual(portErrors,[],'All dependency edges must leave right and enter left horizontally.');
assert.deepEqual(collisions,[],'Dependency paths must avoid every unrelated node.');

assert.deepEqual(nonAdvancingEdges,[],'Every source right port must be left of its target left port.');
assert.deepEqual(backwardSegments,[],'Dependency routes must never move left.');
