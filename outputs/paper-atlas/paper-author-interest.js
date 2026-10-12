'use strict';
// Contributions use the audited person identity for each paper signature.
window.createPaperAuthorInterest=({resolveAuthors,affiliations={}})=>{
  const peopleCache=new Map(),institutionCache=new Map();
  function people(p){
    if(!peopleCache.has(p.id))peopleCache.set(p.id,resolveAuthors(p));
    return peopleCache.get(p.id);
  }
  function active(interest){return Object.values(interest).some(value=>value===false);}
  function cared(p,interest){return people(p).filter(a=>!a.excluded_from_network&&interest[a.group]!==false);}
  function keep(p,interest){return !p.lab||!active(interest)||cared(p,interest).length>0;}
  function institutions(p,interest){
    if(!institutionCache.has(p.id)){
      const entries=[];
      for(const row of affiliations[p.id]||[]){
        const signature=(p.author_records||[]).find(a=>a.id===row.id)?.name||row.name;
        if(!(p.authors||[]).includes(signature))continue;
        const person=resolveAuthors({...p,authors:[signature]})[0];
        if(person)entries.push({person,institutions:row.institutions||[]});
      }
      institutionCache.set(p.id,entries);
    }
    const result=new Map();
    for(const row of institutionCache.get(p.id))if(!row.person.excluded_from_network&&interest[row.person.group]!==false)
      for(const inst of row.institutions)result.set(inst.id,inst.name);
    return result;
  }
  function edges(papers,kind,interest){
    const lab=papers.filter(p=>p.lab),result=[];
    const profiles=new Map(lab.map(p=>[p.id,kind==='author'
      ?new Map(cared(p,interest).filter(a=>a.name!=='Yuheng Jia').map(a=>[a.id,a.name]))
      :institutions(p,interest)]));
    for(let i=0;i<lab.length;i++)for(let j=i+1;j<lab.length;j++){
      const a=lab[i],b=lab[j],pa=profiles.get(a.id),pb=profiles.get(b.id);
      const common=[...pa.keys()].filter(id=>pb.has(id)).sort();if(!common.length)continue;
      const [source,target]=[a.id,b.id].sort();
      const evidence=kind==='author'
        ?{person_ids:common,authors:common.map(id=>pa.get(id)),text:'核查后的人员身份相同；只计入关心的共同作者，排除 Yuheng Jia'}
        :{institution_ids:common,institutions:common.map(id=>pa.get(id)),text:'关心的署名作者共享 OpenAlex 发表机构 ID'};
      result.push({id:kind+':'+source+':'+target,source,target,kind,score:common.length,evidence,tentative:false});
    }
    return result;
  }
  return {active,cared,keep,edges};
};
