'use strict';
(() => {
  const PITCH = 40 * Math.PI / 180;
  const MIN_PITCH=10*Math.PI/180,MAX_PITCH=80*Math.PI/180;
  const finite = (v, fallback = 0) => Number.isFinite(Number(v)) ? Number(v) : fallback;
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
  const extent = values => values.length ? [Math.min(...values),Math.max(...values)] : [2000,2001];
  const hash = value => {let n=2166136261;for(const c of String(value)){n^=c.charCodeAt(0);n=Math.imul(n,16777619);}return (n>>>0)/4294967296;};
  const getHistoryHelper=()=>typeof window!=='undefined'?window.ATLAS_TIMELINE_HISTORY:(typeof require==='function'?require('./timeline-history.js'):null);
  const publicationYear = paper => {
    const helper=getHistoryHelper();if(helper)return helper.publicationYear(paper);
    return Number.isFinite(paper.year)&&paper.year>0?Math.floor(paper.year):null;
  };
  // Orthographic projection: x/y span a horizontal plane; z is vertical time.
  function projectPoint(point,camera={},width=1,height=1){
    const yaw=finite(camera.yaw),pitch=clamp(finite(camera.pitch,PITCH),MIN_PITCH,MAX_PITCH),scale=finite(camera.zoom,1);
    const x=finite(point.x)-finite(camera.target?.x),y=finite(point.y)-finite(camera.target?.y),z=(finite(point.z)-finite(camera.target?.z))*finite(camera.timeScale,1);
    const u=x*Math.cos(yaw)-y*Math.sin(yaw),v=x*Math.sin(yaw)+y*Math.cos(yaw);
    return {x:width/2+finite(camera.panX)+u*scale,y:height/2+finite(camera.panY)+(v*Math.sin(pitch)-z*Math.cos(pitch))*scale,depth:-(v*Math.cos(pitch)+z*Math.sin(pitch)),scale,visible:true};
  }
  function temporalViewportMetrics({height=1,radius=330,zoom=1,pitch=PITCH,totalYears=Infinity}={}){
    const planeDepth=2*Math.max(1,radius)*Math.max(.025,zoom)*Math.sin(clamp(pitch,MIN_PITCH,MAX_PITCH));
    const usableHeight=Math.max(1,height-110),minGap=Math.max(44,.5*planeDepth+22);
    const capacity=Math.max(1,Math.min(Math.max(1,totalYears),Math.floor(Math.max(0,usableHeight-planeDepth)/minGap)+1));
    return {planeDepth,usableHeight,minGap,capacity};
  }
  function rotationCenter(){return {x:0,y:0,z:0};}
  function yearFog(){return 1;}
  function timelineNodeRadius(count,lab=true,zoom=1){
    const known=typeof count==='number'&&Number.isFinite(count)&&count>=0;
    const radius=known?(lab?Math.min(52,6+3.4*Math.sqrt(count)):Math.min(24,4+2*Math.sqrt(count))):(lab?8:5);
    return Math.max(lab?2:1.5,radius*Math.max(.025,finite(zoom,1)));
  }
  function yearPlane(position,radius=280){return !position||position.unknown?[]:Array.from({length:64},(_,i)=>({x:Math.cos(i*Math.PI/32)*radius,y:Math.sin(i*Math.PI/32)*radius,z:position.z}));}
  function cubicPoint(curve,t){const u=1-t;return Object.fromEntries(['x','y','z'].map(k=>[k,u*u*u*finite(curve.a[k])+3*u*u*t*finite(curve.c1[k])+3*u*t*t*finite(curve.c2[k])+t*t*t*finite(curve.b[k])]));}
  function bezierFor(a,b,tangentA,tangentB){
    const dz=b.z-a.z;
    return {a,b,c1:{x:a.x+tangentA.x*dz/3,y:a.y+tangentA.y*dz/3,z:a.z+dz/3},c2:{x:b.x-tangentB.x*dz/3,y:b.y-tangentB.y*dz/3,z:b.z-dz/3}};
  }
  function ellipseHit(point,node,padding=0){return ((point.x-node.x)/(node.rx+padding))**2+((point.y-node.y)/(node.ry+padding))**2<=1;}
  function curveHit(point,samples,width=5){
    for(let i=1;i<samples.length;i++){const a=samples[i-1],b=samples[i],dx=b.x-a.x,dy=b.y-a.y,l=dx*dx+dy*dy,t=l?clamp(((point.x-a.x)*dx+(point.y-a.y)*dy)/l,0,1):0;if(Math.hypot(point.x-a.x-t*dx,point.y-a.y-t*dy)<=width)return true;}return false;
  }
  function fallbackSlices(papers,history,options){
    const dated=papers.map(publicationYear).filter(y=>y!==null),lower=options.lowerYearBucket??2000;
    const min=finite(options.yearFrom,Math.max(lower,extent(dated)[0])),max=finite(options.yearTo,Math.max(min,extent(dated)[1]));
    const years=Array.from({length:Math.max(1,max-min+1)},(_,i)=>min+i);
    return {years,slices:years.map(year=>({year,appearances:papers.filter(p=>publicationYear(p)!==null&&publicationYear(p)<=year).map(p=>({id:p.id+'@'+year,paperId:p.id,year,publicationYear:publicationYear(p),citation:{count:null,status:'missing',scope:'observed_neighborhood'}}))})),unknown:papers.filter(p=>publicationYear(p)===null),lowerYearBucket:lower};
  }
  function buildTimelinePositions(papers,options={}){
    const helper=options.helper||getHistoryHelper(),byPaper=new Map(papers.map(p=>[p.id,p]));
    const annual=options.annual?{...options.annual,slices:options.annual.slices.map(slice=>{const appearances=slice.appearances.filter(p=>byPaper.has(p.paperId));return {...slice,appearances,nodes:appearances};}),unknown:(options.annual.unknown||[]).filter(p=>byPaper.has(p.paperId||p.id))}:(helper?helper.buildAnnualSlices(papers,options.edges||[],options.history||{},options):fallbackSlices(papers,options.history,options));
    const years=annual.years||annual.slices.map(s=>s.year),yearBounds=extent(years);
    const colors=[...new Set(papers.filter(p=>p.lab).map(p=>p.displayColor||'#969aa4'))].sort();
    const xb=extent(papers.map(p=>finite(p.x))),yb=extent(papers.map(p=>finite(p.y)));
    const normal=(v,b)=>(finite(v)-(b[0]+b[1])/2)/Math.max(1,b[1]-b[0]);
    const radius=finite(options.radius,330),height=finite(options.height,Math.max(460,Math.min(1800,years.length*115))),span=Math.max(1,yearBounds[1]-yearBounds[0]);
    const labCount=Math.max(1,papers.filter(p=>p.lab).length),sectors=new Map();let cursor=0;
    for(const color of colors){const n=papers.filter(p=>p.lab&&(p.displayColor||'#969aa4')===color).length;sectors.set(color,{start:cursor,span:n/labCount});cursor+=n/labCount;}
    const anchors=new Map(),grid=new Map(),cellSize=1/Math.sqrt(Math.max(1,papers.length));
    // Pack stable topical sectors; external references use the complete outer annulus.
    const ordered=papers.slice().sort((a,b)=>Number(!!b.lab)-Number(!!a.lab)||String(a.id).localeCompare(String(b.id)));
    for(const p of ordered){const h=hash(p.id+'angle'+(options.seed||0)),rh=hash(p.id+'radius'+(options.seed||0)),sector=sectors.get(p.displayColor||'#969aa4')||{start:0,span:1};let best;
      const separation=cellSize*(p.lab?.9:.65);
      for(let attempt=0;attempt<30;attempt++){
        const angle=(p.lab?sector.start+sector.span*((h+attempt*.61803398875)%1):(h+attempt*.61803398875)%1)*2*Math.PI;
        const r=p.lab?.62*Math.sqrt((rh+attempt*.173)%1):Math.sqrt(.66*.66+(1-.66*.66)*((rh+attempt*.173)%1));
        const embeddingWeight=p.lab?.08:.025,point={x:(1-embeddingWeight)*Math.cos(angle)*r+embeddingWeight*normal(p.x,xb),y:(1-embeddingWeight)*Math.sin(angle)*r+embeddingWeight*normal(p.y,yb)};let collision=false;const gx=Math.floor(point.x/cellSize),gy=Math.floor(point.y/cellSize);
        for(let x=gx-1;x<=gx+1&&!collision;x++)for(let y=gy-1;y<=gy+1&&!collision;y++)for(const neighbor of grid.get(x+','+y)||[])if(Math.hypot(point.x-neighbor.x,point.y-neighbor.y)<separation){collision=true;break;}
        best=point;if(!collision)break;
      }
      anchors.set(p.id,best);const key=Math.floor(best.x/cellSize)+','+Math.floor(best.y/cellSize);if(!grid.has(key))grid.set(key,[]);grid.get(key).push(best);
    }
    const positions=[],planes=[],tracks=new Map();
    for(const slice of annual.slices){const t=(slice.year-yearBounds[0])/span,latestCount=Math.max(1,annual.slices.at(-1)?.appearances.length||1),expansion=Math.max(years.length<=8?.65:.20,Math.sqrt(slice.appearances.length/latestCount)),planeRadius=radius*expansion,z=(t-.5)*height;planes.push({year:slice.year,label:slice.label||String(slice.year),z,radius:planeRadius});
      for(const appearance of slice.appearances){const paper=byPaper.get(appearance.paperId);if(!paper)continue;const anchor=anchors.get(paper.id),p={...appearance,id:appearance.id||paper.id+'@'+slice.year,paperId:paper.id,paper,x:anchor.x*planeRadius,y:anchor.y*planeRadius,z,unknown:false};positions.push(p);if(!tracks.has(paper.id))tracks.set(paper.id,[]);tracks.get(paper.id).push(p);}}
    const limbs=[];
    for(const [paperId,track] of tracks){const tangents=track.map((p,i)=>{const a=track[Math.max(0,i-1)],b=track[Math.min(track.length-1,i+1)],dz=b.z-a.z||1;return {x:(b.x-a.x)/dz,y:(b.y-a.y)/dz};});track.forEach((p,i)=>p.tangent=tangents[i]);for(let i=1;i<track.length;i++)limbs.push({...bezierFor(track[i-1],track[i],tangents[i-1],tangents[i]),paperId,kind:'limb',lab:!!track[i].paper.lab,color:track[i].paper.displayColor||'#969aa4'});}
    const unknown=annual.unknown||[];unknown.forEach((item,i)=>{const paper=item.paper||byPaper.get(item.paperId||item.id)||item;if(!paper.id)return;positions.push({id:paper.id+'@unknown',paperId:paper.id,paper,unknown:true,year:null,citation:{count:null,status:'missing'},x:(i%10-4.5)*48,y:radius+95+Math.floor(i/10)*32,z:-height/2-80});});
    return {positions,planes,limbs,tracks,yearBounds,coordinateBounds:{x:xb,y:yb},radius,height,annual};
  }
  function cubicSlice(curve,from,to){
    const mix=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:finite(a.z)+(finite(b.z)-finite(a.z))*t,depth:finite(a.depth)+(finite(b.depth)-finite(a.depth))*t});
    const split=(c,t)=>{const p=mix(c.a,c.c1,t),q=mix(c.c1,c.c2,t),r=mix(c.c2,c.b,t),u=mix(p,q,t),v=mix(q,r,t),end=mix(u,v,t);return [{...c,a:c.a,c1:p,c2:u,b:end},{...c,a:end,c1:v,c2:r,b:c.b}];};
    const prefix=to<1?split(curve,to)[0]:curve,result=from>0?split(prefix,from/to)[1]:prefix;
    return {...result,a:{...result.a,node:curve.a.node},b:{...result.b,node:curve.b.node},fragmentT:[from,to]};
  }
  function timelineRenderLayers(nodes,curves,planes){
    const layers=new Map();
    const layer=year=>{if(!layers.has(year))layers.set(year,{year,plane:null,nodes:[],crossingCurves:[],sameYearCurves:[]});return layers.get(year);};
    for(const p of planes)layer(p.year).plane=p;
    for(const p of nodes)layer(p.node.year).nodes.push(p);
    for(const c of curves){
      const a=c.a.node?.year??c.a.year,b=c.b.node?.year??c.b.year,year=Math.max(a,b);
      if(Math.abs(a-b)>1){
        const cuts=[0,1];for(let y=Math.min(a,b)+1;y<Math.max(a,b);y++)cuts.push((y-a)/(b-a));cuts.sort((x,y)=>x-y);
        for(let i=1;i<cuts.length;i++){const from=cuts[i-1],to=cuts[i],fragmentYear=Math.ceil(a+(b-a)*(from+to)/2);layer(fragmentYear).crossingCurves.push({...cubicSlice(c,from,to),fragmentYear});}
      }else layer(year)[a===b?'sameYearCurves':'crossingCurves'].push(c);
    }
    for(const item of layers.values())item.nodes.sort((a,b)=>b.depth-a.depth);
    return [...layers.values()].sort((a,b)=>(a.year??-Infinity)-(b.year??-Infinity));
  }
  function createTimeline3D({canvas,onSelectNode=()=>{},onSelectEdge=()=>{},onHover=()=>{},onCameraChange=()=>{},onYearWindowChange=()=>{}}){
    const ctx=canvas.getContext('2d'),camera={yaw:-.25,pitch:PITCH,zoom:1,timeScale:1,panX:0,panY:0,target:{x:0,y:0,z:0}};
    let width=1,height=1,active=false,destroyed=false,frame=null,lastDraw=-Infinity,drag=null,initialFit=true,layout=buildTimelinePositions([]),selected=null,selectedYear=null,hoverId=null;
    let associations=[],projected=[],curves=[],screenPlanes=[],dirty=true,nodeGrid=new Map(),curveGrid=new Map(),lastInput=null,seed=0,lastDrawMs=0,topYear=null,wheelRemainder=0,windowStamp=null,anchor=null,highlightInstanceIds=new Set(),selectedAssociationYear=null;
    const cell=64,key=(x,y)=>Math.floor(x/cell)+','+Math.floor(y/cell);
    const metricsForYear=year=>temporalViewportMetrics({height,radius:layout.planes.find(p=>p.year===year)?.radius||layout.radius,zoom:camera.zoom,pitch:camera.pitch,totalYears:layout.yearBounds[1]-layout.yearBounds[0]+1});
    const viewportMetrics=()=>metricsForYear(topYear??layout.yearBounds[1]);
    function scrollBounds(){
      const [min,max]=layout.yearBounds;
      // Stop when the bottom of the whole viewport first reaches the oldest slice.
      for(let year=max;year>=min;year--)if(year-metricsForYear(year).capacity+1<=min)return [year,max];
      return [min,max];
    }
    const windowCount=()=>viewportMetrics().capacity;
    const yearWindow=()=>[Math.max(layout.yearBounds[0],(topYear??layout.yearBounds[1])-windowCount()+1),topYear??layout.yearBounds[1]];
    function syncYearWindow(){
      topYear=clamp(topYear??layout.yearBounds[1],...scrollBounds());
      const [from,to]=yearWindow(),planes=layout.planes.filter(p=>p.year>=from&&p.year<=to);
      camera.target.z=planes.length?(planes[0].z+planes.at(-1).z)/2:0;
      const metrics=viewportMetrics(),count=planes.length,nativeStep=layout.height/Math.max(1,layout.yearBounds[1]-layout.yearBounds[0]);
      const spacing=count>1?Math.max(metrics.minGap,(metrics.usableHeight-metrics.planeDepth)/(count-1)):metrics.minGap;
      camera.timeScale=spacing/Math.max(.001,nativeStep*camera.zoom*Math.cos(camera.pitch));
      dirty=true;
      const stamp=from+':'+to;if(stamp!==windowStamp){windowStamp=stamp;onYearWindowChange({from,to});}
    }
    function scrollYears(delta){
      const bounds=scrollBounds(),next=clamp((topYear??layout.yearBounds[1])+Math.trunc(finite(delta)),...bounds);
      if(next===topYear)return;
      topYear=next;if(next===bounds[0]||next===bounds[1])wheelRemainder=0;syncYearWindow();hoverId=null;onHover(null);requestDraw();
    }
    const context=node=>({year:node.year,citations:node.citation?.count??null,coverage:node.citation?.status||'missing',citation:node.citation,publicationYear:node.publicationYear,unknown:node.unknown});
    const targetFps=()=>layout.positions.length+layout.limbs.length+associations.length>12000?15:30;
    function requestDraw(){if(!active||destroyed||frame!==null)return;frame=requestAnimationFrame(time=>{frame=null;if(!active||destroyed)return;if(drag&&time-lastDraw<1000/targetFps()){requestDraw();return;}lastDraw=time;draw();});}
    function resize(){const r=canvas.getBoundingClientRect();width=Math.max(1,r.width);height=Math.max(1,r.height);const dpr=Math.min(2,window.devicePixelRatio||1);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);syncYearWindow();requestDraw();}
    const projection=p=>projectPoint(p,camera,width,height);
    function indexBox(grid,entry,x1,y1,x2,y2){for(let x=Math.floor(Math.max(-cell,x1)/cell);x<=Math.floor(Math.min(width+cell,x2)/cell);x++)for(let y=Math.floor(Math.max(-cell,y1)/cell);y<=Math.floor(Math.min(height+cell,y2)/cell);y++){const k=x+','+y;if(!grid.has(k))grid.set(k,[]);grid.get(k).push(entry);}}
    function rebuild(){if(!dirty)return;dirty=false;nodeGrid=new Map();curveGrid=new Map();
      const cy=Math.cos(camera.yaw),sy=Math.sin(camera.yaw),sp=Math.sin(camera.pitch),cp=Math.cos(camera.pitch),scale=camera.zoom,cx=width/2+camera.panX,cv=height/2+camera.panY;
      const fastProject=p=>{const x=p.x-camera.target.x,y=p.y-camera.target.y,z=(p.z-camera.target.z)*camera.timeScale,u=x*cy-y*sy,v=x*sy+y*cy;return {x:cx+u*scale,y:cv+(v*sp-z*cp)*scale,depth:-(v*cp+z*sp),scale,visible:true};};
      const [from,to]=yearWindow();
      screenPlanes=layout.planes.filter(p=>p.year>=from&&p.year<=to).map(p=>({...p,...fastProject({x:0,y:0,z:p.z}),rx:p.radius*camera.zoom,ry:p.radius*camera.zoom*sp})).filter(p=>p.y+p.ry>=0&&p.y-p.ry<=height);
      const shownYears=new Set(screenPlanes.map(p=>p.year));
      buildAssociations(shownYears);
      const inspectedAssociation=associations.find(c=>c.edge.id===selected&&c.year===selectedAssociationYear)||associations.find(c=>c.edge.id===selected);
      selectedAssociationYear=inspectedAssociation?.year??null;
      projected=layout.positions.filter(node=>node.unknown?from===layout.yearBounds[0]:shownYears.has(node.year)).map(node=>{const p=fastProject(node),rx=timelineNodeRadius(node.citation?.count,!!node.paper.lab,camera.zoom),ry=rx*sp;return {...p,node,rx,ry};}).sort((a,b)=>(a.node.year??-Infinity)-(b.node.year??-Infinity)||b.depth-a.depth);
      const screenById=new Map(projected.map(p=>[p.node.id,p]));for(const p of projected)if(p.x+p.rx>=0&&p.y+p.ry>=0&&p.x-p.rx<=width&&p.y-p.ry<=height)indexBox(nodeGrid,p,p.x-p.rx,p.y-p.ry,p.x+p.rx,p.y+p.ry);

      curves=[];for(const curve of [...layout.limbs,...associations]){if(!screenById.has(curve.a.id)||!screenById.has(curve.b.id))continue;const a=screenById.get(curve.a.id)||fastProject(curve.a),b=screenById.get(curve.b.id)||fastProject(curve.b),c1=fastProject(curve.c1),c2=fastProject(curve.c2),points=[a,b,c1,c2],xs=points.map(p=>p.x),ys=points.map(p=>p.y),x1=Math.min(...xs),x2=Math.max(...xs),y1=Math.min(...ys),y2=Math.max(...ys);if(x2< -40||x1>width+40||y2< -40||y1>height+40)continue;const endpoint=screenById.get(curve.b.id),lineWidth=curve.kind==='limb'?2*(endpoint?.ry||6):selected===curve.edge.id&&selectedAssociationYear===curve.year?2.8:curve.strokeWidth,cached={...curve,a,b,c1,c2,lineWidth};curves.push(cached);if(curve.kind!=='limb'){cached.samples=Array.from({length:13},(_,i)=>cubicPoint(cached,i/12));const pad=Math.max(6,lineWidth/2);indexBox(curveGrid,cached,x1-pad,y1-pad,x2+pad,y2+pad);}}
    }
    function draw(){const started=performance.now();rebuild();
      const selectedPapers=new Set(anchor?[anchor.paperId]:[]);
      ctx.clearRect(0,0,width,height);ctx.shadowBlur=0;ctx.globalAlpha=1;
      function drawPlane(p){
        ctx.globalAlpha=1;ctx.shadowBlur=0;ctx.beginPath();ctx.ellipse(p.x,p.y,p.rx,p.ry,0,0,Math.PI*2);
        ctx.fillStyle=p.year===selectedYear?'rgba(184,201,225,.56)':'rgba(207,218,234,.40)';ctx.fill();
        ctx.strokeStyle=p.year===selectedYear?'rgba(100,116,141,.55)':'rgba(126,137,154,.32)';ctx.lineWidth=1;ctx.stroke();
      }
      function drawCurves(items){
        ctx.shadowBlur=0;
      const strokeGroups=new Map();
      for(const c of items){const highlighted=c.kind==='limb'&&selectedPapers.has(c.paperId);
        const alpha=c.kind==='limb'?(selected?(highlighted?.18:.008):(c.lab?.18:.018)):selected===c.edge.id&&selectedAssociationYear===c.year?.82:c.alpha;
        const color=c.color||'#929dae',opacity=Math.max(.005,Math.round(alpha*100)/100),lineWidth=Math.round(c.lineWidth*2)/2,dash=c.dash||[],key=color+'|'+opacity+'|'+lineWidth+'|'+dash.join(',');
        if(!strokeGroups.has(key))strokeGroups.set(key,{color,opacity,lineWidth,dash,paths:[]});strokeGroups.get(key).paths.push(c);
      }
      for(const group of strokeGroups.values()){ctx.globalAlpha=group.opacity;ctx.strokeStyle=group.color;ctx.lineWidth=group.lineWidth;ctx.setLineDash(group.dash);ctx.lineCap='round';ctx.beginPath();for(const c of group.paths){ctx.moveTo(c.a.x,c.a.y);ctx.bezierCurveTo(c.c1.x,c.c1.y,c.c2.x,c.c2.y,c.b.x,c.b.y);}ctx.stroke();}ctx.setLineDash([]);
      }
      function drawNodes(nodes){
      for(const p of nodes){if(p.x+p.rx<0||p.y+p.ry<0||p.x-p.rx>width||p.y-p.ry>height)continue;const n=p.node,paper=n.paper,isSelected=highlightInstanceIds.has(n.id),isHover=hoverId===n.id;ctx.globalAlpha=isSelected||isHover?1:selected?(anchor?.paperId===n.paperId?(paper.lab?.35:.12):.08):paper.displayMuted?.10:paper.lab===false?.16:1;ctx.fillStyle=paper.displayColor||'#969aa4';ctx.shadowColor=isHover||isSelected?ctx.fillStyle:'rgba(50,60,77,.15)';ctx.shadowBlur=isHover?16:isSelected?10:paper.lab&&projected.length<1500?3:0;ctx.beginPath();ctx.ellipse(p.x,p.y,p.rx,p.ry,0,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle='rgba(255,255,255,.85)';ctx.lineWidth=.8;ctx.stroke();ctx.globalAlpha=1;if(isSelected){ctx.strokeStyle='#344b7a';ctx.lineWidth=1;ctx.stroke();}}
      }
      // A higher year's translucent surface must composite over lower nodes and branches.
      for(const item of timelineRenderLayers(projected,curves,screenPlanes)){
        drawCurves(item.crossingCurves);
        if(item.plane)drawPlane(item.plane);
        drawCurves(item.sameYearCurves);
        drawNodes(item.nodes);
      }
      ctx.globalAlpha=1;ctx.shadowBlur=0;ctx.font='12px sans-serif';
      if(screenPlanes.length){const top=Math.max(28,Math.min(...screenPlanes.map(p=>p.y))-20),bottom=Math.min(height-18,Math.max(...screenPlanes.map(p=>p.y))+22),axisX=22;ctx.strokeStyle='#a5aebb';ctx.fillStyle='#657184';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(axisX,bottom);ctx.lineTo(axisX,top);ctx.moveTo(axisX-4,top+7);ctx.lineTo(axisX,top);ctx.lineTo(axisX+4,top+7);ctx.stroke();ctx.fillText('年份 · z',12,Math.max(14,top-9));for(const p of screenPlanes)if(p.y>20&&p.y<height-12){ctx.beginPath();ctx.moveTo(axisX-3,p.y);ctx.lineTo(axisX+3,p.y);ctx.stroke();ctx.fillText(p.label,axisX+9,p.y+4);}}
      ctx.globalAlpha=1;if(projected.some(p=>p.node.unknown)){const p=projection({x:-220,y:layout.radius+95,z:-layout.height/2-80});ctx.fillStyle='#768091';ctx.fillText('年份未知',p.x,p.y+27);}lastDrawMs=performance.now()-started;
    }
    function fit(){
      onHover(null);hoverId=null;camera.panX=0;camera.panY=0;
      const radius=layout.planes.find(p=>p.year===(topYear??layout.yearBounds[1]))?.radius||layout.radius;
      // Reserve vertical space for readable separation; fitting never fixes the number of years.
      camera.zoom=clamp(Math.min(Math.max(1,width-140)/(2*radius),Math.max(1,height-110)/(2*radius*(Math.sin(camera.pitch)+.85))),.025,12);
      syncYearWindow();requestDraw();
    }
    function buildAssociations(shownYears){
      associations=[];highlightInstanceIds=new Set();
      if(!anchor)return;
      const track=layout.tracks.get(anchor.paperId)||[];
      const anchorNode=track.find(p=>p.id===anchor.instanceId)||layout.positions.find(p=>p.id===anchor.instanceId);
      if(anchorNode?.unknown){if(shownYears.has(layout.yearBounds[0]))highlightInstanceIds.add(anchorNode.id);return;}
      const activeNodes=track.filter(p=>shownYears.has(p.year));
      for(const node of activeNodes)highlightInstanceIds.add(node.id);
      if(!activeNodes.length)return;
      const a=activeNodes[0],seen=new Set(),entries=[];
      for(const slice of layout.annual.slices){
        if(!shownYears.has(slice.year)||slice.year<a.year)continue;
        for(const edge of slice.edges||[]){
          if(seen.has(edge.id)||(edge.source!==anchor.paperId&&edge.target!==anchor.paperId)||(edge.kind==='citation'&&edge.target!==anchor.paperId))continue;
          const neighborId=edge.source===anchor.paperId?edge.target:edge.source;
          const b=(layout.tracks.get(neighborId)||[]).find(p=>p.year===slice.year);
          if(!b||b.publicationYear>slice.year||b.year<a.year)continue;
          seen.add(edge.id);entries.push({edge,a,b});
        }
      }
      const scores=entries.map(item=>finite(item.edge.score)),low=Math.min(...scores),high=Math.max(...scores);
      for(const {edge,a,b} of entries){
        const dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z;
        const curve=dz?bezierFor(a,b,a.tangent||{x:0,y:0},b.tangent||{x:0,y:0}):{a,b,c1:{x:a.x+dx*.33-dy*.08,y:a.y+dy*.33+dx*.08,z:a.z},c2:{x:a.x+dx*.67-dy*.08,y:a.y+dy*.67+dx*.08,z:b.z}};
        highlightInstanceIds.add(b.id);
        const strength=high>low?(finite(edge.score)-low)/(high-low):.5;
        associations.push({...curve,kind:'association',lab:!!(a.paper.lab||b.paper.lab),alpha:.45+.25*strength,strokeWidth:1.25+strength,edge,year:b.year,color:a.paper.displayColor||'#929dae',dash:['semantic','keyword'].includes(edge.kind)?[5,4]:[],sourceYear:edge.source===a.paperId?a.year:b.year,targetYear:edge.target===a.paperId?a.year:b.year});
      }
    }
    function select(id,slice){
      rebuild();
      if(!id){selected=null;selectedYear=null;selectedAssociationYear=null;anchor=null;associations=[];curves=[];curveGrid=new Map();highlightInstanceIds=new Set();}
      else{
        const visibleEdge=associations.find(c=>c.edge.id===id&&(slice?.year==null||c.year===slice.year))||associations.find(c=>c.edge.id===id);
        const isEdge=!!visibleEdge||!!slice?.anchorId;
        if(!isEdge||!anchor){
          const paperId=slice?.anchorId||id,track=layout.tracks.get(paperId)||[],year=slice?.anchorYear??slice?.year??yearWindow()[1];
          const node=track.find(p=>p.year===year)||layout.positions.find(p=>p.id===id||(p.unknown&&p.paperId===paperId))||track.filter(p=>p.year<=year).at(-1)||track[0];
          anchor=node?{paperId:node.paperId,year:node.year,instanceId:node.id}:null;
        }
        selected=id;selectedYear=anchor?.year??null;
        selectedAssociationYear=isEdge?(visibleEdge?.year??slice?.year??anchor?.year??null):null;
        if(!isEdge&&anchor?.year!=null){
          const [from,to]=yearWindow();
          if(anchor.year<from||anchor.year>to){topYear=clamp(anchor.year,...scrollBounds());syncYearWindow();}
        }
      }
      dirty=true;requestDraw();
    }
    function contextForPaper(paperId,preferredYear){
      rebuild();
      const own=paperId===anchor?.paperId,track=layout.tracks.get(paperId)||[];
      const shownYears=new Set(screenPlanes.map(p=>p.year));
      const year=preferredYear??selectedAssociationYear??anchor?.year;
      const associated=associations.filter(c=>c.a.paperId===paperId||c.b.paperId===paperId);
      const association=associated.find(c=>c.year===year&&c.edge.id===selected)||associated.find(c=>c.year===year)||(preferredYear==null?associated.find(c=>c.edge.id===selected)||(!own?associated[0]:null):null);
      let node;
      if(own&&selectedAssociationYear==null)node=track.find(p=>p.year===(preferredYear??anchor.year))||layout.positions.find(p=>p.id===anchor.instanceId)||track.find(p=>shownYears.has(p.year));
      else node=association?(association.a.paperId===paperId?association.a:association.b):track.find(p=>p.year===year);
      return node?{...context(node),instanceId:node.id}:null;
    }
    function selectionState(){
      rebuild();
      return {anchor:anchor?{...anchor}:null,selected,selectedYear,selectedAssociationYear,visibleAssociationIds:[...new Set(curves.filter(c=>c.kind==='association').map(c=>c.edge.id))]};
    }
    const pointAt=e=>{const r=canvas.getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top};};
    function planeOccludes(point,year,includeOwn=false){
      return screenPlanes.some(plane=>(includeOwn?plane.year>=year:plane.year>year)&&ellipseHit(point,plane));
    }
    function hitNode(p){rebuild();const candidates=nodeGrid.get(key(p.x,p.y))||[];for(let i=candidates.length-1;i>=0;i--)if(ellipseHit(p,candidates[i],2)&&!planeOccludes(p,candidates[i].node.year??-Infinity))return candidates[i];return null;}
    function hitEdge(p){rebuild();
      const candidates=(curveGrid.get(key(p.x,p.y))||[]).slice().sort((a,b)=>Math.max(b.a.node.year,b.b.node.year)-Math.max(a.a.node.year,a.b.node.year)||Number(b.a.node.year===b.b.node.year)-Number(a.a.node.year===a.b.node.year));
      return candidates.find(c=>{
        let closest=null,best=Infinity;const width=Math.max(5,c.lineWidth/2);
        for(let i=1;i<c.samples.length;i++){const a=c.samples[i-1],b=c.samples[i],dx=b.x-a.x,dy=b.y-a.y,l=dx*dx+dy*dy,t=l?clamp(((p.x-a.x)*dx+(p.y-a.y)*dy)/l,0,1):0,d=Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);if(d<=width&&d<best){best=d;closest=(i-1+t)/(c.samples.length-1);}}
        if(closest===null)return false;
        const a=c.a.node.year,b=c.b.node.year,phase=a===b?a:Math.min(Math.max(a,b),Math.floor(a+(b-a)*closest+1e-8)+1);
        return !planeOccludes(p,phase,a!==b);
      })||null;
    }
    function hover(p){const n=hitNode(p),id=n?.node.id||null;if(id!==hoverId){hoverId=id;onHover(n?.node.paper||null,n?{x:n.x,y:n.y}:p,n?context(n.node):undefined);requestDraw();}canvas.style.cursor=n||hitEdge(p)?'pointer':'grab';}
    const down=e=>{if(!active)return;const p=pointAt(e);drag={...p,startX:p.x,startY:p.y,moved:false,pan:e.shiftKey||e.button===2};canvas.setPointerCapture?.(e.pointerId);hoverId=null;onHover(null);canvas.style.cursor='grabbing';};
    const move=e=>{if(!active)return;const p=pointAt(e);if(!drag){hover(p);return;}const dx=p.x-drag.x,dy=p.y-drag.y;drag.x=p.x;drag.y=p.y;drag.moved ||= Math.hypot(p.x-drag.startX,p.y-drag.startY)>4;if(drag.pan){camera.panX+=dx;camera.panY+=dy;}else {camera.yaw+=dx*.006;camera.pitch=clamp(camera.pitch+dy*.004,MIN_PITCH,MAX_PITCH);onCameraChange({...camera});syncYearWindow();}dirty=true;requestDraw();};
    const up=e=>{if(!drag)return;const moved=drag.moved;drag=null;canvas.releasePointerCapture?.(e.pointerId);if(!moved&&e.button!==2){const p=pointAt(e),node=hitNode(p);if(node){select(node.node.paperId,context(node.node));onSelectNode(node.node.paperId,context(node.node));}else{const edge=hitEdge(p);if(edge){const detail={year:edge.year,anchorId:anchor?.paperId,anchorYear:anchor?.year,sourceYear:edge.sourceYear,targetYear:edge.targetYear};select(edge.edge.id,detail);onSelectEdge(edge.edge,detail);}else{select(null);onSelectNode(null);}}}requestDraw();};
    function zoom(factor){hoverId=null;onHover(null);camera.zoom=clamp(camera.zoom*finite(factor,1),.025,12);syncYearWindow();requestDraw();}
    const listeners={pointerdown:down,pointermove:move,pointerup:up,pointercancel:()=>{drag=null;requestDraw();},pointerleave:()=>{if(!drag){hoverId=null;onHover(null);requestDraw();}},wheel:e=>{if(!active)return;e.preventDefault();
      const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?height:1),bounds=scrollBounds();
      if(!delta)return;
      if((delta>0&&topYear<=bounds[0])||(delta<0&&topYear>=bounds[1])){wheelRemainder=0;return;}
      if(delta*wheelRemainder<0)wheelRemainder=0;
      wheelRemainder+=delta;const steps=Math.trunc(wheelRemainder/80);
      if(steps){wheelRemainder-=steps*80;scrollYears(-steps);}
    },contextmenu:e=>e.preventDefault(),keydown:e=>{if(!active)return;const steps={ArrowUp:1,ArrowDown:-1,PageUp:windowCount(),PageDown:-windowCount()};if(Object.hasOwn(steps,e.key)){e.preventDefault();scrollYears(steps[e.key]);}}};
    for(const [name,handler]of Object.entries(listeners))canvas.addEventListener(name,handler,{passive:false});const observer=new ResizeObserver(resize);observer.observe(canvas);resize();
    return {setData(input={}){if(!lastInput)topYear=null;lastInput={papers:[],edges:[],...input};if(input.randomize)seed++;const options={seed,...input,...input.bounds,history:input.history||input.citationHistory||(typeof window!=='undefined'?window.ATLAS_CITATION_HISTORY:null),yearFrom:input.yearFrom??input.bounds?.yearFrom??input.yearBounds?.[0],yearTo:input.yearTo??input.bounds?.yearTo??input.yearBounds?.[1]};layout=buildTimelinePositions(lastInput.papers,options);syncYearWindow();wheelRemainder=0;dirty=true;hoverId=null;onHover(null);if(input.reset||input.resetViewport)fit();else requestDraw();},setActive(value){active=!!value;if(active){resize();if(initialFit){initialFit=false;fit();}requestDraw();}else{if(frame!==null)cancelAnimationFrame(frame);frame=null;drag=null;onHover(null);}},select,contextForPaper,selectionState,zoom,fit,scrollYears,rotate(angle){camera.yaw=finite(angle);onCameraChange({...camera});dirty=true;requestDraw();},inspect(){rebuild();const metrics=viewportMetrics(),count=yearWindow()[1]-yearWindow()[0]+1;return {scrollBounds:scrollBounds(),yearMetrics:{...metrics,count,spacing:camera.timeScale*(layout.height/Math.max(1,layout.yearBounds[1]-layout.yearBounds[0]))*camera.zoom*Math.cos(camera.pitch)},visibleYearBounds:yearWindow(),topYear,windowCount:windowCount(),targetFps:targetFps(),lastDrawMs,camera:{...camera,target:{...camera.target}},projection:'orthographic',width,height,yearBounds:layout.yearBounds,planes:screenPlanes.map(p=>({...p})),positions:projected.map(p=>({id:p.node.id,paperId:p.node.paperId,year:p.node.year,x:p.x,y:p.y,z:p.node.z,depth:p.depth,scale:p.scale,rx:p.rx,ry:p.ry,citations:p.node.citation?.count??null})),annualEdges:layout.annual.slices.map(s=>({year:s.year,edgeIds:(s.edges||[]).map(e=>e.id)})),anchor:anchor?{...anchor}:null,highlightInstanceIds:[...highlightInstanceIds],selectedAssociationYear,visibleAssociationIds:[...new Set(curves.filter(c=>c.kind==='association').map(c=>c.edge.id))],curveCount:curves.length,limbCount:layout.limbs.length,associationCount:associations.length,curves:curves.map(c=>({kind:c.kind,edgeId:c.edge?.id,paperId:c.paperId,year:c.year,alpha:c.alpha,dash:c.dash||[],sourceYear:c.sourceYear,targetYear:c.targetYear,a:c.a,b:c.b,c1:c.c1,c2:c.c2,samples:c.samples,lineWidth:c.lineWidth})),selected,selectedYear};},destroy(){destroyed=true;if(frame!==null)cancelAnimationFrame(frame);observer.disconnect();for(const [name,handler]of Object.entries(listeners))canvas.removeEventListener(name,handler);onHover(null);}};
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={buildTimelinePositions,projectPoint,rotationCenter,yearPlane,yearFog,cubicPoint,bezierFor,ellipseHit,curveHit,createTimeline3D,temporalViewportMetrics,timelineRenderLayers,timelineNodeRadius,PITCH};
  if(typeof window!=='undefined')window.createTimeline3D=createTimeline3D;
})();
