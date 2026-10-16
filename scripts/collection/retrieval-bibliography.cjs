/* Evidence lists use the full saved collection, independently of graph-node selection. */
const fs = require("node:fs");
module.exports = function ({ nodes, needed, saved }) {
  const records = JSON.parse(fs.readFileSync(saved, "utf8"));
  const bibliography = Object.fromEntries(
    Object.entries(records).filter(([id]) => needed.has(id)),
  );
  // Keep the lab identity and previously adopted graph metadata when already present.
  for (const p of nodes) {
    const entry = {
      id: p.id,
      title: p.title,
      authors: p.authors,
      venue: p.venue,
      year: p.year,
      citations: p.citations ?? null,
      url: p.doi || p.openalex || p.links?.[0] || "",
      source: p.source,
    };
    bibliography[p.id] = entry;
    if (p.openalex) bibliography[p.openalex.split("/").pop()] = entry;
  }
  return bibliography;
};
