const fs=require('fs'),vm=require('vm'),assert=require('assert'),{performance}=require('perf_hooks');
const source=fs.readFileSync('outputs/paper-atlas/dynamic-layout.js','utf8');
function fixture(coords, links, options={}){
  let next=1,time=0,writes=0;const raf=new Map(),handlers={};
  const nodes=coords.map((p,i)=>({id:()=>''+i,p:{...p},width:()=>12,locked:()=>false,data:key=>key==='lab'?p.lab!==false:undefined,
    position(value){if(value){assert(Number.isFinite(value.x)&&Number.isFinite(value.y));this.p={...value};writes++;}return {...this.p};}}));
  const edges=links.map(([a,b,score,kind='semantic'])=>({data:key=>({source:''+a,target:''+b,score,kind})[key]}));
  const cy={nodes:()=>({toArray:()=>nodes}),edges:()=>({toArray:()=>edges}),batch:fn=>fn(),
    on:(event,selector,fn)=>handlers[event]=fn,
    fit(){throw Error('viewport fit');},zoom(){throw Error('viewport zoom');},pan(){throw Error('viewport pan');}};
  const context={window:{},requestAnimationFrame:fn=>{const id=next++;raf.set(id,fn);return id;},cancelAnimationFrame:id=>raf.delete(id)};
  vm.compileFunction(source,['window','requestAnimationFrame','cancelAnimationFrame','performance'])(context.window,context.requestAnimationFrame,context.cancelAnimationFrame,options.clock||performance);const layout=context.window.createDynamicLayout({cy});
  const frames=(count=400)=>{for(let i=0;i<count&&raf.size;i++){const [id,fn]=raf.entries().next().value;raf.delete(id);time+=16.667;fn(time);}};
  return {nodes,layout,frames,raf,pause:ms=>{time+=ms;},event:(type,i)=>handlers[type]({target:nodes[i]}),writes:()=>writes};
}
const distance=(a,b)=>Math.hypot(a.p.x-b.p.x,a.p.y-b.p.y);
const f=fixture([{x:-350,y:-150},{x:-50,y:-150},{x:50,y:150},{x:350,y:150}],[[0,1,.99],[2,3,.801]]);
f.layout.start({kind:'semantic'});f.frames();
const strong=distance(f.nodes[0],f.nodes[1]),weak=distance(f.nodes[2],f.nodes[3]);
assert(strong+30<weak,`strong ${strong}, weak ${weak}`);assert.equal(f.raf.size,0,'converges within finite run');
const clickWrites=f.writes();f.event('grab',0);f.event('free',0);assert.equal(f.raf.size,0,'click does not restart a settled layout');f.frames();assert.equal(f.writes(),clickWrites);
f.layout.start();f.frames(10);const written=f.writes();f.layout.stop();f.frames();assert.equal(f.writes(),written);
f.layout.start();f.layout.start();assert.equal(f.raf.size,1,'new run cancels old');
f.event('grab',0);f.nodes[0].p={x:800,y:250};f.event('drag',0);f.frames(10);assert.deepEqual(f.nodes[0].p,{x:800,y:250});
f.event('free',0);f.frames();assert.deepEqual(f.nodes[0].p,{x:800,y:250},'manual placement persists');
f.event('grab',1);f.nodes[1].p={x:950,y:300};f.event('drag',1);assert.equal(f.raf.size,1,'actual drag restarts settled layout');f.event('free',1);f.frames();assert.deepEqual(f.nodes[1].p,{x:950,y:300});
const empty=fixture([],[]);empty.layout.start();assert.equal(empty.raf.size,0);
const overlap=fixture(Array.from({length:20},()=>({x:0,y:0})),[]);overlap.layout.start();overlap.frames();
assert(overlap.nodes.some(n=>Math.hypot(n.p.x,n.p.y)>10),'isolated pile separates');
const hidden=fixture([{x:0,y:0},{x:500,y:0}],[[0,1,1]]);hidden.layout.start();hidden.frames(1);
const before={...hidden.nodes[0].p};hidden.pause(60000);hidden.frames(1);
assert(Math.hypot(hidden.nodes[0].p.x-before.x,hidden.nodes[0].p.y-before.y)<=12.01,'background pause does not produce a giant step');
const count=1673,coords=Array.from({length:count},(_,i)=>({x:(i%42)*30,y:Math.floor(i/42)*30}));
const links=Array.from({length:12647},(_,i)=>[i%count,(i*17+13)%count,(i%99)/100,'citation']);
const large=fixture(coords,links);const started=performance.now();large.layout.start();large.frames(60);
const duration=performance.now()-started;const updates=large.writes()/count;assert(updates<=16,`large graph got ${updates} updates in one second`);assert(updates>=8,`too few updates: ${updates}`);large.layout.stop();assert(duration<4000,`60 frames took ${duration}ms`);
console.log(`Passed: strong edges shorten (${strong.toFixed(1)} vs ${weak.toFixed(1)}); finite convergence; stop/restart cancellation; viewport untouched; grab/free placement; empty/isolated nodes; 1673 nodes/12647 edges, 60 display frames / ${updates} layout updates ${duration.toFixed(0)}ms.`);



const medium=fixture(coords.slice(0,450),[]);medium.layout.start();medium.frames(60);assert(medium.writes()/450<=31,'medium graph capped at 30 Hz');medium.layout.stop();
let simulatedClock=0;
const slow=fixture(coords,[],{clock:{now:()=>simulatedClock+=25}});slow.layout.start();slow.frames(60);
assert(slow.writes()/count<=11,'expensive updates back off to 10 Hz');assert(slow.writes()/count>=8,'slow graph still updates');slow.layout.stop();
const edgeHeavy=fixture(coords.slice(0,20),links.map(([a,b,s,k])=>[a%20,b%20,s,k]));edgeHeavy.layout.start();edgeHeavy.frames(60);assert(edgeHeavy.writes()/20<=16,'edge count also selects large graph tier');edgeHeavy.layout.stop();
console.log('Passed: medium 30 Hz, edge-heavy 15 Hz, simulated slow hardware 10 Hz.');

const baseline=fixture([{x:-150,y:0},{x:150,y:0}],[[0,1,1]]);
const weighted=fixture([{x:-150,y:0,lab:true},{x:150,y:0,lab:false}],[[0,1,1]]);
baseline.layout.start();weighted.layout.start();baseline.frames(1);weighted.frames(1);
const labRatio=(weighted.nodes[0].p.x+150)/(baseline.nodes[0].p.x+150);
assert(labRatio>.18&&labRatio<.23,`external influence ratio ${labRatio}`);
assert(150-weighted.nodes[1].p.x>=(150-baseline.nodes[1].p.x)*.9,'external still follows lab');
baseline.layout.stop();weighted.layout.stop();
const repelBase=fixture([{x:-20,y:0},{x:20,y:0}],[]);
const repelWeighted=fixture([{x:-20,y:0},{x:20,y:0,lab:false}],[]);
repelBase.layout.start();repelWeighted.layout.start();repelBase.frames(1);repelWeighted.frames(1);
assert(Math.abs(repelWeighted.nodes[0].p.x+20)<Math.abs(repelBase.nodes[0].p.x+20)*.20,'external repulsion further reduced beyond its 0.2 influence weight');
repelBase.layout.stop();repelWeighted.layout.stop();
console.log(`Passed: external weight 0.2, lab displacement ratio ${labRatio.toFixed(3)}, reduced repulsion and preserved external response.`);
