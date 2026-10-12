# coding: utf-8
from pathlib import Path
base=Path('outputs/paper-atlas')
p=base/'index.html';s=p.read_text(encoding='utf-8').replace('<script defer src="app.js">','<script defer src="timeline-3d.js"></script><script defer src="app.js">')
s=s.replace('<div id="graph"></div>','<div id="graph"></div><canvas id="timeline-3d" class="hidden" aria-label="三维时间网络：拖动旋转，Shift 拖动平移，滚轮缩放" tabindex="0"></canvas>')
s=s.replace('<label for="layout-mode">布局</label>','<span id="layout-control"><label for="layout-mode">布局</label>').replace('</select><label id="hub-option"','</select></span><label id="hub-option"')
s=s.replace('<span class="graph-help">','<span id="graph-help" class="graph-help">')
p.write_text(s,encoding='utf-8')
p=base/'panel-layout.css';s=p.read_text(encoding='utf-8')+'''
#timeline-3d { position:absolute; inset:0; width:100%; height:100%; z-index:3; touch-action:none; cursor:grab; }
#timeline-3d:active { cursor:grabbing; }
#timeline-3d:focus-visible { outline:2px solid #6575b7; outline-offset:-2px; }
#layout-control { display:contents; }
#layout-control.hidden { display:none; }
.graph-wrap.is-timeline #node-shadows, .graph-wrap.is-timeline #graph { visibility:hidden; }
.graph-wrap.is-timeline .graph-help { font-size:11px; }
''';p.write_text(s,encoding='utf-8')
p=base/'app.js';s=p.read_text(encoding='utf-8')
marker="  window.installPanelLayout({cy});"
s=s.replace(marker,'''  const timeline3D=window.createTimeline3D({canvas:$('timeline-3d'),
    onSelectNode:id=>id?focus(id,false):clearSelection(),
    onSelectEdge:edge=>edgeDetail(edge),
    onHover:(p,point)=>{
      if(!p){hidePreview();return;}
      hoveredNode=null;
      const card=$('node-preview');
      card.innerHTML=`<div class="preview-title">${esc(p.title)}</div><div class="preview-meta">${p.lab?'实验室论文':'外部文献'} · ${esc(p.year??'年份未知')}<br>${esc(p.authors.slice(0,3).join(', ')||'作者待补充')}</div>`;
      card.classList.remove('hidden');
      card.style.left=Math.max(10,Math.min(point.x+16,cy.width()-card.offsetWidth-10))+'px';
      card.style.top=Math.max(10,Math.min(point.y-card.offsetHeight-16,cy.height()-card.offsetHeight-34))+'px';
    }});
  timeline3D.setData({papers:D.nodes,edges:[],topics:D.topics});
''' + marker)
s=s.replace("    e.preventDefault();e.stopImmediatePropagation();", "    if(state.view==='timeline')return;\n    e.preventDefault();e.stopImmediatePropagation();")
start=s.index("    if(state.view==='timeline') {\n      const years=")
end=s.index("    if(state.view==='authors'&&state.layout", start)
s=s[:start]+'''    const timeline=state.view==='timeline';
    $('timeline-3d').classList.toggle('hidden',!timeline);
    $('graph').parentElement.classList.toggle('is-timeline',timeline);
    timeline3D.setActive(timeline);
    if(timeline)timeline3D.setData({papers:visible,edges:graphData,topics:D.topics,reset:resetViewport});
    $('layout-control').classList.toggle('hidden',timeline);
    $('graph-help').textContent=timeline?'拖拽旋转 · Shift 拖拽平移 · 滚轮缩放':'滚轮缩放 · 拖拽平移';
''' +s[end:]
s=s.replace("    state.selected=id; const n=", "    state.selected=id; if(state.view==='timeline')timeline3D.select(id); const n=")
s=s.replace("if(pan)cy.animate", "if(pan&&state.view!=='timeline')cy.animate")
s=s.replace("  function edgeDetail(e) {\n", "  function edgeDetail(e) {\n    if(state.view==='timeline')timeline3D.select(e.id);\n")
s=s.replace("function clearSelection(){state.selected=null;", "function clearSelection(){state.selected=null;timeline3D.select(null);")
s=s.replace("$('fit').onclick=()=>cy.fit(undefined,65);", "$('fit').onclick=()=>state.view==='timeline'?timeline3D.fit():cy.fit(undefined,65);")
s=s.replace("$('zoom-in').onclick=()=>cy.zoom", "$('zoom-in').onclick=()=>state.view==='timeline'?timeline3D.zoom(1.4):cy.zoom")
s=s.replace("$('zoom-out').onclick=()=>cy.zoom", "$('zoom-out').onclick=()=>state.view==='timeline'?timeline3D.zoom(1/1.4):cy.zoom")
p.write_text(s,encoding='utf-8')
