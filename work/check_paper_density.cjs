const fs=require('fs'),assert=require('assert');
const limit=require('../outputs/paper-atlas/paper-density.js');
const papers=Array.from({length:10},(_,i)=>({id:'p'+i,lab:true}));const edges=[];
for(let i=0;i<10;i++)for(let j=i+1;j<10;j++)edges.push({id:i+'-'+j,source:'p'+i,target:'p'+j,score:1});
const limited=limit(papers,edges);assert.equal(limited.stats.top_k,5);assert.equal(limited.stats.threshold,null);assert.equal(limited.edges.length,35);
assert.deepStrictEqual(limit(papers,edges.slice().reverse()).edges,limited.edges,'same-score selection stable');
const star=Array.from({length:9},(_,i)=>({id:'s'+i,source:'p0',target:'p'+(i+1),score:.1}));assert.equal(limit(papers,star).edges.length,9,'incoming choices retain popular node; no score cutoff');
const source=fs.readFileSync('work/check_frontend_viewport.cjs','utf8').split('const labCount=')[0];
const {cy,el,window,detailClick}=new Function('require',source+';return {cy,el,window,detailClick};')(require);
for(const relation of ['citation','author','semantic']){
 el('relation').onchange({target:{value:relation}});assert(cy.edges().every(e=>e.data('evidence').top_k===5));
 const edge=cy.edges().first();if(edge.length){const from=edge.data('source'),to=edge.data('target');detailClick({paper:from});const html=el('detail-content').innerHTML;assert(html.includes('paper-relations'));assert(!/<details[^>]*\bopen\b/.test(html));assert(html.indexOf('关联论文')<html.indexOf('<summary>摘要</summary>'));assert(html.includes('data-edge="'+edge.id()+'" data-paper="'+to+'"'));detailClick({edge:edge.id(),paper:to});assert(cy.getElementById(edge.id()).hasClass('focus'));assert(el('detail-content').innerHTML.includes(window.ATLAS_DATA.nodes.find(p=>p.id===to).title));}
}
cy.destroy();console.log('PASS: top-five paper selection, stable ties and paper evidence navigation');
