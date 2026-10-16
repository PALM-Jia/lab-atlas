/* Keyword overlap from papers, retaining concrete author/keyword/paper evidence. */
(function (root) {
  "use strict";
  function buildAuthorKeywordRelations({
    authors = [],
    papers = [],
    keywordData = root.ATLAS_PAPER_KEYWORDS || {},
  } = {}) {
    const allowed = new Set(papers.map((p) => p.id)),
      profiles = new Map();
    const vocabulary = new Map(
      (keywordData.vocabulary || []).map((k) => [k.id, k]),
    );
    const valid = (id) =>
      ["annotated", "empty"].includes(keywordData.statuses?.[id]);
    const labels = (id) =>
      keywordData.statuses?.[id] === "annotated"
        ? [
            ...new Map(
              (keywordData.papers?.[id] || [])
                .filter((k) => k.id && vocabulary.has(k.id))
                .map((k) => [k.id, { ...k, ...vocabulary.get(k.id) }]),
            ).values(),
          ]
        : [];
    const unique = [...new Map(authors.map((a) => [a.id, a])).values()].sort(
      (a, b) => a.id.localeCompare(b.id),
    );
    for (const author of unique) {
      const weights = new Map(),
        keywordPapers = new Map(),
        names = new Map(),
        keywordEvidence = new Map(),
        contributions = [];
      let total = 0,
        covered = 0;
      for (const id of new Set(author.papers || [])) {
        if (!allowed.has(id) || !valid(id)) continue;
        const keywords = labels(id);
        const contribution = author.paperWeights?.[id] === 1 ? 1 : 0.2;
        total += contribution;
        covered++;
        contributions.push({
          paper_id: id,
          weight: contribution,
          first_author: author.firstAuthorPapers
            ? author.firstAuthorPapers.includes(id)
            : contribution === 1,
        });
        for (const k of new Map(keywords.map((k) => [k.id, k])).values()) {
          weights.set(k.id, (weights.get(k.id) || 0) + contribution);
          names.set(k.id, k.name);
          if (!keywordPapers.has(k.id)) keywordPapers.set(k.id, []);
          keywordPapers.get(k.id).push(id);
          if (!keywordEvidence.has(k.id)) keywordEvidence.set(k.id, []);
          keywordEvidence.get(k.id).push({ paper_id: id, ...k });
        }
      }
      for (const [id, w] of weights) weights.set(id, w / total);
      profiles.set(author.id, {
        weights,
        keywordPapers,
        names,
        keywordEvidence,
        covered,
        total,
        contributions,
      });
    }
    const publicProfiles = unique.map((author) => {
      const p = profiles.get(author.id);
      return {
        author_id: author.id,
        author_name: author.name,
        total_papers: new Set(
          (author.papers || []).filter((id) => allowed.has(id)),
        ).size,
        profiled_papers: p.covered,
        paper_contributions: p.contributions,
        contribution_weight: p.total,
        keywords: [...p.weights]
          .map(([id, weight]) => ({
            id,
            name: p.names.get(id),
            dimension: vocabulary.get(id)?.dimension,
            weight,
            papers: p.keywordPapers.get(id),
            evidence: p.keywordEvidence.get(id),
          }))
          .sort((a, b) => b.weight - a.weight || a.id.localeCompare(b.id)),
      };
    });
    const edges = [];
    let validPairs = 0;
    for (let i = 0; i < unique.length; i++)
      for (let j = i + 1; j < unique.length; j++) {
        const a = unique[i],
          b = unique[j],
          pa = profiles.get(a.id),
          pb = profiles.get(b.id);
        if (!pa.total || !pb.total) continue;
        validPairs++;
        const union = new Set([...pa.weights.keys(), ...pb.weights.keys()]);
        let numerator = 0,
          denominator = 0;
        const shared = [];
        for (const id of union) {
          const aw = pa.weights.get(id) || 0,
            bw = pb.weights.get(id) || 0,
            idf = keywordData.idf?.[id] || 1;
          numerator += Math.min(aw, bw) * idf;
          denominator += Math.max(aw, bw) * idf;
          if (aw && bw)
            shared.push({
              id,
              name: pa.names.get(id) || pb.names.get(id),
              source_weight: aw,
              target_weight: bw,
              dimension: vocabulary.get(id)?.dimension,
              contribution: Math.min(aw, bw) * idf,
              source_papers: pa.keywordPapers.get(id),
              target_papers: pb.keywordPapers.get(id),
              source_evidence: pa.keywordEvidence.get(id),
              target_evidence: pb.keywordEvidence.get(id),
            });
        }
        if (!numerator || !denominator) continue;
        shared.sort(
          (a, b) => b.contribution - a.contribution || a.id.localeCompare(b.id),
        );
        const score = numerator / denominator,
          ids = [
            ...new Set(
              shared
                .slice(0, 3)
                .flatMap((k) => [...k.source_papers, ...k.target_papers]),
            ),
          ];
        edges.push({
          id: "author_keyword:" + a.id + ":" + b.id,
          source: a.id,
          target: b.id,
          kind: "author_keyword",
          score,
          papers: ids,
          evidence: {
            aggregation: "keyword_jaccard",
            shared_topics: shared,
            shared_keywords: shared,
            keyword_names: shared.map((k) => k.name),
            profiles: [
              publicProfiles.find((p) => p.author_id === a.id),
              publicProfiles.find((p) => p.author_id === b.id),
            ],
            numerator,
            denominator,
            paper_pairs: [],
          },
        });
      }
    const select =
      root.selectAtlasTopEdges ||
      (typeof require === "function"
        ? require("./paper-density.js").selectTopEdges
        : null);
    const result = select(edges, 5);
    result.stats = {
      threshold: null,
      top_k: 5,
      valid_pairs: validPairs,
      positive_pairs: edges.length,
      eligible_pairs: edges.length,
      selected_pairs: result.length,
    };
    result.profiles = publicProfiles;
    return result;
  }
  root.buildAuthorKeywordRelations = buildAuthorKeywordRelations;
  if (typeof module !== "undefined" && module.exports)
    module.exports = buildAuthorKeywordRelations;
})(typeof window !== "undefined" ? window : globalThis);
