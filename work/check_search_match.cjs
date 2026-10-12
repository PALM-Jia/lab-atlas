const assert=require('node:assert/strict');
const match=require('../outputs/paper-atlas/search-match.js');
for(const a of ['semi-supervised','semisupervised','semi supervised','SEMI–SUPERVISED','ｓｅｍｉ－ｓｕｐｅｒｖｉｓｅｄ'])
 for(const b of ['semi-supervised','semisupervised','semi supervised'])assert(match(a,b),`${a} / ${b}`);
assert(match('Deep Semi-Supervised Learning','semisupervised'));
assert(!match('unsupervised learning','semisupervised'));
assert(!match('semi-supervised','semisupervized'));
assert(match('Zhixin Li','zhixinli'));
assert(match('聚类与表示学习','聚类'));
console.log('PASS: hyphens, whitespace, case, fullwidth variants and unrelated-word rejection.');
