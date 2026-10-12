# coding: utf-8
from pathlib import Path
p=Path('work/check_frontend_viewport.cjs');s=p.read_text(encoding='utf-8').replace("assert.equal(el('year-from').min,2010);assert.equal(el('year-to').max,2027);","assert.equal(el('year-from').min,0);assert.equal(el('year-to').max,289);").replace("el(id).value=String(value);","el(id).value=String((value-2010)**2);").replace("el('year-from').value,2024","el('year-from').value,196").replace("el('year-to').value,2024","el('year-to').value,196");s=s.replace("assert.equal(el('year-output').textContent,'−∞ — 2027');", "assert.equal(el('year-output').textContent,'−∞ — 2027');\nassert(el('year-ticks').innerHTML.includes('2023'));\nconst tickPositions=[...el('year-ticks').innerHTML.matchAll(/left:([\\d.]+)%/g)].map(m=>Number(m[1]));\nassert(tickPositions[2]-tickPositions[1]>tickPositions[1]-tickPositions[0],'recent interval wider despite covering fewer years');")
s=s.replace("assert.equal(el('year-output').textContent,'≤2010');", "assert.equal(el('year-output').textContent,'≤2010');\nel('year-to').onkeydown({key:'ArrowRight',preventDefault(){}});assert.equal(el('year-output').textContent,'−∞ — 2011','arrow keys move by calendar year');")
p.write_text(s,encoding='utf-8')
p=Path('work/check_timeline_3d.cjs');s=p.read_text(encoding='utf-8').replace('rotationCenter,yearPlane} = require','rotationCenter,yearPlane,yearFog} = require');s=s.replace("year:2020+i,x:i*10", "year:2027,x:i*10");s=s.replace('const strokes=[],fills=[];', 'const strokes=[],fills=[],fillAlphas=[];').replace('fills.push(this.fillStyle);','fills.push(this.fillStyle);fillAlphas.push(this.globalAlpha);');s=s.replace("graph.setActive(false);assert.equal(queue.length,0);", """assert.equal(yearFog(2000),.18);assert.equal(yearFog(1900),.18);assert.equal(yearFog(2027),1);
assert(yearFog(2015)<yearFog(2020));assert.equal(yearFog(null),1);
strokes.length=0;fillAlphas.length=0;
graph.setData({papers:[{id:'old',year:2000,x:0,y:0,lab:true,match_status:'matched'},{id:'new',year:2027,x:20,y:20,lab:true,match_status:'matched'}],edges:[{id:'fog-edge',source:'old',target:'new'}],yearBounds:[2000,2027],reset:true});flush(550);
const edgeStroke=strokes.find(v=>v.startsWith('rgba(111,132,166,'));assert(Math.abs(Number(edgeStroke.split(',').at(-1).replace(')',''))-.018)<1e-12,'old edge visibly fogged');
assert(fillAlphas.includes(.18)&&fillAlphas.includes(1),'old node fades while recent node remains clear');
graph.setActive(false);assert.equal(queue.length,0);""")
p.write_text(s,encoding='utf-8')

