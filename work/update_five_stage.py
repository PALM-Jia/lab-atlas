from pathlib import Path
p=Path('outputs/paper-atlas/workflow-flow-data.js');s=p.read_text(encoding='utf-8')
s=s.replace("label:'补充采集',description:'按②已经确认的来源 ID 或发布页读取摘要、关键词、主题、被引数及引用关系；先复用已取得的缓存，仅补字段缺口。核心字段提供记录线索，不重新用这些文字重复搜索；发现核心差异时返回②核对。'", "label:'采集并核定',description:'按②确认的记录复用缓存、补齐缺口，核定实验室论文的摘要、关键词、主题、采用被引数及参考、施引记录。未取得的信息和未收齐的记录保留具体状态，无需等待外部文献采集。'")
s=s.replace('用参考、施引记录中的论文标识查找外部文献，沿用实验室论文的字段核对规则，仅扩展一层引用邻域。核心字段在④核定，其余字段在⑤采用。','根据③的参考、施引记录查找外部文献，按同一套规则确定其信息；补全两份记录的论文身份、版本和详情，合并重复条目。仅扩展一层，不把名单条目数当作数据库被引总数。').replace("label:'外部文献查找核对'","label:'采集外部文献'").replace('③和⑤不直接改写','后续采集不直接改写')
s=s.replace("node(final,f.row,4,'left',0,'最终'+f.label,'⑤比较已缓存和后续补充的来源值后采用；两路都没有取得时保留缺失，不要求两路同时有值。'+f.detail,'final');", "node(final,f.row,2,'right',0,(f.row==='counts'?'采用':'最终')+f.label,'③比较缓存与补充来源后确定采用值，未取得的信息保留缺失。'+f.detail,'final');")
s=s.replace('③补充采集的结果与已有值一起在⑤核对采用，省略逐个来源的中间节点。','③补充采集后与已有值共同核定，不等待外部文献采集。').replace('可用缓存值进入⑤字段采用；已有值充分时无须补采。','③核对已有缓存值；已有值充分时无须补采。')
a=s.index(" node('reference-list'");b=s.index(" node('directions'",a)
s=s[:a]+''' node('reference-list','references',2,'right',0,'参考记录','③核定实验室论文引用的文献记录及获取状态，外部身份和详情在④补全。','final');
 node('citing-list','references',2,'right',1,'施引记录','③核定引用实验室论文的文献记录及获取状态；未收齐时如实记录，与数据库被引总数分别保存。','final');
 for(const [id,label,lane] of [['reference-list','参考记录',0],['citing-list','施引记录',1]]){
  edge('collect',id,'value','③采集并核定该方向的记录，保留来源和名单获取状态。');
  edge(id,'external','query','用名单中的外部论文标识确定检索范围，两个方向的重复论文只查询一次。');
  node(id+'-resolved','references',3,'right',lane,label+'（补全）','④核对外部论文后补全该名单的身份、版本和详情，合并重复记录；未取得详情的原始条目仍保留。','final');
  edge(id,id+'-resolved','value','在③记录上补充身份和详情，校正错误对应并去重。');
  edge('external',id+'-resolved','value','用外部论文查找核对结果修正、补全该方向的记录。');
 }
 node('external-info','references',3,'right',2,'外部文献信息','④按与实验室论文相同的规则确定外部论文信息；仅扩展一层引用邻域，不逐字段展开。','final');
 flow.nodes.at(-1).info='identity';
 edge('external','external-info','value','④确定外部论文自身信息，用于详情和后续特征计算。');
''' +s[b:]
s=s.replace("5,'middle',0", "4,'right',0").replace('⑥','⑤')
s=s.replace(" processes: [", " processes: [\n  {id:'features',stage:4,row:'directions',lane:0,label:'生成特征',description:'标题和可用摘要用于方向标签与语义向量；核定署名结合关键词或方向标签生成作者画像。缺摘要可采用仅标题向量；特征保留实际输入与规则。'},")
s=s.replace("})(window.WORKFLOW_FLOW);", " for(const id of ['lab-title','lab-abstract','lab-authors','lab-keywords'])edge(id,'features','query','使用已核定的文本、署名或关键词生成特征；具体必需与可选输入见数据依赖图。');\n for(const id of ['directions','vector','profiles'])edge('features',id,'value','⑤生成特征，保留输入、规则或模型版本及支撑论文。');\n})(window.WORKFLOW_FLOW);")
p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/workflow.html');s=p.read_text(encoding='utf-8');a=s.index('<noscript>');b=s.index('</noscript>',a);s=s[:a]+'<noscript>①建立清单 → ②定位与核对 → ③确定实验室信息 → ④采集外部与补全记录 → ⑤生成特征。'+s[b:];s=s.replace('查找与核对线索','处理所需信息');p.write_text(s,encoding='utf-8')
p=Path('outputs/paper-atlas/workflow-layout.js');s=p.read_text(encoding='utf-8').replace('const offsets={candidates:', 'const offsets={references:-22,citingRecords:22,citationMap:-22,citingMap:22,candidates:');p.write_text(s,encoding='utf-8')
