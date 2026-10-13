window.WORKFLOW_FLOW={
  "rows": [
    {
      "id": "basic",
      "label": "基本信息",
      "info": "identity",
      "height": 172,
      "description": "标题、署名与发表情况共同用于核对论文身份和版本，在同一次核对中确定。确认标识与版本是下一次精确查询的入口。"
    },
    {
      "id": "content",
      "label": "内容与主题",
      "info": "abstract",
      "height": 130,
      "description": "摘要、数据库关键词、数据库主题在③按确认记录采集。三者分别保存：摘要是正文概述，关键词描述具体内容，数据库主题是来源给出的分类。"
    },
    {
      "id": "citations",
      "label": "引用与统计",
      "info": "references",
      "height": 138,
      "description": "被引次数是来源报告的统计值；引用文献和被引记录是两个查询方向取得的条目。④为已有条目补充外部身份和详情，条目数不替代被引总数。"
    },
    {
      "id": "paperfeatures",
      "label": "文献特征",
      "info": "directions",
      "height": 120,
      "description": "每篇论文用自己的标题与可用摘要形成受控关键词、研究领域和语义向量，保存标注审核及模型输入。"
    },
    {
      "id": "profiles",
      "label": "作者画像",
      "info": "profiles",
      "height": 120,
      "description": "按实验室署名论文形成关键词覆盖率画像，以全部有效跨论文对的相似度形成作者语义关联。"
    }
  ],
  "processes": [
    {
      "id": "locate",
      "stage": 1,
      "slot": 0,
      "row": "basic",
      "offset": 65,
      "label": "多源检索\n与核对",
      "description": "并行检索 OpenAlex、Semantic Scholar，按需核对原始发布页。比较标题、作者及发表信息，确定论文身份、版本和核心字段；保留判断依据，以确认标识与版本进入详情采集。"
    },
    {
      "id": "collect",
      "stage": 2,
      "slot": 0,
      "row": "content",
      "offset": 65,
      "label": "按标识采集\n文献详情",
      "description": "按确认标识与版本读取 OpenAlex 主记录，Semantic Scholar 和原始发布页按字段缺口补充。此处采集并确定摘要、关键词、主题、被引统计及两份引用记录，分别保存来源和缺失状态。"
    },
    {
      "id": "external",
      "stage": 3,
      "slot": 0,
      "row": "citations",
      "offset": 67,
      "label": "采集外部文献\n并补全记录",
      "description": "以引用文献和被引记录为输入，合并外部标识并去重，只采集一层外部论文信息。核对条目的身份与版本、补充详情并去重，输出外部文献信息及补全后的两份记录；未匹配条目保留。被引数仍采用来源统计，不按记录数量重算。"
    },
    {
      "id": "features",
      "stage": 4,
      "slot": 1,
      "row": "paperfeatures",
      "offset": 60,
      "label": "生成文献特征",
      "description": "DeepSeek V4.1 Flash 逐篇标注受控关键词，Sol 审核并确定实验室论文主领域；外部主领域由标题与采用关键词映射。本地官方 SPECTER2 生成语义向量。"
    },
    {
      "id": "profile",
      "stage": 4,
      "slot": 1,
      "row": "profiles",
      "offset": 60,
      "label": "聚合作者画像",
      "description": "关键词画像计算受控词项的加权论文覆盖率，确认的空标注计入分母。语义关联按全部有效跨论文对的相似度加权平均。默认一作权重 1、其他署名 0.2；仅看第一作者时，导师一作、学生二作按学生一作计入。"
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
      "description": "实验室主页的原始字段，保留出处与采集时间；与其他两项基本信息共同提供身份核对线索。",
      "kind": "source",
      "settled": false
    },
    {
      "id": "lab-title",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 22,
      "label": "论文标题",
      "info": "title",
      "description": "②多源核对后确定。结合署名和版本关系核对标题变体，确定采用标题，保留其他标题与来源。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "home-authors",
      "row": "basic",
      "stage": 0,
      "slot": 0,
      "offset": 65,
      "label": "署名",
      "info": "authors",
      "description": "实验室主页的原始字段，保留出处与采集时间；与其他两项基本信息共同提供身份核对线索。",
      "kind": "source",
      "settled": false
    },
    {
      "id": "lab-authors",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 65,
      "label": "作者名字",
      "info": "authors",
      "description": "②多源核对后确定。核对作者顺序与人员身份，保留采用署名、来源原值及同名区分依据。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "home-publication",
      "row": "basic",
      "stage": 0,
      "slot": 0,
      "offset": 108,
      "label": "发表情况",
      "info": "publication",
      "description": "实验室主页的原始字段，保留出处与采集时间；与其他两项基本信息共同提供身份核对线索。",
      "kind": "source",
      "settled": false
    },
    {
      "id": "lab-publication",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 108,
      "label": "论文录用情况",
      "info": "publication",
      "description": "②多源核对后确定。结合版本证据核对年份、会议期刊与预印状态，统一等价名称并保留真实差异。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "identity",
      "row": "basic",
      "stage": 1,
      "slot": 1,
      "offset": 150,
      "label": "确认标识与版本",
      "info": "identity",
      "description": "与实验室条目对应的 OpenAlex ID、Semantic Scholar paperId、DOI、arXiv ID 或原始发布页，以及确认的版本关系。关联核对所用的基本信息证据；③按这些定位结果查询。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "lab-abstract",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 22,
      "label": "摘要",
      "info": "abstract",
      "description": "③按确认标识精准采集后确定。摘要可用时提供完整文本；未取得时保存缺失状态。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "lab-keywords",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 65,
      "label": "数据库关键词",
      "info": "keywords",
      "description": "③按确认标识精准采集后确定。保存来源给出的关键词及分数，与数据库主题分别记录。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "lab-topics",
      "row": "content",
      "stage": 2,
      "slot": 1,
      "offset": 108,
      "label": "数据库主题",
      "info": "topics",
      "description": "③按确认标识精准采集后确定。保存 OpenAlex 研究主题及其分数，作为来源分类保存。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "lab-counts",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 22,
      "label": "被引数",
      "info": "counts",
      "description": "③按确认标识精准采集后确定。保存来源报告的被引总数、来源和统计时点；不按已取得的施引名单长度重算。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "reference-list",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 67,
      "label": "引用文献",
      "info": "references",
      "description": "实验室论文所引用的文献条目及来源、收集范围。",
      "kind": "intermediate",
      "settled": false
    },
    {
      "id": "reference-list-resolved",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 67,
      "label": "引用文献（补全后）",
      "info": "references",
      "description": "用外部论文信息核对已有条目的身份和版本、补充详情并去重。保留未匹配条目及记录的获取范围。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "citing-list",
      "row": "citations",
      "stage": 2,
      "slot": 1,
      "offset": 112,
      "label": "被引记录",
      "info": "references",
      "description": "引用实验室论文的文献条目及来源、收集范围；与来源报告的被引总数分别保存。",
      "kind": "intermediate",
      "settled": false
    },
    {
      "id": "citing-list-resolved",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 112,
      "label": "被引记录（补全后）",
      "info": "references",
      "description": "用外部论文信息核对已有条目的身份和版本、补充详情并去重。保留未匹配条目及记录的获取范围。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "external-info",
      "row": "citations",
      "stage": 3,
      "slot": 1,
      "offset": 22,
      "label": "外部文献信息",
      "info": "identity",
      "description": "外部论文的确认身份及可取得的自身信息。用于补全引用文献、被引记录；生成外部论文特征时使用该论文自己的文本。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "directions",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 22,
      "label": "研究领域",
      "info": "directions",
      "description": "六类粗粒度分类，以主领域决定节点颜色和筛选。实验室论文由 Sol 按标题与可用摘要确定；外部论文按标题及已采用关键词映射。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "controlled-keywords",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 60,
      "label": "论文关键词",
      "info": "controlledKeywords",
      "description": "从 49 项受控词表中逐篇标注，DeepSeek V4.1 Flash 读取论文自身标题与可用摘要，Sol 审核后采用。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "vector",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 2,
      "offset": 98,
      "label": "语义向量",
      "info": "vector",
      "description": "本地官方 SPECTER2 读取论文自身标题与可用摘要，无摘要时仅用标题；保留模型版本、输入及截断记录。DOI 与 arXiv 标识不是输入条件。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "keyword-profile",
      "row": "profiles",
      "stage": 4,
      "slot": 2,
      "offset": 41,
      "label": "关键词画像",
      "info": "profiles",
      "description": "关键词分数为当前筛选内实验室署名论文的加权覆盖率；确认的空标注计入分母，排除条目不计入。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "semantic-evidence",
      "row": "profiles",
      "stage": 4,
      "slot": 2,
      "offset": 79,
      "label": "语义关联依据",
      "info": "profiles",
      "description": "全部有效跨论文对的语义相似度按双方署名权重乘积加权平均；排除同篇自比，每位作者保留最相近的 5 位。",
      "kind": "final",
      "settled": true
    },
    {
      "id": "feature-title",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 0,
      "offset": 22,
      "label": "论文标题",
      "info": "title",
      "description": "每篇论文自己的核定标题，用于受控关键词、研究领域及语义向量。",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-title",
        "external-info"
      ]
    },
    {
      "id": "feature-abstract",
      "row": "paperfeatures",
      "stage": 4,
      "slot": 0,
      "offset": 60,
      "label": "摘要",
      "info": "abstract",
      "description": "摘要可用时与该论文标题一同输入；没有摘要时仅使用标题。",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-abstract",
        "external-info"
      ]
    },
    {
      "id": "profile-authors",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 22,
      "label": "作者名字",
      "info": "authors",
      "description": "按已确认署名与顺序确定画像归属和论文贡献。",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "lab-authors"
      ]
    },
    {
      "id": "profile-keywords",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 60,
      "label": "论文关键词",
      "info": "controlledKeywords",
      "description": "逐篇采用的受控关键词按署名贡献形成覆盖率画像。",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "controlled-keywords"
      ]
    },
    {
      "id": "profile-vectors",
      "row": "profiles",
      "stage": 4,
      "slot": 0,
      "offset": 98,
      "label": "语义向量",
      "info": "vector",
      "description": "实验室论文的本地向量提供跨论文对相似度，按署名贡献形成作者语义关联。",
      "kind": "reference",
      "settled": true,
      "sourceIds": [
        "vector"
      ]
    }
  ],
  "edges": [
    {
      "from": "home-title",
      "to": "locate",
      "type": "query",
      "description": "标题、署名、发表情况共同参与同一次身份与版本核对；每项仍独立保存。"
    },
    {
      "from": "locate",
      "to": "lab-title",
      "type": "value",
      "description": "结合署名和版本关系核对标题变体，确定采用标题，保留其他标题与来源。"
    },
    {
      "from": "home-authors",
      "to": "locate",
      "type": "query",
      "description": "标题、署名、发表情况共同参与同一次身份与版本核对；每项仍独立保存。"
    },
    {
      "from": "locate",
      "to": "lab-authors",
      "type": "value",
      "description": "核对作者顺序与人员身份，保留采用署名、来源原值及同名区分依据。"
    },
    {
      "from": "home-publication",
      "to": "locate",
      "type": "query",
      "description": "标题、署名、发表情况共同参与同一次身份与版本核对；每项仍独立保存。"
    },
    {
      "from": "locate",
      "to": "lab-publication",
      "type": "value",
      "description": "结合版本证据核对年份、会议期刊与预印状态，统一等价名称并保留真实差异。"
    },
    {
      "from": "locate",
      "to": "identity",
      "type": "value",
      "description": "确定来源标识和版本对应，保留核对依据。"
    },
    {
      "from": "identity",
      "to": "collect",
      "type": "query",
      "description": "收集阶段按确认标识与版本采集详情，OpenAlex 为主、Semantic Scholar 补缺；当前默认构建读取已采用的本地快照。"
    },
    {
      "from": "collect",
      "to": "lab-abstract",
      "type": "value",
      "description": "从③的详情查询结果确定该字段，保存来源、采用理由和获取状态。"
    },
    {
      "from": "collect",
      "to": "lab-keywords",
      "type": "value",
      "description": "从③的详情查询结果确定该字段，保存来源、采用理由和获取状态。"
    },
    {
      "from": "collect",
      "to": "lab-topics",
      "type": "value",
      "description": "从③的详情查询结果确定该字段，保存来源、采用理由和获取状态。"
    },
    {
      "from": "collect",
      "to": "lab-counts",
      "type": "value",
      "description": "从③的详情查询结果确定该字段，保存来源、采用理由和获取状态。"
    },
    {
      "from": "collect",
      "to": "reference-list",
      "type": "value",
      "description": "③确定本次取得的记录和获取状态。"
    },
    {
      "from": "reference-list",
      "to": "external",
      "type": "query",
      "description": "从该方向已取得的条目提取外部标识，与另一方向合并去重后查询。"
    },
    {
      "from": "external",
      "to": "reference-list-resolved",
      "type": "value",
      "description": "外部查找与核对结果结合原有条目，补充身份、版本及详情并去重，形成补全后的记录。"
    },
    {
      "from": "collect",
      "to": "citing-list",
      "type": "value",
      "description": "③确定本次取得的记录和获取状态。"
    },
    {
      "from": "citing-list",
      "to": "external",
      "type": "query",
      "description": "从该方向已取得的条目提取外部标识，与另一方向合并去重后查询。"
    },
    {
      "from": "external",
      "to": "citing-list-resolved",
      "type": "value",
      "description": "外部查找与核对结果结合原有条目，补充身份、版本及详情并去重，形成补全后的记录。"
    },
    {
      "from": "external",
      "to": "external-info",
      "type": "value",
      "description": "按外部标识查询并核对，确定外部论文信息及缺失状态。"
    },
    {
      "from": "features",
      "to": "directions",
      "type": "value",
      "description": "保存结果所用输入、署名权重与支撑论文。"
    },
    {
      "from": "features",
      "to": "controlled-keywords",
      "type": "value",
      "description": "保存结果所用输入、署名权重与支撑论文。"
    },
    {
      "from": "features",
      "to": "vector",
      "type": "value",
      "description": "保存结果所用输入、署名权重与支撑论文。"
    },
    {
      "from": "profile",
      "to": "keyword-profile",
      "type": "value",
      "description": "保存结果所用输入、署名权重与支撑论文。"
    },
    {
      "from": "profile",
      "to": "semantic-evidence",
      "type": "value",
      "description": "保存结果所用输入、署名权重与支撑论文。"
    },
    {
      "from": "feature-title",
      "to": "features",
      "type": "query",
      "description": "每篇论文自己的核定标题，用于受控关键词、研究领域及语义向量。"
    },
    {
      "from": "feature-abstract",
      "to": "features",
      "type": "query",
      "description": "摘要可用时与该论文标题一同输入；没有摘要时仅使用标题。"
    },
    {
      "from": "profile-authors",
      "to": "profile",
      "type": "query",
      "description": "按已确认署名与顺序确定画像归属和论文贡献。"
    },
    {
      "from": "profile-keywords",
      "to": "profile",
      "type": "query",
      "description": "逐篇采用的受控关键词按署名贡献形成覆盖率画像。"
    },
    {
      "from": "profile-vectors",
      "to": "profile",
      "type": "query",
      "description": "实验室论文的本地向量提供跨论文对相似度，按署名贡献形成作者语义关联。"
    }
  ]
};
