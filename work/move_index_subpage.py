# coding: utf-8
from pathlib import Path
base=Path('outputs/paper-atlas')
p=base/'index.html';s=p.read_text(encoding='utf-8');s=s.replace('<button id="reset" class="quiet">','<a id="paper-index-link" class="quiet" href="papers.html">论文索引 ↗</a><button id="reset" class="quiet">');a=s.index('      <div class="list-head">');b=s.index('    </section>',a);s=s[:a]+s[b:];p.write_text(s,encoding='utf-8')
p=base/'panel-layout.css';s=p.read_text(encoding='utf-8').replace('auto auto minmax(0, 1fr) auto clamp(100px, 22vh, 190px)','auto auto minmax(0, 1fr)');p.write_text(s,encoding='utf-8')
p=base/'app.js';s=p.read_text(encoding='utf-8');a=s.index('  function renderList() {');b=s.index('  function focus(',a);s=s[:a]+'''  function updateIndexLink(){
    const query=new URLSearchParams({search:state.search,topic:state.topic,from:String(state.yearFrom),to:String(state.yearTo),unknown:state.unknownYears?'1':'0',external:state.external?'1':'0',status:state.status,view:state.view,relation:state.relation});
    $('paper-index-link').setAttribute('href','papers.html?'+query.toString());
  }
'''+s[b:];s=s.replace('renderList();','updateIndexLink();');s=s.replace("  $('lab-only').onclick=()=>{state.labOnly=!state.labOnly;updateIndexLink();};\n",'');s=s.replace('hub:false,labOnly:true,selected:null','hub:false,selected:null');s=s.replace('visible=visible.filter(p=>p.lab||connected.has(p.id));','visible=visible.filter(p=>p.lab||connected.has(p.id)||p.id===state.selected);')
s=s.replace("  $('relation').value='coupling';\n  render();", """  const requestedPaper=new URLSearchParams(window.location?.search||'').get('paper');
  if(nodeMap.has(requestedPaper))state.selected=requestedPaper;
  $('relation').value='coupling';
  render();""")
p.write_text(s,encoding='utf-8')
p=Path('work/check_frontend_viewport.cjs');s=p.read_text(encoding='utf-8').replace('console,URL,setTimeout','console,URL,URLSearchParams,setTimeout');p.write_text(s,encoding='utf-8')
