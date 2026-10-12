const fs=require('fs'),p='outputs/paper-atlas/workflow-layout.js';let s=fs.readFileSync(p,'utf8');const marker=s.indexOf('// Source branches'),tail=s.slice(marker);let head=s.slice(0,marker);
head=head.replace(" const columnWidths=data.stages.map((_,stage)=>Math.max(144,...data.artifacts.filter(a=>a.stage===stage).map(a=>nodeWidth(a)+24)));",` const artifacts=new Map(data.artifacts.map(n=>[n.id,n]));
 const ranks=new Map(),visiting=new Set();
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
 const groupWidth=widths=>widths.reduce((sum,w)=>sum+w,0)+32*(widths.length-1);
 const columnWidths=subcolumns.map(widths=>Math.max(144,groupWidth(widths)+24));`);
head=head.replace(" const point=n=>({x:columns[n.stage].center,y:firstY+rows.get(n.track||info.get(n.info).track)*pitch+(offsets[n.id]||0)});\r\n const artifacts=new Map(data.artifacts.map(n=>[n.id,n]));",` const point=n=>{
  const widths=subcolumns[n.stage],r=ranks.get(n.id),col=columns[n.stage];
  const x=col.left+(col.width-groupWidth(widths))/2+widths.slice(0,r).reduce((sum,w)=>sum+w+32,0)+widths[r]/2;
  return {x,y:firstY+rows.get(n.track||info.get(n.info).track)*pitch+(offsets[n.id]||0)};
 };`);
if((head.match(/const artifacts=/g)||[]).length!==1)throw new Error('Point block replacement failed.');
head=head.replace("  if((source.x===target.x||source.y===target.y)&&clear(source,target))return [];", "  if(source.x>=target.x)throw new Error('Dependency must advance right: '+e.id);\n  if(source.y===target.y&&clear(source,target))return [];");
head=head.replace("  const xs=unique([start.x,finish.x,...columns.map(c=>c.left),cursor]);", "  const xs=unique([start.x,finish.x,...columns.map(c=>c.left),...boxes.flatMap(r=>[r.left-6,r.right+6]),cursor]).filter(x=>x>=start.x&&x<=finish.x);");
head=head.replace("[[1,0],[0,1],[-1,0],[0,-1]]", "[[1,0],[0,1],[0,-1]]");
fs.writeFileSync(p,head+tail,'utf8');
const q='work/check_dag_routes.cjs';let test=fs.readFileSync(q,'utf8');
test=test.replace("const collisions=[],portErrors=[],diagonalSegments=[],started=Date.now();", "const collisions=[],portErrors=[],diagonalSegments=[],backwardSegments=[],nonAdvancingEdges=[],started=Date.now();");
test=test.replace(" const points=path.filter", " if(path[0].x>=path[path.length-1].x)nonAdvancingEdges.push(edge.id);\n const points=path.filter");
test=test.replace("  const p=points[i-1],q=points[i];", "  const p=points[i-1],q=points[i];\n  if(q.x<p.x)backwardSegments.push({edge:edge.id,p,q});");
test=test.replace("collisions,portErrors,diagonalSegments,elapsedMs", "collisions,portErrors,diagonalSegments,backwardSegments,nonAdvancingEdges,elapsedMs");
test+="\nassert.deepEqual(nonAdvancingEdges,[],'Every source right port must be left of its target left port.');\nassert.deepEqual(backwardSegments,[],'Dependency routes must never move left.');\n";
fs.writeFileSync(q,test,'utf8');
