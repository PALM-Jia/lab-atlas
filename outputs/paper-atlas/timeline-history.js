/* Pure offline temporal projections. No DOM, clock, query, or data mutation. */
(function (root, factory) {
  const selector =
    (root && root.selectAtlasTopEdges) ||
    (typeof require === "function"
      ? require("./paper-density.js").selectTopEdges
      : null);
  const api = factory(selector);
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.ATLAS_TIMELINE_HISTORY = api;
})(typeof window === "object" ? window : null, function (sharedSelector) {
  "use strict";
  // The atlas year range ends at 2027; records without a usable publication
  // year are placed in that latest slice so they remain visible by default.
  const LATEST_YEAR = 2027;
  function validYear(value) {
    return Number.isInteger(value) && value > 0 ? value : null;
  }
  function datedYear(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}(?:T|$)/.test(value))
      return null;
    const date = value.slice(0, 10);
    const parsed = new Date(date + "T00:00:00Z");
    return Number.isFinite(parsed.getTime()) &&
      parsed.toISOString().slice(0, 10) === date
      ? validYear(Number(date.slice(0, 4)))
      : null;
  }
  function publicationYear(paper) {
    const versions = (paper.versions || [])
      .map(
        (v) =>
          datedYear(v.publication_date) ||
          datedYear(v.date) ||
          validYear(v.year),
      )
      .filter((y) => y !== null);
    return versions.length
      ? Math.min(...versions)
      : datedYear(paper.publication_date) ||
          validYear(paper.year) ||
          LATEST_YEAR;
  }
  function citationAt(entry, year) {
    const available = !!entry && entry.status !== "missing";
    const count = available
      ? (entry.annual || []).reduce(
          (n, row) =>
            n +
            (validYear(row.year) !== null && row.year <= year ? row.count : 0),
          0,
        )
      : null;
    return {
      count,
      unknownYearCount: entry ? entry.unknownYearCount : null,
      observedCount: entry ? entry.observedCount : null,
      databaseTotal: entry ? entry.databaseTotal : null,
      scope: entry ? entry.scope : "unavailable",
      status: entry ? entry.status : "missing",
      complete: !!(entry && entry.complete),
      snapshot: entry ? entry.snapshot : null,
    };
  }
  function edgeActiveAt(edge, papersById, year) {
    const source =
      papersById instanceof Map
        ? papersById.get(edge.source)
        : papersById[edge.source];
    const target =
      papersById instanceof Map
        ? papersById.get(edge.target)
        : papersById[edge.target];
    if (!source || !target) return false;
    if (edge.kind === "citation" && !source.lab && !target.lab) return false;
    const sourceYear = publicationYear(source),
      targetYear = publicationYear(target);
    return (
      sourceYear !== null &&
      targetYear !== null &&
      sourceYear <= year &&
      targetYear <= year
    );
  }
  function selectTopEdges(edges, k) {
    if (sharedSelector) return sharedSelector(edges, k);
    const ranks = new Map(),
      selected = [];
    const ranked = edges
      .filter((e) => e.source !== e.target && Number.isFinite(e.score))
      .slice()
      .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
    for (const edge of ranked) {
      const selectedBy = [];
      for (const id of [edge.source, edge.target]) {
        const rank = (ranks.get(id) || 0) + 1;
        ranks.set(id, rank);
        if (rank <= k) selectedBy.push(id);
      }
      if (selectedBy.length)
        selected.push({
          ...edge,
          evidence: {
            ...edge.evidence,
            threshold: null,
            threshold_rule: "top_k_union",
            top_k: k,
            selected_by: selectedBy,
          },
        });
    }
    return selected;
  }
  function buildAnnualSlices(papers, edges, history, options) {
    options = options || {};
    const lowerYearBucket = validYear(options.lowerYearBucket) || 2000;
    const entries = history && history.papers ? history.papers : history || {};
    const byId = new Map(papers.map((p) => [p.id, p]));
    const dated = papers.map((p) => ({
      paper: p,
      publicationYear: publicationYear(p),
    }));
    const known = dated.filter((p) => p.publicationYear !== null);
    const observedYears = known.map((p) =>
      Math.max(lowerYearBucket, p.publicationYear),
    );
    const yearFrom = Math.max(
      lowerYearBucket,
      validYear(options.yearFrom) ||
        (observedYears.length ? Math.min(...observedYears) : lowerYearBucket),
    );
    const yearTo =
      validYear(options.yearTo) ||
      (observedYears.length ? Math.max(...observedYears) : yearFrom);
    const years = [];
    for (let year = yearFrom; year <= yearTo; year++) years.push(year);
    const slices = years.map((year) => {
      const appearances = known
        .filter((p) => p.publicationYear <= year)
        .map((p) => ({
          id: p.paper.id + "@" + year,
          paperId: p.paper.id,
          year,
          publicationYear: p.publicationYear,
          citation: citationAt(entries[p.paper.id], year),
        }));
      return {
        year,
        label: year === lowerYearBucket ? "≤" + lowerYearBucket : String(year),
        appearances,
        nodes: appearances,
        edges: selectTopEdges(
          edges.filter((e) => edgeActiveAt(e, byId, year)),
          5,
        ),
      };
    });
    const unknown = dated
      .filter((p) => p.publicationYear === null)
      .map((p) => ({
        id: p.paper.id + "@unknown",
        paperId: p.paper.id,
        year: null,
        publicationYear: null,
        citation: {
          count: null,
          status: "unknown_publication_year",
          scope: entries[p.paper.id]
            ? entries[p.paper.id].scope
            : "unavailable",
        },
      }));
    return { years, slices, unknown, lowerYearBucket, yearFrom, yearTo };
  }
  return { publicationYear, citationAt, edgeActiveAt, buildAnnualSlices };
});
