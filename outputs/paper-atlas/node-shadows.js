'use strict';
// Screen-space shadows stay subtle at every zoom level and never intercept input.
window.installNodeShadows = ({canvas, cy}) => {
  const ctx=canvas.getContext('2d');
  if(!ctx) return;
  let frame=null;
  function draw() {
    frame=null;
    const width=cy.width(),height=cy.height(),ratio=window.devicePixelRatio||1;
    const pixelWidth=Math.round(width*ratio),pixelHeight=Math.round(height*ratio);
    if(canvas.width!==pixelWidth||canvas.height!==pixelHeight){canvas.width=pixelWidth;canvas.height=pixelHeight;}
    ctx.setTransform(ratio,0,0,ratio,0,0);
    ctx.clearRect(0,0,width,height);
    const glowing=[];
    cy.nodes().forEach(n=>{
      if(!n.visible()) return;
      const p=n.renderedPosition(),r=n.renderedWidth()/2;
      if(n.hasClass('hover')) glowing.push({p,r});
      const author=n.data('authorNode');
      const spread=author?5:3,outer=r+spread;
      if(p.x+outer<0||p.x-outer>width||p.y+outer<0||p.y-outer>height) return;
      const y=p.y+(author?2:1.5),alpha=(author ? .24 : .14)*n.effectiveOpacity();
      const gradient=ctx.createRadialGradient(p.x,y,Math.max(0,r-1),p.x,y,outer);
      gradient.addColorStop(0,`rgba(35,45,65,${alpha})`);
      gradient.addColorStop(.45,`rgba(35,45,65,${alpha*.55})`);
      gradient.addColorStop(1,'rgba(35,45,65,0)');
      ctx.fillStyle=gradient;ctx.beginPath();ctx.arc(p.x,y,outer,0,Math.PI*2);
      ctx.arc(p.x,p.y,r,0,Math.PI*2,true);ctx.fill('evenodd');
    });
    // Draw the hover halo last, centered on the node, without changing its border.
    glowing.forEach(({p,r})=>{
      const outer=r+9;
      const gradient=ctx.createRadialGradient(p.x,p.y,Math.max(0,r-1),p.x,p.y,outer);
      gradient.addColorStop(0,'rgba(99,85,168,.5)');
      gradient.addColorStop(.35,'rgba(99,85,168,.25)');
      gradient.addColorStop(1,'rgba(99,85,168,0)');
      ctx.fillStyle=gradient;ctx.beginPath();ctx.arc(p.x,p.y,outer,0,Math.PI*2);
      ctx.arc(p.x,p.y,r,0,Math.PI*2,true);ctx.fill('evenodd');
    });
  }
  const schedule=()=>{if(frame===null)frame=requestAnimationFrame(draw);};
  cy.on('pan zoom position resize add remove style data layoutstop',schedule);
  window.addEventListener('resize',schedule);
  schedule();
};
