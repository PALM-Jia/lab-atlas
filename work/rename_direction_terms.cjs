const fs=require('node:fs');
const dir='outputs/paper-atlas';
for(const name of fs.readdirSync(dir).filter(n=>n.startsWith('workflow')&&/\.(js|html|css)$/.test(n))){
 const p=dir+'/'+name,s=fs.readFileSync(p,'utf8');
 const next=s.replace(/(?<!研究)方向标签/g,'研究方向标签').replace(/(?<!研究)方向画像/g,'研究方向画像');
 if(next!==s){fs.writeFileSync(p,next);console.log(name);}
}
