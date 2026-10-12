const fs=require('fs'),vm=require('vm');const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync('outputs/paper-atlas/workflow-data.js','utf8'),c);const m=c.window.WORKFLOW_MAP,s=c.window.WORKFLOW_STAGES;
for(const e of m.dependencies.filter(e=>e.to==='external')){e.type='alternative';e.group='external-scope';e.explanation='至少一个方向需提供可查询的外部标识；参考和施引记录共同定义外部范围，合并重复标识后采集。';}
m.artifacts.find(a=>a.id==='identity').definition='经多源核对确认的论文标识与版本对应，关联已核对的主页和候选核心证据。②据这些证据确定标题、署名和发表情况；③只使用确认标识与版本精确采集详情。';
for(const e of m.dependencies.filter(e=>e.from==='identity'&&['title','authors','publication'].includes(e.to)))e.explanation='依据已确认身份和版本所关联的主页与候选核心证据，在②确定采用值，并保留来源原值和采用理由。';
fs.writeFileSync('outputs/paper-atlas/workflow-data.js','window.WORKFLOW_STAGES = '+JSON.stringify(s,null,2)+';\nwindow.WORKFLOW_MAP = '+JSON.stringify(m,null,2)+';\n');
