"use strict";
(() => {
  const data = window.ATLAS_AUTHOR_IDENTITIES;
  const people = new Map(data.people.map((p) => [p.id, p]));
  const occurrences = new Map(
    data.occurrences.map((o) => [o.paper_id + "\u0000" + o.name, o.person_id]),
  );
  window.resolveAtlasPaperAuthors = (paper) => {
    const resolved = new Map();
    for (const name of paper.authors || []) {
      const id = occurrences.get(paper.id + "\u0000" + name);
      const person = people.get(id) || {
        id: "unresolved-" + paper.id + "-" + name,
        name,
        identity_note: "新增署名尚未进行人员核查。",
      };
      const displayName = person.display_name || person.name;
      resolved.set(person.id, {
        ...person,
        name: displayName,
        identity_name: person.name,
        excluded_from_network: (
          window.ATLAS_AUTHOR_GROUPS.excludedPersonIds || []
        ).includes(person.id),
        group: window.ATLAS_AUTHOR_GROUPS.assignments[person.name] || "other",
      });
    }
    return [...resolved.values()];
  };
  window.atlasStudentFirstAuthor = (authors) =>
    authors[0]?.name === "Yuheng Jia" && authors.length > 1
      ? authors[1]
      : authors[0];
})();
