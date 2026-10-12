const fs=require('fs');global.window=global;require('../outputs/paper-atlas/workflow-data.js');
const s=WORKFLOW_STAGES,d=WORKFLOW_MAP;
const edit=(id,values)=>Object.assign(s.find(x=>x.id===id),values);
edit('match',{title:'核对身份与核心字段',summary:'固定实验室论文身份、标题、人员署名和发表情况。',description:'比较来源标识、标题、作者、年份和版本，必要时继续补查；同时完成作者消歧、署名顺序和实验室分类核对。',input:'主页原值、候选身份字段、发布页证据及确认名册。',added:'论文身份与版本对应，以及核对后的标题、人员署名、年份与发表情况。',fixed:'实验室论文的来源 ID、版本、标题、人员身份、署名顺序、分类及年份发表情况；无法确定的内容保留具体疑点。',method:'明确标识、等价名称和已确认身份自动归并；复杂身份、版本或人员问题由 AI 比较来源证据。',note:'正式版优先，人员分类以确认名册为准。②固定核心字段；③采集摘要等其余字段。后续遇到核心差异，返回②重新核对后再固定，不在③或⑤直接改写。'});
edit('collect',{title:'采集其余信息',summary:'复用缓存并补充摘要、关键词、主题、被引数和引用关系。',description:'按②确认的记录和发布页，先复用候选缓存中其余字段，再按缺口读取；标题、人员署名、年份发表使用②固定结果。',input:'②固定的实验室论文记录、核心字段和已返回的其余字段缓存。',added:'摘要、论文关键词、数据库主题、被引次数，以及参考和施引两个方向的引用关系。',fixed:'各来源其余字段原值、引用关系原始记录和取得状态。',note:'各来源独立保留原值、采集时间与失败记录，⑤再采用其余字段。发现核心差异时返回②核对。被引总数、实际取得的施引条目数、其中已匹配详情的条目数分别统计。'});
edit('external',{description:'从实验室引用关系的另一端取得外部论文，去重、核对身份并固定它们自身的标题、人员署名和发表情况；其余字段留到⑤采用。',fixed:'外部论文身份、版本、标题、人员署名、年份发表情况及检索范围；摘要等其余字段保存来源原值。',note:'外部记录与实验室记录分别固定。遇到外部核心差异时返回④核对；不回写实验室核心字段，不递归扩展外部引用，也不建立外部—外部引用边。'});
edit('adopt',{title:'采用其余字段',summary:'采用摘要、关键词、主题、被引数，并归一引用关系。',description:'对③④取得的其余字段比较来源与版本后确定采用值；以已确认的论文身份合并重复引用关系。',input:'②④固定的身份和核心字段，以及③④取得的摘要、关键词、主题、被引数和引用关系原值。',added:'其余字段的来源差异判定和引用关系去重结果。',fixed:'摘要、关键词、主题、被引次数与引用关系记录；各项附带来源原值、采用理由及缺失状态。',method:'规则与已确认对应自动处理；少量实质字段分歧由 AI 比较现有证据。',note:'标题、人员署名、年份发表已在②或④固定。新核心差异返回对应核对阶段处理；⑤不直接修正核心字段。其他字段需要新证据时返回相应采集阶段，每次重新固定都保留来源与理由。'});
edit('directions',{input:'②固定的实验室标题、④固定的外部标题，以及⑤采用的可用摘要。'});
edit('vector',{input:'②④分别固定的论文标题、⑤采用的可用摘要，以及固定模型与文本处理规则。'});
edit('profiles',{input:'②固定的实验室人员 ID、署名顺序，⑤采用的论文关键词与⑥a的方向标签。'});
edit('output',{input:'②④固定的核心字段、⑤采用的其余字段与引用关系，以及⑥生成的特征。'});
d.stages.find(x=>x.id==='locate').label='② 定位与核对';d.stages.find(x=>x.id==='collect').label='③ 采集其余信息';d.stages.find(x=>x.id==='adopt').label='⑤ 采用其余字段';
const track=(id,values)=>Object.assign(d.tracks.find(x=>x.id===id),values);
track('identity',{used:'③只读取确认记录的其余字段；无法确定数据库身份时，已核对的主页核心字段仍在②固定。'});
track('text',{collect:'①取得主页标题；②对照独立来源并固定实验室标题；③采集摘要；④固定外部标题并取得其摘要原值。',fixed:'实验室标题在②、外部标题在④分别固定；各来源摘要在⑤采用。'});
track('authors',{collect:'①保留主页署名；②核对其他来源与实验室名册；④核对外部文献的自身署名。',fixed:'实验室人员身份、署名顺序和分类在②固定；外部人员署名在④固定。',stages:['match','external','profiles','output']});
track('publication',{collect:'①取得主页发表信息；②比较独立来源并固定实验室年份发表；③采集被引数；④固定外部年份发表并取得其被引数。',fixed:'实验室年份发表在②、外部年份发表在④固定；被引次数在⑤采用，保留统计来源和时间。'});
const core=[['title','标题','标题'],['authors','人员署名','人员身份、署名顺序和分类'],['publication','年份发表','年份与发表情况']];
for(const [id,label,long] of core){Object.assign(d.information.find(x=>x.id===id),{sources:[0,1],settle:1,lifecycles:[{scope:'实验室论文',sources:[0,1],settle:1,end:[`实验室${label}`,`②对照各来源并固定实验室论文的${long}；新差异返回②核对。`]},{scope:'外部文献',sources:[3],settle:3,end:[`外部${label}`,`④核对并固定外部论文自身的${long}，不替换实验室结果。`]}],description:`实验室论文的${long}在②对照各来源后固定；外部论文在④单独核对并固定。`,scope:'不同来源先保留各自原值，核对时汇合为对应论文的采用值；③与⑤不直接修改已固定的核心字段。'});}
const art=(id,values)=>Object.assign(d.artifacts.find(x=>x.id===id),values);
art('sourceTitle',{stage:1,label:'候选标题',detail:'openalex',definition:'各候选来源的原始标题及别名，保留各自来源，供②判断版本并采用。'});
art('sourceAuthors',{stage:1,label:'候选署名',detail:'openalex',definition:'各候选来源的署名与顺序，②结合主页和确认名册核对人员身份。'});
art('sourcePublication',{stage:1,label:'候选发表信息',detail:'openalex',definition:'各候选版本的年份、会议期刊和预印状态，②对照来源后采用。'});
art('title',{stage:1,label:'实验室标题',detail:'match',definition:'②核对后固定的实验室论文标题；保持版本对应。后续新差异返回②核对。'});
art('authors',{stage:1,label:'实验室人员署名',detail:'match',definition:'②固定的实验室论文人员 ID、署名顺序与名册分类；同名人员经核对分别处理。'});
art('publication',{stage:1,label:'实验室发表信息',detail:'match',definition:'②固定的实验室论文年份与发表情况，附带版本、来源差异与采用理由。'});
art('identity',{definition:'②论文来源 ID、版本关系和优先版本的判定结果，含已确认对应及未确定原因；核心字段依据此判定采用，未匹配数据库时可固定经核对的主页值。'});
art('external',{definition:'④从实验室引用关系另一端取得并去重的外部论文；分别固定身份、版本、标题、人员署名和年份发表，摘要等其余字段保留来源原值。'});
art('summary',{definition:'分别汇总实验室与外部条目的核心字段、其余字段及附带来源、时间和采用理由；被引总数、已取得施引条目数与已匹配详情数分别展示。'});
d.dependencies=d.dependencies.filter(e=>!(e.from==='identity'&&['sourceTitle','sourceAuthors','sourcePublication'].includes(e.to))&&!(e.from==='external'&&['title','authors','publication'].includes(e.to)));
function edge(from,to,type,explanation){d.dependencies.push({id:from+'--'+to,from,to,type,explanation});}
for(const to of ['sourceTitle','sourceAuthors','sourcePublication'])edge('candidates',to,'required','②按来源保留候选原值，供核心字段核对使用。');
for(const to of ['title','authors','publication'])edge('identity',to,'required','②根据身份与版本判定采用核心字段；未匹配数据库时可采用经核对的主页值，后续差异返回②。');
for(const to of ['directions','vector'])edge('external',to,'optional','追加④已固定的外部论文自身标题作为其文本输入；不替代实验室标题。');
edge('external','appearance','optional','追加外部论文自身的年份发表与人员字段；实验室核心字段保持②结果。');
edge('external','summary','optional','追加外部论文自身的核心字段、来源与获取状态，单独汇总，不替代实验室条目。');
function save(){const line=x=>' '+JSON.stringify(x);fs.writeFileSync('outputs/paper-atlas/workflow-data.js','window.WORKFLOW_STAGES = [\n'+s.map(line).join(',\n')+'\n];\nwindow.WORKFLOW_MAP = {\n stages: [\n'+d.stages.map(line).join(',\n')+'\n ],\n tracks: [\n'+d.tracks.map(line).join(',\n')+'\n ],\n information: [\n'+d.information.map(line).join(',\n')+'\n ],\n artifacts: [\n'+d.artifacts.map(line).join(',\n')+'\n ],\n dependencies: [\n'+d.dependencies.map(line).join(',\n')+'\n ]\n};\n','utf8');}
save();console.log('Core field stages updated: '+d.artifacts.length+' artifacts, '+d.dependencies.length+' edges');
