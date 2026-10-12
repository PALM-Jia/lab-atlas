(() => {
  'use strict';
  const D=window.ATLAS_DATA,$=id=>document.getElementById(id),topics=new Map(D.topics.map(t=>[t.id,t]));
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol);}catch{return false;}};
  const params=new URLSearchParams(location.search),year=value=>Math.max(2010,Math.min(2027,Number.isFinite(Number(value))?Number(value):2010));
  const defaults={search:'',topic:'',from:2023,to:2027,unknown:true,external:false,status:''};
  const state={...defaults,search:params.get('search')||'',topic:topics.has(params.get('topic'))?params.get('topic'):'',from:params.has('from')?year(params.get('from')):2023,to:params.has('to')?year(params.get('to')):2027,unknown:params.get('unknown')!=='0',external:params.get('external')==='1',status:['matched','unmatched','title'].includes(params.get('status'))?params.get('status'):''};
  if(state.from>state.to)state.from=state.to;
  const returnParams=new URLSearchParams(params);returnParams.delete('paper');const preserved=new URLSearchParams();for(const k of ['view','relation','authorRelation','authorGroup','topicModes','groupModes','authorInterest'])if(params.has(k))preserved.set(k,params.get(k));
  function query(paper){const q=new URLSearchParams(preserved);for(const k of ['search','topic','status'])if(state[k])q.set(k,state[k]);q.set('from',state.from);q.set('to',state.to);q.set('unknown',state.unknown?'1':'0');q.set('external',state.external?'1':'0');if(paper)q.set('paper',paper);return q;}
  function matches(p){
    if(!state.external&&!p.lab)return false;
    if(state.topic&&!(p.tags||[]).includes(state.topic))return false;
    if(p.year==null?!state.unknown:Math.max(2010,p.year)<state.from||p.year>state.to)return false;
    if(state.status==='matched'&&p.match_status!=='matched')return false;
    if(state.status==='unmatched'&&(!p.lab||p.match_status==='matched'))return false;
    if(state.status==='title'&&((p.authors||[]).length||p.abstract))return false;
    return !state.search||window.atlasSearchMatch([p.title,...p.authors||[],...(p.tags||[]).map(t=>topics.get(t)?.name||t),...(p.keywords||[]).flatMap(k=>[k.name,...(topics.get(k.id)?.aliases||[])])].join(' '),state.search);
  }
  function row(p){const links=[...new Set(p.links||[])].filter(safeURL);const badge=p.lab?(p.match_status==='matched'?'已匹配 OpenAlex':!(p.authors||[]).length&&!p.abstract?'仅标题':'未匹配 OpenAlex'):'外部文献';return `<article class="index-paper"><div class="index-paper-heading"><h3>${esc(p.title)}</h3><span class="badge ${p.lab&&p.match_status!=='matched'?'pending':''}">${badge}</span></div><p class="index-paper-meta">${esc(p.year??'年份未知')} · ${esc(p.venue||p.publication_status||'发表来源未取得')}<br>${esc((p.authors||[]).join(', ')||'作者未取得')}</p><div class="index-paper-tags">${(p.tags||[]).map(t=>`<span class="pill" title="${esc((p.keywords||[]).find(k=>k.id===t)?.exact_quote||'')}">${esc(topics.get(t)?.name||t)}</span>`).join('')}</div><div class="index-paper-actions"><a href="index.html?${esc(new URLSearchParams({paper:p.id}).toString())}">在网络中查看 ↗</a>${links.map((url,i)=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${i?'其他来源':'论文来源'} ↗</a>`).join('')}</div></article>`;}
  function render(){const papers=D.nodes.filter(matches).sort((a,b)=>(b.year??-Infinity)-(a.year??-Infinity)||Number(b.lab)-Number(a.lab)||a.title.localeCompare(b.title));const lab=papers.filter(p=>p.lab).length;$('index-count').textContent=`${papers.length} 篇 · 实验室 ${lab} · 外部 ${papers.length-lab}`;$('index-list').innerHTML=papers.length?papers.map(row).join(''):'<p class="index-empty">无匹配论文。</p>';$('return-network').href='index.html'+(returnParams.size?'?'+returnParams.toString():'');history.replaceState(null,'','papers.html?'+query().toString());}
  function sync(){for(const k of ['search','topic','from','to','status'])$('index-'+k).value=state[k];for(const k of ['unknown','external'])$('index-'+k).checked=state[k];}
  $('index-topic').innerHTML='<option value="">全部关键词</option>'+D.topics.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join('');
  const years=Array.from({length:18},(_,i)=>i+2010).map(y=>`<option value="${y}">${y===2010?'−∞':y}</option>`).join('');$('index-from').innerHTML=years;$('index-to').innerHTML=years;
  for(const k of ['search','topic','from','to','status','unknown','external'])$('index-'+k).addEventListener(k==='search'?'input':'change',()=>{state[k]=['unknown','external'].includes(k)?$('index-'+k).checked:['from','to'].includes(k)?year($('index-'+k).value):$('index-'+k).value;if(state.from>state.to){if(k==='from')state.to=state.from;else state.from=state.to;}sync();render();});
  $('index-reset').addEventListener('click',()=>{Object.assign(state,defaults);sync();render();});sync();render();
})();
