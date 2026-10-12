window.WORKFLOW_MAP = {
 stages:[
  {id:'import',label:'① 建立清单',mode:'外部查询 · 自动',details:['import']},
  {id:'candidates',label:'② 收集候选',mode:'外部查询 · AI 按需',details:['openalex','semantic','original']},
  {id:'match',label:'③ 确认论文与版本',mode:'本地处理 · 自动',details:['match'],fixed:true},
  {id:'collect',label:'④ 补齐信息',mode:'外部查询 · 自动',details:['collect']},
  {id:'external',label:'⑤ 扩充外部文献',mode:'外部查询 · 自动',details:['external']},
  {id:'adopt',label:'⑥ 采用字段',mode:'本地处理 · AI 按需',details:['adopt'],fixed:true},
  {id:'features',label:'⑦ 生成特征',mode:'本地处理 · 自动',details:['directions','vector','profiles']},
  {id:'output',label:'⑧ 关联与输出',mode:'本地处理 · 自动',details:['output']}
 ],
 tracks:[
  {id:'identity',label:'论文与版本',color:'#687b9a',description:'③固定各来源记录与版本的对应；④按这份对应表读取字段。',stages:['import','openalex','match']},
  {id:'text',label:'标题与摘要',color:'#4386b9',description:'主页标题和各来源文本在⑥确定采用值，再分别生成方向标签、语义向量。没有摘要时可仅使用标题。',stages:['adopt','directions','vector']},
  {id:'authors',label:'作者与人员',color:'#448a79',description:'⑥将论文署名对应到实际人员；共同署名直接生成作者关联，关键词与方向用于汇总作者画像。',stages:['adopt','profiles','output']},
  {id:'keywords',label:'关键词与主题',color:'#bd873d',description:'保存数据库及原始发布页提供的关键词与主题；关键词用于作者画像，数据库主题可直接用于论文关联。',stages:['collect','adopt','profiles']},
  {id:'citations',label:'参考与施引',color:'#8b6db2',description:'④取得引用名单，⑤补外部文献详情，⑥归一文献对应后生成引用边。已有对应标识即可建边，不依赖摘要、语义向量。',stages:['collect','external','output']},
  {id:'evidence',label:'来源证据',color:'#89909c',description:'主页、查询和字段原值随采集保留；检索汇总同时读取原始证据与采用值，不必等待特征或连线计算。',stages:['import','collect','adopt','output']}
 ],
 nodes:[
  ['seed',0,'identity','清单编号','import','fixed'],['candidate',1,'identity','各来源候选','candidates'],['matched',2,'identity','记录与版本','match','fixed'],['record',3,'identity','确认的记录','collect'],
  ['homeText',0,'text','主页标题','import'],['candidateText',1,'text','候选文本','candidates'],['labText',3,'text','标题 / 摘要','collect'],['extText',4,'text','外部文本','external'],['adoptText',5,'text','采用文本','adopt','fixed'],['direction',6,'text','方向标签','directions','',-21],['vector',6,'text','语义向量','vector','',21],['paperOutput',7,'text','论文关联','output'],
  ['homeAuthors',0,'authors','主页署名','import'],['labAuthors',3,'authors','论文署名','collect'],['extAuthors',4,'authors','外部署名','external'],['people',5,'authors','人员与署名','adopt','fixed'],['profile',6,'authors','作者画像','profiles'],['authorOutput',7,'authors','作者关联','output'],
  ['keywords',3,'keywords','关键词 / 主题','collect'],['extTopics',4,'keywords','外部主题','external'],['adoptKeywords',5,'keywords','采用关键词 / 主题','adopt','fixed'],['topicOutput',7,'keywords','论文主题关联','output'],
  ['reference',3,'citations','参考 / 施引名单','collect','fixed'],['external',4,'citations','外部文献集合','external','fixed'],['citationMatch',5,'citations','文献对应','adopt','fixed'],['citationOutput',7,'citations','引用关联','output'],
  ['snapshot',0,'evidence','主页快照','import'],['queries',1,'evidence','查询与核对证据','candidates'],['fields',3,'evidence','来源字段与状态','collect'],['externalEvidence',4,'evidence','外部来源字段','external'],['adoption',5,'evidence','采用值与分歧','adopt'],['summary',7,'evidence','检索汇总','output']
 ].map(([id,stage,track,label,detail,kind,offset])=>({id,stage,track,label,detail,kind,offset:offset||0})),
 edges:[
  ['seed','candidate'],['candidate','matched'],['matched','record'],
  ['homeText','candidateText'],['homeText','adoptText','bypass'],['candidateText','labText'],['record','labText','dependency'],['labText','extText'],['extText','adoptText'],['adoptText','direction'],['adoptText','vector'],['direction','paperOutput'],['vector','paperOutput'],
  ['homeAuthors','labAuthors'],['record','labAuthors','dependency'],['labAuthors','extAuthors'],['extAuthors','people'],['people','profile'],['people','authorOutput','bypass'],['profile','authorOutput'],['direction','profile','dependency'],
  ['record','keywords','dependency'],['keywords','extTopics'],['extTopics','adoptKeywords'],['adoptKeywords','profile','dependency'],['adoptKeywords','topicOutput'],
  ['record','reference','dependency'],['reference','external'],['external','citationMatch'],['citationMatch','citationOutput'],['external','extText','dependency'],['external','extAuthors','dependency'],['external','extTopics','dependency'],
  ['snapshot','queries'],['queries','fields'],['fields','externalEvidence'],['externalEvidence','adoption'],['adoption','summary'],['fields','summary','bypass']
 ].map(([from,to,kind])=>({from,to,kind:kind||'flow'}))
};
