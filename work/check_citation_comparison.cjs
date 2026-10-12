const fs=require('fs'),assert=require('assert');
const report=JSON.parse(fs.readFileSync('outputs/paper-atlas/citation-comparison.json','utf8'));
assert.equal(report.rows.length,1673);assert.equal(new Set(report.rows.map(r=>r.id)).size,1673);
for(const row of report.rows)for(const key of ['openalex','semantic_scholar','crossref']){const value=row[key];assert(['success','missing','not_requested'].includes(value.status));if(value.status==='success')assert(Number.isInteger(value.count)&&value.count>=0);if(value.status==='missing')assert(value.reason&&value.reason!=='unknown');}
for(const scope of ['lab','external'])for(const key of ['openalex','semantic_scholar','crossref']){const item=report.summary[scope][key];assert.equal(item.success+item.missing+item.not_requested,report.summary[scope].total);}
assert.equal(report.rows.find(r=>r.id==='lab-cafae06c3f4f').semantic_scholar.status,'missing');
let prefix=fs.readFileSync('work/check_frontend_viewport.cjs','utf8').split('const labCount=')[0];
prefix=prefix.replace('const context=vm.createContext',"window.location={search:'?paper=lab-d50fd9c219f7'};const context=vm.createContext");
prefix=prefix.replace("vm.runInContext(fs.readFileSync('outputs/paper-atlas/app.js','utf8'),context);","vm.runInContext(fs.readFileSync('outputs/paper-atlas/citation-counts.js','utf8'),context);vm.runInContext(fs.readFileSync('outputs/paper-atlas/app.js','utf8'),context);");
const app=new Function('require',prefix+'return {cy,el,detailClick,allYears};')(require);
app.el('care-all').onclick();app.allYears();app.detailClick({paper:'lab-d50fd9c219f7'});const details=app.el('detail-content').innerHTML;
for(const label of ['OpenAlex','Semantic Scholar','Crossref','retrieval.html?paper='])assert(details.includes(label));
for(const count of [26,24,21])assert(details.includes('>'+count+'</b>'));
app.cy.destroy();
console.log('PASS: 1673 unique papers, provider accounting 100%, valid counts, version conflict excluded, all three counts rendered in paper details.');


