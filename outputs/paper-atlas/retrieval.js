/* Static evidence dashboard. All detail lists remain open. */
(() => {
  "use strict";
  const D = window.ATLAS_RETRIEVAL,
    $ = (id) => document.getElementById(id);
  const paperMap = new Map(
      [...D.papers, ...(D.external || [])].map((p) => [p.id, p]),
    ),
    authorMap = new Map(D.authors.map((a) => [a.id, a]));
  const names = {
    title: "标题",
    authors: "作者",
    year: "年份",
    venue: "会议／期刊",
    abstract: "摘要",
    references: "参考文献",
    citing: "施引文献",
    citations: "被引次数",
    keywords: "关键词",
    topics: "OpenAlex 研究主题",
    vector: "内容相似度向量",
    identity: "论文链接",
  };
  const paperColumnHelp = {
    title:
      "同一篇论文的主页标题与 OpenAlex 候选标题。加粗的是身份核对后采用的标题，其他观察值保留作版本对照。",
    authors:
      "论文作者及署名顺序。主页署名与 OpenAlex 署名分别保存；已确认的姓名变体合并，作者增减或顺序差异并列保留。",
    year: "论文的发表年份，来自主页发表情况与 OpenAlex 记录。主页标为预印本时显示“预印”；不同年份保留作版本对照。",
    venue:
      "论文发表的会议或期刊，来自主页发表情况与 OpenAlex 记录。简称与全称归一；预印本和正式发表记录分别保留。",
    abstract:
      "从确认 OpenAlex work ID 的精确详情取得的摘要。用于关键词标注和内容相似度计算；点击查看完整摘要。",
    references:
      "这篇论文引用的文献，从 OpenAlex 参考名单取得。按数据库标识查找标题等详情，未取得标题的条目保留标识。",
    citing:
      "引用这篇论文的文献，来自 OpenAlex 施引查询。来源报告的总数、取得的名单和文献详情分别统计。",
    citations:
      "OpenAlex 报告的被引次数：优先采用施引查询总数，主记录计数作为对照；名单长度不替代被引总数。",
    keywords:
      "依据论文标题和可用摘要，从版本化的受控关键词词表标注；每个关键词附连续原文证据。点击查看证据和采用理由；“无匹配关键词”是有效空结果，“标注未采用”不参与关键词统计。",
    topics:
      "从匹配的 OpenAlex 记录读取研究主题及相关度，用于查看数据库分类结果。",
    vector:
      "在本地用 SPECTER2 把论文标题及可用摘要转换为 768 维数值，用于计算内容相似度。没有摘要时只用标题。",
    identity:
      "论文确认后的 OpenAlex work ID、DOI 和相关链接。通过题名、作者及版本信息核对后采用；work ID 用于查询论文详情和引用关系。",
  };
  const authorColumnHelp = {
    name: "合并已确认姓名写法后的作者姓名，结合论文署名、实验室名册及身份资料确定。同名但无法确认是同一人的记录分开保留。",
    aliases:
      "已确认属于这位作者的其他姓名写法，来自论文署名和身份核对资料。“—”表示没有记录其他写法。",
    group:
      "在读学生、毕业学生或其他。按你提供的实验室名册分类，未列入前两类的归为“其他”。",
    papers:
      "实验室论文列表中，这位作者署名的论文数。按已核对的作者身份关联论文；点击查看对应名单。",
    identity:
      "论文署名是否已对应到确定的人员。结合单位、邮箱及合作记录核对；“待核对”表示同名归属未确定，“未关联论文”表示名册中有此人但没有对应论文。",
    keywords:
      "关键词在作者论文中的加权出现比例，按原始署名顺序给第一作者权重 1、其他作者 0.2。分母包含已采用标注的论文及有效空结果，未采用标注的论文不计入。",
    sources:
      "用于核对人员身份和分类的资料，包括实验室名册、论文署名及已保存的公开资料链接。",
  };
  const externalColumnHelp = {
    title:
      "外部文献的标题，来自已匹配的数据库记录。用于辨认与实验室论文关联的文献。",
    authors:
      "外部文献的作者名单，来自已匹配的数据库记录，按来源中的署名顺序展示。",
    year: "外部文献的发表年份，来自已匹配的数据库记录。",
    venue: "外部文献的会议或期刊名称，来自已匹配的数据库记录。",
    abstract: "外部文献的摘要，来自已取得的数据库记录；点击查看完整摘要。",
  };
  const columnHelp = (key) =>
    state.view === "authors"
      ? authorColumnHelp[key]
      : state.view === "external"
        ? externalColumnHelp[key] || paperColumnHelp[key]
        : paperColumnHelp[key];
  const stateLabels = {
    ready: "已取得值",
    partial: "部分详情缺失",
    empty: "来源返回空",
    missing: "无可用值",
    review: "身份待核对",
    derived: "论文聚合",
    unlinked: "未关联论文",
    different: "来源差异",
    annotated: "已标注关键词",
    excluded: "标注未采用",
  };
  const definitions = {
    papers: [
      ["title", "标题", 330],
      ["authors", "作者", 250],
      ["year", "年份", 115],
      ["venue", "会议／期刊", 180],
      ["abstract", "摘要", 250],
      ["references", "参考文献", 175],
      ["citing", "施引文献", 160],
      ["citations", "被引次数", 200],
      ["keywords", "关键词", 300],
      ["topics", "OpenAlex 研究主题", 260],
      ["vector", "内容相似度向量", 240],
      ["identity", "论文链接", 180],
    ],
    authors: [
      ["name", "作者", 230],
      ["aliases", "姓名变体", 155],
      ["group", "人员分类", 120],
      ["papers", "署名论文", 120],
      ["identity", "身份核对", 220],
      ["keywords", "关键词 · 加权出现比例", 430],
      ["sources", "来源", 230],
    ],
  };
  definitions.external = definitions.papers.filter(([key]) =>
    [
      "title",
      "authors",
      "year",
      "venue",
      "abstract",
      "keywords",
      "topics",
      "vector",
      "identity",
    ].includes(key),
  );
  const defaults = {
    view: "papers",
    search: "",
    field: "all",
    status: "all",
    source: "all",
    group: "all",
    sort: "title",
    ascending: true,
    page: 0,
    pageSize: 50,
    selected: null,
    widths: { papers: {}, authors: {}, external: {} },
  };
  let saved = {};
  try {
    saved =
      JSON.parse(
        window.localStorage?.getItem("lab-atlas-retrieval-v1") || "{}",
      ) || {};
  } catch {}
  const state = {
    ...defaults,
    ...saved,
    widths: {
      papers: { ...saved.widths?.papers },
      authors: { ...saved.widths?.authors },
      external: { ...saved.widths?.external },
    },
  };
  if (["openalex", "semantic_scholar", "crossref"].includes(state.sort))
    state.sort = "citations";
  if (["openalex", "semantic_scholar", "crossref"].includes(state.field))
    state.field = "citations";
  if (!["papers", "authors", "external"].includes(state.view))
    state.view = "papers";
  if (state.sort === "issues") state.sort = "title";
  if (["directions", "research_task"].includes(state.sort))
    state.sort = "keywords";
  if (["directions", "research_task"].includes(state.field))
    state.field = "keywords";
  if (
    ![
      "all",
      "gaps",
      "ready",
      "partial",
      "empty",
      "missing",
      "review",
      "unlinked",
      "different",
      "excluded",
    ].includes(state.status)
  )
    state.status = "all";
  if (![0, 25, 50, 100].includes(state.pageSize)) state.pageSize = 50;
  if (!Number.isInteger(state.page) || state.page < 0) state.page = 0;
  if (typeof state.search !== "string") state.search = "";
  const params = new URLSearchParams(window.location?.search || "");
  if (paperMap.has(params.get("paper"))) {
    state.view = D.external.some((p) => p.id === params.get("paper"))
      ? "external"
      : "papers";
    state.search = paperMap.get(params.get("paper")).title;
    state.selected = params.get("paper");
    state.page = 0;
    state.field = state.status = state.source = state.group = "all";
  }
  if (authorMap.has(params.get("author"))) {
    state.view = "authors";
    state.search = authorMap.get(params.get("author")).name;
    state.selected = params.get("author");
    state.page = 0;
    state.field = state.status = state.source = state.group = "all";
  }
  if (state.view !== "authors" && Object.hasOwn(names, params.get("field")))
    state.field = params.get("field");
  const esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const href = (url) => (/^https?:\/\//.test(url || "") ? esc(url) : "");
  const save = () => {
    try {
      window.localStorage?.setItem(
        "lab-atlas-retrieval-v1",
        JSON.stringify(state),
      );
    } catch {}
  };
  const badge = (state) =>
    `<span class="state state-${esc(state)}">${esc(stateLabels[state] || state)}</span>`;
  const sourceName = (s) =>
    /^https?:/.test(s.name || "")
      ? "论文发布页"
      : String(s.name || "")
          .replace(/^Semantic Scholar [a-f0-9]{40}$/, "Semantic Scholar")
          .replace(/^论文原始发布页$/, "论文发布页");
  const providerName = (name) => sourceName({ name });
  const sources = (list) =>
    `<div class="source">${(list || []).map((s) => (href(s.url) ? `<a href="${href(s.url)}" title="${esc(s.originalValue || sourceName(s))}" target="_blank" rel="noopener">${esc(sourceName(s))} ↗</a>` : `<span title="${esc(s.originalValue || sourceName(s))}">${esc(sourceName(s))}</span>`)).join("")}</div>`;
  const tag = (name, extra = "", adopted = false) =>
    `<span class="tag${adopted ? " adopted" : ""}">${esc(name)}${extra}</span>`;
  const paperButton = (id) => {
    const p = paperMap.get(id);
    return p
      ? `<button class="title-link" data-paper="${esc(id)}">${esc(p.title)}</button>`
      : esc(id);
  };
  const authorButton = (a) =>
    a.excluded || !authorMap.has(a.id)
      ? esc(a.name)
      : `<button class="link-button" data-author="${esc(a.id)}">${esc(a.name)}</button>`;
  const percent = (n) => (n * 100).toFixed(1) + "%";
  const keywordBadge = (f) =>
    f.state === "empty"
      ? '<span class="state state-empty">无匹配关键词</span>'
      : badge(f.state);
  const fieldBadge = (f, key) =>
    key === "keywords"
      ? keywordBadge(f)
      : key === "citing" && f.state === "empty" && f.total === 0
        ? '<span class="state state-empty">0 篇施引文献</span>'
        : badge(f.state);
  const fieldComplete = (f, key) =>
    ["ready", "annotated"].includes(f.state) ||
    (f.state === "empty" && ["keywords", "citing"].includes(key));
  const authorKeywordEmpty = (a) =>
    a.papers.length
      ? '<span class="state state-empty">无可汇总的关键词</span>'
      : badge("unlinked");
  const keywordDetail = (f) =>
    f.value.length
      ? f.value
          .map(
            (k) =>
              `<div class="detail-item">${tag(k.name, "", true)}<p class="source">${k.evidence_field === "title" ? "标题" : "摘要"}：${esc(k.exact_quote)}</p><p>${esc(k.reason_zh)}</p></div>`,
          )
          .join("")
      : keywordBadge(f);
  const paperKeys = Object.keys(names);
  const activePaperKeys = () =>
    state.view === "external"
      ? definitions.external.map(([key]) => key)
      : paperKeys;
  const paperProviders = (p) => [
    ...new Set(
      activePaperKeys().flatMap((key) => {
        const f = p.fields[key];
        return [
          ...(f?.sources || []),
          ...(f?.observations || []).flatMap((o) => o.sources || []),
        ]
          .map(sourceName)
          .filter(Boolean);
      }),
    ),
  ];
  const observedText = (v) =>
    Array.isArray(v)
      ? v
          .map((x) =>
            typeof x === "object" ? x.name || x.id || JSON.stringify(x) : x,
          )
          .join(" · ")
      : String(v ?? "");
  const differenceBadge = (f) =>
    f.relationship
      ? `<span class="state state-derived">${esc(f.relationship)}</span>`
      : f.different
        ? badge("different")
        : "";
  function observationMarkup(f, format = (v) => esc(observedText(v))) {
    return (
      (f.observations || [])
        .map(
          (o) =>
            `<div class="observation"><span class="${o.adopted ? "adopted" : ""}">${format(o.value)}</span>${sources(o.sources)}</div>`,
        )
        .join("") + differenceBadge(f)
    );
  }
  function citationMarkup(p, full = false) {
    const f = p.fields.citations;
    if (!full) {
      const shortName = (name) =>
        ({
          "OpenAlex 施引查询": "OpenAlex·施引",
          OpenAlex: "OpenAlex",
          "Semantic Scholar": "S2",
          Crossref: "Crossref",
        })[name] || name;
      const item = (o) =>
        `<button class="count-link citation-count${o.adopted ? " adopted" : ""}" data-paper="${esc(p.id)}" data-section="field-citations" title="${esc(o.sources.map((s) => s.name).join("、"))}${o.adopted ? "；采用值" : ""}">${o.value}<span class="citation-provider">${esc(o.sources.map((s) => shortName(s.name)).join("/"))}</span></button>`;
      const observations = f.observations || [];
      const adopted = observations.find((o) => o.adopted) || observations[0];
      if (!adopted)
        return `<button class="count-link" data-paper="${esc(p.id)}" data-section="field-citations">未取得</button>`;
      const others = observations.filter((o) => o !== adopted);
      return (
        `<div class="citation-primary">${item(adopted)}</div>` +
        (others.length
          ? `<div class="citation-alternatives">${others.map(item).join('<span class="muted"> · </span>')}</div>`
          : "")
      );
    }
    const failures = (f.attempts || [])
      .filter((a) => a.state !== "ready")
      .map(
        (a) =>
          `<div class="source" title="${esc(a.reason)}">${esc(a.name)} · ${esc(full ? a.reason : /HTTP \d+/.exec(a.reason)?.[0] || (/DataCite/.test(a.reason) ? "DataCite DOI" : a.state === "review" ? "身份待核对" : /DOI/.test(a.reason) ? "无 DOI" : "无可用计数"))}</div>`,
      )
      .join("");
    return (
      observationMarkup(f, (v) => `<span class="value">${v}</span>`) +
      (f.observations.length ? "" : badge("missing")) +
      failures
    );
  }
  function coverage() {
    const rows = state.view === "external" ? D.external : D.papers,
      c = D.meta.coverage;
    const counts = (key) =>
      rows.filter((p) => ["ready", "annotated"].includes(p.fields[key].state))
        .length;
    const items =
      state.view === "external"
        ? [
            ["外部文献", rows.length, null],
            ["关键词非空", counts("keywords"), rows.length],
          ]
        : [
            ["论文", c.total, null],
            ["作者名单", D.authors.length, null],
            ["参考文献详情", c.referenceTitles, c.referenceIDs],
            ["施引文献详情", c.citingTitles, c.citingTotal],
            ["关键词非空", c.keywords, c.total],
          ];
    items.push(
      [
        "无匹配关键词",
        rows.filter((p) => p.fields.keywords.state === "empty").length,
        null,
      ],
      [
        "标注未采用",
        rows.filter((p) => p.fields.keywords.state === "excluded").length,
        null,
      ],
      ["研究主题有值", counts("topics"), rows.length],
      ["内容向量", counts("vector"), rows.length],
    );
    $("coverage").innerHTML = items
      .map(
        ([name, n, total]) =>
          `<div class="metric"><span>${name}</span><strong>${n}${total != null ? `<small>/${total}</small>` : ""}</strong>${total != null ? `<small>${total > 0 ? percent(n / total) : "—"}</small>` : ""}</div>`,
      )
      .join("");
  }
  function setupControls() {
    document
      .querySelectorAll("[data-view]")
      .forEach((b) =>
        b.classList.toggle("active", b.dataset.view === state.view),
      );
    const paper = state.view !== "authors";
    $("source-label").hidden = !paper;
    $("group-label").hidden = paper;
    const fields = paper
      ? Object.entries(names).filter(
          ([key]) =>
            state.view !== "external" ||
            definitions.external.some(([id]) => id === key),
        )
      : [
          ["papers", "署名论文"],
          ["identity", "身份核对"],
          ["keywords", "作者关键词"],
        ];
    if (!fields.some(([key]) => key === state.field)) state.field = "all";
    $("field").innerHTML =
      '<option value="all">全部字段</option>' +
      fields
        .map(([key, name]) => `<option value="${key}">${name}</option>`)
        .join("");
    $("status").querySelector('option[value="empty"]').textContent =
      state.field === "keywords" ? "无匹配关键词" : "来源返回空";
    state.source = providerName(state.source);
    const providers = [
      ...new Set(
        (state.view === "external" ? D.external : D.papers).flatMap(
          paperProviders,
        ),
      ),
    ].sort();
    if (state.source !== "all" && !providers.includes(state.source))
      state.source = "all";
    $("source").innerHTML =
      '<option value="all">全部</option>' +
      providers
        .map((name) => `<option value="${esc(name)}">${esc(name)}</option>`)
        .join("");
    for (const id of ["search", "field", "status", "source", "group"])
      $(id).value = state[id];
    $("page-size").value = String(state.pageSize);
  }
  function rowStates(row) {
    if (state.view !== "authors")
      return (state.field === "all" ? activePaperKeys() : [state.field]).map(
        (k) =>
          row.fields[k]?.state === "annotated"
            ? "ready"
            : row.fields[k]?.state || "missing",
      );
    const states = {
      papers: row.papers.length ? "ready" : "unlinked",
      identity: row.state,
      keywords: row.keywords.length
        ? "ready"
        : row.papers.length
          ? "empty"
          : "unlinked",
    };
    return state.field === "all"
      ? Object.values(states)
      : [states[state.field] || "missing"];
  }
  function filtered() {
    const query = state.search.trim().toLowerCase(),
      isPaper = state.view !== "authors";
    let rows = (
      isPaper ? (state.view === "external" ? D.external : D.papers) : D.authors
    ).filter((row) => {
      const text = isPaper
        ? [
            row.title,
            ...paperKeys.flatMap((k) =>
              (row.fields[k]?.observations || []).flatMap((o) => [
                observedText(o.value),
                ...(o.sources || []).map((s) => s.originalValue || ""),
              ]),
            ),
            ...(row.fields.authors?.value || []).flatMap((a) => [
              a.name,
              authorMap.get(a.id)?.chinese || "",
            ]),
            row.fields.venue?.value?.name,
            row.fields.venue?.value?.year,
            ...(row.fields.keywords?.value || []).map((k) => k.name),
          ].join(" ")
        : [
            row.name,
            row.chinese,
            ...row.aliases,
            ...row.keywords.map((k) => k.name),
          ].join(" ");
      if (query && !window.atlasSearchMatch(text, query)) return false;
      if (
        isPaper &&
        state.source !== "all" &&
        !paperProviders(row).includes(state.source)
      )
        return false;
      if (!isPaper && state.group !== "all" && row.group !== state.group)
        return false;
      const statuses = rowStates(row);
      if (state.status === "different")
        return (
          isPaper &&
          (state.field === "all" ? activePaperKeys() : [state.field]).some(
            (k) => row.fields[k]?.different,
          )
        );
      return (
        state.status === "all" ||
        (state.status === "gaps" &&
          (isPaper
            ? (state.field === "all" ? activePaperKeys() : [state.field]).some(
                (k) => !fieldComplete(row.fields[k], k),
              )
            : statuses.some((s) => s !== "ready" && s !== "empty"))) ||
        (state.status === "ready" &&
          (isPaper
            ? (state.field === "all" ? activePaperKeys() : [state.field]).every(
                (k) => fieldComplete(row.fields[k], k),
              )
            : statuses.every((s) => s === "ready"))) ||
        statuses.includes(state.status)
      );
    });
    const value = (row) => {
      if (!isPaper) {
        if (state.sort === "papers") return row.papers.length;
        if (state.sort === "keywords") return row.keywords.length;
        if (state.sort === "group") return D.meta.groups[row.group].name;
        if (state.sort === "aliases") return row.aliases.join(" · ");
        if (state.sort === "identity") return row.identityLabel;
        if (state.sort === "sources")
          return (
            row.sources.map((s) => s.name + " " + s.url).join(" · ") ||
            row.rosterSource ||
            ""
          );
        return row.name;
      }
      const f = row.fields;
      if (state.sort === "year")
        return f.year.isPreprint
          ? Infinity
          : (f.year.adoptedValue ?? f.year.value ?? -Infinity);
      if (state.sort === "venue")
        return f.venue.adoptedValue || f.venue.value.name;
      if (state.sort === "citations")
        return f.citations.adoptedValue ?? -Infinity;
      if (state.sort === "references") return f.references.total;
      if (state.sort === "citing") return f.citing.total ?? -Infinity;
      if (["authors", "keywords", "topics"].includes(state.sort))
        return f[state.sort].value.length;
      if (state.sort === "vector") return f.vector.state === "ready" ? 1 : 0;
      if (state.sort === "abstract")
        return f.abstract.adoptedValue || f.abstract.value || "";
      if (state.sort === "identity")
        return [
          f.identity.value.openalex,
          f.identity.value.doi,
          f.identity.value.semantic_scholar,
        ]
          .filter(Boolean)
          .join(" · ");
      if (state.sort === "issues")
        return paperKeys.filter((k) => f[k].state !== "ready").length;
      return row.title;
    };
    return rows.sort((a, b) => {
      const problemOrder =
        Number(Boolean(cellStatus(b, state.sort))) -
        Number(Boolean(cellStatus(a, state.sort)));
      if (problemOrder) return problemOrder;
      const av = value(a),
        bv = value(b),
        order =
          typeof av === "number" && typeof bv === "number"
            ? av === bv
              ? 0
              : av < bv
                ? -1
                : 1
            : String(av).localeCompare(String(bv), "zh-CN");
      const yearTie =
        isPaper &&
        state.sort === "year" &&
        a.fields.year.isPreprint &&
        b.fields.year.isPreprint
          ? (a.fields.year.value ?? -Infinity) ===
            (b.fields.year.value ?? -Infinity)
            ? 0
            : (a.fields.year.value ?? -Infinity) <
                (b.fields.year.value ?? -Infinity)
              ? -1
              : 1
          : 0;
      return (
        (state.ascending ? order : -order) ||
        (state.ascending ? yearTie : -yearTie) ||
        a.id.localeCompare(b.id)
      );
    });
  }
  function paperCell(p, key) {
    const f = p.fields[key];
    if (key === "title")
      return (
        observationMarkup(f, (v) =>
          v === p.title
            ? paperButton(p.id)
            : `<button class="title-link" data-paper="${esc(p.id)}">${esc(v)}</button>`,
        ) + (p.fields.identity.state === "review" ? badge("review") : "")
      );
    if (key === "authors")
      return f.observations?.length
        ? observationMarkup(f, (v) =>
            v
              .map((name) => {
                const a = f.value.find(
                  (a) => a.raw === name || a.name === name,
                );
                return a ? authorButton(a) : esc(name);
              })
              .join(" · "),
          )
        : badge(f.state);
    if (key === "venue") return observationMarkup(f) || badge("missing");
    if (key === "year") return observationMarkup(f) || badge("missing");
    if (key === "abstract")
      return f.observations?.length
        ? observationMarkup(
            f,
            (v) =>
              `<button class="link-button compact-text" data-paper="${esc(p.id)}" data-section="field-abstract">${esc(v.slice(0, 55))}${v.length > 55 ? "…" : ""}</button>`,
          )
        : badge("missing");
    if (key === "references")
      return f.total
        ? `<button class="count-link adopted" data-reference="${p.id}">参考文献 ${f.total} 篇 · 有详情 ${f.parsed} 篇</button>${sources(f.sources)}`
        : badge(f.state) + sources(f.sources);
    if (key === "citations") return citationMarkup(p);
    if (key === "citing")
      return `${f.total > 0 ? `<button class="count-link adopted" data-paper="${esc(p.id)}" data-section="citing">施引文献 ${f.total} 篇 · 有详情 ${f.parsed} 篇</button>` : fieldBadge(f, key)}${sources(f.sources)}`;
    if (key === "keywords")
      return (
        (f.value.length
          ? f.value
              .slice(0, 2)
              .map((k) => tag(k.name, "", true))
              .join("") +
            (f.value.length > 2
              ? `<button class="count-link" aria-label="查看完整关键词" data-paper="${esc(p.id)}" data-section="field-keywords">…</button>`
              : "")
          : keywordBadge(f)) + sources(f.sources)
      );
    if (["topics"].includes(key))
      return (
        (f.value.length
          ? f.value
              .slice(0, 2)
              .map((t) =>
                tag(
                  t.name,
                  key === "topics" && Number.isFinite(t.score)
                    ? " " + percent(t.score)
                    : "",
                  true,
                ),
              )
              .join("") +
            (f.value.length > 2
              ? `<button class="count-link" data-paper="${esc(p.id)}" data-section="field-${key}" aria-label="查看完整条目">…</button>`
              : "")
          : fieldBadge(f, key)) + sources(f.sources)
      );
    if (key === "vector") {
      if (f.state === "ready")
        return `<button class="link-button adopted" data-paper="${esc(p.id)}" data-section="field-vector">${f.input?.fields?.includes("abstract") ? "标题＋摘要" : "仅标题"}</button>${sources(f.sources)}`;
      const explanation = f.explanation || "";
      const summary = /HTTP\s*\d+/.test(explanation)
        ? "未生成 · " + explanation.match(/HTTP\s*\d+/)[0]
        : "未生成";
      return `<button class="link-button" data-paper="${esc(p.id)}" data-section="field-vector" title="${esc(explanation)}">${esc(summary)}</button>`;
    }
    if (key === "identity")
      return (
        [
          f.value.openalex
            ? `<a href="${href(f.value.openalex)}" target="_blank" rel="noopener">OpenAlex ↗</a>`
            : "",
          f.value.doi
            ? `<a href="${href(f.value.doi)}" target="_blank" rel="noopener">DOI ↗</a>`
            : "",
          f.value.semantic_scholar
            ? `<a href="https://www.semanticscholar.org/paper/${esc(f.value.semantic_scholar)}" target="_blank" rel="noopener">Semantic Scholar ↗</a>`
            : "",
        ]
          .filter(Boolean)
          .join("<br>") + (f.state !== "ready" ? badge(f.state) : "")
      );
    const gaps = paperKeys
      .filter((k) => !fieldComplete(p.fields[k], k))
      .map((k) => names[k]);
    return `<button class="count-link" data-paper="${p.id}" data-section="collection">${gaps.length ? gaps.map((name) => tag(name)).join("") : "各字段已有值"}</button>`;
  }
  function authorCell(a, key) {
    if (key === "name")
      return `<button class="title-link" data-author="${esc(a.id)}">${esc(a.name)}</button>${a.chinese && a.chinese !== a.name ? `<div class="muted">${esc(a.chinese)}</div>` : ""}`;
    if (key === "aliases")
      return a.aliases.length ? a.aliases.map(esc).join("<br>") : "—";
    if (key === "group")
      return (
        `<span class="adopted">${esc(D.meta.groups[a.group].name)}</span>` +
        (a.rosterSource
          ? '<div class="source">用户确认名册</div>'
          : '<div class="source">人员分类</div>')
      );
    if (key === "papers")
      return a.papers.length
        ? `<button class="count-link value" data-author="${esc(a.id)}" data-section="author-papers">${a.papers.length}</button>`
        : badge("unlinked");
    if (key === "identity")
      return (
        `<span class="${a.state === "ready" ? "adopted" : ""}">${esc(a.identityLabel)}</span>` +
        (a.state !== "ready" ? "<br>" + badge(a.state) : "")
      );
    if (key === "keywords")
      return a.keywords.length
        ? a.keywords
            .slice(0, 2)
            .map((k) => tag(k.name, ` <b>${percent(k.weight)}</b>`, true))
            .join("") +
            (a.keywords.length > 2
              ? `<button class="count-link" aria-label="查看完整关键词" data-author="${esc(a.id)}" data-section="author-keywords">…</button>`
              : "") +
            '<div class="source">标题/摘要标注 · 按作者汇总</div>'
        : authorKeywordEmpty(a);
    return (
      sources(a.sources) +
      (a.rosterSource ? '<div class="source">用户提供名册</div>' : "") +
      (a.papers.length ? '<div class="source">实验室论文署名</div>' : "")
    );
  }
  function cellStatus(row, key) {
    if (state.view === "authors") {
      if (key === "identity" && row.state === "review") return "cell-conflict";
      if (
        (key === "identity" && row.state === "unlinked") ||
        (key === "papers" && !row.papers.length) ||
        (key === "keywords" && !row.keywords.length)
      )
        return "cell-missing";
      return "";
    }
    const f = row.fields[key];
    if (!f) return "";
    if (f.state === "review" || (f.different && !f.relationship))
      return "cell-conflict";
    if (
      ["missing", "partial", "unlinked", "excluded"].includes(f.state) ||
      (f.state === "empty" && !["citing", "keywords"].includes(key))
    )
      return "cell-missing";
    return "";
  }
  function columnCoverage(rows, key) {
    const obtained = (row) => {
      if (state.view === "authors") {
        if (key === "name") return !!row.name;
        if (key === "aliases") return row.aliases.length > 0;
        if (key === "group") return !!D.meta.groups[row.group];
        if (key === "papers") return row.papers.length > 0;
        if (key === "identity") return row.state === "ready";
        if (key === "keywords") return row.keywords.length > 0;
        if (key === "sources")
          return (
            row.sources.length > 0 ||
            !!row.rosterSource ||
            row.papers.length > 0
          );
        return false;
      }
      const f = row.fields[key];
      return (
        ["ready", "annotated"].includes(f?.state) ||
        (key === "keywords" && f?.state === "empty") ||
        (key === "citing" && f?.state === "empty" && f.total === 0)
      );
    };
    const count = rows.filter(obtained).length;
    const paperRules = {
      references: "取得非空参考名单，且名单内每条文献均有标题。",
      citing: "施引名单与详情已收齐；来源明确报告 0 条也计入。",
      citations: "至少一个来源有可用计数，0 次也计入；来源间有差异仍计入。",
      identity: "至少一个数据库记录已通过匹配核对。",
      vector: "已取得并通过校验的向量。",
      keywords:
        "已采用标题/摘要标注，包括无匹配关键词的有效空结果；标注未采用不计入。",
    };
    const authorRules = {
      name: "已有姓名。",
      aliases: "记录有其他姓名写法。",
      group: "已有分类，包括“其他”。",
      papers: "至少关联一篇实验室论文。",
      identity: "人员身份已确认。",
      keywords: "至少有一个论文关键词可用于统计。",
      sources: "至少有一项资料或论文署名来源。",
    };
    const rule =
      state.view === "authors"
        ? authorRules[key]
        : paperRules[key] || "已有可用内容；来源间有差异仍计入。";
    return {
      text: rows.length ? percent(count / rows.length) : "—",
      help: `到位率：筛选结果 ${count} / ${rows.length}。${rule}`,
    };
  }
  function columnWidth(key, width) {
    const saved = state.widths[state.view]?.[key];
    return Number.isFinite(saved) && saved >= 90 && saved <= 900
      ? saved
      : width;
  }
  function render() {
    coverage();
    setupControls();
    const rows = filtered(),
      size = state.pageSize || Math.max(rows.length, 1),
      pages = Math.max(1, Math.ceil(rows.length / size));
    state.page = Math.min(state.page, pages - 1);
    const columns = definitions[state.view],
      rates = Object.fromEntries(
        columns.map(([key]) => [key, columnCoverage(rows, key)]),
      ),
      widths = columns.map(([key, , width]) => columnWidth(key, width));
    $("data-table").style.width = widths.reduce((a, b) => a + b, 0) + "px";
    $("columns").innerHTML = columns
      .map(
        ([key], i) => `<col data-column="${key}" style="width:${widths[i]}px">`,
      )
      .join("");
    $("table-head").innerHTML =
      "<tr>" +
      columns
        .map(
          ([key, label]) =>
            `<th data-key="${key}" title="${esc(columnHelp(key) + "\n" + rates[key].help)}" aria-sort="${state.sort === key ? (state.ascending ? "ascending" : "descending") : "none"}"><button class="heading-button" data-sort="${key}" title="${esc(columnHelp(key) + "\n" + rates[key].help)}"><span class="heading-label">${label}${state.sort === key ? (state.ascending ? " ↑" : " ↓") : ""}</span><span class="column-coverage">(${rates[key].text})</span></button><span role="separator" tabindex="0" aria-orientation="vertical" aria-label="调整${label}列宽" class="resizer" data-resize="${key}"></span></th>`,
        )
        .join("") +
      "</tr>";
    $("table-body").innerHTML = rows
      .slice(state.page * size, (state.page + 1) * size)
      .map(
        (row) =>
          `<tr class="${state.selected === row.id ? "selected" : ""}">${columns.map(([key]) => `<td data-field="${key}" class="${cellStatus(row, key)}">${state.view !== "authors" ? paperCell(row, key) : authorCell(row, key)}</td>`).join("")}</tr>`,
      )
      .join("");
    $("data-table").setAttribute(
      "aria-label",
      `${state.view === "external" ? "外部文献" : state.view === "papers" ? "论文" : "作者"} ${rows.length} / ${state.view === "external" ? D.external.length : state.view === "papers" ? D.papers.length : D.authors.length}`,
    );
    $("page-count").textContent = `${state.page + 1} / ${pages} 页`;
    $("prev").disabled = state.page === 0;
    $("next").disabled = state.page >= pages - 1;
    $("empty").hidden = rows.length > 0;
    if (state.selected) detail(state.selected);
    else $("detail").hidden = true;
    save();
    return rows;
  }
  function routeMarkup(route) {
    return `<div class="source-history"><b>${esc(route.name || "查询路径")}</b>${href(route.url) ? ` · <a href="${href(route.url)}" target="_blank" rel="noopener">来源 ↗</a>` : ""}<div class="route">${esc(route.url || "")}</div>${route.result ? `<p class="route">${esc(route.result)}</p>` : ""}</div>`;
  }
  function priorMarkup(record) {
    if (!record) return "";
    return (
      `<div class="route">${esc(record.route || "")} · ${esc(record.reason || "")}</div>` +
      priorMarkup(record.previous_attempt)
    );
  }
  function fieldPaperDetail(p) {
    const f = p.fields;
    const metadata = ["title", "authors", "year", "venue", "abstract"]
      .map(
        (key) =>
          `<h3 id="field-${key}">${names[key]}</h3>${
            observationMarkup(
              f[key],
              key === "authors"
                ? (v) =>
                    v
                      .map((name) => {
                        const a = f.authors.value.find(
                          (a) => a.raw === name || a.name === name,
                        );
                        return a ? authorButton(a) : esc(name);
                      })
                      .join(" · ")
                : undefined,
            ) || badge("missing")
          }${key === "venue" ? (f[key].observations || []).flatMap((o) => o.sources.filter((s) => s.originalValue && s.originalValue !== o.value).map((s) => `<div class="source">${esc(s.name)} 原名：${esc(s.originalValue)}</div>`)).join("") : ""}`,
      )
      .join("");
    const renderRecords = (ids) =>
      ids
        .map((id, i) => {
          const r = D.bibliography[id];
          return `<div class="reference">${i + 1}. ${r ? (paperMap.has(r.id) ? paperButton(r.id) : href(r.url) ? `<a href="${href(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>` : esc(r.title)) : `${esc(id)}<div class="source">标题、作者与发表信息未取得</div>`}${r ? `<div class="muted">${esc(r.authors.join(", ") || "作者未取得")}<br>${esc(r.venue || "会议／期刊未取得")} ${esc(r.year ?? "年份未取得")}</div>` : ""}</div>`;
        })
        .join("");
    const records = renderRecords(f.references.value),
      citingRecords = renderRecords(f.citing.ids);
    return `<h2>${esc(p.title)}</h2><a href="index.html?paper=${encodeURIComponent(p.id)}">在网络中查看 ↗</a>${metadata}<h3 id="field-citations">被引次数</h3>${citationMarkup(p, true)}${f.citations.attempts.map((a) => `<div class="source">${esc(a.name)} · ${esc(a.snapshot || "日期未记录")}</div>`).join("")}<h3 id="field-keywords">关键词</h3>${keywordDetail(f.keywords)}${sources(f.keywords.sources)}<p class="muted">${esc(f.keywords.explanation)}</p>${["topics", "vector"].map((key) => `<section class="detail-item"><h3 id="field-${key}">${names[key]}</h3>${key === "vector" ? badge(f[key].state) : f[key].value.map((t) => tag(t.name, key === "topics" && Number.isFinite(t.score) ? " " + percent(t.score) : "", true)).join("") || fieldBadge(f[key], key)}<p>${esc(f[key].explanation)}</p>${sources(f[key].sources)}${key === "vector" ? `${(f[key].routes || []).map((r) => routeMarkup({ name: r.provider || r.source, url: r.url, result: r.result })).join("")}` : ""}</section>`).join("")}<h3 id="failures">查询记录与身份核对</h3>${p.issues.map((i) => `<section class="detail-item"><b>${esc(i.field)}</b><p>${esc(i.reason)}</p>${i.routes.map(routeMarkup).join("")}${priorMarkup(i.previous)}${i.agency ? routeMarkup({ name: "DOI 注册机构", url: i.agency.url, result: i.agency.agency?.label }) : ""}</section>`).join("") || '<p class="muted">没有失败记录</p>'}<h3 id="references">参考文献</h3><p>${esc(f.references.explanation)}</p>${sources(f.references.sources)}${records}<h3 id="citing">施引文献</h3><p>${esc(f.citing.explanation)}</p>${sources(f.citing.sources)}${citingRecords}<h3>论文来源</h3>${p.links
      .filter(href)
      .map(
        (url) =>
          `<p class="route"><a href="${href(url)}" target="_blank" rel="noopener">${esc(url)}</a></p>`,
      )
      .join("")}`;
  }
  function authorDetail(a) {
    return `<h2>${esc(a.name)}${a.chinese && a.chinese !== a.name ? " · " + esc(a.chinese) : ""}</h2><p>${esc(D.meta.groups[a.group].name)} · ${esc(a.identityLabel)}</p>${a.identityNote ? `<p>${esc(a.identityNote)}</p>` : ""}<h3>姓名变体</h3>${a.aliases.map((name) => tag(name)).join("") || "—"}<h3>身份与分类来源</h3>${sources(a.sources)}${a.rosterSource ? `<p class="route">${esc(a.rosterSource)}</p>` : ""}<h3 id="author-keywords">作者关键词 · 加权出现比例</h3><p class="muted">按原始署名顺序，第一作者权重 1、其他作者 0.2。比例为含该词的论文权重占已采用标注论文总权重，分母包含有效空结果。</p>${a.keywords.length ? a.keywords.map((k) => `<div class="detail-item">${tag(k.name, ` <b>${percent(k.weight)}</b>`, true)}<div>${k.papers.map((id) => `<div>${paperButton(id)}</div>`).join("")}</div></div>`).join("") : authorKeywordEmpty(a)}<h3 id="author-papers">署名论文 · ${a.papers.length}</h3>${a.papers.map((id) => `<div class="detail-item">${paperButton(id)}<div class="muted">${esc(paperMap.get(id)?.fields.venue.value.name || "")} ${esc(paperMap.get(id)?.fields.venue.value.year ?? "")}</div></div>`).join("") || badge("unlinked")}`;
  }
  function detail(id) {
    const item =
      state.view !== "authors" ? paperMap.get(id) : authorMap.get(id);
    if (!item) {
      state.selected = null;
      $("detail").hidden = true;
      return;
    }
    $("detail").hidden = false;
    $("detail-content").innerHTML =
      state.view !== "authors" ? fieldPaperDetail(item) : authorDetail(item);
  }
  function select(view, id, section) {
    if (state.view !== view) {
      state.view = view;
      state.search =
        (view !== "authors" ? paperMap : authorMap).get(id)?.[
          view !== "authors" ? "title" : "name"
        ] || "";
      state.field = state.status = state.source = state.group = "all";
      state.page = 0;
      state.sort = view !== "authors" ? "title" : "papers";
      state.ascending = view !== "authors";
    }
    state.selected = id;
    render();
    $("detail").scrollTop = 0;
    if (section) $(section)?.scrollIntoView({ block: "start" });
  }
  document.addEventListener("click", (event) => {
    const paper = event.target.closest("[data-paper]"),
      author = event.target.closest("[data-author]"),
      reference = event.target.closest("[data-reference]"),
      sort = event.target.closest("[data-sort]");
    if (paper)
      select(
        D.external.some((p) => p.id === paper.dataset.paper)
          ? "external"
          : "papers",
        paper.dataset.paper,
        paper.dataset.section,
      );
    else if (author)
      select("authors", author.dataset.author, author.dataset.section);
    else if (reference)
      select("papers", reference.dataset.reference, "references");
    else if (sort) {
      const key = sort.dataset.sort;
      if (state.sort === key) state.ascending = !state.ascending;
      else {
        state.sort = key;
        state.ascending = ["title", "name", "group"].includes(key);
      }
      state.page = 0;
      render();
    }
  });
  document.querySelectorAll("[data-view]").forEach(
    (button) =>
      (button.onclick = () => {
        state.view = button.dataset.view;
        state.field = state.status = state.source = state.group = "all";
        state.search = "";
        state.page = 0;
        state.selected = null;
        state.sort = state.view !== "authors" ? "title" : "papers";
        state.ascending = state.view !== "authors";
        render();
      }),
  );
  $("search").oninput = (e) => {
    state.search = e.target.value;
    state.page = 0;
    render();
  };
  for (const key of ["field", "status", "source", "group"])
    $(key).onchange = (e) => {
      state[key] = e.target.value;
      if (key === "field" && state.field !== "all" && state.status === "all")
        state.status = "gaps";
      state.page = 0;
      render();
    };
  $("page-size").onchange = (e) => {
    state.pageSize = Number(e.target.value);
    state.page = 0;
    render();
  };
  $("prev").onclick = () => {
    state.page--;
    render();
    $("table-scroll").scrollTop = 0;
  };
  $("next").onclick = () => {
    state.page++;
    render();
    $("table-scroll").scrollTop = 0;
  };
  $("close-detail").onclick = () => {
    state.selected = null;
    render();
  };
  $("reset").onclick = () => {
    Object.assign(state, {
      ...defaults,
      widths: { papers: {}, authors: {}, external: {} },
    });
    render();
  };
  let drag = null;
  $("table-head").addEventListener("pointerdown", (e) => {
    const handle = e.target.closest("[data-resize]");
    if (!handle || e.button !== 0) return;
    const col = $("columns").querySelector(
      `[data-column="${handle.dataset.resize}"]`,
    );
    drag = {
      handle,
      key: handle.dataset.resize,
      x: e.clientX,
      width: parseFloat(col.style.width),
      col,
    };
    handle.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  $("table-head").addEventListener("pointermove", (e) => {
    if (!drag) return;
    const width = Math.round(
      Math.max(
        drag.key === "title" || drag.key === "name" ? 200 : 90,
        Math.min(900, drag.width + e.clientX - drag.x),
      ),
    );
    drag.col.style.width = width + "px";
    state.widths[state.view][drag.key] = width;
    const total = definitions[state.view].reduce(
      (n, [key, , base]) => n + columnWidth(key, base),
      0,
    );
    $("data-table").style.width = total + "px";
  });
  for (const type of ["pointerup", "pointercancel"])
    $("table-head").addEventListener(type, () => {
      drag = null;
      save();
    });
  $("table-head").addEventListener("keydown", (e) => {
    const handle = e.target.closest("[data-resize]");
    if (!handle || !["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    e.preventDefault();
    const key = handle.dataset.resize,
      base = definitions[state.view].find((c) => c[0] === key)[2];
    state.widths[state.view][key] = Math.max(
      90,
      Math.min(
        900,
        columnWidth(key, base) + (e.key === "ArrowRight" ? 20 : -20),
      ),
    );
    render();
  });
  $("export").onclick = () => {
    const rows = filtered(),
      quote = (v) => '"' + String(v ?? "").replace(/"/g, '""') + '"';
    let lines;
    if (state.view !== "authors") {
      const keys =
        state.view === "external"
          ? definitions.external.map(([key]) => key)
          : paperKeys;
      const value = (p, k) => {
        const f = p.fields[k];
        if (f.observations?.length)
          return f.observations
            .map(
              (o) =>
                (o.adopted ? "采用：" : "") +
                observedText(o.value) +
                " [" +
                o.sources
                  .map(
                    (s) =>
                      s.name +
                      " " +
                      s.url +
                      (s.originalValue ? " 原名：" + s.originalValue : ""),
                  )
                  .join("; ") +
                "]",
            )
            .join(" | ");
        if (k === "references") return f.value.join("; ");
        if (k === "citing") return f.ids.join("; ");
        if (["keywords", "topics"].includes(k))
          return f.value.map((k) => k.name).join("; ");
        return typeof f.value === "object"
          ? JSON.stringify(f.value)
          : (f.value ?? "");
      };
      lines = [
        [
          "ID",
          ...keys.map((k) => names[k]),
          ...keys.map((k) => names[k] + "状态"),
          ...keys.map((k) => names[k] + "来源差异"),
          "字段说明",
          "请求记录",
        ],
        ...rows.map((p) => [
          p.id,
          ...keys.map((k) => value(p, k)),
          ...keys.map((k) => stateLabels[p.fields[k].state]),
          ...keys.map((k) => (p.fields[k].different ? "是" : "否")),
          keys
            .map((k) => names[k] + ": " + (p.fields[k].explanation || ""))
            .join(" | "),
          p.issues
            .map(
              (i) =>
                i.field +
                ": " +
                i.reason +
                " " +
                i.routes.map((r) => r.url + " " + r.result).join("; "),
            )
            .join(" | "),
        ]),
      ];
    } else
      lines = [
        [
          "ID",
          "姓名",
          "中文姓名",
          "姓名变体",
          "分类",
          "论文数",
          "论文标题",
          "身份核对",
          "关键词加权出现比例",
          "来源",
        ],
        ...rows.map((a) => [
          a.id,
          a.name,
          a.chinese,
          a.aliases.join("; "),
          D.meta.groups[a.group].name,
          a.papers.length,
          a.papers.map((id) => paperMap.get(id)?.title).join("; "),
          a.identityLabel,
          a.keywords.map((k) => k.name + " " + percent(k.weight)).join("; "),
          a.sources
            .map((s) => s.url)
            .concat(a.rosterSource || [])
            .join("; "),
        ]),
      ];
    const blob = new Blob(
        ["\uFEFF" + lines.map((row) => row.map(quote).join(",")).join("\r\n")],
        { type: "text/csv;charset=utf-8" },
      ),
      url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = "lab-atlas-" + state.view + "-retrieval.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  render();
})();
