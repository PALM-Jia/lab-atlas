window.WORKFLOW_MAP={
  "stages": [
    {
      "id": "import",
      "label": "① 整理实验室清单",
      "mode": "本地解析 · 自动"
    },
    {
      "id": "locate",
      "fixed": true,
      "label": "② 核对论文与作者身份",
      "mode": "OpenAlex 查询 · 规则判定"
    },
    {
      "id": "collect",
      "fixed": true,
      "label": "③ 采集论文详情",
      "mode": "OpenAlex 精确查询 · 自动"
    },
    {
      "id": "external",
      "fixed": true,
      "label": "④ 补全外部文献",
      "mode": "OpenAlex 批量查询 · 自动"
    },
    {
      "id": "features",
      "label": "⑤ 生成文献特征与作者画像",
      "mode": "本地计算 / 固定标注 · 自动为主，AI 受控介入"
    }
  ],
  "tracks": [
    {
      "id": "identity",
      "color": "#687b9a"
    },
    {
      "id": "text",
      "color": "#4386b9"
    },
    {
      "id": "authors",
      "color": "#448a79"
    },
    {
      "id": "keywords",
      "color": "#bd873d"
    },
    {
      "id": "publication",
      "color": "#ac6f77"
    },
    {
      "id": "citations",
      "color": "#8b6db2"
    },
    {
      "id": "labFeatures",
      "color": "#4386b9"
    },
    {
      "id": "externalFeatures",
      "color": "#7b8798"
    }
  ],
  "information": [
    {
      "id": "identity",
      "name": "论文身份与版本对应",
      "track": "identity"
    },
    {
      "id": "title",
      "name": "标题",
      "track": "text"
    },
    {
      "id": "authors",
      "name": "作者与人员",
      "track": "authors"
    },
    {
      "id": "publication",
      "name": "年份与发表情况",
      "track": "publication"
    },
    {
      "id": "abstract",
      "name": "摘要",
      "track": "text"
    },
    {
      "id": "keywords",
      "name": "数据库关键词",
      "track": "keywords"
    },
    {
      "id": "topics",
      "name": "数据库主题",
      "track": "keywords"
    },
    {
      "id": "counts",
      "name": "被引数",
      "track": "publication"
    },
    {
      "id": "references",
      "name": "引用关系",
      "track": "citations"
    },
    {
      "id": "directions",
      "name": "研究领域",
      "track": "labFeatures"
    },
    {
      "id": "vector",
      "name": "语义向量",
      "track": "labFeatures"
    },
    {
      "id": "profiles",
      "name": "作者画像",
      "track": "authors"
    },
    {
      "id": "controlledKeywords",
      "name": "论文关键词",
      "track": "labFeatures"
    }
  ]
};
