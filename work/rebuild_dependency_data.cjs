const fs=require('node:fs');
const root='outputs/paper-atlas/';
const ids=['import','locate','collect','external','features'];
const titles=['建立主页清单','多源检索与一致化','按标识精确采集','采集外部与补全关系','生成特征与作者画像'];
const stageText=[
 ['读取主页条目，建立实验室论文清单。','为每个主页条目建立稳定编号，保存标题、署名、年份发表和链接原值。','实验室论文主页。','主页条目、标题、署名、年份发表、原始链接。','实验室论文范围与主页原值。','实验室主页。','自动解析并记录出处。','各字段保存出处与采集时间；请求失败单独记录。'],
 ['并行检索多源候选，确认身份、版本及核心字段。','OpenAlex 与 Semantic Scholar 并行检索候选，按需核对原始发布页；比较标题、署名、发表情况和版本证据后固定核心结果。','主页标题、署名、发表、链接和已确认人员名册。','候选核心证据、来源标识与版本对应。','论文身份、确认标识与版本、标题、人员署名及年份发表。','OpenAlex 与 Semantic Scholar 并行；原始发布页按需核对。','规则处理明确匹配；AI 按需比较身份、版本或人员歧义。','只向③传递确认标识与版本；摘要、关键词、主题、被引数由③精确采集。核心差异返回②核对。'],
 ['以确认标识与版本精确采集其余字段和两份引用记录。','仅以②确认的标识与版本为入口，以 OpenAlex 为主源；Semantic Scholar 和原始发布页按字段缺口补充，并记录采用依据、缺失与列表取得范围。','②确认的论文标识与版本。','摘要、关键词、数据库主题、来源被引数、参考记录、施引记录及获取状态。','上述字段的采用值和本次取得的两份引用记录。','OpenAlex 主源；其他来源按字段补缺。','按确认标识查询、来源规则采用和请求重试。','被引总数、已取得施引条目数与已匹配详情数分别统计；没有确认标识的条目保留缺失状态。'],
 ['采集外部论文信息，分别补全参考与施引记录。','从③已取得的两份记录提取外部标识，取得外部论文自身信息；分别补充端点身份与详情、归一和去重，保留未匹配项。','③已取得的参考记录、施引记录及端点标识。','外部身份、标题、署名、发表、摘要、关键词、主题、被引数及端点匹配结果。','外部信息及状态、分别补全的参考记录与施引记录。','OpenAlex 按标识采集；其他来源按字段补缺。','标识核对、字段采用、端点匹配与去重。','补全已有条目详情不代表名单全量；不改③被引总数，不递归采集外部引用。'],
 ['分别生成实验室与外部论文特征，聚合实验室作者画像。','每篇论文仅以自身标题及可用摘要生成方向标签和向量；仅按实验室论文已确认的人员署名，聚合关键词与方向画像。','②实验室标题署名、③实验室摘要关键词、④外部自身文本以及规则模型。','实验室与外部各自的方向标签、语义向量；实验室作者关键词画像与方向画像。','特征输入、规则模型版本、画像及支撑实验室论文。','本地计算。','固定规则模型与署名贡献权重。','每篇论文标题必需、摘要可选；外部论文不参与实验室作者画像。一作权重 1、其他署名 0.2；Yuheng Jia 一作时按第二作者计一作。']
];
const stages=ids.map((id,i)=>{const s=stageText[i];return {id,n:['①','②','③','④','⑤'][i],group:i===0?'import':i===4?'features':'retrieval',title:titles[i],mode:i===4?'local':'remote',...(i>0&&i<4?{checkpoint:true}:{}),...(i===1?{ai:true}:{}),summary:s[0],description:s[1],input:s[2],added:s[3],fixed:s[4],source:s[5],method:s[6],note:s[7]};});
const tracks=[
 ['identity','论文身份与版本','#687b9a','主页线索、候选核心证据、来源标识与版本','②并行多源检索，核对身份与版本；④确定外部身份。','②固定实验室确认标识和版本；④固定外部对应。','③仅按确认标识与版本查询。'],
 ['text','标题与摘要','#4386b9','主页标题、确认标题、摘要','②固定实验室标题；③取得实验室摘要；④取得外部自身文本。','核心标题在②固定，摘要在③采用；外部文本在④独立采用。','每篇论文以自身标题及可用摘要生成特征。'],
 ['authors','作者与人员','#448a79','署名顺序、人员对应、实验室名册分类','②核对实验室署名与名册；④取得外部署名。','②固定实验室署名顺序及人员身份。','仅实验室署名论文贡献作者画像。'],
 ['keywords','关键词与主题','#bd873d','关键词分数、数据库主题分数','③按确认标识采集；④独立采集外部字段。','实验室值在③采用，外部值在④采用。','实验室关键词贡献作者画像；主题与推断方向分开保存。'],
 ['publication','发表与被引','#ac6f77','年份发表、来源被引总数与统计时点','②固定年份发表；③取得被引数；④独立取得外部发表与被引数。','实验室发表在②固定，被引数在③采用。','被引总数与已取得及已匹配施引条目数分别统计。'],
 ['citations','引用关系','#8b6db2','参考记录、施引记录、端点标识、获取状态','③分别取得两份记录；④按端点标识采集外部信息。','④分别补全已有条目的身份详情并去重。','保留未匹配项；补全不代表名单全量，不改③被引总数。'],
 ['labFeatures','实验室论文特征','#4386b9','实验室论文方向标签、语义向量','⑤使用实验室论文自身文本。','记录输入与规则模型版本。','方向标签与实验室署名共同贡献方向画像。'],
 ['externalFeatures','外部论文特征','#7b8798','外部论文方向标签、语义向量','⑤使用④取得的外部论文自身文本。','独立保存每篇外部论文的特征。','外部特征不参与实验室作者画像。']
].map(([id,label,color,fields,collect,fixed,used])=>({id,label,color,fields,collect,fixed,used,stages:ids.filter((_,i)=>i>0)}));
const infoSpecs=[['identity','identity','论文身份与版本对应',1],['title','text','标题',1],['authors','authors','作者与人员',1],['publication','publication','年份与发表情况',1],['abstract','text','摘要',2],['keywords','keywords','论文关键词',2],['topics','keywords','数据库主题',2],['counts','publication','被引次数',2],['references','citations','引用关系',3],['directions','labFeatures','方向标签',4],['vector','labFeatures','语义向量',4],['profiles','authors','作者画像',4]];
const information=infoSpecs.map(([id,track,name,settle])=>{
 const derived=settle===4;
 const description=id==='identity'?'②以并行多源核心证据确认身份和版本，④独立核对外部身份。':id==='references'?'③分别保存已取得的参考与施引记录；④分别补全端点身份和详情，保留未匹配项。':id==='profiles'?'⑤仅按实验室论文的确认署名聚合关键词画像与方向画像。':derived?'⑤使用每篇论文自身标题和可用摘要，分别生成实验室与外部论文特征。':`实验室${name}在${settle===1?'②核对固定':'③按确认标识与版本采集采用'}，外部${name}在④独立采集采用。`;
 const scope=id==='counts'?'来源被引总数、已取得施引条目数和已匹配详情数互不替代；④不改③统计。':id==='references'?'补全已有记录不代表名单全量取得；不递归采集外部引用。':id==='profiles'?'实验室署名必需；缺关键词的论文不贡献关键词画像。外部论文不贡献画像。':derived?'标题必需，摘要可选；实验室与外部论文使用各自文本，保留规则模型版本。':'保存来源原值、确认依据、缺失和获取状态。';
 const item={id,track,name,sources:derived?[4]:[settle],settle,description,scope,...(derived?{derived:true}:{})};
 if(!derived){
  item.lifecycles=id==='references'?[{scope:'参考记录',sources:[2,3],settle:3,branches:[{stage:2,label:'参考记录',description:'③取得的实验室论文参考条目及获取状态。'}],end:['参考记录与详情','④补全已有参考条目的身份详情，保留未匹配项。']},{scope:'施引记录',sources:[2,3],settle:3,branches:[{stage:2,label:'施引记录',description:'③取得的施引条目及获取状态。'}],end:['施引记录与详情','④补全已有施引条目详情，不改③被引总数。']}]:[{scope:'实验室论文',sources:[settle],settle,branches:[{stage:settle,label:settle===1?'候选核心证据':'确认标识与版本',description:settle===1?'②并行多源检索并按需核对原始发布页，仅比较身份版本及核心字段。':'③仅以确认标识与版本查询，OpenAlex 为主源，其他来源按字段补缺。'}],end:[`实验室${name}`,description]},{scope:'外部论文',sources:[3],settle:3,branches:[{stage:3,label:'外部自身信息',description:'④按引用记录端点标识取得外部论文自身信息。'}],end:[`外部${name}`,'④独立采用外部自身字段，保留缺失和获取状态。']}];
 }
 return item;
});
const artifacts=[];
const a=(id,info,stage,label,definition,track)=>artifacts.push({id,info,stage,label,detail:ids[stage],definition,...(track?{track}:{})});
a('homeTitle','title',0,'主页标题','主页标题原值与出处，供候选检索及核心核对。');
a('homeAuthors','authors',0,'主页署名','主页署名顺序与出处，供身份及人员核对。');
a('homePublication','publication',0,'主页发表','主页年份发表与出处，供版本及核心核对。');
a('candidates','identity',1,'多源候选','OpenAlex 与 Semantic Scholar 并行检索所得身份、版本及标题署名发表证据；按需附原始发布页证据。');
a('identity','identity',1,'确认标识与版本','②固定的论文身份、来源标识及版本对应；无法确认时记录具体疑点，不进入③精确采集。');
a('title','title',1,'实验室标题','②依据已确认身份版本和多源核心证据固定的标题。');
a('authors','authors',1,'实验室署名','②固定的人员对应、署名顺序与名册分类。');
a('publication','publication',1,'实验室发表','②固定的年份、会刊与版本状态。');
a('abstract','abstract',2,'实验室摘要','③以确认标识版本查询得到的摘要采用值、出处及缺失状态。');
a('keywords','keywords',2,'实验室关键词','③精确采集的关键词、分数、采用依据和缺失状态。');
a('topics','topics',2,'实验室主题','③精确采集的数据库主题及分数，与推断方向独立。');
a('counts','counts',2,'实验室被引数','③采用的来源被引总数及统计时点；④不改此值。');
a('references','references',2,'参考记录','③实际取得的参考条目、端点标识和获取范围；不保证名单全量。');
a('citingRecords','references',2,'施引记录','③实际取得的施引条目、端点标识和获取范围，与来源被引总数分开。');
a('external','identity',3,'外部论文信息','④按两份已取得记录的端点标识核对外部身份，采集其自身标题署名发表、摘要、关键词、主题及被引数。');
a('citationMap','references',3,'参考记录与详情','④分别补全已取得参考条目的端点身份和详情、去重；保留未匹配项及获取范围。');
a('citingMap','references',3,'施引记录与详情','④分别补全已取得施引条目的端点身份和详情、去重；保留未匹配项，不改③被引总数。');
a('directions','directions',4,'实验室方向标签','⑤从实验室论文自身标题及可用摘要生成方向标签。','labFeatures');
a('vector','vector',4,'实验室语义向量','⑤从实验室论文自身标题及可用摘要计算语义向量。','labFeatures');
a('externalDirections','directions',4,'外部方向标签','⑤从外部论文自身标题及可用摘要生成方向标签，不贡献实验室作者画像。','externalFeatures');
a('externalVector','vector',4,'外部语义向量','⑤从外部论文自身标题及可用摘要计算向量，不使用实验室文本。','externalFeatures');
a('keywordProfile','profiles',4,'作者关键词画像','仅聚合实验室署名论文的关键词分数，保存支撑论文与署名权重。');
a('directionProfile','profiles',4,'作者方向画像','仅聚合实验室署名论文的方向标签，保存支撑论文与署名权重。');
const dependencies=[];
const e=(from,to,type,explanation)=>dependencies.push({id:from+'--'+to,from,to,type,explanation});
e('homeTitle','candidates','required','必需：主页标题为并行多源候选检索提供起点。');
e('homeAuthors','candidates','optional','可选：主页署名可缩小候选范围并支持人员核对。');
e('homePublication','candidates','optional','可选：主页年份发表可辅助身份与版本核对。');
e('candidates','identity','required','必需：候选核心证据用于确认论文身份、来源标识与版本；疑点保留。');
for(const id of ['title','authors','publication'])e('identity',id,'required','必需：核心字段须对应②确认的论文身份与版本，并基于已核对的多源证据固定。');
for(const id of ['abstract','keywords','topics','counts','references','citingRecords'])e('identity',id,'required','必需：③仅以②确认标识与版本精确查询；OpenAlex 为主源，其他来源按字段缺口补充，缺失与取得范围随字段保存。');
for(const id of ['references','citingRecords'])e(id,'external','optional','可选：本方向已取得条目提供外部端点标识；两方向合并确定查询范围，至少有一条可确认标识才查询对应外部论文。');
e('references','citationMap','required','必需：以③已取得参考记录为基础补全详情并去重；保留原条目与获取范围，不代表名单全量。');
e('citingRecords','citingMap','required','必需：以③已取得施引记录为基础补全详情并去重；保留原条目与获取范围，不改③被引总数。');
e('external','citationMap','optional','可选：已匹配外部身份与详情补入参考条目；未匹配条目保留。');
e('external','citingMap','optional','可选：已匹配外部身份与详情补入施引条目；未匹配条目保留，不重算被引总数。');
for(const id of ['directions','vector']){e('title',id,'required','必需：实验室论文自身确认标题作为该论文特征输入。');e('abstract',id,'optional','可选：实验室论文自身摘要可用时一并输入；缺摘要时使用标题。');}
for(const id of ['externalDirections','externalVector'])e('external',id,'required','必需：使用外部论文自身确认标题；自身摘要为可选文本，没有标题时不生成该论文特征。');
e('authors','keywordProfile','required','必需：按实验室论文的确认人员署名与顺序确定画像归属和贡献权重。');
e('keywords','keywordProfile','required','必需：实验室论文关键词与分数贡献关键词画像；缺关键词条目不贡献该画像。');
e('authors','directionProfile','required','必需：作者方向画像按实验室署名论文归属与贡献权重聚合。');
e('directions','directionProfile','required','必需：仅实验室论文自身方向标签贡献作者方向画像；外部特征不参与。');
const map={stages:stages.map((s,i)=>({id:s.id,label:s.n+' '+s.title,mode:i===4?'本地计算 · 自动':i===1?'并行查询＋核对 · AI 按需':'外部查询 · 自动',details:[s.id],...(s.checkpoint?{fixed:true}:{})})),tracks,information,artifacts,dependencies};
fs.writeFileSync(root+'workflow-data.js','window.WORKFLOW_STAGES = '+JSON.stringify(stages,null,2)+';\nwindow.WORKFLOW_MAP = '+JSON.stringify(map,null,2)+';\n');
