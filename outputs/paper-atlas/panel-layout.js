(function () {
  'use strict';
  window.installPanelLayout = function ({ cy }) {
    const workspace = document.getElementById('workspace');
    const sidebarButton = document.getElementById('toggle-sidebar');
    const detailsButton = document.getElementById('toggle-details');
    const graph = document.getElementById('graph');
    if (!workspace || !sidebarButton || !detailsButton || !graph) return;
    const narrow = window.matchMedia('(max-width: 900px)');
    let resizeFrame = 0;
    const controls = [
      { button: sidebarButton, panel: 'sidebar', label: '筛选', className: 'sidebar-collapsed' },
      { button: detailsButton, panel: 'details', label: '详情', className: 'details-collapsed' }
    ];
    const widths={};let saved={};
    try{saved=JSON.parse(window.localStorage?.getItem('paper-atlas-panels-v1')||'{}')||{};}catch{}
    for(const control of controls){
      const width=saved.widths?.[control.panel];
      if(Number.isFinite(width)&&width>=(control.panel==='sidebar'?180:240)&&width<=640){
        widths[control.panel]=width;workspace.style.setProperty('--'+control.panel+'-size',width+'px');
      }
      if(saved.collapsed?.[control.panel]===true)workspace.classList.add(control.className);
    }
    function savePanels(){
      try{window.localStorage?.setItem('paper-atlas-panels-v1',JSON.stringify({widths,collapsed:Object.fromEntries(controls.map(c=>[c.panel,workspace.classList.contains(c.className)]))}));}catch{}
    }
    function updateButtons() {
      controls.forEach(({ button, panel, label, className }) => {
        const expanded = !workspace.classList.contains(className);
        button.classList.add('panel-toggle');
        button.setAttribute('aria-controls', panel);
        button.setAttribute('aria-expanded', String(expanded));
        button.textContent = panel === 'sidebar' ? (expanded ? '‹' : '›') : (expanded ? '›' : '‹');
        button.title = (expanded ? '收起' : '展开') + label + '栏';
        button.setAttribute('aria-label', button.title);
      });
    }
    function scheduleResize() {
      if (resizeFrame) return;
      resizeFrame = window.requestAnimationFrame(() => {
        resizeFrame = 0;
        if (cy.destroyed && cy.destroyed()) return;
        const zoom = cy.zoom();
        const pan = { ...cy.pan() };
        cy.resize();
        cy.viewport({ zoom, pan });
      });
    }
    controls.forEach((control,index) => {
      const handle=document.createElement('div');
      handle.className='panel-resizer '+control.panel+'-resizer';
      handle.tabIndex=0;
      handle.setAttribute('role','separator');
      handle.setAttribute('aria-orientation','vertical');
      handle.setAttribute('aria-label','调整'+control.label+'栏宽度');
      handle.setAttribute('aria-controls',control.panel);
      workspace.appendChild(handle);
      const panel=document.getElementById(control.panel);
      const minimum=index===0?180:240;
      function setWidth(value){
        const other=controls[1-index];
        const otherWidth=workspace.classList.contains(other.className)?0:document.getElementById(other.panel).getBoundingClientRect().width;
        const maximum=Math.max(minimum,Math.min(640,workspace.clientWidth-otherWidth-280));
        const width=Math.round(Math.max(minimum,Math.min(maximum,value)));
        workspace.style.setProperty('--'+control.panel+'-size',width+'px');
        widths[control.panel]=width;savePanels();
        handle.setAttribute('aria-valuemin',minimum);
        handle.setAttribute('aria-valuemax',maximum);
        handle.setAttribute('aria-valuenow',width);
        scheduleResize();
      }
      let drag=null;
      handle.addEventListener('pointerdown',event=>{
        if(event.button!==0||narrow.matches)return;
        event.preventDefault();
        drag={id:event.pointerId,x:event.clientX,width:panel.getBoundingClientRect().width};
        handle.setPointerCapture(event.pointerId);
        workspace.classList.add('panel-resizing');
      });
      handle.addEventListener('pointermove',event=>{
        if(!drag||drag.id!==event.pointerId)return;
        setWidth(drag.width+(event.clientX-drag.x)*(index===0?1:-1));
      });
      function endDrag(){drag=null;workspace.classList.remove('panel-resizing');}
      handle.addEventListener('pointerup',endDrag);
      handle.addEventListener('pointercancel',endDrag);
      handle.addEventListener('lostpointercapture',endDrag);
      handle.addEventListener('keydown',event=>{
        if(narrow.matches||!['ArrowLeft','ArrowRight'].includes(event.key))return;
        event.preventDefault();
        setWidth(panel.getBoundingClientRect().width+(event.key==='ArrowRight'?20:-20)*(index===0?1:-1));
      });
    });
    controls.forEach(control => control.button.addEventListener('click', () => {
      const opening = workspace.classList.contains(control.className);
      if (narrow.matches && opening) {
        controls.forEach(other => {
          if (other !== control) workspace.classList.add(other.className);
        });
      }
      workspace.classList.toggle(control.className);
      updateButtons();
      scheduleResize();
      savePanels();
    }));
    function collapseNarrowPanels() {
      if (narrow.matches) controls.forEach(control => workspace.classList.add(control.className));
      updateButtons();
      scheduleResize();
    }
    workspace.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !narrow.matches) return;
      const activePanel = controls.find(control => document.getElementById(control.panel).contains(document.activeElement));
      controls.forEach(control => workspace.classList.add(control.className));
      updateButtons();
      if (activePanel) activePanel.button.focus();
      savePanels();
    });
    if (narrow.addEventListener) narrow.addEventListener('change', collapseNarrowPanels);
    else narrow.addListener(collapseNarrowPanels);
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(scheduleResize);
      observer.observe(graph);
    } else window.addEventListener('resize', scheduleResize);
    collapseNarrowPanels();
  };
})();
