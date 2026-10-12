const fs=require('fs'),assert=require('assert'),build=require('../outputs/paper-atlas/author-relations.js');
const authors=['a','b','c'].map(id=>({id,name:id,papers:[id],paperWeights:{[id]:1}})),papers=authors.map(a=>({id:a.id,tags:[]}));
const scores=[['a','b',-.2],['a','c',0],['b','c',.9]];
const edges=build({authors,papers,mode:'semantic',paperEdges:scores.map(([source,target,score])=>({source,target,score,kind:'semantic'}))});
assert.equal(edges.length,3);assert.equal(edges.stats.threshold,null);assert.deepEqual(edges.map(e=>e.score),[-.2,0,.9]);
assert.equal(build({authors:[{id:'x',papers:['a']},{id:'y',papers:['a']}],papers,mode:'semantic',paperEdges:[]}).length,0);
let src=fs.readFileSync('work/check_dynamic_layout.cjs','utf8').split('const distance=')[0];
src=src.replace("fs.readFileSync('outputs/paper-atlas/dynamic-layout.js','utf8')", "fs.readFileSync('outputs/paper-atlas/dynamic-layout.js','utf8').replace('return {start,stop};','return {start,stop,inspect:()=>run};')");
const fixture=new Function('require',src+';return fixture;')(require);
for(const n of [31,65]){
 const coords=Array.from({length:n},(_,i)=>({x:250*Math.cos(i/n*2*Math.PI),y:250*Math.sin(i/n*2*Math.PI)})),links=[];
 for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)links.push([i,j,.8+.2*((i+j)%13)/12,'author_semantic']);
 const f=fixture(coords,links);f.layout.start();const r=f.layout.inspect();
 for(const p of r.points){const sum=r.edges.filter(e=>e.a===p||e.b===p).reduce((s,e)=>s+e.pull,0);assert(sum<=.075+1e-12);}
 f.frames(600);assert(f.nodes.every(p=>Number.isFinite(p.p.x)&&Number.isFinite(p.p.y)));
 const extent=Math.max(...f.nodes.map(p=>Math.hypot(p.p.x,p.p.y)));assert(extent>40,'layout must not collapse to one point');f.layout.stop();console.log(n+' authors: all edges, bounded attraction, finite layout; extent '+extent.toFixed(1));
}
console.log('PASS: zero/negative scores retained; unavailable comparisons omitted; total attraction bounded');
