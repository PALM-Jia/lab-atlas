window.WORKFLOW_FLOW={
  "rows": [
    {
      "id": "basic",
      "label": "基本信息",
      "info": "identity",
      "height": 172,
      "description": "主页标题、署名、发表情况怎样通过检索与规则核对，变成采用的论文标题、作者名字、论文录用情况和确认标识与版本。"
    },
    {
      "id": "content",
      "label": "内容与主题",
      "info": "abstract",
      "height": 130,
      "description": "按确认标识执行的精确详情查询怎样提供合格摘要、数据库关键词和数据库主题。"
    },
    {
      "id": "citations",
      "label": "引用与统计",
      "info": "references",
      "height": 138,
      "description": "被引数、引用文献和被引记录怎样分别取得；外部文献补全怎样形成完整的一层外部文献信息与补全后的双向关系列表。"
    },
    {
      "id": "paperfeatures",
      "label": "文献特征",
      "info": "directions",
      "height": 120,
      "description": "已核对的论文标题和合格摘要怎样生成研究领域、受控论文关键词和本地 SPECTER2 语义向量。"
    },
    {
      "id": "profiles",
      "label": "作者画像",
      "info": "profiles",
      "height": 120,
      "description": "逐篇作者名字怎样归一到实验室人员实体，并结合论文关键词和语义向量聚合出关键词画像与语义关联依据。"
    }
  ],
  "processes": [
    {
      "id": "locate",
      "stage": 1,
      "slot": 0,
      "row": "basic",
      "offset": 65,
      "label": "检索与规则核对",
      "description": "以主页 DOI、arXiv 标识、标题限定搜索、完整标题搜索和有限标题变体建立 OpenAlex 候选；仅使用纯身份字段联合检验标题词汇、作者交集、年份、规范化载体、非论文类型排除与正式版优先条件，输出采用的论文标题、作者名字、录用情况及确认的 work ID 与版本。"
    },
    {
      "id": "collect",
      "stage": 2,
      "slot": 0,
      "row": "content",
      "offset": 65,
      "label": "按标识采集文献详情",
      "description": "按阶段二确认的 OpenAlex work ID 重新发起精确查询与被引分页查询；检验摘要自然语言有效性，分别保存主记录被引数、查询接口总数与双向引用名单，并执行身份漂移检查，输出合格摘要、数据库关键词、数据库主题、被引数、引用文献和被引记录。"
    },
    {
      "id": "external",
      "stage": 3,
      "slot": 0,
      "row": "citations",
      "offset": 67,
      "label": "采集外部文献并补全记录",
      "description": "汇集实验室论文主动引用的作品与引用实验室论文的作品，剔除实验室自身论文后，按先批量、后逐个补漏的方式查询一层唯一外部 ID；处理 canonical ID 重定向合并，筛选连接至少两篇不同实验室论文的网络节点，输出外部文献信息与补全后的引用、被引记录。"
    },
    {
      "id": "features",
      "stage": 4,
      "slot": 1,
      "row": "paperfeatures",
      "offset": 60,
      "label": "生成文献特征",
      "description": "读取已核对的论文标题和合格摘要（无摘要时仅用标题），通过固定版本的本地 SPECTER2 生成 L2 归一化语义向量；基于版本化的受控关键词词表抽取带连续原文证据的论文关键词（或复用符合严苛一致性条件的旧标注），并按版本化规则映射研究领域。"
    },
    {
      "id": "profile",
      "stage": 4,
      "slot": 1,
      "row": "profiles",
      "offset": 60,
      "label": "聚合作者画像",
      "description": "依据 OpenAlex author ID、有效 ORCID、合著结构、机构、署名顺序和硬性同名分离约束将逐篇作者署名归一到实验室人员实体；按一作 1.0、其他 0.2（导师一作学生二作时学生按 1.0）加权归一化已完成标注论文的关键词与语义特征，输出关键词画像与语义关联依据。"
    }
  ],
  "nodes": [
    {
      "id": "home-title",
      "row": "basic",
      "stage": 0,
      "slot": 0,
      "offset": 22,
      "label": "标题",
      "info": "title",
      "kind": "source",
      "settled": false,
      "description": "从实验室主页论文段落直接提取的原始标题文本。Unicode NFKC、大小写、标点、连字符和空白规范化仅用于识别主页内重复展示和构造检索词，原始标题字符串原样保留。"
    },
    {
      "id": "lab-title",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 22,
      "label": "论文标题",
      "info": "title",
      "kind": "final",
      "settled": true,
      "description": "通过身份核对后正式采用的论文标题。排版与固定拼写差异可归一，涉及研究任务、方法或对象的实质性词义变化需额外证据；未确认身份的条目继续保留主页标题。"
    },
    {
      "id": "home-authors",
      "row": "basic",
      "stage": 0,
      "slot": 0,
      "offset": 65,
      "label": "署名",
      "info": "authors",
      "kind": "source",
      "settled": false,
      "description": "主页条目记载的原始作者姓名字符串与署名顺序。它用于与 OpenAlex 候选比对作者交集，当数据库缺少作者名单时不会被空值覆盖。"
    },
    {
      "id": "lab-authors",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 65,
      "label": "作者名字",
      "info": "authors",
      "kind": "final",
      "settled": true,
      "description": "身份确认后提取的逐篇作者署名（occurrence），包含作者顺序、规范化姓名、OpenAlex author ID、ORCID、机构和名单候选。逐篇署名与实验室人员实体分开保存。"
    },
    {
      "id": "home-publication",
      "row": "basic",
      "stage": 0,
      "slot": 0,
      "offset": 108,
      "label": "发表情况",
      "info": "publication",
      "kind": "source",
      "settled": false,
      "description": "主页记载的年份、会议简称或期刊名称、预印本状态及 DOI/arXiv 链接。载体名称经规范化后用于候选比对，主页原始描述持续保留。"
    },
    {
      "id": "lab-publication",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 108,
      "label": "论文录用情况",
      "info": "publication",
      "kind": "final",
      "settled": true,
      "description": "核对确认后的发表年份、规范化会议或期刊载体、论文类型与版本状态。主页原始发表描述与 OpenAlex 采用值同时保留。"
    },
    {
      "id": "identity",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 150,
      "label": "确认标识与版本",
      "info": "identity",
      "kind": "final",
      "settled": true,
      "description": "唯一锁定的 OpenAlex work ID、DOI、正式版或预印本状态及版本判断依据。同作品多版本在满足标题家族、作者顺序与载体兼容时优先采用正式版，作为精确详情查询的唯一入口。"
    },
    {
      "id": "lab-abstract",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 22,
      "label": "摘要",
      "info": "abstract",
      "kind": "final",
      "settled": true,
      "description": "阶段三按确认 work ID 重新精确查询取得的论文摘要。需通过固定规则过滤会议元信息、网页提示语、错误页面和重复字段；无效摘要标为 `invalid` 并保留原始响应，不进入特征计算。"
    },
    {
      "id": "lab-keywords",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 65,
      "label": "数据库关键词",
      "info": "keywords",
      "kind": "final",
      "settled": true,
      "description": "精确详情查询返回的 OpenAlex 原生 `keywords` 字段及分数。保留数据库原始来源值，与阶段五基于 版本化的受控关键词词表生成的“论文关键词”分开管理。"
    },
    {
      "id": "lab-topics",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 108,
      "label": "数据库主题",
      "info": "topics",
      "kind": "final",
      "settled": true,
      "description": "精确详情查询返回的 OpenAlex 原生 `topics` 学科主题分类。作为数据库事实字段保存，用于展示与对照，不直接替代受控关键词或派生研究领域。"
    },
    {
      "id": "lab-counts",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 22,
      "label": "被引数",
      "info": "counts",
      "kind": "final",
      "settled": true,
      "description": "同时保存 OpenAlex 主记录的 `cited_by_count`、被引查询接口报告的总数、年度被引数（`counts_by_year`）、查询时间与完整性状态。优先采用被引查询接口报告总数，不用被引名单长度替代被引数。"
    },
    {
      "id": "reference-list",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 67,
      "label": "引用文献",
      "info": "references",
      "kind": "intermediate",
      "settled": false,
      "description": "精确详情中 `referenced_works` 返回的该论文主动引用的作品 ID 列表。分别记录正常取得、明确空列表、查询失败或身份未确定状态，交由阶段四补全详情。"
    },
    {
      "id": "reference-list-resolved",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 67,
      "label": "引用文献（补全后）",
      "info": "references",
      "kind": "final",
      "settled": true,
      "description": "主动引用文献列表经过批量查询、遗漏单查和 canonical ID 重定向合并后的完整记录集合。查不到详情的 ID 仍保留请求状态与失败原因。"
    },
    {
      "id": "citing-list",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 112,
      "label": "被引记录",
      "info": "references",
      "kind": "intermediate",
      "settled": false,
      "description": "通过被引查询接口获取的引用该论文的作品 ID 列表。独立保存查询路径、接口报告总数、已取得名单与分页截断状态（`partial`）。"
    },
    {
      "id": "citing-list-resolved",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 112,
      "label": "被引记录（补全后）",
      "info": "references",
      "kind": "final",
      "settled": true,
      "description": "施引文献列表经过 canonical ID 去重和详情补查后的完整记录集合。完整关系名单与前端网络节点筛选结果分开保存。"
    },
    {
      "id": "external-info",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 22,
      "label": "外部文献信息",
      "info": "identity",
      "kind": "final",
      "settled": true,
      "description": "一层引用与被引邻域中所有唯一外部作品的详情记录及网络入选集合。完整外部记录全部保留；进入网络的节点必须与至少两篇不同实验室论文存在直接引用或被引关系。"
    },
    {
      "id": "directions",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 22,
      "label": "研究领域",
      "info": "directions",
      "kind": "final",
      "settled": true,
      "description": "由受控关键词和版本化映射规则派生生成的粗粒度研究领域标签，用于图谱节点染色与检索筛选，不修改底层数据库主题事实。"
    },
    {
      "id": "controlled-keywords",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 60,
      "label": "论文关键词",
      "info": "controlledKeywords",
      "kind": "final",
      "settled": true,
      "description": "基于版本化的受控关键词词表生成的论文关键词列表。每个关键词均附带标题或摘要中的连续原文引文并通过机械校验；未命中词表时，空列表属于有效确认结果（`empty`）。"
    },
    {
      "id": "vector",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 98,
      "label": "语义向量",
      "info": "vector",
      "kind": "final",
      "settled": true,
      "description": "由固定版本的本地 SPECTER2 模型对标题和合格摘要生成的定长 L2 归一化向量。完整保存输入哈希、模型版本、CLS 池化方式、维度与范数验收状态。"
    },
    {
      "id": "keyword-profile",
      "row": "profiles",
      "stage": 4,
      "slot": 2,
      "offset": 41,
      "label": "关键词画像",
      "info": "profiles",
      "kind": "final",
      "settled": true,
      "description": "按第一作者 1.0、其他作者 0.2（导师一作、学生二作时学生按 1.0 计入）聚合归一化得到的作者受控关键词分布。存在人员阻塞项或未完成关键词任务时标为 `partial`。"
    },
    {
      "id": "semantic-evidence",
      "row": "profiles",
      "stage": 4,
      "slot": 2,
      "offset": 79,
      "label": "语义关联依据",
      "info": "profiles",
      "kind": "final",
      "settled": true,
      "description": "由论文语义向量、受控关键词分布与已确认的人员归属共同派生的论文间语义关联及作者间主题关联依据。未确认归并的同名作者保持独立，不自动合并关联。"
    },
    {
      "id": "feature-title",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 0,
      "offset": 22,
      "label": "论文标题",
      "info": "title",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-title",
        "external-info"
      ],
      "description": "传入阶段五特征生成任务的已核对论文标题文本。与可用摘要一同计算 SHA-256 输入指纹，作为 SPECTER2 向量与受控关键词标注的锁定文本输入。"
    },
    {
      "id": "feature-abstract",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 0,
      "offset": 60,
      "label": "摘要",
      "info": "abstract",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-abstract",
        "external-info"
      ],
      "description": "传入阶段五特征生成任务的通过质量检查的本篇摘要。当摘要缺失或被判为无效时，特征生成任务自动仅使用论文标题执行，并如实记录输入状态。"
    },
    {
      "id": "profile-authors",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 22,
      "label": "作者名字",
      "info": "authors",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-authors"
      ],
      "description": "进入人员归一与画像聚合的逐篇作者 occurrence 输入。结合 OpenAlex ID、ORCID、合著结构与分离约束完成人员实体映射，并根据署名顺序确定单篇贡献权重。"
    },
    {
      "id": "profile-keywords",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 60,
      "label": "论文关键词",
      "info": "controlledKeywords",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "controlled-keywords"
      ],
      "description": "已完成机械校验的论文受控关键词结果，作为计算作者关键词得分的分子输入；已确认为空的关键词标注计入作者画像归一化分母。"
    },
    {
      "id": "profile-vectors",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 98,
      "label": "语义向量",
      "info": "vector",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "vector"
      ],
      "description": "已验收通过的论文级 SPECTER2 语义向量，为计算作者之间的主题与语义关联提供底层表征输入。"
    }
  ],
  "edges": [
    {
      "from": "home-title",
      "to": "locate",
      "type": "query",
      "description": "主页提取的三项原始文本与内含的 DOI/arXiv 标识共同作为身份检索线索；主页原文持续保留，检索过程使用排版规范化副本。"
    },
    {
      "from": "locate",
      "to": "lab-title",
      "type": "value",
      "description": "候选通过联合规则检验后，分别输出采用的标题、逐篇作者署名列表和录用情况；各字段独立记录状态，数据库缺失作者时不会覆盖主页原始署名。"
    },
    {
      "from": "home-authors",
      "to": "locate",
      "type": "query",
      "description": "以主页 DOI、arXiv 标识、标题限定搜索、完整标题搜索和有限标题变体建立 OpenAlex 候选；仅使用纯身份字段联合检验标题词汇、作者交集、年份、规范化载体、非论文类型排除与正式版优先条件，输出采用的论文标题、作者名字、录用情况及确认的 work ID 与版本。"
    },
    {
      "from": "locate",
      "to": "lab-authors",
      "type": "value",
      "description": "论文采用的作者名字与署名顺序；数据库缺署名时保留主页名单。作者ID、ORCID、单位和实验室人员对应另存，歧义进入例外队列。"
    },
    {
      "from": "home-publication",
      "to": "locate",
      "type": "query",
      "description": "以主页 DOI、arXiv 标识、标题限定搜索、完整标题搜索和有限标题变体建立 OpenAlex 候选；仅使用纯身份字段联合检验标题词汇、作者交集、年份、规范化载体、非论文类型排除与正式版优先条件，输出采用的论文标题、作者名字、录用情况及确认的 work ID 与版本。"
    },
    {
      "from": "locate",
      "to": "lab-publication",
      "type": "value",
      "description": "采用年份、会刊和版本状态，保留主页与OpenAlex原值。会刊缩写归一不掩盖真正的版本或年份差异。"
    },
    {
      "from": "locate",
      "to": "identity",
      "type": "value",
      "description": "只有唯一确认或满足正式版优先条件的候选才会生成确认的 OpenAlex work ID；未匹配或多候选歧义条目在此收束并阻断后续详情查询。"
    },
    {
      "from": "identity",
      "to": "collect",
      "type": "query",
      "description": "精确详情查询只接收已确认的 OpenAlex work ID 作为入口；身份搜索阶段附带的摘要、计数和引用字段不直接跨阶段沿用。"
    },
    {
      "from": "collect",
      "to": "lab-abstract",
      "type": "value",
      "description": "由确认 work ID 的精确详情接口返回，各自独立保存来源、质量检查结果与字段状态。"
    },
    {
      "from": "collect",
      "to": "lab-keywords",
      "type": "value",
      "description": "精确详情查询返回的 OpenAlex 原生 `keywords` 字段及分数。保留数据库原始来源值，与阶段五基于 版本化的受控关键词词表生成的“论文关键词”分开管理。"
    },
    {
      "from": "collect",
      "to": "lab-topics",
      "type": "value",
      "description": "精确详情查询返回的 OpenAlex 原生 `topics` 学科主题分类。作为数据库事实字段保存，用于展示与对照，不直接替代受控关键词或派生研究领域。"
    },
    {
      "from": "collect",
      "to": "lab-counts",
      "type": "value",
      "description": "同时保存 OpenAlex 主记录的 `cited_by_count`、被引查询接口报告的总数、年度被引数（`counts_by_year`）、查询时间与完整性状态。优先采用被引查询接口报告总数，不用被引名单长度替代被引数。"
    },
    {
      "from": "collect",
      "to": "reference-list",
      "type": "value",
      "description": "精确查询分别输出主动引用的作品 ID 清单与分页拉取的施引作品 ID 清单，两者使用不同路径保存并各自记录分页完整性。"
    },
    {
      "from": "reference-list",
      "to": "external",
      "type": "query",
      "description": "两份名单去除实验室自身论文后，合并提取出一层邻域的唯一外部 ID 集合，带着原始关系方向进入批量与单篇补查。"
    },
    {
      "from": "external",
      "to": "reference-list-resolved",
      "type": "value",
      "description": "主动引用文献列表经过批量查询、遗漏单查和 canonical ID 重定向合并后的完整记录集合。查不到详情的 ID 仍保留请求状态与失败原因。"
    },
    {
      "from": "collect",
      "to": "citing-list",
      "type": "value",
      "description": "通过被引查询接口获取的引用该论文的作品 ID 列表。独立保存查询路径、接口报告总数、已取得名单与分页截断状态（`partial`）。"
    },
    {
      "from": "citing-list",
      "to": "external",
      "type": "query",
      "description": "提取这份名单的已知ID，与引用文献合并去重后补全；查询截断状态单独保留。"
    },
    {
      "from": "external",
      "to": "citing-list-resolved",
      "type": "value",
      "description": "施引文献列表经过 canonical ID 去重和详情补查后的完整记录集合。完整关系名单与前端网络节点筛选结果分开保存。"
    },
    {
      "from": "external",
      "to": "external-info",
      "type": "value",
      "description": "经 canonical ID 重定向合并后，并列输出完整的一层外部文献库、筛选出的双连接网络节点集合以及补全详情后的双向引用记录。"
    },
    {
      "from": "features",
      "to": "directions",
      "type": "value",
      "description": "在固定模型权重、版本化的受控关键词词表和原文证据机械校验下，分别输出三项派生文献特征。"
    },
    {
      "from": "features",
      "to": "controlled-keywords",
      "type": "value",
      "description": "基于版本化的受控关键词词表生成的论文关键词列表。每个关键词均附带标题或摘要中的连续原文引文并通过机械校验；未命中词表时，空列表属于有效确认结果（`empty`）。"
    },
    {
      "from": "features",
      "to": "vector",
      "type": "value",
      "description": "由固定版本的本地 SPECTER2 模型对标题和合格摘要生成的定长 L2 归一化向量。完整保存输入哈希、模型版本、CLS 池化方式、维度与范数验收状态。"
    },
    {
      "from": "profile",
      "to": "keyword-profile",
      "type": "value",
      "description": "在人员归并证据链与依赖检查通过后，输出每位实验室人员的加权关键词画像与主题关联依据；存在阻塞身份或未完成标注时标记为 `partial`。"
    },
    {
      "from": "profile",
      "to": "semantic-evidence",
      "type": "value",
      "description": "由论文语义向量、受控关键词分布与已确认的人员归属共同派生的论文间语义关联及作者间主题关联依据。未确认归并的同名作者保持独立，不自动合并关联。"
    },
    {
      "from": "feature-title",
      "to": "features",
      "type": "query",
      "description": "实验室论文与入选网络外部论文的锁定标题和合格摘要（附 SHA-256 输入指纹）进入特征流水线；无效或缺失摘要被拦截，任务降级为仅使用标题。"
    },
    {
      "from": "feature-abstract",
      "to": "features",
      "type": "query",
      "description": "读取已核对的论文标题和合格摘要（无摘要时仅用标题），通过固定版本的本地 SPECTER2 生成 L2 归一化语义向量；基于版本化的受控关键词词表抽取带连续原文证据的论文关键词（或复用符合严苛一致性条件的旧标注），并按版本化规则映射研究领域。"
    },
    {
      "from": "profile-authors",
      "to": "profile",
      "type": "query",
      "description": "逐篇作者名字提供人员归一锚点与署名顺序权重，已完成校验的论文关键词与语义向量提供聚合内容；单篇论文重复署名只计一次，未完成关键词标注的论文不计入分母。"
    },
    {
      "from": "profile-keywords",
      "to": "profile",
      "type": "query",
      "description": "依据 OpenAlex author ID、有效 ORCID、合著结构、机构、署名顺序和硬性同名分离约束将逐篇作者署名归一到实验室人员实体；按一作 1.0、其他 0.2（导师一作学生二作时学生按 1.0）加权归一化已完成标注论文的关键词与语义特征，输出关键词画像与语义关联依据。"
    },
    {
      "from": "profile-vectors",
      "to": "profile",
      "type": "query",
      "description": "依据 OpenAlex author ID、有效 ORCID、合著结构、机构、署名顺序和硬性同名分离约束将逐篇作者署名归一到实验室人员实体；按一作 1.0、其他 0.2（导师一作学生二作时学生按 1.0）加权归一化已完成标注论文的关键词与语义特征，输出关键词画像与语义关联依据。"
    }
  ]
};
