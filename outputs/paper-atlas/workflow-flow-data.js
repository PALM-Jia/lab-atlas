/* Acquisition milestones. Detailed computational inputs live in WORKFLOW_MAP. */
window.WORKFLOW_FLOW = {
 rows:[
  {id:'basic',label:'基本信息',info:'identity',height:172,description:'标题、署名与发表情况共同用于核对论文身份和版本，在同一次核对中确定。确认标识与版本是下一次精确查询的入口。'},
  {id:'content',label:'内容与主题',info:'abstract',height:130,description:'摘要、数据库关键词、数据库主题在③按确认记录采集。三者分别保存：摘要是正文概述，关键词描述具体内容，数据库主题是来源给出的分类。'},
  {id:'citations',label:'引用与统计',info:'references',height:138,description:'被引次数是来源报告的统计值；引用文献和被引记录是两个查询方向取得的条目。④为已有条目补充外部身份和详情，条目数不替代被引总数。'},
  {id:'paperfeatures',label:'文献特征',info:'directions',height:120,description:'每篇论文用自己的标题与可用摘要形成受控关键词、研究领域和语义向量，保存标注审核及模型输入。'},
  {id:'profiles',label:'作者画像',info:'profiles',height:120,description:'按实验室署名论文形成关键词覆盖率画像，以全部有效跨论文对的相似度形成作者语义关联。'}
 ],
 processes:[
  {id:'locate',stage:1,slot:0,row:'basic',offset:65,label:'多源检索\n与核对',description:'并行检索 OpenAlex、Semantic Scholar，按需核对原始发布页。比较标题、作者及发表信息，确定论文身份、版本和核心字段；保留判断依据，以确认标识与版本进入详情采集。'},
  {id:'collect',stage:2,slot:0,row:'content',offset:65,label:'按标识采集\n文献详情',description:'按确认标识与版本读取 OpenAlex 主记录，Semantic Scholar 和原始发布页按字段缺口补充。此处采集并确定摘要、关键词、主题、被引统计及两份引用记录，分别保存来源和缺失状态。'},
  {id:'external',stage:3,slot:0,row:'citations',offset:67,label:'采集外部文献\n并补全记录',description:'以引用文献和被引记录为输入，合并外部标识并去重，只采集一层外部论文信息。核对条目的身份与版本、补充详情并去重，输出外部文献信息及补全后的两份记录；未匹配条目保留。被引数仍采用来源统计，不按记录数量重算。'},
  {id:'features',stage:4,slot:1,row:'paperfeatures',offset:60,label:'生成文献特征',description:'DeepSeek V4.1 Flash 逐篇标注受控关键词，Sol 审核并确定实验室论文主领域；外部主领域由标题与采用关键词映射。本地官方 SPECTER2 生成语义向量。'},
  {id:'profile',stage:4,slot:1,row:'profiles',offset:60,label:'聚合作者画像',description:'关键词画像计算受控词项的加权论文覆盖率，确认的空标注计入分母。语义关联按全部有效跨论文对的相似度加权平均。默认一作权重 1、其他署名 0.2；仅看第一作者时，导师一作、学生二作按学生一作计入。'}
 ],nodes:[],edges:[]
};
(function(f){
 const node=(id,row,stage,slot,offset,label,info,description)=>f.nodes.push({id,row,stage,slot,offset,label,info,description,kind:stage===0?'source':'final',settled:stage!==0});
 const edge=(from,to,type,description)=>f.edges.push({from,to,type,description});
 const core=[
  ['title',22,'标题','论文标题','结合署名和版本关系核对标题变体，确定采用标题，保留其他标题与来源。'],
  ['authors',65,'署名','作者名字','核对作者顺序与人员身份，保留采用署名、来源原值及同名区分依据。'],
  ['publication',108,'发表情况','论文录用情况','结合版本证据核对年份、会议期刊与预印状态，统一等价名称并保留真实差异。']
 ];
 for(const [id,offset,home,final,detail] of core){
  node('home-'+id,'basic',0,0,offset,home,id,'实验室主页的原始字段，保留出处与采集时间；与其他两项基本信息共同提供身份核对线索。');
  node('lab-'+id,'basic',1,1,offset,final,id,'②多源核对后确定。'+detail);
  edge('home-'+id,'locate','query','标题、署名、发表情况共同参与同一次身份与版本核对；每项仍独立保存。');
  edge('locate','lab-'+id,'value',detail);
 }
 node('identity','basic',1,1,150,'确认标识与版本','identity','与实验室条目对应的 OpenAlex ID、Semantic Scholar paperId、DOI、arXiv ID 或原始发布页，以及确认的版本关系。关联核对所用的基本信息证据；③按这些定位结果查询。');
 edge('locate','identity','value','确定来源标识和版本对应，保留核对依据。');
 edge('identity','collect','query','按确认标识与版本采集详情，OpenAlex 为主、Semantic Scholar 补缺，并复用已有记录缓存。');
 const fields=[
  ['abstract','content',22,'摘要','摘要可用时提供完整文本；未取得时保存缺失状态。'],
  ['keywords','content',65,'数据库关键词','保存来源给出的关键词及分数，与数据库主题分别记录。'],
  ['topics','content',108,'数据库主题','保存 OpenAlex 研究主题及其分数，作为来源分类保存。'],
  ['counts','citations',22,'被引数','保存来源报告的被引总数、来源和统计时点；不按已取得的施引名单长度重算。']
 ];
 for(const [id,row,offset,label,desc] of fields){node('lab-'+id,row,2,1,offset,label,id,'③按确认标识精准采集后确定。'+desc);edge('collect','lab-'+id,'value','从③的详情查询结果确定该字段，保存来源、采用理由和获取状态。');}
 for(const [id,label,offset] of [['reference-list','引用文献',67],['citing-list','被引记录',112]]){
  node(id,'citations',2,1,offset,label,'references',id==='reference-list'?'实验室论文所引用的文献条目及来源、收集范围。':'引用实验室论文的文献条目及来源、收集范围；与来源报告的被引总数分别保存。');
  Object.assign(f.nodes.at(-1),{kind:'intermediate',settled:false});
  node(id+'-resolved','citations',3,1,offset,label+'（补全后）','references','用外部论文信息核对已有条目的身份和版本、补充详情并去重。保留未匹配条目及记录的获取范围。');
  edge('collect',id,'value','③确定本次取得的记录和获取状态。');
  edge(id,'external','query','从该方向已取得的条目提取外部标识，与另一方向合并去重后查询。');
  edge('external',id+'-resolved','value','外部查找与核对结果结合原有条目，补充身份、版本及详情并去重，形成补全后的记录。');
 }
 node('external-info','citations',3,1,22,'外部文献信息','identity','外部论文的确认身份及可取得的自身信息。用于补全引用文献、被引记录；生成外部论文特征时使用该论文自己的文本。');
 edge('external','external-info','value','按外部标识查询并核对，确定外部论文信息及缺失状态。');
 for(const [id,row,offset,label,info,desc,process] of [
  ['directions','paperfeatures',22,'研究领域','directions','六类粗粒度分类，以主领域决定节点颜色和筛选。实验室论文由 Sol 按标题与可用摘要确定；外部论文按标题及已采用关键词映射。','features'],
  ['controlled-keywords','paperfeatures',60,'论文关键词','controlledKeywords','从 49 项受控词表中逐篇标注，DeepSeek V4.1 Flash 读取论文自身标题与可用摘要，Sol 审核后采用。','features'],
  ['vector','paperfeatures',98,'语义向量','vector','本地官方 SPECTER2 读取论文自身标题与可用摘要，无摘要时仅用标题；保留模型版本、输入及截断记录。DOI 与 arXiv 标识不是输入条件。','features'],
  ['keyword-profile','profiles',41,'关键词画像','profiles','关键词分数为当前筛选内实验室署名论文的加权覆盖率；确认的空标注计入分母，排除条目不计入。','profile'],
  ['semantic-evidence','profiles',79,'语义关联依据','profiles','全部有效跨论文对的语义相似度按双方署名权重乘积加权平均；排除同篇自比，每位作者保留最相近的 5 位。','profile']
 ]){node(id,row,4,2,offset,label,info,desc);edge(process,id,'value','保存结果所用输入、署名权重与支撑论文。');}
 const inputs=[
  ['feature-title','paperfeatures',22,'论文标题','title',['lab-title','external-info'],'features','每篇论文自己的核定标题，用于受控关键词、研究领域及语义向量。'],
  ['feature-abstract','paperfeatures',60,'摘要','abstract',['lab-abstract','external-info'],'features','摘要可用时与该论文标题一同输入；没有摘要时仅使用标题。'],
  ['profile-authors','profiles',22,'作者名字','authors',['lab-authors'],'profile','按已确认署名与顺序确定画像归属和论文贡献。'],
  ['profile-keywords','profiles',60,'论文关键词','controlledKeywords',['controlled-keywords'],'profile','逐篇采用的受控关键词按署名贡献形成覆盖率画像。'],
  ['profile-vectors','profiles',98,'语义向量','vector',['vector'],'profile','实验室论文的本地向量提供跨论文对相似度，按署名贡献形成作者语义关联。']
 ];
 for(const [id,row,offset,label,info,sourceIds,process,description] of inputs){
  node(id,row,4,0,offset,label,info,description);
  Object.assign(f.nodes.at(-1),{kind:'reference',sourceIds});
  edge(id,process,'query',description);
 }
})(window.WORKFLOW_FLOW);
