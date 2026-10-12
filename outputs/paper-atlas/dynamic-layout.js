'use strict';
(() => {
  // Work in model coordinates: layout never changes the user's viewport.
  window.createDynamicLayout = ({cy}) => {
    let frame = null, run = null, enabled = false, lastOptions = {};
    const held = new Set();
    const dragged = new Set();
    cy.on('grab', 'node', e => {
      held.add(e.target.id());
    });
    cy.on('drag', 'node', e => {
      if(!enabled||dragged.has(e.target.id()))return;
      dragged.add(e.target.id());
      if(!run)start(lastOptions);
      if(run){run.ticks=Math.min(run.ticks,200);run.started=null;}
    });
    cy.on('free', 'node', e => {
      held.delete(e.target.id());
      if(!dragged.delete(e.target.id()))return;
      const p = run?.byId.get(e.target.id());
      if (p) { Object.assign(p, e.target.position()); p.vx = p.vy = 0; p.pinned = true;
        run.ticks=Math.min(run.ticks,200);run.started=null; }
    });
    function stop() {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null; run = null; enabled = false;
    }
    function start({kind} = {}) {
      stop();
      enabled=true;lastOptions={kind};
      const nodes = cy.nodes().toArray();
      if (!nodes.length) return;
      const points = nodes.map((node, i) => {
        const p = node.position();
        return {node, index:i, id:node.id(), x:Number.isFinite(p.x) ? p.x : Math.cos(i)*40,
          y:Number.isFinite(p.y) ? p.y : Math.sin(i)*40, vx:0, vy:0, fx:0, fy:0,
          radius:Math.max(3, Number(node.width())/2 || 6),
          weight:node.data('lab')===false ? .2 : 1,
          repulsion:node.data('lab')===false ? .7 : .85, semanticStrength:0, degree:0, pinned:false};
      });
      const byId = new Map(points.map(p => [p.id,p]));
      const edges = cy.edges().toArray().map(e => {
        const a=byId.get(e.data('source')), b=byId.get(e.data('target'));
        return {a,b,kind:e.data('kind') || kind || 'relation', score:Number(e.data('score')) || 0,strength:e.data('edgeStrength')};
      }).filter(e => e.a && e.b && e.a !== e.b);
      const ranges = new Map();
      for (const e of edges) {
        const r=ranges.get(e.kind) || [Infinity,-Infinity];
        r[0]=Math.min(r[0],e.score); r[1]=Math.max(r[1],e.score); ranges.set(e.kind,r);
        e.a.degree++; e.b.degree++;
      }
      for (const e of edges) {
        const [min,max]=ranges.get(e.kind);
        // Preserve actual semantic score differences (rather than rounded buckets).
        e.strength=Number.isFinite(e.strength)?Math.max(0,Math.min(1,e.strength)):max>min ? (e.score-min)/(max-min) : .5;
        e.length=e.a.radius+e.b.radius+28+95*(1-e.strength);
        e.pull=2.7*(.004+.012*e.strength)/Math.sqrt(Math.max(1,e.a.degree,e.b.degree));
        if(e.kind==='author_semantic'){e.a.semanticStrength+=e.strength;e.b.semanticStrength+=e.strength;}
      }
      // Bound each author's total spring strength even when all pairs are present.
      for(const e of edges)if(e.kind==='author_semantic')e.pull=.075*e.strength/Math.max(1,e.a.semanticStrength,e.b.semanticStrength);
      const totalWeight=points.reduce((s,p)=>s+p.weight,0);
      const center={x:points.reduce((s,p)=>s+p.x*p.weight,0)/totalWeight,
        y:points.reduce((s,p)=>s+p.y*p.weight,0)/totalWeight};
      const large=points.length>=1000||edges.length>=8000;
      const medium=!large&&(points.length>=400||edges.length>=3000);
      const fps=large?15:medium?30:60;
      run={points,byId,edges,center,ticks:0,started:null,lastUpdate:null,
        interval:1000/fps,steps:large?1:2,maxDuration:large?80000:medium?45000:30000};
      frame=requestAnimationFrame(tick);
    }
    function step(r) {
      const cellSize=90, grid=new Map();
      for (const p of r.points) {
        if (held.has(p.id)) { Object.assign(p,p.node.position()); p.vx=p.vy=0; }
        p.fx=(r.center.x-p.x)*.00012; p.fy=(r.center.y-p.y)*.00012;
        const key=Math.floor(p.x/cellSize)+','+Math.floor(p.y/cellSize);
        const list=grid.get(key) || []; list.push(p); grid.set(key,list);
      }
      // Bounded neighbor samples keep a dense initial pile linear in node count.
      for (let i=0;i<r.points.length;i++) {
        const p=r.points[i], gx=Math.floor(p.x/cellSize), gy=Math.floor(p.y/cellSize);
        for (let ox=-1;ox<=1;ox++) for (let oy=-1;oy<=1;oy++) {
          const list=grid.get((gx+ox)+','+(gy+oy)); if (!list) continue;
          const stride=Math.max(1,Math.ceil(list.length/16));
          for (let j=i%stride;j<list.length;j+=stride) {
            const q=list[j]; if(p===q)continue;
            let dx=p.x-q.x,dy=p.y-q.y,d=Math.hypot(dx,dy);
            if(d<.01) { const angle=(i+1)*2.399963+ q.index*.7;
              dx=Math.cos(angle);dy=Math.sin(angle);d=1; }
            const gap=p.radius+q.radius+14;
            const force=.85*Math.min(3,70/(d*d+50)+Math.max(0,gap-d)*.065);
            p.fx+=dx/d*force*q.weight*q.repulsion; p.fy+=dy/d*force*q.weight*q.repulsion;
          }
        }
      }
      for (const e of r.edges) {
        const dx=e.b.x-e.a.x,dy=e.b.y-e.a.y,d=Math.max(1,Math.hypot(dx,dy));
        const force=Math.max(-2,Math.min(2,(d-e.length)*e.pull));
        // Source weight controls its influence; external papers follow the lab anchors.
        e.a.fx+=dx/d*force*e.b.weight;e.a.fy+=dy/d*force*e.b.weight;
        e.b.fx-=dx/d*force*e.a.weight;e.b.fy-=dy/d*force*e.a.weight;
      }
      let movement=0;
      const cooling=Math.max(.08,1-r.ticks/650);
      for (const p of r.points) {
        if(held.has(p.id)||p.pinned||p.node.locked?.())continue;
        p.vx=(p.vx+p.fx*cooling)*.78;p.vy=(p.vy+p.fy*cooling)*.78;
        const speed=Math.hypot(p.vx,p.vy);
        if(speed>5){p.vx*=5/speed;p.vy*=5/speed;}
        p.x+=p.vx*1.2;p.y+=p.vy*1.2;movement+=Math.hypot(p.vx,p.vy)*1.2;
      }
      r.ticks++; return movement/r.points.length;
    }
    function tick(time) {
      frame=null; const r=run;if(!r)return;
      if(r.started===null)r.started=time;
      if(r.lastUpdate!==null&&time-r.lastUpdate<r.interval-.1){
        frame=requestAnimationFrame(tick);return;
      }
      r.lastUpdate=time;
      const clock=()=>typeof performance!=='undefined'?performance.now():Date.now();
      const started=clock();
      let movement=0;
      for(let i=0;i<r.steps;i++)movement=step(r);
      cy.batch(() => { for(const p of r.points) {
        if(!held.has(p.id)&&!p.pinned&&!p.node.locked?.())p.node.position({x:p.x,y:p.y});
      }});
      // Slow hardware gets more time between updates instead of a catch-up burst.
      const cost=clock()-started;
      r.interval=Math.min(100,Math.max(r.interval,cost*4));
      if((r.ticks>120&&movement<.018&&!held.size)||r.ticks>=3300||time-r.started>=r.maxDuration){run=null;return;}
      frame=requestAnimationFrame(tick);
    }
    return {start,stop};
  };
})();
