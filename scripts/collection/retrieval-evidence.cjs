// Field-level observations preserve each source; differences never overwrite values.
const labels = {
  openalex: "OpenAlex",
  semantic_scholar: "Semantic Scholar",
  crossref: "Crossref",
};
const venue = require("./venue-normalization.cjs");
function canonicalField(value, key) {
  const norm = (s) =>
    String(s ?? "")
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[^\p{L}\p{N}]/gu, "");
  if (key === "authors")
    return value
      .map((s) =>
        norm(
          String(s).includes(",")
            ? String(s).split(",").reverse().join(" ")
            : s,
        ),
      )
      .join("|");
  if (key === "venue") return venue(value).id;
  return typeof value === "string" ? norm(value) : JSON.stringify(value);
}
module.exports = function ({
  p,
  fields,
  comparison,
  homepageRecord,
  publicRecord,
  source,
  homepage,
  snapshot,
}) {
  const canonical = (v, k) =>
    k === "authors"
      ? require("./author-list-normalization.cjs")(p, v)
      : canonicalField(v, k);
  const add = (key, value, src, extra = {}) => {
    if (
      value == null ||
      value === "" ||
      (Array.isArray(value) && !value.length)
    )
      return;
    fields[key].observations ??= [];
    fields[key].observations.push({ value, source: src, ...extra });
  };
  fields.year = {
    value: p.year ?? null,
    state: Number.isFinite(p.year) ? "ready" : "missing",
    sources: fields.venue.sources,
  };
  fields.abstract = {
    value: p.abstract || "",
    state: p.abstract ? "ready" : "missing",
    sources: [
      source(
        p.metadata_sources?.abstract || p.source,
        /^https?:/.test(p.metadata_sources?.abstract || "")
          ? p.metadata_sources.abstract
          : p.openalex || homepage,
      ),
    ],
  };
  fields.citing = {
    value: p.citing_collected ?? null,
    state:
      p.citing_collected > 0
        ? p.citing_complete
          ? "ready"
          : "partial"
        : p.citing_status === "database_observed"
          ? "empty"
          : "missing",
    sources: [source("OpenAlex", p.openalex)],
    total: p.citing_total ?? null,
  };
  fields.citations = {
    value: null,
    state: "missing",
    sources: [],
    observations: [],
    attempts: [],
  };
  for (const [key, name] of Object.entries(labels)) {
    const f = fields[key];
    fields.citations.attempts.push({
      name,
      state: f.state,
      reason: f.reason,
      url: f.sources[0]?.url || "",
      snapshot: f.snapshot,
    });
    if (f.state === "ready")
      add("citations", f.value, f.sources[0], { snapshot: f.snapshot });
  }
  if (fields.citations.observations.length) {
    fields.citations.state = "ready";
    fields.citations.sources = fields.citations.observations.map(
      (o) => o.source,
    );
  }
  // Retain the saved citing-query total separately from the work-record count.
  if (fields.openalex.state === "ready" && Number.isFinite(p.citing_total))
    add(
      "citations",
      p.citing_total,
      source(
        "OpenAlex 施引查询",
        "https://api.openalex.org/works?filter=cites:" +
          p.openalex.split("/").pop(),
      ),
    );
  add("title", p.list_title || p.title, source("实验室主页", homepage));
  const chosen = p.versions?.find((v) => v.id === p.openalex);
  if (p.openalex)
    add("title", chosen?.title || p.title, source("OpenAlex", p.openalex));
  add("authors", p.authors, fields.authors.sources[0]);
  add("authors", p.list_authors, source("实验室主页", homepage));
  add("venue", p.venue, fields.venue.sources[0]);
  add("venue", p.list_venue, source("实验室主页", homepage));
  add("year", p.year, fields.year.sources[0]);
  add("year", p.list_year, source("实验室主页", homepage));
  fields.year.isPreprint = homepageRecord?.publication_status === "预印本";
  if (fields.year.isPreprint)
    add("year", "预印", source("实验室主页", homepage));
  add("abstract", p.abstract, fields.abstract.sources[0]);
  if (publicRecord) {
    const src = source(
      "论文原始发布页",
      publicRecord.source || publicRecord.links?.[0],
    );
    for (const k of ["title", "authors", "abstract", "year"])
      add(k, publicRecord[k], src);
  }
  for (const [key, name] of Object.entries(labels)) {
    const r = comparison?.[key];
    if (r?.status !== "success") continue;
    const src = source(name, r.url);
    add("title", Array.isArray(r.title) ? r.title[0] : r.title, src);
    add("year", r.year, src);
    add(
      "authors",
      r.authors
        ?.map((a) => (typeof a === "string" ? a : a.name))
        .filter(Boolean),
      src,
    );
  }
  for (const [key, f] of Object.entries(fields)) {
    if (!f.observations) continue;
    const groups = new Map();
    for (const o of f.observations) {
      const id = canonical(o.value, key);
      if (!groups.has(id))
        groups.set(id, {
          value:
            key === "venue"
              ? venue(o.value).label
              : key === "authors" &&
                  canonical(o.value, key) === canonical(p.authors, key)
                ? p.authors
                : o.value,
          sources: [],
        });
      const g = groups.get(id);
      if (
        !g.sources.some(
          (s) => s.name === o.source.name && s.url === o.source.url,
        )
      )
        g.sources.push({
          ...o.source,
          snapshot: o.snapshot,
          ...(["venue", "authors"].includes(key)
            ? {
                originalValue:
                  key === "authors" ? o.value.join(" · ") : o.value,
                rawValue: o.value,
              }
            : {}),
        });
    }
    f.observations = [...groups.values()];
    f.different = f.observations.length > 1;
    if (f.observations.length && f.state === "missing") f.state = "ready";
  }
  // Venue is now its own column; a missing year is handled in the year field.
  const adopt = (key, value) => {
    const f = fields[key];
    let o = f.observations?.find(
      (o) => canonical(o.value, key) === canonical(value, key),
    );
    if (!o) o = f.observations?.[0];
    if (!o) return;
    o.adopted = true;
    f.adoptedValue = o.value;
    f.adoptedSources = o.sources;
    f.observations.sort((a, b) => Number(!!b.adopted) - Number(!!a.adopted));
  };
  adopt("title", p.title);
  adopt("authors", p.authors);
  adopt("abstract", p.abstract);
  const homepagePublication =
    /arxiv|cornell/i.test(p.venue || "") && homepageRecord?.venue;
  adopt("venue", homepagePublication ? homepageRecord.venue : p.venue);
  adopt(
    "year",
    fields.year.isPreprint
      ? "预印"
      : homepagePublication && Number.isFinite(homepageRecord.year)
        ? homepageRecord.year
        : p.year,
  );
  const countSource =
    fields.citations.observations.find((o) =>
      o.sources.some((s) => s.name === "OpenAlex 施引查询"),
    ) ||
    fields.citations.observations.find((o) =>
      o.sources.some((s) => s.name === "OpenAlex"),
    ) ||
    fields.citations.observations.find((o) =>
      o.sources.some((s) => s.name === "Semantic Scholar"),
    ) ||
    fields.citations.observations[0];
  if (countSource) {
    adopt("citations", countSource.value);
    fields.citations.value = countSource.value;
  }
  fields.citations.adoptionReason =
    Number.isFinite(p.citing_total) && fields.openalex.state === "ready"
      ? "采用当前施引查询快照的报告总数；论文记录中的计数另行保留。"
      : fields.openalex.state === "ready"
        ? "采用 OpenAlex 论文记录计数。"
        : "OpenAlex 无可用计数，采用 Semantic Scholar，再由 Crossref 补缺。";
  fields.venue.state = fields.venue.observations?.length ? "ready" : "missing";
  const venueValues = (fields.venue.observations || []).map((o) => o.value);
  if (venueValues.length === 2 && venueValues.includes("arXiv"))
    fields.venue.relationship = "预印本／发表记录";
  if (
    venueValues.length === 2 &&
    venueValues.includes("LNCS") &&
    venueValues.includes("ECCV")
  )
    fields.venue.relationship = "会议／论文集系列";
  fields.citations.explanation =
    fields.citations.adoptionReason +
    " 各来源相同值合并来源，不同值并列，不相加。";
  fields.references.collectionNote = "Semantic Scholar 参考文献补缺尚未接入";
  fields.citing.collectionNote = "Semantic Scholar 施引名单补缺尚未接入";
  fields.keywords.collectionNote =
    "OpenAlex 自动关键词；作者关键词尚未统一汇总";
  fields.citations.collectionNote =
    "Google Scholar 未采集；Crossref 保留已有结果";
  fields.references.explanation = fields.references.total
    ? `${fields.references.total} 个参考文献 ID；${fields.references.parsed} 条已取得标题，${fields.references.total - fields.references.parsed} 条缺标题等详情。`
    : fields.references.state === "empty"
      ? "OpenAlex 参考文献字段返回空列表。"
      : "未取得参考文献列表；具体身份查询路径见详情。";
  fields.citing.explanation =
    p.citing_collected > 0
      ? `已收集 ${p.citing_collected} 条，OpenAlex 报告 ${p.citing_total ?? "未知"} 条。`
      : fields.citing.state === "empty"
        ? "OpenAlex 施引查询返回空列表。"
        : "未取得施引名单；具体查询路径见详情。";
  fields.keywords.explanation = fields.keywords.value.length
    ? "OpenAlex 自动标注关键词。"
    : p.openalex
      ? "OpenAlex 关键词字段返回空列表。"
      : "未匹配 OpenAlex 记录，关键词字段尚未取得。";
  fields.identity.explanation =
    fields.identity.state === "review"
      ? "论文版本或候选身份尚未确认。"
      : fields.identity.state === "missing"
        ? "尚无已校验的 OpenAlex 或 Semantic Scholar 记录。"
        : "至少一个数据库记录已通过身份校验。";
  for (const key of ["title", "authors", "venue", "year", "abstract"])
    fields[key].explanation = fields[key].observations?.length
      ? "列出已保存来源的值；大小写和标点差异归并。"
      : "现有记录没有该字段的可用值。";
  if (fields.venue.observations?.length)
    fields.venue.explanation =
      "会刊简称与全称按别名表归一；保留各来源原名。预印本、会议、Findings、Workshop 和论文集系列分别保留。";
  if (fields.venue.relationship)
    fields.venue.explanation +=
      " 当前记录属于" + fields.venue.relationship + "并存。";
  fields.authors.explanation =
    "同篇论文内归并姓名顺序、缩写、标点、数据库编号及已核对的解析或拼写错误；保留各来源原始名单，署名顺序和成员差异分别保留。";
  return fields;
};
