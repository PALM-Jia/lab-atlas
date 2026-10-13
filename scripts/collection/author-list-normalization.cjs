// Equivalence is scoped to one verified paper; author order remains significant.
const norm=s=>String(s).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,'');
const words=s=>String(s).replace(/\s*\(\d+\)\s*$/,'').replace(/,/g,' ').normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[];
const corrections={'lab-bc765488bcf7':{'jingwnag':'jingwang'},'lab-1f9013eb2f8b':{'xinyinzhang':'xinyingzhang'}};
module.exports=(paper,list)=>{
 const anchors=paper.authors||[],out=[];
 for(let i=0;i<list.length;i++){
  let name=list[i];if(String(name).includes(','))name=String(name).split(',').reverse().join(' ');let key=norm(name);const fragments=anchors.find(a=>norm(a)===norm(name+(list[i+1]||'')));
  if(fragments){out.push(norm(fragments));i++;continue;}
  key=corrections[paper.id]?.[key]||key;
  const candidates=anchors.filter(a=>{
   if(norm(a)===key)return true;
   const aw=words(a),nw=words(name);
   if(norm(aw.join(''))===norm(nw.join('')))return true;
   if(aw.length===nw.length&&aw.length>=2&&aw.every((x,j)=>x===nw[nw.length-1-j]))return true;
   return aw.length===nw.length&&aw.length>=2&&aw.at(-1)===nw.at(-1)&&aw.every((x,j)=>x===nw[j]||nw[j].length===1&&x.startsWith(nw[j])||x.length===1&&nw[j].startsWith(x));
  });
  out.push(candidates.length===1?norm(candidates[0]):key);
 }
 return out.join('|');
};
