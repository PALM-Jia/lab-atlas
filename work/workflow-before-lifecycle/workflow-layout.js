/* Geometry only. Stage content and dependencies live in workflow-data.js. */
window.WorkflowLayout = {
 build(data){
  const columnWidth=151, left=120, firstY=124, pitch=82;
  const height=firstY+(data.tracks.length-1)*pitch+60;
  const trackIndex=new Map(data.tracks.map((t,i)=>[t.id,i]));
  const nodes=new Map(data.nodes.map(n=>[n.id,n]));
  const featureOffset={direction:-21,vector:21};
  const point=n=>({x:left+columnWidth*(n.stage+.5),y:firstY+trackIndex.get(n.track)*pitch+(featureOffset[n.id]||0)});
  const vertices=e=>{
   const a=nodes.get(e.from),b=nodes.get(e.to),s=point(a),t=point(b);
   if(e.kind==='direct'){
    const offset=(a.stage===0||b.stage===7)?31:17;
    return [{x:s.x+23,y:s.y},{x:s.x+23,y:s.y+offset},{x:t.x-25,y:s.y+offset},{x:t.x-25,y:t.y}];
   }
   if(s.y!==t.y){const x=s.x===t.x?s.x-68:(s.x+t.x)/2;return [{x,y:s.y},{x,y:t.y}];}
   return [];
  };
  return {columnWidth,left,firstY,pitch,height,width:left+data.stages.length*columnWidth+22,point,vertices};
 }
};
