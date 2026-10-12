const fs=require('fs'),assert=require('assert');
const source=fs.readFileSync('work/check_frontend_viewport.cjs','utf8').split('const labCount=')[0];
const {cy,el,views,window}=new Function('require',source+';return {cy,el,views,window};')(require);
const counts=(id,attr)=>new Map([...el(id).innerHTML.matchAll(new RegExp('data-'+attr+'="([^"]+)"[\\s\\S]*?（(\\d+)）','g'))].map(m=>[m[1],Number(m[2])]));
const labs=window.ATLAS_DATA.nodes.filter(p=>p.lab&&p.year>=2023&&p.year<=2027);
const helper=window.createPaperAuthorInterest({resolveAuthors:window.resolveAtlasPaperAuthors,affiliations:window.ATLAS_AUTHOR_AFFILIATIONS});
const papers=labs.filter(p=>helper.keep(p,{current:true,graduated:true,other:false}));
for(const t of window.ATLAS_DATA.topics)assert.equal(counts('topics','category').get(t.id),papers.filter(p=>p.tags.includes(t.id)).length);
const interestBefore=counts('paper-author-interest','care');
el('care-all').onclick();assert.deepStrictEqual(counts('paper-author-interest','care'),interestBefore,'counts ignore their own care selection');
views[1].onclick();const before=counts('topics','category');
for(const [id,num] of before){const set=new Set();for(const p of labs)for(const a of window.resolveAtlasPaperAuthors(p))if(!a.excluded_from_network&&a.name!=='Yuheng Jia'&&a.group===id)set.add(a.id);assert.equal(num,set.size,'author counts deduplicate audited identities');}
el('topics').click({target:{closest:()=>({dataset:{category:'current'}})}});assert.deepStrictEqual(counts('topics','category'),before,'muting authors retains facet counts');
el('search').oninput({target:{value:'this-query-matches-no-paper-982'}});
setTimeout(()=>{for(const n of counts('topics','category').values())assert.equal(n,0,'search updates counts');cy.destroy();console.log('PASS: direction paper counts, deduplicated author counts, own-state independence and search updates.');},300);
