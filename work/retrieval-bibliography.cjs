/* Evidence lists use the full saved collection, independently of graph-node selection. */
const fs=require('node:fs'),path=require('node:path');
module.exports=function({nodes,needed,cache}){
 const bibliography={},best=new Map();
 for(const file of fs.readdirSync(cache).filter(f=>f.endsWith('.json')).sort()){
  let data;try{data=JSON.parse(fs.readFileSync(path.join(cache,file),'utf8'));}catch{continue;}
  const records=Array.isArray(data?.results)?data.results:/^https:\/\/openalex\.org\/W\d+$/.test(data?.id||'')?[data]:[];
  for(const w of records){
   const id=typeof w?.id==='string'&&/^https:\/\/openalex\.org\/W\d+$/.test(w.id)?w.id.split('/').pop():null;
   if(!needed.has(id)||!(w.display_name||w.title))continue;
   const authors=(w.authorships||[]).map(a=>a.author?.display_name).filter(Boolean);
   const venue=w.primary_location?.source?.display_name||w.host_venue?.display_name||'';
   const score=Number(authors.length>0)+Number(Number.isFinite(w.publication_year))+Number(!!venue);
   const previous=best.get(id);
   if(previous&&(previous.score>score||previous.score===score&&(previous.updated||'')>=(w.updated_date||'')))continue;
   best.set(id,{score,updated:w.updated_date||'',entry:{id,title:w.display_name||w.title,authors,venue,year:w.publication_year??null,citations:w.cited_by_count??null,url:w.doi||w.id,source:'OpenAlex',recordUrl:w.id}});
  }
 }
 for(const [id,{entry}] of best)bibliography[id]=entry;
 // Keep the lab identity and previously adopted graph metadata when already present.
 for(const p of nodes){
  const entry={id:p.id,title:p.title,authors:p.authors,venue:p.venue,year:p.year,citations:p.citations??null,url:p.doi||p.openalex||p.links?.[0]||'',source:p.source};
  bibliography[p.id]=entry;if(p.openalex)bibliography[p.openalex.split('/').pop()]=entry;
 }
 return bibliography;
};
