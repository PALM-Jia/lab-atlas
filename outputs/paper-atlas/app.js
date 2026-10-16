"use strict";
(() => {
  const D = window.ATLAS_DATA;
  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    String(s ?? "").replace(
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
  const safeURL = (s) => {
    try {
      const u = new URL(s);
      return ["http:", "https:"].includes(u.protocol) ? u.href : null;
    } catch {
      return null;
    }
  };
  const topicMap = new Map(D.topics.map((t) => [t.id, t]));
  const researchFields = window.ATLAS_PAPER_FIELDS;
  const fieldMap = new Map(researchFields.fields.map((f) => [f.id, f]));
  const unclassifiedField = {
    id: "unclassified",
    name: "未分领域",
    color: "#969aa4",
  };
  const primaryField = (p) =>
    fieldMap.has(researchFields.papers[p.id]?.primary)
      ? researchFields.papers[p.id].primary
      : "unclassified";
  const reviewedKeywords = (p) =>
    p.keywords || window.ATLAS_PAPER_KEYWORDS?.papers?.[p.id] || [];
  const keywordSearch = (p) =>
    reviewedKeywords(p).flatMap((k) => [
      k.name,
      ...(topicMap.get(k.id)?.aliases || []),
    ]);
  const nodeMap = new Map(D.nodes.map((p) => [p.id, p]));
  const seedExtent = Math.max(
    1,
    ...D.nodes.flatMap((p) => [Math.abs(p.x || 0), Math.abs(p.y || 0)]),
  );
  const seedScale = Math.min(1, 500 / seedExtent);
  const oaMap = new Map(
    D.nodes
      .filter((p) => p.openalex)
      .map((p) => [p.openalex.split("/").pop(), p]),
  );
  const E = window.ATLAS_NETWORK_EVIDENCE || { papers: {}, bibliography: {} };
  for (const p of D.nodes) {
    const fields = E.papers[p.id]?.fields;
    if (Number.isFinite(fields?.citations.adoptedValue))
      p.citations = fields.citations.adoptedValue;
    if (Number.isFinite(fields?.year.adoptedValue))
      p.year = fields.year.adoptedValue;
  }
  const evidenceUI = window.createNetworkEvidenceUI({
    evidence: E,
    nodeMap,
    oaMap,
    topicMap,
    fieldMap,
    researchFields,
    esc,
    safeURL,
  });
  const semanticPaperEdges = D.edges.filter(
    (e) =>
      e.kind === "semantic" &&
      nodeMap.get(e.source)?.lab &&
      nodeMap.get(e.target)?.lab,
  );
  const kinds = {
    citation: "直接引用",
    coupling: "共同参考文献",
    cocitation: "共同被引",
    author: "共同作者",
    author_keyword: "论文关键词分布相似",
    keyword: "论文关键词重合",
    semantic: "标题与摘要相似",
    author_semantic: "标题与摘要相似",
    institution: "共同机构",
  };
  const yearBounds = [2010, 2027];
  const latestYear = yearBounds[1];
  let savedState = {};
  try {
    savedState =
      JSON.parse(
        window.localStorage?.getItem("paper-atlas-state-v1") || "{}",
      ) || {};
  } catch {}
  const state = {
    view: "papers",
    field: "",
    search: "",
    authorshipMode: "muted",
    yearFrom: 2023,
    yearTo: latestYear,
    external: true,
    relation: "citation",
    authorRelation: "coauthor",
    authorGroup: "",
    hub: false,
    selected: null,
  };
  const timelineHistory = window.ATLAS_CITATION_HISTORY;
  const temporal = window.ATLAS_TIMELINE_HISTORY;
  let timelineContext = null,
    timelineSlices = null,
    timelineCandidates = [],
    timelineTopYear = null,
    timelineDetailPaper = null,
    pendingTimelineDetail = false;
  const authorGroups = window.ATLAS_AUTHOR_GROUPS.groups;
  const fieldModes = {},
    groupModes = { ...window.ATLAS_AUTHOR_GROUPS.defaultAuthorModes };
  const authorInterest = { ...window.ATLAS_AUTHOR_GROUPS.defaultPaperInterest };
  function resetCategoryDefaults() {
    for (const modes of [fieldModes, groupModes, authorInterest])
      for (const key of Object.keys(modes)) delete modes[key];
    Object.assign(groupModes, window.ATLAS_AUTHOR_GROUPS.defaultAuthorModes);
    Object.assign(
      authorInterest,
      window.ATLAS_AUTHOR_GROUPS.defaultPaperInterest,
    );
  }
  const paperAuthorInterest = window.createPaperAuthorInterest({
    resolveAuthors: window.resolveAtlasPaperAuthors,
    affiliations: window.ATLAS_AUTHOR_AFFILIATIONS,
  });
  const modeNames = { show: "显示", muted: "弱化", hidden: "不显示" };
  const nextMode = { show: "muted", muted: "hidden", hidden: "show" };
  function paperMode(p) {
    return fieldModes[primaryField(p)] || "show";
  }
  let visible = [],
    graphData = [],
    paperDensityStats = null;
  let renderedView = null;
  const viewports = new Map();
  for (const [view, viewport] of Object.entries(savedState.viewports || {})) {
    if (
      ["papers", "authors"].includes(view) &&
      Number.isFinite(viewport?.zoom) &&
      viewport.zoom >= 0.12 &&
      viewport.zoom <= 4 &&
      Number.isFinite(viewport?.pan?.x) &&
      Number.isFinite(viewport?.pan?.y)
    )
      viewports.set(view, viewport);
  }
  const positions = new Map();
  const cy = cytoscape({
    container: $("graph"),
    elements: [],
    minZoom: 0.12,
    maxZoom: 4,
    style: [
      {
        selector: "node",
        style: {
          "background-color": "data(color)",
          width: "data(size)",
          height: "data(size)",
          "border-width": 1.5,
          "border-color": "data(color)",
          label: "",
          "font-size": 10,
          "font-family": "Segoe UI, Microsoft YaHei",
          color: "#39424b",
          "text-wrap": "ellipsis",
          "text-max-width": 160,
          "text-valign": "bottom",
          "text-margin-y": 7,
          "overlay-opacity": 0,
        },
      },
      {
        selector: "node[!lab]",
        style: { "background-opacity": 0.25, "border-width": 1, opacity: 0.65 },
      },
      {
        selector: "node[pending]",
        style: { "border-style": "dashed", "background-opacity": 0.35 },
      },
      { selector: "node[authorNode]", style: { label: "" } },
      {
        selector: "edge",
        style: {
          width: "data(edgeWidth)",
          "line-color": "#b0b7c7",
          opacity: "data(edgeOpacity)",
          "curve-style": "bezier",
          "target-arrow-shape": "none",
          "arrow-scale": 0.55,
          "overlay-opacity": 0,
        },
      },
      {
        selector: 'edge[kind="citation"]',
        style: {
          "target-arrow-shape": "triangle",
          "target-arrow-color": "#929bb4",
        },
      },
      { selector: "edge[tentative]", style: { "line-style": "dashed" } },
      {
        selector:
          'edge[kind="author_keyword"], edge[kind="author_topic"], edge[kind="author_semantic"]',
        style: { "line-style": "dashed" },
      },
      {
        selector: "node[displayMuted]",
        style: {
          "background-color": "#a9adb5",
          "border-color": "#b9bec6",
          opacity: 0.28,
        },
      },
      {
        selector: "edge[displayMuted]",
        style: { "line-color": "#c8cbd0", "target-arrow-color": "#c8cbd0" },
      },
      { selector: ".faded", style: { opacity: 0.12 } },
      { selector: "edge.faded", style: { opacity: "data(fadedOpacity)" } },
      {
        selector: "node.focus",
        style: {
          "border-width": 3,
          "border-color": "#29313a",
          "z-index": 10,
          opacity: 1,
        },
      },
      { selector: "node.neighbor", style: { opacity: 1 } },
      {
        selector: "edge.focus",
        style: {
          "line-color": "#6575b7",
          "target-arrow-color": "#6575b7",
          width: "data(focusWidth)",
          opacity: "data(focusOpacity)",
        },
      },
      { selector: "edge.inspected", style: { opacity: 0.9 } },
      { selector: "node.hover", style: { "z-index": 20, opacity: 1 } },
    ],
  });
  const dynamicLayout = window.createDynamicLayout({ cy });
  let hoveredNode = null,
    overlayFrame = null;
  const timeline3D = window.createTimeline3D({
    canvas: $("timeline-3d"),
    onSelectNode: (id, context) => {
      timelineContext = context || null;
      id ? focus(id, false, context) : clearSelection();
    },
    onSelectEdge: (edge, context) => {
      timelineContext = context || null;
      timelineDetailPaper = null;
      edgeDetail(edge);
    },
    onCameraChange: (camera) => {
      $("timeline-rotation").value = Math.round(
        (((((camera.yaw * 180) / Math.PI + 180) % 360) + 360) % 360) - 180,
      );
    },
    onYearWindowChange: (range) => {
      timelineTopYear = range.to;
      if (state.view === "timeline")
        $("visible-count").textContent =
          visible.filter((p) => temporal.publicationYear(p) <= range.to)
            .length + " 篇论文";
      scheduleTimelineDetail();
    },
    onHover: (p, point, context) => {
      if (!p) {
        hidePreview();
        return;
      }
      hoveredNode = null;
      const card = $("node-preview");
      card.innerHTML = evidenceUI.preview(
        p,
        state.view === "timeline"
          ? timelinePaperContext(p, context?.year)
          : null,
      );
      card.classList.remove("hidden");
      card.style.left =
        Math.max(
          10,
          Math.min(point.x + 16, cy.width() - card.offsetWidth - 10),
        ) + "px";
      card.style.top =
        Math.max(
          10,
          Math.min(
            point.y - card.offsetHeight - 16,
            cy.height() - card.offsetHeight - 34,
          ),
        ) + "px";
    },
  });
  function scheduleTimelineDetail() {
    if (pendingTimelineDetail || state.view !== "timeline" || !state.selected)
      return;
    pendingTimelineDetail = true;
    Promise.resolve().then(() => {
      pendingTimelineDetail = false;
      if (state.view !== "timeline" || !state.selected) return;
      const scene =
          timeline3D.selectionState?.() || timeline3D.inspect?.() || {},
        selectedElement = cy.getElementById(state.selected);
      if (selectedElement.isEdge()) {
        timelineContext = {
          ...timelineContext,
          year: scene.selectedAssociationYear ?? timelineContext?.year,
          anchorId: scene.anchor?.paperId,
          anchorYear: scene.anchor?.year,
        };
        const p =
          timelineDetailPaper && evidenceUI.find(timelineDetailPaper.paperId);
        if (p) paperDetail(p, timeline3D.contextForPaper?.(p.id));
        else edgeDetail(selectedElement.data());
      } else {
        const p = nodeMap.get(state.selected),
          context = timeline3D.contextForPaper?.(state.selected);
        if (p) {
          timelineContext = context || timelineContext;
          paperDetail(p, context);
        }
      }
    });
  }
  window.ATLAS_TIMELINE_VIEW = timeline3D;
  function timelinePaperContext(
    p,
    year = timelineContext
      ? timelineContext.year
      : (timelineTopYear ?? state.yearTo),
  ) {
    const effectiveYear = Number.isInteger(year) ? year : latestYear;
    return {
      year: effectiveYear,
      citation: temporal.citationAt(
        timelineHistory.papers[p.id],
        effectiveYear,
      ),
    };
  }
  window.installPanelLayout({ cy });
  window.installNodeShadows({ canvas: $("node-shadows"), cy });
  // DOM overlays keep text in screen pixels while the graph zooms and pans.
  const authorLabels = new Map();
  function preview(n) {
    hoveredNode = n;
    const p = nodeMap.get(n.id()),
      author = n.data("authorNode");
    $("node-preview").innerHTML = author
      ? `<div class="preview-title">${esc(n.data("label"))}</div><div class="preview-meta">${esc(authorGroups[n.data("group")].name)} · 参与 ${n.data("papers").length} 篇实验室论文 · ${n.degree()} 位关联作者</div>`
      : evidenceUI.preview(p);
    $("node-preview").classList.remove("hidden");
    scheduleOverlays();
  }
  function hidePreview() {
    hoveredNode = null;
    $("node-preview").classList.add("hidden");
    scheduleOverlays();
  }
  function buildAuthorLabels() {
    authorLabels.clear();
    $("author-labels").replaceChildren();
    if (state.view !== "authors") return;
    cy.nodes().forEach((n) => {
      const b = document.createElement("button");
      b.className = "author-label";
      b.type = "button";
      b.innerHTML = `${esc(n.data("label"))}<small>${n.data("papers").length}</small>`;
      b.setAttribute(
        "aria-label",
        `${n.data("label")}，${n.data("papers").length} 篇论文`,
      );
      b.onclick = () => focus(n.id(), false);
      b.onmouseenter = () => {
        n.addClass("hover");
        preview(n);
      };
      b.onmouseleave = () => {
        n.removeClass("hover");
        hidePreview();
      };
      $("author-labels").append(b);
      authorLabels.set(n.id(), b);
    });
  }
  function scheduleOverlays() {
    if (overlayFrame === null)
      overlayFrame = requestAnimationFrame(updateOverlays);
  }
  function updateOverlays() {
    overlayFrame = null;
    const width = cy.width(),
      height = cy.height();
    if (hoveredNode && !hoveredNode.removed()) {
      const p = hoveredNode.renderedPosition(),
        card = $("node-preview");
      const left = Math.min(
        Math.max(10, p.x + 16),
        Math.max(10, width - card.offsetWidth - 10),
      );
      const top = Math.min(
        Math.max(10, p.y - card.offsetHeight - 18),
        Math.max(10, height - card.offsetHeight - 34),
      );
      card.style.left = left + "px";
      card.style.top = top + "px";
    }
    if (!authorLabels.size) return;
    const occupied = [];
    const nodes = cy
      .nodes()
      .toArray()
      .sort(
        (a, b) =>
          Number(b.hasClass("focus") || b.hasClass("neighbor")) -
            Number(a.hasClass("focus") || a.hasClass("neighbor")) ||
          b.data("papers")?.length - a.data("papers")?.length,
      );
    for (const n of nodes) {
      const b = authorLabels.get(n.id());
      if (!b) continue;
      b.hidden = false;
      const p = n.renderedPosition(),
        w = b.offsetWidth,
        h = b.offsetHeight;
      b.classList.toggle("is-focus", n.hasClass("focus"));
      b.classList.toggle("is-faded", n.hasClass("faded"));
      b.classList.toggle("is-muted", !!n.data("displayMuted"));
      if (
        n.data("displayMuted") &&
        !n.hasClass("focus") &&
        !n.hasClass("hover")
      ) {
        b.hidden = true;
        continue;
      }
      // Minor labels yield to prominent names; hovering any node reveals its full card.
      const box = {
        x: Math.max(4, Math.min(width - w - 4, p.x - w / 2)),
        y: p.y + n.renderedHeight() / 2 + 5,
        w,
        h,
      };
      const outside =
        p.x < 0 || p.x > width || p.y < 0 || box.y + h > height - 32;
      const overlap = occupied.some(
        (r) =>
          box.x < r.x + r.w + 5 &&
          box.x + w + 5 > r.x &&
          box.y < r.y + r.h + 3 &&
          box.y + h + 3 > r.y,
      );
      if (outside || overlap) {
        b.hidden = true;
        continue;
      }
      b.style.left = box.x + "px";
      b.style.top = box.y + "px";
      occupied.push(box);
    }
  }
  cy.on("pan zoom position resize", scheduleOverlays);
  // Faster wheel zoom, anchored at the pointer; native drag and touch gestures remain enabled.
  $("graph").parentElement.addEventListener(
    "wheel",
    (e) => {
      if (state.view === "timeline") return;
      e.preventDefault();
      e.stopImmediatePropagation();
      const rect = $("graph").getBoundingClientRect();
      const delta =
        e.deltaY *
        (e.deltaMode === 1 ? 24 : e.deltaMode === 2 ? cy.height() : 1);
      const level = Math.max(
        cy.minZoom(),
        Math.min(
          cy.maxZoom(),
          cy.zoom() * Math.exp(-Math.max(-160, Math.min(160, delta)) * 0.0035),
        ),
      );
      cy.zoom({
        level,
        renderedPosition: { x: e.clientX - rect.left, y: e.clientY - rect.top },
      });
    },
    { passive: false, capture: true },
  );
  function short(s) {
    return s.length > 65 ? s.slice(0, 62) + "…" : s;
  }
  function filters(
    p,
    {
      ignoreTopics = false,
      ignoreAuthorInterest = false,
      ignoreExternal = false,
    } = {},
  ) {
    if (
      state.view !== "authors" &&
      !ignoreAuthorInterest &&
      !paperAuthorInterest.keep(p, authorInterest)
    )
      return false;
    if (!ignoreTopics && state.view !== "authors" && paperMode(p) === "hidden")
      return false;
    if (
      !ignoreTopics &&
      state.view !== "authors" &&
      state.field &&
      primaryField(p) !== state.field
    )
      return false;
    const dated =
      state.view === "timeline"
        ? temporal.publicationYear(p)
        : Number.isFinite(Number(p.year)) && Number(p.year) > 0
          ? Math.floor(Number(p.year))
          : latestYear;
    if (
      (state.view !== "timeline" &&
        Math.max(yearBounds[0], dated) < state.yearFrom) ||
      dated > state.yearTo
    )
      return false;
    if (!ignoreExternal && !state.external && !p.lab) return false;
    const searchAuthors =
      state.view !== "authors" &&
      !ignoreAuthorInterest &&
      p.lab &&
      paperAuthorInterest.active(authorInterest)
        ? paperAuthorInterest.cared(p, authorInterest).map((a) => a.name)
        : p.authors;
    if (
      state.search &&
      !window.atlasSearchMatch(
        [
          p.title,
          ...searchAuthors,
          ...p.tags.map((t) => topicMap.get(t)?.name || t),
          ...keywordSearch(p),
        ].join(" "),
        state.search,
      )
    )
      return false;
    return true;
  }
  function paperElements(papers, edges) {
    const elements = papers.map((p) => ({
      data: {
        id: p.id,
        label: short(p.title),
        lab: p.lab,
        ...(p.displayMuted ? { displayMuted: true } : {}),
        ...(p.match_status !== "matched" && p.lab ? { pending: true } : {}),
        size: Math.min(
          50,
          8 +
            3 *
              Math.log2(
                1 +
                  (Number.isFinite(p.citations) && p.citations >= 0
                    ? p.citations
                    : 0),
              ),
        ),
        color: p.displayColor,
      },
      position: { x: p.x, y: p.y },
    }));
    return elements.concat(
      edges.map((e) => ({
        data: {
          ...e,
          ...(e.tentative ? { tentative: true } : { tentative: undefined }),
        },
      })),
    );
  }
  function authorsGraph() {
    // Show collaboration documented by the imported lab papers. External papers stay in paper maps.
    const papers = (
      state.hub
        ? D.nodes.filter(
            (p) => p.lab && filters(p, { ignoreAuthorInterest: true }),
          )
        : visible
    ).filter((p) => p.lab);
    const authors = new Map(),
      links = new Map();
    for (const p of papers) {
      const allRecords = window.resolveAtlasPaperAuthors(p),
        firstAuthorId = (
          state.authorshipMode === "only" && state.authorRelation !== "coauthor"
            ? window.atlasStudentFirstAuthor(allRecords)
            : allRecords[0]
        )?.id;
      const records = allRecords.filter((a) => {
        const hubAuthor = state.hub && a.name === "Yuheng Jia";
        return (
          !a.excluded_from_network &&
          (hubAuthor || a.name !== "Yuheng Jia") &&
          (hubAuthor || (groupModes[a.group] || "show") !== "hidden") &&
          (hubAuthor ||
            state.authorshipMode !== "only" ||
            state.authorRelation === "coauthor" ||
            a.id === firstAuthorId)
        );
      });
      const names = records.map((a) => [a.id, a.name]);
      for (const [key, name] of names) {
        if (!authors.has(key)) {
          const person = records.find((a) => a.id === key);
          authors.set(key, {
            id: "a-" + key,
            name,
            group: person.group,
            identityNote: person.identity_note,
            papers: [],
            paperWeights: {},
            firstAuthorPapers: [],
            topics: new Map(),
          });
        }
        const a = authors.get(key);
        a.papers.push(p.id);
        a.paperWeights[p.id] =
          key === firstAuthorId || state.authorshipMode === "all" ? 1 : 0.2;
        if (key === firstAuthorId) a.firstAuthorPapers.push(p.id);
        for (const t of p.tags) a.topics.set(t, (a.topics.get(t) || 0) + 1);
      }
      for (let i = 0; i < names.length; i++)
        for (let j = i + 1; j < names.length; j++) {
          const pair = [names[i][0], names[j][0]].sort(),
            key = pair.join(":");
          if (!links.has(key))
            links.set(key, {
              id: "collab:" + key,
              source: "a-" + pair[0],
              target: "a-" + pair[1],
              kind: "author",
              papers: [],
              score: 0,
              evidence: { text: "共同署名论文" },
            });
          links.get(key).papers.push(p.id);
          links.get(key).score++;
        }
    }
    const top = [...authors.values()]
      .sort(
        (a, b) => b.papers.length - a.papers.length || a.id.localeCompare(b.id),
      )
      .slice(0, 65);
    const ids = new Set(top.map((a) => a.id));
    graphData =
      state.authorRelation === "coauthor"
        ? window.selectAtlasTopEdges(
            [...links.values()].filter(
              (e) => ids.has(e.source) && ids.has(e.target),
            ),
            5,
          )
        : window.buildAuthorRelations({
            authors: top,
            papers,
            paperEdges: semanticPaperEdges,
            mode: state.authorRelation,
          });
    const nodes = top.map((a, i) => ({
      data: {
        id: a.id,
        label: a.name,
        group: a.group,
        ...(groupModes[a.group] === "muted" ? { displayMuted: true } : {}),
        identityNote: a.identityNote,
        lab: true,
        authorNode: true,
        papers: a.papers,
        size: 10 + Math.sqrt(a.papers.length) * 5,
        color:
          groupModes[a.group] === "muted"
            ? "#a9adb5"
            : authorGroups[a.group].color,
      },
      position: {
        x: 250 * Math.cos((i / top.length) * 2 * Math.PI),
        y: 250 * Math.sin((i / top.length) * 2 * Math.PI),
      },
    }));
    return [...nodes, ...graphData.map((e) => ({ data: e }))];
  }
  function render({ resetViewport = false, randomize = false } = {}) {
    dynamicLayout.stop();
    if (resetViewport) {
      viewports.clear();
      positions.clear();
    } else if (renderedView) {
      viewports.set(renderedView, { zoom: cy.zoom(), pan: { ...cy.pan() } });
      if (renderedView !== "timeline") {
        if (!positions.has(renderedView))
          positions.set(renderedView, new Map());
        cy.nodes().forEach((n) =>
          positions.get(renderedView).set(n.id(), { ...n.position() }),
        );
      }
    }
    const viewport = viewports.get(state.view);
    hidePreview();
    visible = D.nodes
      .filter((p) => filters(p))
      .map((p) => {
        const muted = state.view !== "authors" && paperMode(p) === "muted";
        return {
          ...p,
          displayMuted: muted,
          displayColor: muted
            ? "#a9adb5"
            : fieldMap.get(primaryField(p))?.color || unclassifiedField.color,
        };
      });
    const ids = new Set(visible.map((p) => p.id));
    graphData = D.edges.filter(
      (e) =>
        ids.has(e.source) &&
        ids.has(e.target) &&
        e.kind === state.relation &&
        (e.kind !== "citation" ||
          nodeMap.get(e.source)?.lab ||
          nodeMap.get(e.target)?.lab),
    );
    if (
      state.view !== "authors" &&
      ["author", "institution"].includes(state.relation)
    )
      graphData = paperAuthorInterest.edges(
        visible,
        state.relation,
        authorInterest,
      );
    if (state.view !== "authors" && state.relation === "keyword")
      graphData = window.buildPaperKeywordRelations({
        papers: visible,
        keywordData: window.ATLAS_PAPER_KEYWORDS,
      });
    paperDensityStats = null;
    if (state.view !== "authors") {
      if (state.view === "timeline") {
        timelineCandidates = graphData;
        timelineSlices = temporal.buildAnnualSlices(
          visible,
          timelineCandidates,
          timelineHistory,
          {
            yearFrom: state.yearFrom === 2010 ? 2000 : state.yearFrom,
            yearTo: state.yearTo,
            lowerYearBucket: 2000,
          },
        );
        graphData = [
          ...new Map(
            timelineSlices.slices.flatMap((s) => s.edges).map((e) => [e.id, e]),
          ).values(),
        ];
      } else {
        const limited = window.limitPaperEdges(visible, graphData, 5);
        graphData = limited.edges;
        paperDensityStats = limited.stats;
      }
      const connected = new Set(graphData.flatMap((e) => [e.source, e.target]));
      visible = visible.filter(
        (p) =>
          p.lab ||
          connected.has(p.id) ||
          (p.id === state.selected &&
            !(
              state.view === "papers" &&
              paperAuthorInterest.active(authorInterest)
            )),
      );
    }
    let elements =
      state.view === "authors"
        ? authorsGraph()
        : paperElements(visible, graphData);
    const sizeNodes = elements.filter((e) => !e.data.source);
    const mixedSizes = window.atlasMixedNodeSizes(
      sizeNodes.map((e) => e.data.size),
      state.view === "authors" ? { min: 10, max: 60 } : { min: 8, max: 50 },
    );
    sizeNodes.forEach((e, i) => (e.data.size = mixedSizes[i]));
    if (randomize) {
      const layout = new Map();
      for (const e of elements)
        if (!e.data.source) {
          const angle = Math.random() * 2 * Math.PI,
            radius = 300 * Math.sqrt(Math.random());
          layout.set(e.data.id, {
            x: radius * Math.cos(angle),
            y: radius * Math.sin(angle),
          });
        }
      positions.set(state.view, layout);
    }
    if (state.view !== "timeline") {
      const saved = positions.get(state.view);
      elements.forEach((e) => {
        if (saved?.has(e.data.id)) e.position = { ...saved.get(e.data.id) };
        else if (state.view === "papers" && e.position)
          e.position = {
            x: e.position.x * seedScale,
            y: e.position.y * seedScale,
          };
      });
    }
    const nodeCount = elements.length - graphData.length;
    const meanDegree = nodeCount ? (2 * graphData.length) / nodeCount : 0;
    const edgeFade = meanDegree > 5 ? 5 / meanDegree : 1;
    const mutedNodes = new Set(
      elements
        .filter((e) => !e.data.source && e.data.displayMuted)
        .map((e) => e.data.id),
    );
    const scoreRanges = new Map();
    for (const e of graphData) {
      const score = Number(e.score) || 0,
        range = scoreRanges.get(e.kind) || [Infinity, -Infinity];
      range[0] = Math.min(range[0], score);
      range[1] = Math.max(range[1], score);
      scoreRanges.set(e.kind, range);
    }
    for (const element of elements) {
      const e = element.data;
      if (!e.source) continue;
      const [low, high] = scoreRanges.get(e.kind),
        score = Number(e.score) || 0;
      e.edgeStrength = high > low ? (score - low) / (high - low) : 0.5;
      if (e.kind === "author_semantic")
        e.edgeStrength = 0.02 + 0.98 * e.edgeStrength ** 3;
      e.edgeWidth = 0.6 + 1.8 * e.edgeStrength;
      e.focusWidth = e.edgeWidth + 1;
      e.displayMuted =
        mutedNodes.has(e.source) || mutedNodes.has(e.target) ? true : undefined;
      const base = e.kind.startsWith("author_")
        ? 0.42
        : e.tentative
          ? 0.2
          : 0.32;
      e.edgeOpacity =
        base *
        (0.35 + 0.65 * e.edgeStrength) *
        edgeFade *
        (e.displayMuted ? 0.45 : 1);
      e.fadedOpacity = 0.12 * (0.35 + 0.65 * e.edgeStrength) * edgeFade;
      e.focusOpacity =
        e.kind === "author_semantic" ? 0.08 + 0.82 * e.edgeStrength : 0.9;
      if (e.kind === "author_semantic") {
        e.edgeOpacity =
          (0.025 + 0.5 * e.edgeStrength) *
          Math.sqrt(edgeFade) *
          (e.displayMuted ? 0.45 : 1);
        e.fadedOpacity = e.edgeOpacity * 0.15;
      }
    }
    cy.batch(() => {
      cy.elements().remove();
      cy.add(elements);
    });
    if (state.selected && !cy.getElementById(state.selected).length)
      clearSelection();
    const timeline = state.view === "timeline";
    $("timeline-3d").classList.toggle("hidden", !timeline);
    $("graph").parentElement.classList.toggle("is-timeline", timeline);
    if (timeline) {
      if (
        timelineContext?.year != null &&
        (timelineContext.year < timelineSlices.yearFrom ||
          timelineContext.year > state.yearTo)
      )
        timelineContext = null;
      timeline3D.setData({
        papers: visible,
        edges: timelineCandidates,
        history: timelineHistory,
        annual: timelineSlices,
        yearFrom: timelineSlices.yearFrom,
        yearTo: state.yearTo,
        lowerYearBucket: 2000,
        reset: resetViewport,
        randomize,
      });
    }
    timeline3D.setActive(timeline);
    $("timeline-controls").classList.toggle("hidden", !timeline);
    $("graph-help").textContent = timeline
      ? "拖拽：旋转 / 俯仰 · 滚轮：切换年份"
      : "滚轮缩放 · 拖拽平移";
    if (viewport) cy.viewport(viewport);
    else if (cy.nodes().length) cy.fit(undefined, 65);
    renderedView = state.view;
    updateTopics();
    $("paper-author-panel").classList.toggle(
      "hidden",
      state.view === "authors",
    );
    $("external-option").classList.toggle("hidden", state.view === "authors");
    const externalCount = D.nodes.filter(
      (p) => !p.lab && filters(p, { ignoreExternal: true }),
    ).length;
    $("external-label").textContent = `显示外部文献（${externalCount}）`;
    const hubPaperCount = D.nodes.filter(
      (p) =>
        p.lab &&
        filters(p, { ignoreAuthorInterest: true }) &&
        window.resolveAtlasPaperAuthors(p).some((a) => a.name === "Yuheng Jia"),
    ).length;
    $("hub-label").textContent = `包含 Yuheng Jia（${hubPaperCount}）`;
    updateAuthorInterest();
    buildAuthorLabels();
    scheduleOverlays();
    document
      .querySelectorAll("[data-view]")
      .forEach((b) =>
        b.classList.toggle("active", b.dataset.view === state.view),
      );
    $("relation").classList.toggle("hidden", state.view === "authors");
    $("author-relation").classList.toggle("hidden", state.view !== "authors");
    $("hub-option").classList.toggle("hidden", state.view !== "authors");
    $("first-author-option").classList.toggle(
      "hidden",
      state.view !== "authors" || state.authorRelation === "coauthor",
    );
    const authorshipLabel = "仅看第一作者";
    const authorshipCount = visible.filter((p) => p.lab).length;
    const authorshipDescription = {
      all: "全部署名等权计入",
      muted: "非一作权重为0.2",
      only: "只计一作论文（包括导师一作学生二作）",
    }[state.authorshipMode];
    const authorshipButton = $("first-author-only");
    for (const [mode, style] of [
      ["all", "hidden"],
      ["muted", "muted"],
      ["only", "show"],
    ])
      authorshipButton.classList.toggle(
        "is-" + style,
        state.authorshipMode === mode,
      );
    authorshipButton.setAttribute(
      "aria-checked",
      { all: "false", muted: "mixed", only: "true" }[state.authorshipMode],
    );
    authorshipButton.setAttribute(
      "aria-label",
      `${authorshipLabel}（${authorshipCount}）：${authorshipDescription}`,
    );
    authorshipButton.title = `${authorshipDescription}；${authorshipCount}`;
    authorshipButton.innerHTML = `<span class="state-box" aria-hidden="true">${{ all: "", muted: "−", only: "✓" }[state.authorshipMode]}</span><span>${authorshipLabel}（${authorshipCount}）</span>`;
    $("visible-count").textContent = timeline
      ? visible.filter((p) => temporal.publicationYear(p) <= timelineTopYear)
          .length + " 篇论文"
      : cy.nodes().length + " 个节点";
    $("empty").classList.toggle(
      "hidden",
      visible.length > 0 &&
        (state.view === "authors" ? cy.nodes().length > 0 : true),
    );
    $("empty").textContent =
      state.view === "authors" ? "无匹配作者。" : "无匹配论文。";
    if (visible.length && !graphData.length && state.view === "papers") {
      $("empty").classList.remove("hidden");
      $("empty").textContent = "当前筛选下没有此类连接。";
    }
    explainRelation();
    saveViewState();
    if (state.selected) focus(state.selected, false);
    if (state.view !== "timeline")
      dynamicLayout.start({
        kind:
          state.view === "authors"
            ? graphData[0]?.kind || "author"
            : state.relation,
      });
  }
  function explainRelation() {
    const descriptions = {
      keyword: "按论文关键词的重合程度连线，在实验室论文中常见的词影响较小。",
      citation: "依据 OpenAlex 参考文献记录，箭头由引用论文指向被引用论文。",
      coupling:
        "两篇论文引用相同文献。强度 = 共同参考数 ÷ √(两篇参考数乘积)；共同参考至少 2 篇，强度 ≥ 6.0%。",
      cocitation:
        "采集到的其他论文同时引用这两篇论文。强度 = 共同施引数 ÷ √(两篇已采集施引数乘积)。每篇种子最多采集 600 篇施引文献。",
      author:
        "两篇实验室论文有共同作者时连线，强度为共同作者人数。按核对后的人员身份计算，排除 Yuheng Jia。",
      institution:
        "两篇实验室论文共享 OpenAlex 发表署名机构 ID，强度为共同机构数。",
      semantic: "按论文标题和摘要的语义相似程度连线；没有摘要时使用标题。",
    };
    const authorDescriptions = {
      semantic:
        "比较两位作者的不同论文对，按署名权重取标题与摘要相似度的平均值。同一篇论文不与自身比较。",
      keywords:
        "按作者关键词画像的重合程度连线。画像汇总筛选内署名论文的关键词，在实验室论文中常见的词影响较小。",
      coauthor: "两位作者共同署名论文时连线，强度为共同论文数。",
    };
    const author = state.view === "authors";
    const kind = author
      ? {
          coauthor: "author",
          keywords: "author_keyword",
          semantic: "author_semantic",
        }[state.authorRelation]
      : state.relation;
    let description = author
      ? authorDescriptions[state.authorRelation]
      : descriptions[state.relation];
    const authorshipRule = {
      all: "所有署名论文等权计入。",
      muted: "一作论文权重 1，其他署名论文权重 0.2。",
      only: "只计一作论文（包括导师一作学生二作）",
    }[state.authorshipMode];
    const weightExplanation =
      author && state.authorRelation !== "coauthor"
        ? `<p>${esc(authorshipRule)}</p>`
        : "";
    if (!author && state.relation === "author")
      description =
        "两篇实验室论文有共同作者时连线，只计入关心的作者，排除 Yuheng Jia。";
    if (state.view === "timeline" && state.relation === "citation")
      description = "从所选论文最早的可见年度节点，向上连接引用它的文献。";
    const keywordCoverage =
      (author && state.authorRelation === "keywords") ||
      (!author && state.relation === "keyword")
        ? `<p><a href="retrieval.html?field=keywords" target="_blank" rel="noopener">查看关键词依据 ↗</a></p>`
        : "";
    const selectionRule = `<p>${state.view === "timeline" ? "每个年份内，" : ""}各${author ? "作者" : "论文"}选取${!author && state.relation === "citation" ? "5 条引用关联" : "最强的 5 条关联"}，合并两端选择。</p>`;
    const timelineRule =
      state.view === "timeline"
        ? `<p>选中论文后，同时激活它各年的可见节点。粗枝线延续同一论文，${["citation", "author"].includes(state.relation) ? "细实线" : "细虚线"}从最早的可见节点向上连接关联文献，每条关系只绘制一次。</p><p>节点大小按截至该年的累计被引数计算；外部文献只计已采集邻域的被引记录。缺少被引记录的节点使用固定大小。</p>`
        : "";
    const heading =
      author && state.authorRelation === "coauthor" ? "共同署名" : kinds[kind];
    $("relation-explanation").innerHTML =
      `<h3>${esc(heading)}</h3><p>${esc(description)}</p>${weightExplanation}${selectionRule}${timelineRule}${keywordCoverage}`;
  }
  function saveViewState() {
    const query = new URLSearchParams({
      search: state.search,
      field: state.field,
      from: String(state.yearFrom),
      to: String(state.yearTo),
      external: state.external ? "1" : "0",
      view: state.view,
      relation: state.relation,
      authorRelation: state.authorRelation,
      fieldModes: JSON.stringify(fieldModes),
      groupModes: JSON.stringify(groupModes),
      authorInterest: JSON.stringify(authorInterest),
    });
    query.set("fieldSchema", "six-v1");
    query.set("hub", state.hub ? "1" : "0");
    query.set("authorshipMode", state.authorshipMode);
    if (
      renderedView &&
      state.view === renderedView &&
      state.view !== "timeline"
    )
      viewports.set(state.view, { zoom: cy.zoom(), pan: { ...cy.pan() } });
    try {
      window.localStorage?.setItem(
        "paper-atlas-state-v1",
        JSON.stringify({
          query: query.toString(),
          viewports: Object.fromEntries(viewports),
        }),
      );
    } catch {}
  }
  let stateSaveTimer;
  cy.on("pan zoom", () => {
    clearTimeout(stateSaveTimer);
    stateSaveTimer = setTimeout(saveViewState, 150);
  });
  function focus(id, pan = true, explicitTimelineContext = null) {
    const paper = evidenceUI.find(id);
    if (paper) id = paper.id;
    const n = cy.getElementById(id);
    if (!n.length) {
      if (paper) paperDetail(paper);
      return;
    }
    if (n.isEdge()) {
      edgeDetail(n.data());
      return;
    }
    state.selected = id;
    if (state.view === "timeline") {
      const context =
        explicitTimelineContext || timeline3D.contextForPaper?.(id);
      timeline3D.select(id, context || undefined);
      timelineContext = timeline3D.contextForPaper?.(id) ||
        context || { year: timelineTopYear };
    }
    cy.elements().removeClass("faded focus neighbor inspected");
    if (n.length) {
      cy.elements().addClass("faded");
      n.closedNeighborhood().removeClass("faded");
      n.addClass("focus");
      n.connectedEdges().addClass("focus");
      n.neighborhood("node").addClass("neighbor");
      if (pan && state.view !== "timeline")
        cy.animate({ center: { eles: n }, duration: 250 });
    }
    const p = nodeMap.get(id);
    if (p) paperDetail(p);
    else if (n.data("authorNode")) authorDetail(n);
    scheduleOverlays();
    saveViewState();
  }
  function paperDetail(p, contextOverride = null) {
    $("clear-selection").hidden = false;
    const context =
      state.view === "timeline"
        ? contextOverride ||
          timeline3D.contextForPaper?.(p.id, timelineContext?.year) ||
          timelinePaperContext(p)
        : null;
    const sliceYear = context
      ? context.year
      : (timelineContext?.year ?? timelineTopYear ?? state.yearTo);
    const scene =
      state.view === "timeline"
        ? timeline3D.selectionState?.() || timeline3D.inspect?.() || {}
        : null;
    const shown =
      scene && scene.anchor?.paperId === p.id
        ? new Set(scene.visibleAssociationIds)
        : null;
    const detailEdges = shown
      ? graphData.filter((e) => shown.has(e.id))
      : state.view === "timeline"
        ? timelineSlices?.slices.find((s) => s.year === sliceYear)?.edges || []
        : graphData;
    const related = detailEdges
      .filter((e) => e.source === p.id || e.target === p.id)
      .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
      .map((e) => {
        const v = e.evidence || {},
          percent = (e.score * 100).toFixed(1) + "%";
        const summary =
          e.kind === "citation"
            ? e.source === p.id
              ? "参考文献"
              : "施引文献"
            : e.kind === "author"
              ? `共同作者 ${e.score} 位`
              : e.kind === "institution"
                ? `共同机构 ${e.score} 个`
                : e.kind === "semantic"
                  ? `语义相似度 ${percent}`
                  : e.kind === "keyword"
                    ? `关键词重合度 ${percent}`
                    : v.count
                      ? `共同文献 ${v.count} 篇 · 强度 ${percent}`
                      : `连接强度 ${percent}`;
        return {
          paper_id: e.source === p.id ? e.target : e.source,
          edge_id: e.id,
          summary,
          labels: [
            ...(v.shared_keywords || []).map((k) => k.name),
            ...(v.topic_names || []),
            ...(v.tags || []).map((t) => topicMap.get(t)?.name || t),
            ...(v.authors || []),
          ],
        };
      });
    timelineDetailPaper = context
      ? { paperId: p.id, year: context.year }
      : null;
    $("detail-content").innerHTML = evidenceUI.render(
      p,
      related,
      context ? timelinePaperContext(p, context.year) : null,
    );
  }
  function keywordProof(k) {
    if (Array.isArray(k)) return k.map(keywordProof).join("；");
    return [
      { title: "标题", abstract: "摘要" }[k.evidence_field] || k.evidence_field,
      k.exact_quote ? "“" + k.exact_quote + "”" : "",
      k.reason_zh,
    ]
      .filter(Boolean)
      .join(" · ");
  }
  function evidencePaper(id, edgeId) {
    return evidenceUI.link(id, edgeId);
  }
  function evidenceLinks(ids, edgeId) {
    return (ids || []).map((id) => evidencePaper(id, edgeId)).join("");
  }
  function highlightEdges(ids) {
    cy.elements().removeClass("faded focus neighbor inspected");
    cy.elements().addClass("faded");
    for (const id of ids) {
      const edge = cy.getElementById(id);
      edge.removeClass("faded").addClass("focus inspected");
      edge.connectedNodes().removeClass("faded").addClass("neighbor");
    }
    scheduleOverlays();
  }
  function authorRelationMeaning(e) {
    const v = e.evidence || {};
    if (v.aggregation === "weighted_mean")
      return `<p class="detail-meta">论文相似度加权平均 ${(e.score * 100).toFixed(1) + "%"} · ${v.pair_count} 对论文</p>`;
    const topics = (v.shared_topics || []).slice(0, 3);
    if (!topics.length) return "";
    const profiles = v.profiles || [],
      percent = (value) => (value * 100).toFixed(1) + "%";
    return `<div class="detail-section"><h3>主要共同关键词</h3><div class="pills">${topics.map((t) => `<span class="pill">${esc(t.name)} (${esc(profiles[0]?.author_name || "")}: ${percent(t.source_weight)}, ${esc(profiles[1]?.author_name || "")}: ${percent(t.target_weight)})</span>`).join("")}</div></div>`;
  }
  function authorProfileMarkup(profile, showAuthor = true) {
    if (!profile) return "";
    if (profile.semantic)
      return `<div class="detail-section author-profile"><h3>${showAuthor ? esc(profile.author_name) + " · " : ""}用于比较的论文</h3>${profile.paper_contributions.map((p) => `<div>${evidencePaper(p.paper_id)}<span class="detail-meta">署名权重占比 ${(p.share * 100).toFixed(1)}%${p.title_only ? " · 仅标题" : ""}</span></div>`).join("")}</div>`;
    const entries = [...(profile.keywords || profile.topics || [])].sort(
      (a, b) => b.weight - a.weight || a.id.localeCompare(b.id),
    );
    const row = (t) =>
      `<span class="pill" title="${esc(keywordProof(t.evidence || []))}">${esc(topicMap.get(t.id)?.name || t.name)} (${(t.weight * 100).toFixed(1)}%)</span>`;
    return `<div class="detail-section author-profile"><h3>${showAuthor ? esc(profile.author_name) + " · " : ""}关键词</h3>${entries.length ? '<div class="pills">' + entries.map(row).join("") + "</div>" : '<p class="detail-meta">暂无关键词。</p>'}</div>`;
  }
  function edgeDetail(e) {
    $("clear-selection").hidden = false;
    state.selected = e.id;
    if (state.view === "timeline") {
      const shown =
        (timeline3D.selectionState?.() || timeline3D.inspect?.() || {})
          .visibleAssociationIds || [];
      if (
        timelineDetailPaper &&
        [e.source, e.target].includes(timelineDetailPaper.paperId) &&
        (!shown.includes(e.id) ||
          timelineContext?.year !== timelineDetailPaper.year)
      ) {
        timelineContext = {
          year: timelineDetailPaper.year,
          anchorId: timelineDetailPaper.paperId,
          anchorYear: timelineDetailPaper.year,
        };
      }
      timeline3D.select(e.id, timelineContext);
      const inspectedYear = (
        timeline3D.selectionState?.() ||
        timeline3D.inspect?.() ||
        {}
      ).selectedAssociationYear;
      if (Number.isInteger(inspectedYear))
        timelineContext = { ...timelineContext, year: inspectedYear };
    }
    highlightEdges([e.id]);
    const a = nodeMap.get(e.source),
      b = nodeMap.get(e.target);
    const arrow = e.kind === "citation" ? "→" : "↔";
    const basis =
      e.kind === "semantic"
        ? `语义相似度 ${(e.score * 100).toFixed(1)}% · 比较文本：${e.evidence?.text?.replace(/^本地 SPECTER2：/, "").replace(/；余弦相似度$/, "") || "标题与可用摘要"}`
        : e.kind === "citation"
          ? "OpenAlex 记录：左侧论文引用右侧论文。"
          : e.kind === "author"
            ? state.view === "authors"
              ? `共同署名 ${e.papers?.length || e.score} 篇论文`
              : "共同作者"
            : e.evidence?.text;
    $("detail-content").innerHTML =
      `${state.view === "timeline" && timelineContext?.year != null ? `<div class="detail-meta">${esc(timelineContext.year)} 年切片</div>` : ""}<div class="detail-meta" style="margin-top:22px">${esc(a?.title || cy.getElementById(e.source).data("label"))} ${arrow} ${esc(b?.title || cy.getElementById(e.target).data("label"))}</div>${e.kind.startsWith("author_") || e.kind === "keyword" ? "" : `<div class="detail-section"><h3>证据</h3><p class="abstract">${e.kind.startsWith("author_") ? "" : esc(basis)}</p>${e.evidence?.count ? `<p class="detail-meta">共同文献 ${e.evidence.count} 篇 · 归一化强度 ${(e.score * 100).toFixed(1) + "%"}</p>` : ""}${e.evidence?.authors ? `<div class="pills">${e.evidence.authors.map((n) => `<span class="pill">${esc(n)}</span>`).join("")}</div>` : ""}${e.evidence?.tags ? `<div class="pills">${e.evidence.tags.map((t) => `<span class="pill">${esc(topicMap.get(t)?.name || t)}</span>`).join("")}</div>` : ""}${evidenceLinks(e.evidence?.ids, e.id)}${e.papers && !e.kind.startsWith("author_") ? e.papers.map((id) => evidencePaper(id, e.id)).join("") : ""}</div>`}${e.kind === "cocitation" ? '<p class="missing">共同被引基于本次已采集邻域，部分种子设有采集上限。</p>' : ""}`;
    if (e.kind === "keyword") {
      $("detail-content").insertAdjacentHTML(
        "beforeend",
        `<section class="detail-section keyword-evidence"><h3>共同关键词 · ${(e.score * 100).toFixed(1)}%</h3>${(
          e.evidence?.shared_keywords || []
        )
          .map(
            (k) =>
              `<details><summary>${esc(k.name)}</summary>${[
                [a?.title || "论文 1", k.source_evidence],
                [b?.title || "论文 2", k.target_evidence],
              ]
                .map(
                  ([label, proof]) =>
                    `<p class="detail-note"><b>${esc(label)}</b> ${esc(keywordProof(proof || {}))}</p>`,
                )
                .join("")}</details>`,
          )
          .join("")}</section>`,
      );
    }
    const extra = [
      ...(e.evidence?.topic_names || []),
      ...(e.evidence?.institutions || []),
      ...(e.evidence?.series || []),
    ];
    if (extra.length && !e.kind.startsWith("author_"))
      $("detail-content").insertAdjacentHTML(
        "beforeend",
        `<div class="detail-section"><h3>关联字段</h3><div class="pills">${extra.map((v) => `<span class="pill">${esc(v)}</span>`).join("")}</div></div>`,
      );
    if (e.kind.startsWith("author_")) {
      $("detail-content").insertAdjacentHTML(
        "beforeend",
        authorRelationMeaning(e),
      );
      if (e.kind !== "author_semantic")
        $("detail-content").insertAdjacentHTML(
          "beforeend",
          (e.evidence?.profiles || [])
            .map((p) =>
              authorProfileMarkup(
                graphData.profiles?.find((v) => v.author_id === p.author_id) ||
                  p,
              ),
            )
            .join(""),
        );
      if (e.evidence?.aggregation === "keyword_jaccard") {
        const keys = e.evidence.shared_topics.slice(0, 3);
        $("detail-content").insertAdjacentHTML(
          "beforeend",
          `<section class="detail-section"><h3>支撑论文</h3>${keys.map((k) => `<h3>${esc(k.name)}</h3>${e.evidence.profiles.map((p, i) => `<p class="detail-meta">${esc(p.author_name)}</p>${(i ? k.target_papers : k.source_papers).map((id) => evidencePaper(id, e.id)).join("")}`).join("")}`).join("")}</section>`,
        );
      }
      const shared = e.evidence?.shared_papers || [];
      if (shared.length)
        $("detail-content").insertAdjacentHTML(
          "beforeend",
          `<div class="detail-section"><h3>共同署名论文</h3>${shared.map((id) => evidencePaper(id, e.id)).join("")}</div>`,
        );
      const pairs = e.evidence?.paper_pairs || [];
      if (pairs.length)
        $("detail-content").insertAdjacentHTML(
          "beforeend",
          `<div class="detail-section">${e.evidence?.aggregation === "weighted_mean" ? "<h3>代表论文对</h3>" : "<section><h3>支撑论文对</h3>"}${pairs.map((pair) => `<div>${evidencePaper(pair.source, e.id)}<span class="detail-meta">↔ ${Number.isFinite(pair.score) ? (pair.score * 100).toFixed(1) + "%" : ""}${pair.weight ? " · " + "署名权重 " + pair.source_weight + " / " + pair.target_weight : ""}</span>${evidencePaper(pair.target, e.id)}</div>`).join("")}${e.evidence?.aggregation === "weighted_mean" ? "" : "</section>"}</div>`,
        );
      if (e.kind === "author_semantic")
        $("detail-content").insertAdjacentHTML(
          "beforeend",
          (e.evidence?.profiles || [])
            .map((p) => authorProfileMarkup(p))
            .join(""),
        );
    }
  }
  function authorDetail(n) {
    $("clear-selection").hidden = false;
    const papers = n.data("papers").map((id) => nodeMap.get(id));
    const authorEdges = graphData
      .filter((e) => e.source === n.id() || e.target === n.id())
      .sort((a, b) => b.score - a.score);
    const profile = graphData.profiles?.find((p) => p.author_id === n.id());
    const allWeights = new Map();
    let keywordTotal = 0;
    for (const p of papers) {
      if (
        !["annotated", "empty"].includes(
          p.keyword_status || window.ATLAS_PAPER_KEYWORDS?.statuses?.[p.id],
        )
      )
        continue;
      const records = window.resolveAtlasPaperAuthors(p),
        first =
          state.authorshipMode === "only" && state.authorRelation !== "coauthor"
            ? window.atlasStudentFirstAuthor(records)
            : records[0];
      const contribution =
        "a-" + first?.id === n.id() || state.authorshipMode === "all" ? 1 : 0.2;
      keywordTotal += contribution;
      for (const k of new Map(
        reviewedKeywords(p).map((k) => [k.id, k]),
      ).values())
        allWeights.set(k.id, (allWeights.get(k.id) || 0) + contribution);
    }
    const keywordProfile = profile?.keywords
      ? profile
      : {
          keywords: [...allWeights].map(([id, weight]) => ({
            id,
            name: topicMap.get(id)?.name || id,
            dimension: topicMap.get(id)?.dimension,
            weight: weight / keywordTotal,
            evidence: papers.flatMap((p) =>
              reviewedKeywords(p)
                .filter((k) => k.id === id)
                .map((k) => ({ paper_id: p.id, ...k })),
            ),
          })),
        };
    const profileMarkup =
      authorProfileMarkup(keywordProfile, false) +
      (profile?.semantic ? authorProfileMarkup(profile, false) : "");
    const edgeList = authorEdges.length
      ? `<div class="detail-section"><h3>关联作者</h3><div class="pills">${authorEdges.map((e) => `<button class="pill" data-edge="${esc(e.id)}">${esc(cy.getElementById(e.source === n.id() ? e.target : e.source).data("label"))} (${e.kind === "author" ? e.score : (e.score * 100).toFixed(1) + "%"})</button>`).join("")}</div></div>`
      : "";
    $("detail-content").innerHTML =
      `<h2 class="detail-title">${esc(n.data("label"))}</h2><span class="pill">${esc(authorGroups[n.data("group")].name)}</span>${profileMarkup}${edgeList}${profile?.semantic ? "" : `<div class="detail-section"><h3>相关论文</h3>${papers.map((p) => `<button class="neighbor" data-paper="${esc(p.id)}">${esc(p.title)}</button>`).join("")}</div>`}${n.data("identityNote") ? `<p class="detail-note">${esc(n.data("identityNote"))}</p>` : ""}`;
  }
  function clearSelection() {
    state.selected = null;
    timelineContext = null;
    timelineDetailPaper = null;
    timeline3D.select(null);
    cy.elements().removeClass("faded focus neighbor inspected");
    $("detail-content").innerHTML = "";
    $("clear-selection").hidden = true;
    hidePreview();
    scheduleOverlays();
    saveViewState();
  }
  $("lab-count").textContent = D.meta.stats.lab;
  $("external-count").textContent = D.meta.stats.external;
  $("updated").textContent =
    "数据更新 " + (D.meta.keywords?.updated || D.meta.updated).slice(0, 10);
  let yearTimer;
  const yearToSlider = (year) => (year - yearBounds[0]) ** 2;
  const sliderToYear = (value) =>
    yearBounds[0] +
    Math.round(Math.sqrt(Math.max(0, Math.min(289, Number(value)))));
  function updateYearControls() {
    $("year-from").value = yearToSlider(state.yearFrom);
    $("year-to").value = yearToSlider(state.yearTo);
    $("year-from").setAttribute(
      "aria-valuetext",
      state.yearFrom === yearBounds[0]
        ? "2010年及以前"
        : `${state.yearFrom} 年`,
    );
    $("year-to").setAttribute(
      "aria-valuetext",
      state.yearTo === yearBounds[0]
        ? "2010年及更早论文"
        : `${state.yearTo} 年`,
    );
    const span = yearToSlider(yearBounds[1]);
    $("year-range").style.setProperty(
      "--range-start",
      (yearToSlider(state.yearFrom) / span) * 100 + "%",
    );
    $("year-range").style.setProperty(
      "--range-end",
      (yearToSlider(state.yearTo) / span) * 100 + "%",
    );
    // Both thumbs remain usable when the interval reaches either endpoint.
    $("year-from").style.zIndex = state.yearFrom === yearBounds[1] ? "3" : "2";
  }
  ["year-from", "year-to"].forEach((id) => {
    const input = $(id);
    input.min = 0;
    input.max = yearToSlider(yearBounds[1]);
    const change = (e) => {
      const year = sliderToYear(e.target.value);
      if (id === "year-from") state.yearFrom = Math.min(year, state.yearTo);
      else state.yearTo = Math.max(year, state.yearFrom);
      updateYearControls();
      clearTimeout(yearTimer);
      if (e.type === "input") yearTimer = setTimeout(render, 120);
      else render();
    };
    input.oninput = change;
    input.onchange = change;
    input.onkeydown = (e) => {
      const direction = {
        ArrowRight: 1,
        ArrowUp: 1,
        ArrowLeft: -1,
        ArrowDown: -1,
      }[e.key];
      if (!direction) return;
      e.preventDefault();
      const year = Math.max(
        yearBounds[0],
        Math.min(
          yearBounds[1],
          (id === "year-from" ? state.yearFrom : state.yearTo) + direction,
        ),
      );
      input.value = yearToSlider(year);
      change({ target: input, type: "change" });
    };
  });
  $("year-ticks").innerHTML = [2010, 2018, 2023, latestYear]
    .map(
      (year) =>
        `<span style="left:${(yearToSlider(year) / 289) * 100}%">${year === 2010 ? "−∞" : year}</span>`,
    )
    .join("");
  updateYearControls();
  $("topics").addEventListener("click", (e) => {
    const b = e.target.closest("[data-category]");
    if (!b) return;
    const modes = state.view === "authors" ? groupModes : fieldModes;
    modes[b.dataset.category] = nextMode[modes[b.dataset.category] || "show"];
    state.field = "";
    render();
  });
  function authorCategoryCounts(papers, { authorView = false } = {}) {
    const groups = new Map(
      Object.keys(authorGroups).map((id) => [id, new Set()]),
    );
    for (const p of papers) {
      const records = window.resolveAtlasPaperAuthors(p);
      const first = (
        state.authorshipMode === "only" && state.authorRelation !== "coauthor"
          ? window.atlasStudentFirstAuthor(records)
          : records[0]
      )?.id;
      for (const a of records) {
        if (a.excluded_from_network) continue;
        if (
          authorView &&
          ((!state.hub && a.name === "Yuheng Jia") ||
            (state.authorshipMode === "only" &&
              state.authorRelation !== "coauthor" &&
              a.id !== first))
        )
          continue;
        groups.get(a.group)?.add(a.id);
      }
    }
    return new Map([...groups].map(([id, people]) => [id, people.size]));
  }
  function updateTopics() {
    const author = state.view === "authors",
      modes = author ? groupModes : fieldModes;
    $("category-heading").textContent = author ? "作者分类" : "研究领域";
    const categories = author
      ? Object.entries(authorGroups).map(([id, g]) => ({ id, ...g }))
      : [
          ...researchFields.fields,
          ...(D.nodes.some((p) => primaryField(p) === "unclassified")
            ? [unclassifiedField]
            : []),
        ];
    const candidates = D.nodes.filter(
      (p) => p.lab && filters(p, { ignoreTopics: true }),
    );
    const counts = author
      ? authorCategoryCounts(candidates, { authorView: true })
      : new Map(
          categories.map((t) => [
            t.id,
            candidates.filter((p) => primaryField(p) === t.id).length,
          ]),
        );
    const categoryMarkup = (t) => {
      const mode = modes[t.id] || "show",
        checked = { show: "true", muted: "mixed", hidden: "false" }[mode];
      return `<button type="button" class="topic category-state is-${mode}" role="checkbox" aria-checked="${checked}" aria-label="${esc(t.name)}：${modeNames[mode]}，${counts.get(t.id) || 0} ${author ? "人" : "篇实验室论文"}" data-category="${t.id}"><span class="state-box" style="--category-color:${esc(t.color)}" aria-hidden="true">${{ show: "✓", muted: "−", hidden: "" }[mode]}</span><span title="${author ? "当前年份和搜索范围内的去重作者人数" : "当前其他筛选条件下，以该领域为主领域的实验室论文数"}">${esc(t.name)}（${counts.get(t.id) || 0}）</span><small>${modeNames[mode]}</small></button>`;
    };
    $("topics").classList.remove("keyword-chips");
    $("topics").innerHTML = categories.map(categoryMarkup).join("");
  }
  $("clear-topic").onclick = () => {
    state.field = "";
    const modes = state.view === "authors" ? groupModes : fieldModes;
    for (const key of Object.keys(modes)) delete modes[key];
    render();
  };
  function updateAuthorInterest() {
    const counts = authorCategoryCounts(
      D.nodes.filter(
        (p) => p.lab && filters(p, { ignoreAuthorInterest: true }),
      ),
    );
    $("paper-author-interest").innerHTML = Object.entries(authorGroups)
      .map(([id, g]) => {
        const care = authorInterest[id] !== false;
        return `<button type="button" class="topic category-state ${care ? "is-show" : "is-hidden"}" role="checkbox" aria-checked="${care}" aria-label="${esc(g.name)}：${care ? "关心" : "不关心"}，${counts.get(id) || 0} 人" data-care="${id}"><span class="state-box" style="--category-color:#9399a3" aria-hidden="true">${care ? "✓" : ""}</span><span title="当前其他筛选条件下的去重作者人数">${esc(g.name)}（${counts.get(id) || 0}）</span><small>${care ? "关心" : "不关心"}</small></button>`;
      })
      .join("");
  }
  $("paper-author-interest").addEventListener("click", (e) => {
    const b = e.target.closest("[data-care]");
    if (!b) return;
    authorInterest[b.dataset.care] = authorInterest[b.dataset.care] === false;
    render();
  });
  $("care-all").onclick = () => {
    for (const key of Object.keys(authorInterest)) delete authorInterest[key];
    render();
  };
  let searchTimer;
  $("search").oninput = (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.search = e.target.value.trim().toLowerCase();
      render();
    }, 180);
  };
  $("first-author-only").onclick = () => {
    state.authorshipMode = { all: "muted", muted: "only", only: "all" }[
      state.authorshipMode
    ];
    render();
  };
  $("relation").onchange = (e) => {
    state.relation = e.target.value;
    render();
  };
  $("author-relation").onchange = (e) => {
    state.authorRelation = e.target.value;
    render();
  };
  ["external", "hub"].forEach(
    (k) =>
      ($(k).onchange = (e) => {
        state[k] = e.target.checked;
        render();
      }),
  );
  document.querySelectorAll("[data-view]").forEach(
    (b) =>
      (b.onclick = () => {
        state.view = b.dataset.view;
        state.selected = null;
        clearSelection();
        render();
      }),
  );
  document.body.addEventListener("click", (e) => {
    const edgeButton = e.target.closest("[data-edge]");
    if (edgeButton) {
      focus(edgeButton.dataset.edge, false);
      if (edgeButton.dataset.paper) {
        const paper = evidenceUI.find(edgeButton.dataset.paper);
        if (paper) paperDetail(paper);
      }
      return;
    }
    const b = e.target.closest("[data-paper]");
    if (!b) return;
    if (state.view === "authors") {
      const related = graphData.filter(
        (edge) =>
          edge.papers?.includes(b.dataset.paper) &&
          (edge.source === state.selected || edge.target === state.selected),
      );
      if (related.length) highlightEdges(related.map((edge) => edge.id));
      else {
        cy.elements().removeClass("faded focus neighbor inspected");
        cy.elements().addClass("faded");
        cy.nodes()
          .filter((n) => n.data("papers")?.includes(b.dataset.paper))
          .removeClass("faded")
          .addClass("neighbor");
        scheduleOverlays();
      }
      const paper = evidenceUI.find(b.dataset.paper);
      if (paper) paperDetail(paper);
      return;
    }
    focus(b.dataset.paper);
  });
  $("clear-selection").onclick = clearSelection;
  $("reset").onclick = () => render({ randomize: true });
  $("timeline-rotation").oninput = (e) =>
    timeline3D.rotate((Number(e.target.value) * Math.PI) / 180);
  for (const [id, step] of [
    ["timeline-rotate-left", -15],
    ["timeline-rotate-right", 15],
  ])
    $(id).onclick = () => {
      const degrees =
        ((((Number($("timeline-rotation").value) + step + 180) % 360) + 360) %
          360) -
        180;
      $("timeline-rotation").value = degrees;
      timeline3D.rotate((degrees * Math.PI) / 180);
    };
  $("fit").onclick = () =>
    state.view === "timeline" ? timeline3D.fit() : cy.fit(undefined, 65);
  $("zoom-in").onclick = () =>
    state.view === "timeline"
      ? timeline3D.zoom(1.4)
      : cy.zoom({
          level: Math.min(4, cy.zoom() * 1.4),
          renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
        });
  $("zoom-out").onclick = () =>
    state.view === "timeline"
      ? timeline3D.zoom(1 / 1.4)
      : cy.zoom({
          level: Math.max(0.12, cy.zoom() / 1.4),
          renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
        });
  cy.on("tap", "node", (e) => focus(e.target.id(), false));
  cy.on("tap", "edge", (e) => edgeDetail(e.target.data()));
  cy.on("tap", (e) => {
    if (e.target === cy) clearSelection();
  });
  cy.on("mouseover", "node", (e) => {
    e.target.addClass("hover");
    preview(e.target);
  });
  cy.on("mouseout", "node", (e) => {
    e.target.removeClass("hover");
    hidePreview();
  });
  const incoming = new URLSearchParams(
    typeof savedState.query === "string" ? savedState.query : "",
  );
  for (const [key, value] of new URLSearchParams(window.location?.search || ""))
    incoming.set(key, value);
  try {
    const values = JSON.parse(incoming.get("authorInterest") || "{}");
    if (incoming.has("authorInterest"))
      for (const key of Object.keys(authorInterest)) delete authorInterest[key];
    for (const [key, value] of Object.entries(values))
      if (Object.hasOwn(authorGroups, key) && typeof value === "boolean")
        authorInterest[key] = value;
  } catch {}
  for (const [param, modes, allowed] of [
    [
      "fieldModes",
      fieldModes,
      new Map([...fieldMap, [unclassifiedField.id, unclassifiedField]]),
    ],
    ["groupModes", groupModes, new Map(Object.entries(authorGroups))],
  ]) {
    try {
      const values = JSON.parse(incoming.get(param) || "{}");
      if (param === "fieldModes" && incoming.get("fieldSchema") !== "six-v1")
        continue;
      if (incoming.has(param))
        for (const key of Object.keys(modes)) delete modes[key];
      for (const [key, mode] of Object.entries(values))
        if (allowed.has(key) && Object.hasOwn(modeNames, mode))
          modes[key] = mode;
    } catch {}
  }
  if (["all", "muted", "only"].includes(incoming.get("authorshipMode")))
    state.authorshipMode = incoming.get("authorshipMode");
  else if (incoming.has("firstAuthorOnly"))
    state.authorshipMode =
      incoming.get("firstAuthorOnly") === "1" ? "only" : "muted";
  if (
    ["citation", "author", "semantic", "keyword"].includes(
      incoming.get("relation"),
    )
  )
    state.relation = incoming.get("relation");
  else if (incoming.get("relation") === "topic") state.relation = "semantic";
  const requestedPaper = incoming.get("paper");
  if (nodeMap.has(requestedPaper)) {
    state.selected = requestedPaper;
    state.view = "papers";
  } else {
    for (const key of ["search", "field"])
      if (incoming.has(key)) state[key] = incoming.get(key);
    if (["papers", "authors", "timeline"].includes(incoming.get("view")))
      state.view = incoming.get("view");
    if (incoming.get("authorRelation") === "topic")
      state.authorRelation = "keywords";
    else if (
      ["coauthor", "keywords", "semantic"].includes(
        incoming.get("authorRelation"),
      )
    )
      state.authorRelation = incoming.get("authorRelation");
    for (const key of ["hub"])
      if (incoming.has(key)) state[key] = incoming.get(key) === "1";
    if (Object.hasOwn(authorGroups, incoming.get("authorGroup")))
      for (const key of Object.keys(authorGroups))
        groupModes[key] =
          key === incoming.get("authorGroup") ? "show" : "hidden";
    for (const [key, param] of [
      ["yearFrom", "from"],
      ["yearTo", "to"],
    ])
      if (incoming.has(param) && Number.isFinite(Number(incoming.get(param))))
        state[key] = Math.max(
          2010,
          Math.min(latestYear, Math.round(Number(incoming.get(param)))),
        );
    state.yearFrom = Math.min(state.yearFrom, state.yearTo);
    if (incoming.has("external"))
      state.external = incoming.get("external") !== "0";
  }
  if (!fieldMap.has(state.field) && state.field !== "unclassified")
    state.field = "";
  $("relation").value = state.relation;
  $("search").value = state.search;
  $("author-relation").value = state.authorRelation;
  $("external").checked = state.external;
  $("hub").checked = state.hub;

  updateYearControls();
  updateTopics();
  render();
  window.addEventListener("resize", () => cy.resize());
})();
