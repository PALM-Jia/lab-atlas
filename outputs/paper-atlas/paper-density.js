/* Shared per-node top-K union for every displayed relation. */
(function (root) {
  "use strict";
  function selectTopEdges(edges, k = 5) {
    const ranks = new Map(),
      result = [];
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
        result.push({
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
    return result;
  }
  function limitPaperEdges(papers, edges, k = 5) {
    const available = new Set(papers.map((p) => p.id));
    const candidates = edges.filter(
      (e) => available.has(e.source) && available.has(e.target),
    );
    const selected = selectTopEdges(candidates, k),
      degrees = new Map(),
      candidateDegrees = new Map();
    for (const e of candidates)
      for (const id of [e.source, e.target])
        candidateDegrees.set(id, (candidateDegrees.get(id) || 0) + 1);
    for (const e of selected)
      for (const id of [e.source, e.target])
        degrees.set(id, (degrees.get(id) || 0) + 1);
    const lab = papers.filter((p) => p.lab),
      nodeCount = papers.filter((p) => p.lab || degrees.has(p.id)).length;
    return {
      edges: selected,
      stats: {
        top_k: k,
        threshold: null,
        candidate_edges: candidates.length,
        selected_edges: selected.length,
        mean_degree: nodeCount ? (2 * selected.length) / nodeCount : 0,
        total_papers: lab.length,
        eligible_papers: lab.filter(
          (p) => (candidateDegrees.get(p.id) || 0) >= 2,
        ).length,
        covered_papers: lab.filter((p) => (degrees.get(p.id) || 0) >= 2).length,
        missing_papers: lab.filter((p) => !candidateDegrees.has(p.id)).length,
        insufficient_candidates: lab.filter(
          (p) => candidateDegrees.get(p.id) === 1,
        ).length,
      },
    };
  }
  root.selectAtlasTopEdges = selectTopEdges;
  root.limitPaperEdges = limitPaperEdges;
  root.coverSemanticPapers = limitPaperEdges;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = limitPaperEdges;
    module.exports.selectTopEdges = selectTopEdges;
    module.exports.coverSemanticPapers = limitPaperEdges;
  }
})(typeof window !== "undefined" ? window : globalThis);
