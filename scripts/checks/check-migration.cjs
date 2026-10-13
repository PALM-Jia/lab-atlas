'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const baseline=JSON.parse(fs.readFileSync(path.join(root,'data/maintenance/migration-baseline.json'),'utf8'));
let checked=0;
for(const [name,expected] of Object.entries(baseline.files)){
 if(name==='relations-full.json')continue; // Removed duplicate: canonical edges reside in data.json.
 const bytes=fs.readFileSync(path.join(root,'data/atlas',name));
 assert.equal(bytes.length,expected.bytes,name+' byte size');
 assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),expected.sha256,name+' exact migrated bytes');checked++;
}
console.log(JSON.stringify({check:'migration-byte-baseline',files:checked,removed_duplicate:'relations-full.json'}));
