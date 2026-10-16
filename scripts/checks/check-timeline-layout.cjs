'use strict';
const assert=require('node:assert/strict');
const {buildTimelinePositions,projectPoint,bezierFor,cubicPoint,ellipseHit,curveHit,PITCH,createTimeline3D,temporalViewportMetrics}=require('../../outputs/paper-atlas/timeline-3d.js');
const helper=require('../../outputs/paper-atlas/timeline-history.js');
const papers=[{id:'old',year:2000,x:0,y:0,lab:true,displayColor:'#aabbcc',citations:999999,displaySize:999},{id:'new',year:2002,x:1,y:1,lab:true,displayColor:'#aabbcc'},{id:'unknown',year:null,x:2,y:2,lab:true}];
const history={papers:{old:{status:'partial',scope:'database_citing_list',annual:[{year:2001,count:2},{year:2003,count:3}]}}};
const layout=buildTimelinePositions(papers,{helper,history,yearFrom:2000,yearTo:2003});
const reused=buildTimelinePositions(papers,{annual:layout.annual,helper:{buildAnnualSlices(){throw new Error('cached annual slices must not be rebuilt');}},yearFrom:2000,yearTo:2003});
assert.deepEqual(reused.positions.map(p=>({id:p.id,citation:p.citation})),layout.positions.map(p=>({id:p.id,citation:p.citation})));
const cachedSubset=buildTimelinePositions([papers[0]],{annual:layout.annual}),freshSubset=buildTimelinePositions([papers[0]],{helper,history,yearFrom:2000,yearTo:2003});
assert.deepEqual(cachedSubset.planes,freshSubset.planes,'cached slices exclude removed unconnected nodes from plane expansion');
assert.deepEqual(cachedSubset.positions.map(p=>({id:p.id,x:p.x,y:p.y,citation:p.citation})),freshSubset.positions.map(p=>({id:p.id,x:p.x,y:p.y,citation:p.citation})));
assert.equal(layout.tracks.get('old').length,4);
assert.equal(layout.tracks.get('new').length,2);
assert.equal(layout.positions.filter(p=>p.unknown).length,0);
assert.deepEqual(layout.tracks.get('old').map(p=>p.citation.count),[0,2,2,5]);
assert(layout.planes.at(-1).z>layout.planes[0].z);
assert(layout.planes.at(-1).radius>layout.planes[0].radius);
const camera={yaw:.7,pitch:PITCH,zoom:2};
const a=projectPoint({x:2,y:4,z:0},camera,800,600),b=projectPoint({x:2,y:4,z:900},camera,800,600);
assert.equal(a.scale,b.scale);assert.equal(a.x,b.x);assert(b.y<a.y);
assert(b.depth<a.depth,'higher year plane is closer to the elevated camera and drawn later');
const d=projectPoint({x:2,y:4,z:0},{...camera,pitch:70*Math.PI/180,distance:2},800,600);
assert.equal(a.x,d.x);assert.equal(a.scale,d.scale);assert.notEqual(a.y,d.y,'pitch changes the plane inclination');
const twice=projectPoint({x:2,y:4,z:0},{...camera,zoom:4},800,600);
assert(Math.abs((twice.x-400)-2*(a.x-400))<1e-9);assert(Math.abs((twice.y-300)-2*(a.y-300))<1e-9);
const stretched=projectPoint({x:2,y:4,z:900},{...camera,timeScale:2},800,600);
assert.equal(stretched.x,b.x);assert.equal(stretched.scale,b.scale);assert(Math.abs((stretched.y-a.y)-2*(b.y-a.y))<1e-9,'timeScale stretches only the temporal axis');
for(let i=1;i<layout.limbs.length;i++){const left=layout.limbs[i-1],right=layout.limbs[i];if(left.paperId!==right.paperId)continue;for(const axis of ['x','y','z'])assert(Math.abs(3*(left.b[axis]-left.c2[axis])-3*(right.c1[axis]-right.a[axis]))<1e-8);}
assert(ellipseHit({x:10,y:0},{x:0,y:0,rx:12,ry:6}));assert(!ellipseHit({x:0,y:9},{x:0,y:0,rx:12,ry:6}));
const curve=bezierFor({x:0,y:0,z:0},{x:20,y:30,z:40},{x:0,y:0},{x:0,y:0});
assert.deepEqual(cubicPoint(curve,0),curve.a);assert.deepEqual(cubicPoint(curve,1),curve.b);
const samples=Array.from({length:17},(_,i)=>cubicPoint(curve,i/16));assert(curveHit(cubicPoint(curve,.5),samples,1));assert(!curveHit({x:100,y:100},samples,1));
// Canvas mock checks annual data, pitch, visible-window fitting and interactions.
global.window={ATLAS_TIMELINE_HISTORY:helper,devicePixelRatio:1};global.ResizeObserver=class{observe(){}disconnect(){}};global.requestAnimationFrame=()=>1;global.cancelAnimationFrame=()=>{};
let canvasHeight=700;
const ctx=new Proxy({},{get:()=>()=>{}}),listeners={},selectedNodes=[],hoveredNodes=[];
const canvas={getContext:()=>ctx,getBoundingClientRect:()=>({width:1000,height:canvasHeight,left:0,top:0}),addEventListener:(k,v)=>listeners[k]=v,removeEventListener(){},style:{}};
const view=createTimeline3D({canvas,onSelectNode:(id,context)=>selectedNodes.push({id,context}),onHover:(paper,pos,context)=>{if(paper)hoveredNodes.push({id:paper.id,context});}});
const input={papers,edges:[{id:'link',source:'old',target:'new',kind:'semantic',score:1}],history,yearFrom:2000,yearTo:2003};
view.setData({...input,reset:true});view.setActive(true);
let state=view.inspect();
assert.equal(state.projection,'orthographic');
assert(state.windowCount>=1&&state.windowCount<=4,'capacity is bounded only by the four-year supplied scope');
assert.equal(state.topYear,2003);
assert.deepEqual(state.visibleYearBounds,[Math.max(2000,2003-state.windowCount+1),2003]);
function assertVisibleFit(s){
  const dated=s.positions.filter(p=>p.year!==null);
  assert(dated.length);
  assert(dated.every(p=>Number.isFinite(p.depth)),'inspection exposes true projected depth');
  for(let i=1;i<dated.length;i++)assert(dated[i-1].year<dated[i].year||(dated[i-1].year===dated[i].year&&dated[i-1].depth+1e-9>=dated[i].depth),'visible scene follows annual layers with depth order inside each plane');
  assert(dated.every(p=>p.year>=s.visibleYearBounds[0]&&p.year<=s.visibleYearBounds[1]),'hidden-year nodes must not enter the projection or hit index');
  assert(s.planes.every(p=>p.year>=s.visibleYearBounds[0]&&p.year<=s.visibleYearBounds[1]));
  assert(dated.every(p=>p.x-p.rx>0&&p.x+p.rx<1000&&p.y-p.ry>0&&p.y+p.ry<canvasHeight),'fit uses the current window');
  for(const p of dated)assert(Math.abs(p.ry/p.rx-Math.sin(s.camera.pitch))<1e-9,'ellipse inclination follows actual camera pitch');
  for(const curve of s.curves)for(const endpoint of [curve.a,curve.b])if(endpoint.node&&endpoint.node.year!==null)assert(endpoint.node.year>=s.visibleYearBounds[0]&&endpoint.node.year<=s.visibleYearBounds[1],'curve requires both endpoints in the window');
}
assertVisibleFit(state);
const hiddenYearPosition=state.positions.find(p=>p.paperId==='old'&&p.year===2003);
const node0=state.positions.find(p=>p.paperId==='old'&&p.year===2002);assert(node0.rx<=52,'annual counts determine bounded radius, not current citation totals');
assert.equal(node0.citations,2);
assert.deepEqual(state.annualEdges[0].edgeIds,[]);assert.deepEqual(state.annualEdges[2].edgeIds,['link']);
const pitchBefore=state.camera.pitch;view.rotate(.4);state=view.inspect();assert.equal(state.camera.yaw,.4);assert.equal(state.camera.pitch,pitchBefore);
const pointer=(x,y)=>({clientX:x,clientY:y,pointerId:1,button:0,shiftKey:false});
listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(470,350));listeners.pointerup(pointer(470,350));state=view.inspect();assert.notEqual(state.camera.yaw,.4);assert.notEqual(state.camera.pitch,pitchBefore);
listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(400,-100000));listeners.pointerup(pointer(400,-100000));state=view.inspect();assert(state.camera.pitch>=10*Math.PI/180-1e-9&&state.camera.pitch<=80*Math.PI/180+1e-9);const clampA=state.camera.pitch;
listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(400,100000));listeners.pointerup(pointer(400,100000));state=view.inspect();const clampB=state.camera.pitch;
assert.deepEqual([clampA,clampB].sort((a,b)=>a-b),[10*Math.PI/180,80*Math.PI/180]);
view.fit();state=view.inspect();assertVisibleFit(state);
let prevented=false;const zoomBefore=state.camera.zoom;listeners.wheel({deltaY:100,preventDefault(){prevented=true;}});state=view.inspect();assert(prevented);assert.equal(state.topYear,2002);assert.deepEqual(state.visibleYearBounds,[Math.max(2000,2002-state.windowCount+1),2002]);assert.equal(state.camera.zoom,zoomBefore,'wheel moves years without changing zoom');
view.fit();state=view.inspect();assertVisibleFit(state);
// A coordinate formerly occupied by a hidden 2003 instance cannot select that year.
const formerlyVisible=hiddenYearPosition;listeners.pointermove(pointer(formerlyVisible.x,formerlyVisible.y));listeners.pointerdown(pointer(formerlyVisible.x,formerlyVisible.y));listeners.pointerup(pointer(formerlyVisible.x,formerlyVisible.y));
for(const hit of [...selectedNodes,...hoveredNodes])if(hit.id)assert(hit.context.year===null||hit.context.year>=state.visibleYearBounds[0]&&hit.context.year<=state.visibleYearBounds[1]);
view.setData({...input,papers:papers.filter(p=>p.id!=='unknown')});state=view.inspect();assert.equal(state.topYear,2002,'filter updates preserve browsed year');assert(state.windowCount>=1&&state.windowCount<=4);
view.setData({...input,yearFrom:2002,yearTo:2003});state=view.inspect();assert(state.visibleYearBounds[0]>=2002&&state.visibleYearBounds[1]<=2003,'changed year bounds clamp the browsed window');
view.setData({...input,yearFrom:2000,yearTo:2001});state=view.inspect();assert(state.topYear<=2001&&state.visibleYearBounds[0]>=2000);
view.setData({...input,reset:true});view.scrollYears(-1000);state=view.inspect();assert(state.visibleYearBounds[0]>=2000);view.scrollYears(1000);state=view.inspect();assert.equal(state.topYear,2003);
view.fit();state=view.inspect();assertVisibleFit(state);view.destroy();
// Pure viewport geometry has no artificial year-count cap.
const metricInput={height:700,radius:330,zoom:.8,pitch:PITCH,totalYears:100};
const metrics=temporalViewportMetrics(metricInput);
assert.equal(metrics.planeDepth,2*330*.8*Math.sin(PITCH));
assert.equal(metrics.minGap,Math.max(44,.5*metrics.planeDepth+22));
assert.equal(metrics.usableHeight,590);
const low=temporalViewportMetrics({...metricInput,pitch:10*Math.PI/180});
const high=temporalViewportMetrics({...metricInput,pitch:80*Math.PI/180});
assert(low.capacity>high.capacity,'viewing near the side exposes more year slices');
assert(temporalViewportMetrics({...metricInput,height:1400}).capacity>=metrics.capacity);
assert(temporalViewportMetrics({...metricInput,zoom:.4}).capacity>=metrics.capacity);
assert(temporalViewportMetrics({...metricInput,height:2000,zoom:.2,pitch:10*Math.PI/180}).capacity>4);
assert.equal(temporalViewportMetrics({...metricInput,totalYears:2}).capacity,Math.min(2,metrics.capacity));
// Integrated geometry responds to pitch and zoom without refitting or changing the selected top year.
canvasHeight=700;
const dynamic=createTimeline3D({canvas});dynamic.setData({...input,yearTo:2025,reset:true});dynamic.setActive(true);
const setPitchAtLimit=delta=>{listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(400,300+delta));listeners.pointerup(pointer(400,300+delta));return dynamic.inspect();};
const nearSide=setPitchAtLimit(-100000),nearTop=setPitchAtLimit(100000);
assert(nearSide.windowCount>nearTop.windowCount);
assert.equal(nearSide.topYear,nearTop.topYear);
function assertGeometricSpacing(info){
  const radius=Math.max(...info.planes.map(p=>p.radius));
  const geometry=temporalViewportMetrics({height:canvasHeight,radius,zoom:info.camera.zoom,pitch:info.camera.pitch,totalYears:26});
  const planes=info.planes.slice().sort((a,b)=>a.year-b.year);
  for(let i=1;i<planes.length;i++){const screenGap=Math.abs(planes[i].y-planes[i-1].y);assert(screenGap+1e-7>=geometry.minGap,'projected year spacing respects the geometric overlap budget');const projectedGap=Math.abs(planes[i].z-planes[i-1].z)*info.camera.timeScale*info.camera.zoom*Math.cos(info.camera.pitch);assert(Math.abs(screenGap-projectedGap)<1e-7,'inspected temporal scale matches actual projected year gaps');}
  assert(planes.every(p=>p.y-p.ry>=-1e-7&&p.y+p.ry<=canvasHeight+1e-7),'planes fit the projected temporal window');
}
assertGeometricSpacing(nearSide);assertGeometricSpacing(nearTop);
const capacityBefore=nearTop.windowCount;dynamic.zoom(.5);const zoomedOut=dynamic.inspect();assert(zoomedOut.windowCount>=capacityBefore);assertGeometricSpacing(zoomedOut);
const countBeforeResize=zoomedOut.windowCount;canvasHeight=1400;dynamic.setActive(true);const taller=dynamic.inspect();assert(taller.windowCount>=countBeforeResize);assertGeometricSpacing(taller);
const totalYears=taller.yearBounds[1]-taller.yearBounds[0]+1;assert(taller.windowCount<=totalYears);
dynamic.destroy();

