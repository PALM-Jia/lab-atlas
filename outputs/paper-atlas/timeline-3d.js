'use strict';
(() => {
  const finite = (v, fallback = 0) => Number.isFinite(Number(v)) ? Number(v) : fallback;
  const extent = values => values.length ? [Math.min(...values), Math.max(...values)] : [0, 1];
  const normalize = (v, bounds, size) => (finite(v) - (bounds[0] + bounds[1]) / 2) * size / Math.max(1, bounds[1] - bounds[0]);
  function buildTimelinePositions(papers, options = {}) {
    const lowerYearBucket=options.lowerYearBucket;
    const bucketYear=year=>Number.isFinite(lowerYearBucket)?Math.max(lowerYearBucket,year):year;
    const years = papers.filter(p => Number.isFinite(p.year) && p.year > 0).map(p => bucketYear(p.year));
    const yearBounds = options.yearBounds || extent(years);
    const coordinateBounds = options.coordinateBounds || {
      x: extent(papers.map(p => finite(p.x))), y: extent(papers.map(p => finite(p.y)))
    };
    const positions = papers.map(p => ({
      id: p.id, paper: p,
      x: Number.isFinite(p.year) && p.year > 0 ? normalize(bucketYear(p.year), yearBounds, 900) : -560,
      y: normalize(p.x, coordinateBounds.x, 520),
      z: normalize(p.y, coordinateBounds.y, 520),
      unknown: !(Number.isFinite(p.year) && p.year > 0)
    }));
    return {positions, yearBounds, coordinateBounds,lowerYearBucket};
  }
  function projectPoint(point, camera, width, height) {
    const yaw = finite(camera.yaw), pitch = finite(camera.pitch);
    const x=finite(point.x)-finite(camera.target?.x),y=finite(point.y)-finite(camera.target?.y),z=finite(point.z)-finite(camera.target?.z);
    const x1 = x * Math.cos(yaw) + z * Math.sin(yaw);
    const z1 = -x * Math.sin(yaw) + z * Math.cos(yaw);
    const y1 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
    const z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
    const distance = Math.max(100, finite(camera.distance, 1800));
    const depth = distance + z2;
    const scale = finite(camera.zoom, 1) * distance / Math.max(60, depth);
    return {x: width / 2 + finite(camera.panX) + x1 * scale,
      y: height / 2 + finite(camera.panY) + y1 * scale, depth, scale, visible: depth > 60};
  }
  function rotationCenter(positions){
    const center={x:0,y:0,z:0};let total=0;
    for(const p of positions){const weight=p.paper?.lab===false?.2:1;total+=weight;for(const axis of ['x','y','z'])center[axis]+=finite(p[axis])*weight;}
    if(total)for(const axis of ['x','y','z'])center[axis]/=total;
    return center;
  }
  function yearPlane(position){
    return !position||position.unknown?[]:[{x:position.x,y:-285,z:-285},{x:position.x,y:285,z:-285},{x:position.x,y:285,z:285},{x:position.x,y:-285,z:285}];
  }
  function yearFog(year,yearBounds,lowerYearBucket=2000){
    if(!Number.isFinite(year)||year<=0)return 1;
    const [min,max]=yearBounds;
    if(max<=min)return 1;
    const t=Math.max(0,Math.min(1,(Math.max(lowerYearBucket,year)-min)/(max-min)));
    return .18+.82*t*t;
  }
  function createTimeline3D({canvas, onSelectNode = () => {}, onSelectEdge = () => {}, onHover = () => {}}) {
    const ctx = canvas.getContext('2d');
    let active = false, frame = null, destroyed = false, width = 1, height = 1;
    let positions = [], edges = [], byId = new Map(), projected = [], selected = null, hoverId = null;
    let bounds = null, fogBounds = [0,1], drag = null, lastDraw = -Infinity, initialFit = true, topicMap = new Map(), edgeFade = 1;
    const camera = {yaw: -.42, pitch: -.22, zoom: 1, panX: 0, panY: 0, distance: 1800,target:{x:0,y:0,z:0}};
    function requestDraw() {
      if (!active || destroyed || frame !== null) return;
      frame = requestAnimationFrame(time => {
        frame = null;
        if (!active || destroyed) return;
        if (drag && time - lastDraw < 1000 / 30) { requestDraw(); return; }
        lastDraw = time; draw();
      });
    }
    function resize() {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, rect.width); height = Math.max(1, rect.height);
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); requestDraw();
    }
    const projection = p => projectPoint(p, camera, width, height);
    function line(a, b, color, thickness = 1) {
      if (!a.visible || !b.visible) return;
      ctx.strokeStyle = color; ctx.lineWidth = thickness;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    function label(point, text, color = '#56657d') {
      const p = projection(point); if (!p.visible) return;
      ctx.font = '13px sans-serif'; ctx.fillStyle = 'rgba(255,255,255,.86)';
      const w = ctx.measureText(text).width;
      ctx.fillRect(p.x - 3, p.y - 14, w + 6, 18);
      ctx.fillStyle = color; ctx.fillText(text, p.x, p.y);
    }
    function drawAxes() {
      if (!bounds) return;
      const origin = {x: -450, y: 285, z: 285};
      line(projection(origin), projection({x:450,y:285,z:285}), '#71839b', 1.6);
      line(projection(origin), projection({x:-450,y:-285,z:285}), '#aeb8c6');
      line(projection(origin), projection({x:-450,y:285,z:-285}), '#aeb8c6');
      label({x:450,y:355,z:285}, '时间 / 年份');
      label({x:-450,y:-305,z:285}, '关联空间 Y');
      label({x:-450,y:285,z:-305}, '关联空间 Z');
      const [min,max] = bounds.yearBounds, span = max-min;
      const tickCount=Math.max(2,Math.min(5,Math.floor(width/150)));
      const ticks=new Set(Array.from({length:tickCount},(_,i)=>Math.round(min+span*i/(tickCount-1))));
      for (const year of [...ticks].sort((a,b)=>a-b)) {
        const x = normalize(year, bounds.yearBounds, 900);
        line(projection({x,y:280,z:285}),projection({x,y:291,z:285}),'#71839b');
        label({x,y:312,z:285},String(year));
      }
      if (positions.some(p=>p.unknown)) {
        line(projection({x:-560,y:-270,z:285}),projection({x:-560,y:270,z:285}),'#b4bcc8');
        label({x:-650,y:375,z:285},'年份未知');
      }
    }
    function draw() {
      ctx.clearRect(0,0,width,height);
      const selectedPosition=byId.get(selected);
      const plane=yearPlane(selectedPosition).map(projection);
      if(plane.length&&plane.every(p=>p.visible)){
        ctx.beginPath();ctx.moveTo(plane[0].x,plane[0].y);for(const p of plane.slice(1))ctx.lineTo(p.x,p.y);ctx.closePath();
        ctx.fillStyle='rgba(89,106,181,0.12)';ctx.fill();
        ctx.strokeStyle='rgba(89,106,181,0.38)';ctx.lineWidth=1;ctx.stroke();
        const year=Math.max(bounds.lowerYearBucket||0,selectedPosition.paper.year);
        label({x:selectedPosition.x,y:-300,z:285},`${year} 年${selectedPosition.paper.year<year?'（含更早）':''}`,'#596ab5');
      }
      drawAxes();
      const selectedEdge = edges.find(e=>e.id===selected);
      const selectedNodes = new Set(selectedEdge ? [selectedEdge.source,selectedEdge.target] : selected ? [selected] : []);
      const neighbors = new Set(selectedNodes);
      if (selected && !selectedEdge) for (const e of edges) {
        if (e.source === selected) neighbors.add(e.target);
        if (e.target === selected) neighbors.add(e.source);
      }
      projected = positions.map(p=>({...projection(p), node:p}));
      const screenMap = new Map(projected.map(p=>[p.node.id,p]));
      for (const e of edges) {
        const a = screenMap.get(e.source), b = screenMap.get(e.target);
        if (!a || !b) continue;
        const highlighted = selectedEdge ? e.id===selectedEdge.id : selected && (e.source===selected || e.target===selected);
        const fog=Math.min(yearFog(a.node.paper.year,fogBounds,bounds.lowerYearBucket),yearFog(b.node.paper.year,fogBounds,bounds.lowerYearBucket));
        const muted=a.node.paper.displayMuted||b.node.paper.displayMuted;
        const strength=Number.isFinite(e.edgeStrength)?e.edgeStrength:1,weightFade=.35+.65*strength;
        const edgeWidth=Number.isFinite(e.edgeWidth)?e.edgeWidth:.7;
        line(a,b,highlighted ? 'rgba(71,91,140,.58)' : muted ? `rgba(160,164,172,${(selected ? .035 : .045)*weightFade*edgeFade*fog})` : selected ? `rgba(126,144,173,${.035*weightFade*edgeFade*fog})` : `rgba(111,132,166,${.10*weightFade*edgeFade*fog})`,highlighted?edgeWidth+1:edgeWidth);
      }
      projected.sort((a,b)=>b.depth-a.depth);
      for (const p of projected) {
        if (!p.visible) continue;
        const paper = p.node.paper, diameter=paper.displaySize??Math.min(50,8+3*Math.log2(1+(Number.isFinite(paper.citations)&&paper.citations>=0?paper.citations:0))), r = Math.max(2,Math.min(25,diameter/2*p.scale));
        p.radius = r;
        if (p.x < -r || p.y < -r || p.x > width+r || p.y > height+r) continue;
        const pending=paper.lab && paper.match_status!=='matched';
        const fog=selectedNodes.has(p.node.id)?1:yearFog(paper.year,fogBounds,bounds.lowerYearBucket);
        ctx.globalAlpha = (selected && !neighbors.has(p.node.id) ? .12 : pending ? .4 : paper.lab ? 1 : .62)*fog*(paper.displayMuted&&!selectedNodes.has(p.node.id)?.28:1);
        ctx.shadowColor = 'rgba(39,59,96,.25)'; ctx.shadowBlur = paper.lab ? 5 : 2;
        const classification=window.ATLAS_PAPER_FIELDS?.papers?.[paper.id];
        ctx.fillStyle = paper.displayColor || (paper.displayMuted ? '#a9adb5' : window.ATLAS_PAPER_FIELDS?.fields?.find(f=>f.id===classification?.primary)?.color || '#969aa4');
        ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();
        ctx.shadowBlur = 0;
        if (pending) {ctx.globalAlpha=(selected&&!neighbors.has(p.node.id)?.12:.8)*fog*(paper.displayMuted&&!selectedNodes.has(p.node.id)?.28:1);ctx.setLineDash([2,2]);ctx.strokeStyle=ctx.fillStyle;ctx.lineWidth=1.2;ctx.stroke();ctx.setLineDash([]);}
        if (selectedNodes.has(p.node.id)) {ctx.globalAlpha=1;ctx.strokeStyle='#253f85';ctx.lineWidth=2;ctx.stroke();}
      }
      ctx.globalAlpha = 1;
      if (!positions.length) {ctx.font='15px sans-serif';ctx.fillStyle='#65738c';ctx.fillText('当前筛选无论文',width/2-55,height/2);}
    }
    function fit() {
      hoverId=null;onHover(null);
      Object.assign(camera,{yaw:-.42,pitch:-.22,zoom:1,panX:0,panY:0,distance:1800});
      // Fit the visible volume, including papers outside the chosen laboratory year range.
      const points = [...positions,{x:-450,y:-305,z:285},{x:475,y:355,z:285},{x:-450,y:285,z:-305}];
      if(positions.some(p=>p.unknown))points.push({x:-650,y:375,z:285});
      let maxRadius = 600;
      camera.target=rotationCenter(positions);
      for (const p of points) maxRadius=Math.max(maxRadius,Math.hypot(p.x-camera.target.x,p.y-camera.target.y,p.z-camera.target.z));
      camera.distance=Math.max(1800,maxRadius*3);
      const projectedFit=points.map(projection);
      const xs=extent(projectedFit.map(p=>p.x-width/2)),ys=extent(projectedFit.map(p=>p.y-height/2));
      camera.zoom=Math.min((width-130)/Math.max(900,2*Math.max(...xs.map(Math.abs))),(height-130)/Math.max(650,2*Math.max(...ys.map(Math.abs))));
      camera.zoom=Math.max(.025,camera.zoom);
      requestDraw();
    }
    function pointAt(event) {const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top};}
    function hitNode(point) {
      for (let i=projected.length-1;i>=0;i--) {
        const p=projected[i]; if(p.visible && Math.hypot(point.x-p.x,point.y-p.y)<=Math.max(8,p.radius||3))return p;
      } return null;
    }
    function hitEdge(point) {
      const screenMap=new Map(projected.map(p=>[p.node.id,p]));let found=null,best=5;
      for(const e of edges){
        const a=screenMap.get(e.source),b=screenMap.get(e.target);if(!a?.visible||!b?.visible)continue;
        const dx=b.x-a.x,dy=b.y-a.y,l=dx*dx+dy*dy;if(!l)continue;
        const t=Math.max(0,Math.min(1,((point.x-a.x)*dx+(point.y-a.y)*dy)/l));
        const d=Math.hypot(point.x-a.x-t*dx,point.y-a.y-t*dy);
        if(d<best){best=d;found=e;}
      }return found;
    }
    function hover(point) {
      const node=hitNode(point),id=node?.node.id||null;
      if (id!==hoverId) {hoverId=id;onHover(node?.node.paper||null,node?{x:node.x,y:node.y}:point);}
      canvas.style.cursor=node?'pointer':'grab';
    }
    const down=e=>{if(!active)return;const p=pointAt(e);drag={...p,startX:p.x,startY:p.y,moved:false,pan:e.shiftKey||e.button===2};canvas.setPointerCapture?.(e.pointerId);hoverId=null;onHover(null);canvas.style.cursor='grabbing';};
    const move=e=>{if(!active)return;const p=pointAt(e);if(!drag){hover(p);return;}const dx=p.x-drag.x,dy=p.y-drag.y;drag.x=p.x;drag.y=p.y;drag.moved ||= Math.hypot(p.x-drag.startX,p.y-drag.startY)>4;if(drag.pan){camera.panX+=dx;camera.panY+=dy;}else{camera.yaw+=dx*.006;camera.pitch=Math.max(-1.5,Math.min(1.5,camera.pitch+dy*.006));}requestDraw();};
    const up=e=>{if(!drag)return;const moved=drag.moved;drag=null;canvas.releasePointerCapture?.(e.pointerId);if(!moved&&e.button!==2){const p=pointAt(e),node=hitNode(p);if(node)onSelectNode(node.node.id);else{const edge=hitEdge(p);if(edge)onSelectEdge(edge);else{selected=null;onSelectNode(null);requestDraw();}}}requestDraw();};
    const leave=()=>{if(!drag){hoverId=null;onHover(null);}};
    const wheel=e=>{if(!active)return;e.preventDefault();zoom(Math.exp(-Math.max(-200,Math.min(200,e.deltaY))*.002));};
    const context=e=>e.preventDefault();
    function zoom(factor){hoverId=null;onHover(null);camera.zoom=Math.max(.025,Math.min(12,camera.zoom*finite(factor,1)));requestDraw();}
    const listeners={pointerdown:down,pointermove:move,pointerup:up,pointercancel:()=>{drag=null;requestDraw();},pointerleave:leave,wheel,contextmenu:context};
    for(const [name,handler] of Object.entries(listeners))canvas.addEventListener(name,handler,{passive:false});
    const observer=new ResizeObserver(resize);observer.observe(canvas);resize();
    return {
      setData({papers=[],edges:nextEdges=[],topics=[],yearBounds,coordinateBounds,lowerYearBucket,reset=false}){
        if(topics.length)topicMap=new Map(topics.map(t=>[t.id,t]));
        if(!bounds || yearBounds || coordinateBounds){
          const built=buildTimelinePositions(papers,{yearBounds:yearBounds||bounds?.yearBounds,coordinateBounds:coordinateBounds||bounds?.coordinateBounds,lowerYearBucket:lowerYearBucket??bounds?.lowerYearBucket});
          bounds={yearBounds:built.yearBounds,coordinateBounds:built.coordinateBounds,lowerYearBucket:built.lowerYearBucket};
        }
        positions=buildTimelinePositions(papers,bounds).positions;byId=new Map(positions.map(p=>[p.id,p]));
        fogBounds=extent(positions.filter(p=>!p.unknown).map(p=>Math.max(bounds.lowerYearBucket??2000,p.paper.year)));
        camera.target=rotationCenter(positions);
        edges=nextEdges.filter(e=>byId.has(e.source)&&byId.has(e.target)&&(e.kind!=='citation'||byId.get(e.source).paper.lab||byId.get(e.target).paper.lab));
        const meanDegree=positions.length?2*edges.length/positions.length:0;
        edgeFade=meanDegree>5?5/meanDegree:1;
        hoverId=null;onHover(null);if(reset)fit();else requestDraw();
      },
      setActive(value){active=!!value;if(active){resize();if(initialFit){initialFit=false;fit();}requestDraw();}else{if(frame!==null)cancelAnimationFrame(frame);frame=null;drag=null;onHover(null);}},
      select(id){selected=id;requestDraw();},zoom,fit,
      destroy(){destroyed=true;if(frame!==null)cancelAnimationFrame(frame);observer.disconnect();for(const [name,handler]of Object.entries(listeners))canvas.removeEventListener(name,handler);onHover(null);}
    };
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={buildTimelinePositions,projectPoint,rotationCenter,yearPlane,yearFog};
  if(typeof window!=='undefined')window.createTimeline3D=createTimeline3D;
})();
