# coding: utf-8
from pathlib import Path
p=Path('outputs/paper-atlas/panel-layout.css');s=p.read_text(encoding='utf-8').replace('auto auto minmax(0, 1fr) auto 80px','auto auto minmax(0, 1fr)').replace('.explorer > .paper-list { height: auto; min-height: 0; overflow: auto; overscroll-behavior: contain; }\n','');p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/app.js');s=p.read_text(encoding='utf-8');s=s.replace("  const requestedPaper=new URLSearchParams(window.location?.search||'').get('paper');\n  if(nodeMap.has(requestedPaper))state.selected=requestedPaper;\n  $('relation').value='coupling';", """  const incoming=new URLSearchParams(window.location?.search||'');
  const requestedPaper=incoming.get('paper');
  if(nodeMap.has(requestedPaper))state.selected=requestedPaper;
  else {
    for(const key of ['search','topic','status'])if(incoming.has(key))state[key]=incoming.get(key);
    if(['papers','authors','timeline'].includes(incoming.get('view')))state.view=incoming.get('view');
    if(['citation','coupling','cocitation','author','institution','semantic','topic','series'].includes(incoming.get('relation')))state.relation=incoming.get('relation');
    for(const [key,param] of [['yearFrom','from'],['yearTo','to']])if(incoming.has(param)&&Number.isFinite(Number(incoming.get(param))))state[key]=Math.max(2010,Math.min(2027,Math.round(Number(incoming.get(param)))));
    state.yearFrom=Math.min(state.yearFrom,state.yearTo);
    for(const [key,param] of [['external','external'],['unknownYears','unknown']])if(incoming.has(param))state[key]=incoming.get(param)!=='0';
  }
  $('relation').value=state.relation;$('search').value=state.search;$('status').value=state.status;
  $('external').checked=state.external;$('year-unknown').checked=state.unknownYears;
  updateYearControls();updateTopics();""");p.write_text(s,encoding='utf-8')