// Boundaries stop the whole visible window rather than shrinking its lower end.
canvasHeight=1000;
const allFit=createTimeline3D({canvas});allFit.setData({...input,yearTo:2001,reset:true});allFit.setActive(true);
const visibleSignature=info=>({camera:info.camera,topYear:info.topYear,bounds:info.visibleYearBounds,count:info.yearMetrics.count,ids:info.positions.map(p=>p.id)});
const allFitState=allFit.inspect();assert.deepEqual(allFitState.visibleYearBounds,[2000,2001]);assert.deepEqual(allFitState.scrollBounds,[2001,2001]);
for(const delta of [500,-500,5,-5,80,-80])listeners.wheel({deltaY:delta,preventDefault(){}});
allFit.scrollYears(-1000);allFit.scrollYears(1000);assert.deepEqual(visibleSignature(allFit.inspect()),visibleSignature(allFitState),'when all years fit, outward and inward scrolling leave camera and full scope unchanged');allFit.destroy();
canvasHeight=700;
const boundary=createTimeline3D({canvas});boundary.setData({...input,yearTo:2025,reset:true});boundary.setActive(true);
listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(400,-100000));listeners.pointerup(pointer(400,-100000));
boundary.scrollYears(-1000);const earliest=boundary.inspect();assert.equal(earliest.visibleYearBounds[0],2000);assert.equal(earliest.topYear,earliest.scrollBounds[0]);assert(earliest.yearMetrics.count>1,'earliest boundary retains the geometric multi-year window');
boundary.scrollYears(1);listeners.wheel({deltaY:500,preventDefault(){}});assert.deepEqual(visibleSignature(boundary.inspect()),visibleSignature(earliest),'a large wheel event reaching the boundary clamps without shrinking the window');for(let i=0;i<5;i++)listeners.wheel({deltaY:5,preventDefault(){}});
assert.deepEqual(visibleSignature(boundary.inspect()),visibleSignature(earliest),'overscrolling earliest year does not shrink the window, change its count or move camera');
listeners.wheel({deltaY:-80,preventDefault(){}});const reversed=boundary.inspect();assert.equal(reversed.topYear,earliest.topYear+1,'reverse scrolling responds immediately after ignored boundary deltas');
listeners.wheel({deltaY:30,preventDefault(){}});assert.equal(boundary.inspect().topYear,reversed.topYear);
listeners.wheel({deltaY:-80,preventDefault(){}});assert.equal(boundary.inspect().topYear,reversed.topYear+1,'opposite-direction fractional residue is cleared on reversal');
boundary.scrollYears(1000);const latest=boundary.inspect();assert.equal(latest.topYear,2025);assert.equal(latest.topYear,latest.scrollBounds[1]);
listeners.wheel({deltaY:-500,preventDefault(){}});for(let i=0;i<5;i++)listeners.wheel({deltaY:-5,preventDefault(){}});assert.deepEqual(visibleSignature(boundary.inspect()),visibleSignature(latest));
listeners.wheel({deltaY:80,preventDefault(){}});assert.equal(boundary.inspect().topYear,2024,'reverse scrolling responds immediately at the latest boundary');
boundary.scrollYears(-1000);const beforeGeometry=boundary.inspect();boundary.zoom(.5);const afterGeometry=boundary.inspect();assert(afterGeometry.scrollBounds[0]>=beforeGeometry.scrollBounds[0]);assert(afterGeometry.topYear>=afterGeometry.scrollBounds[0]&&afterGeometry.topYear<=afterGeometry.scrollBounds[1]);assert.equal(afterGeometry.visibleYearBounds[0],2000,'zooming out at the earliest boundary recalculates and clamps the full window');
canvasHeight=1400;boundary.setActive(true);const afterResize=boundary.inspect();assert(afterResize.scrollBounds[0]>=afterGeometry.scrollBounds[0]);assert(afterResize.topYear>=afterResize.scrollBounds[0]);assert.equal(afterResize.visibleYearBounds[0],2000);listeners.pointerdown(pointer(400,300));listeners.pointermove(pointer(400,100000));listeners.pointerup(pointer(400,100000));const afterPitch=boundary.inspect();assert(afterPitch.scrollBounds[0]<=afterResize.scrollBounds[0],'a steeper pitch reduces full-window capacity and recalculates the earliest legal top year');assert(afterPitch.topYear>=afterPitch.scrollBounds[0]&&afterPitch.topYear<=afterPitch.scrollBounds[1]);boundary.scrollYears(-1000);assert.equal(boundary.inspect().visibleYearBounds[0],2000);boundary.destroy();

console.log('Timeline layout checks passed: annual citations, orthographic scaling, C1 limbs, ellipse/Bezier hits, geometric year window, pitch clamps, wheel year browsing, current-window fit and hidden-year hit exclusion and full-window scrolling boundaries.');
