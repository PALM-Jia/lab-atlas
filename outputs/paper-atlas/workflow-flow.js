// Port runs include the corner radius, leaving at least 16 px of straight line.
const FLOW_PORT_RUN = 24,
  FLOW_CORNER_RADIUS = 8,
  FLOW_HEADER_HEIGHT = 76;
window.renderWorkflowFlow = function (data, map, guide) {
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
  const measure = (label) =>
    Math.max(
      84,
      ...label
        .split("\n")
        .map(
          (line) =>
            [...line].reduce(
              (s, c) => s + (/[\u0000-\u007f]/.test(c) ? 7 : 12),
              0,
            ) + 24,
        ),
    );
  const left = 88,
    gap = FLOW_PORT_RUN * 2;
  let cursor = left,
    y = FLOW_HEADER_HEIGHT;
  const all = [
    ...data.nodes,
    ...data.processes.map((n) => ({ ...n, process: true })),
  ];
  const rows = data.rows.map((row) => {
    const r = { ...row, top: y };
    y += r.height;
    return r;
  });
  const rowMap = new Map(rows.map((r) => [r.id, r]));
  const colors = new Map(map.tracks.map((t) => [t.id, t.color])),
    info = new Map(map.information.map((i) => [i.id, i]));
  let previousRightPadding = 0;
  const columns = map.stages.map((stage, index) => {
    const local = all.filter((n) => n.stage === index),
      count = Math.max(0, ...local.map((n) => n.slot)) + 1;
    const stageGap = gap,
      padding = [2, 3].includes(index) ? 10 : 6;
    // Entering a bent cross-stage edge needs the 24 px port run plus a 16 px gutter.
    const routeGutter = [1, 2, 3].includes(index)
      ? Math.max(FLOW_PORT_RUN + 16, FLOW_PORT_RUN * 2 - previousRightPadding)
      : 0;
    const leftPadding = Math.max(padding, routeGutter);
    const sizes = Array.from({ length: count }, (_, slot) =>
      Math.max(
        84,
        ...local.filter((n) => n.slot === slot).map((n) => measure(n.label)),
      ),
    );
    const width = Math.max(
        measure(stage.label),
        sizes.reduce((s, w) => s + w, 0) +
          stageGap * (count - 1) +
          leftPadding +
          padding,
      ),
      points = [];
    let x = cursor + leftPadding;
    for (const w of sizes) {
      points.push(x + w / 2);
      x += w + stageGap;
    }
    const c = { left: cursor, width, center: cursor + width / 2, points };
    previousRightPadding = cursor + width - (points.at(-1) + sizes.at(-1) / 2);
    cursor += width;
    return c;
  });
  const items = all.map((n) => ({
    ...n,
    x: columns[n.stage].points[n.slot],
    y: rowMap.get(n.row).top + n.offset,
    width: measure(n.label),
    height: n.label.split("\n").length * 20 + 8,
    color: n.process ? "#6b6585" : colors.get(info.get(n.info).track),
  }));
  const registry = new Map(items.map((n) => [n.id, n])),
    width = cursor + 12,
    height = y;
  const edges = data.edges.map((e, index) => ({
    ...e,
    id: "flow-edge-" + index,
    fromNode: registry.get(e.from),
    toNode: registry.get(e.to),
  }));
  const paths = routeFields(items, columns, width, height);
  const routed = new Map(edges.map((e) => [e.id, paths(e)]));
  bundleFieldRoutes(edges, routed, items, columns);
  const headers = map.stages
    .map(
      (s, i) =>
        `<button data-stage="${s.id}" class="stage-header${s.fixed ? " checkpoint" : ""}" style="left:${columns[i].left}px;width:${columns[i].width}px" aria-pressed="false"><strong>${esc(s.label)}</strong><small>${esc(s.mode)}</small></button>`,
    )
    .join("");
  const bands = rows
    .map(
      (r) =>
        `<div class="flow-row" style="top:${r.top}px;height:${r.height}px;--track:${colors.get(info.get(r.info).track)}"><div class="flow-row-header"><button class="flow-group-label" data-flow-group="${r.id}" aria-pressed="false">${esc(r.label)}</button></div></div>`,
    )
    .join("");
  const grid = columns
    .map(
      (c) =>
        `<span class="flow-column" style="left:${c.left}px;width:${c.width}px;top:${FLOW_HEADER_HEIGHT}px;height:${height - FLOW_HEADER_HEIGHT}px"></span>`,
    )
    .join("");
  const visible = edges
    .map((e) => {
      const points = routed.get(e.id),
        branch = fieldBranch(points),
        shared = e.fromNode.process && e.type === "value",
        color =
          e.type === "query" ? "#9396a8" : shared ? "#9693a5" : e.toNode.color;
      return `<path d="${roundedFieldPath(points)}" data-flow-trace="${e.id}" class="flow-visible ${e.type}" ${shared ? "" : `marker-end="url(#flow-arrow)"`} style="stroke:${color}"/>${shared ? `<path d="${roundedFieldPath(branch)}" data-flow-trace="${e.id}" class="flow-visible" marker-end="url(#flow-arrow)" style="stroke:${e.toNode.color}"/>` : ""}`;
    })
    .join("");
  const lines = `<svg class="flow-paths" width="${width}" height="${height}"><defs><marker id="flow-arrow" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 6 3 L 0 6 Z" fill="context-stroke"/></marker></defs><g class="flow-ink">${visible}</g>${edges.map((e) => `<path data-flow-edge="${e.id}" role="button" tabindex="0" aria-pressed="false" aria-label="${esc(e.fromNode.label)} → ${esc(e.toNode.label)}" d="${roundedFieldPath(routed.get(e.id))}" class="flow-hit"/>`).join("")}</svg>`;
  const labels = items
    .map(
      (n) =>
        `<button class="flow-node ${n.process ? "flow-process" : n.settled ? "life-settle" : "life-event"}" data-flow-node="${n.id}" ${n.process ? `data-action="${n.id}"` : `data-info="${n.info}"`} style="left:${n.x}px;top:${n.y - n.height / 2}px;width:${n.width}px;height:${n.height}px;--track:${n.color}">${esc(n.label)}</button>`,
    )
    .join("");
  return {
    html: `${bands}${grid}${lines}${labels}<div class="lifecycle-header"><span class="flow-corner" aria-hidden="true"></span>${headers}</div>`,
    width,
    height,
    portRun: FLOW_PORT_RUN,
    cornerRadius: FLOW_CORNER_RADIUS,
    columns,
    routes: routed,
    nodes: registry,
    edges: new Map(edges.map((e) => [e.id, e])),
  };
};
function routeFields(items, columns, width, height) {
  const boxes = items.map((n) => ({
    id: n.id,
    left: n.x - n.width / 2 - 4,
    right: n.x + n.width / 2 + 4,
    top: n.y - n.height / 2 - 6,
    bottom: n.y + n.height / 2 + 6,
  }));
  const unique = (v) => [...new Set(v)].sort((a, b) => a - b);
  const clear = (a, b, ignore = []) =>
    !boxes
      .filter((r) => !ignore.includes(r.id))
      .some((r) =>
        a.x === b.x
          ? a.x > r.left &&
            a.x < r.right &&
            Math.max(a.y, b.y) > r.top &&
            Math.min(a.y, b.y) < r.bottom
          : a.y > r.top &&
            a.y < r.bottom &&
            Math.max(a.x, b.x) > r.left &&
            Math.min(a.x, b.x) < r.right,
      );
  return (e) => {
    const a = e.fromNode,
      b = e.toNode,
      source = { x: a.x + a.width / 2, y: a.y },
      target = { x: b.x - b.width / 2, y: b.y };
    if (target.x <= source.x)
      throw Error("Non-forward edge: " + e.from + " -> " + e.to);
    if (source.y === target.y && clear(source, target, [e.from, e.to]))
      return [source, target];
    if (a.stage !== b.stage) {
      const x = Math.max(columns[b.stage].left + 16, target.x - FLOW_PORT_RUN),
        candidate = [source, { x, y: source.y }, { x, y: target.y }, target];
      if (
        x - source.x >= FLOW_PORT_RUN &&
        target.x - x >= FLOW_PORT_RUN &&
        candidate
          .slice(1)
          .every((p, i) => clear(candidate[i], p, [e.from, e.to]))
      )
        return compactFieldPoints(candidate);
    }
    const start = { x: source.x + FLOW_PORT_RUN, y: source.y },
      finish = { x: target.x - FLOW_PORT_RUN, y: target.y };
    const endpointColumns = [...new Set([a.stage, b.stage])].map(
      (i) => columns[i],
    );
    const allowed = (x) =>
      endpointColumns.some(
        (c) => x >= c.left + 16 && x <= c.left + c.width - 16,
      );
    const xs = unique([
      start.x,
      finish.x,
      ...endpointColumns.flatMap((c) => [c.left + 20, c.left + c.width - 20]),
      ...boxes.flatMap((r) => [r.left - 12, r.right + 12]),
    ]).filter((x) => x >= start.x && x <= finish.x);
    const ys = unique([
      start.y,
      finish.y,
      82,
      height - 14,
      ...boxes.flatMap((r) => [r.top - 10, r.bottom + 10]),
    ]);
    const nx = xs.length,
      index = (x, y) => y * nx + x,
      coords = (i) => ({ x: xs[i % nx], y: ys[Math.floor(i / nx)] });
    const first = index(xs.indexOf(start.x), ys.indexOf(start.y)),
      last = index(xs.indexOf(finish.x), ys.indexOf(finish.y));
    const distance = new Map([[first, 0]]),
      previous = new Map(),
      open = [first],
      closed = new Set();
    const heuristic = (i) => {
      const p = coords(i);
      return Math.abs(p.x - finish.x) + Math.abs(p.y - finish.y);
    };
    while (open.length) {
      let best = 0;
      for (let i = 1; i < open.length; i++)
        if (
          distance.get(open[i]) + heuristic(open[i]) <
          distance.get(open[best]) + heuristic(open[best])
        )
          best = i;
      const current = open.splice(best, 1)[0];
      if (current === last) break;
      if (closed.has(current)) continue;
      closed.add(current);
      const x = current % nx,
        y = Math.floor(current / nx),
        p = coords(current);
      for (const [dx, dy] of [
        [1, 0],
        [0, 1],
        [0, -1],
      ]) {
        if (dy && !allowed(p.x)) continue;
        const xx = x + dx,
          yy = y + dy;
        if (xx < 0 || xx >= nx || yy < 0 || yy >= ys.length) continue;
        const next = index(xx, yy),
          q = coords(next);
        if (closed.has(next) || !clear(p, q)) continue;
        const cost =
          distance.get(current) + Math.abs(p.x - q.x) + Math.abs(p.y - q.y) + 2;
        if (cost < (distance.get(next) ?? Infinity)) {
          distance.set(next, cost);
          previous.set(next, current);
          open.push(next);
        }
      }
    }
    if (!distance.has(last)) throw Error("No stage-local route: " + e.id);
    const route = [];
    for (let n = last; n !== undefined; n = previous.get(n))
      route.unshift(coords(n));
    return compactFieldPoints([source, ...route, target]);
  };
}
function compactFieldPoints(points) {
  const out = [];
  for (const p of points) {
    if (out.length && out.at(-1).x === p.x && out.at(-1).y === p.y) continue;
    while (out.length > 1) {
      const a = out.at(-2),
        b = out.at(-1);
      if ((a.x === b.x && b.x === p.x) || (a.y === b.y && b.y === p.y))
        out.pop();
      else break;
    }
    out.push(p);
  }
  return out;
}
function roundedFieldPath(input) {
  const p = compactFieldPoints(input);
  if (!p.length) return "";
  let d = `M ${p[0].x} ${p[0].y}`;
  for (let i = 1; i < p.length - 1; i++) {
    const a = p[i - 1],
      b = p[i],
      c = p[i + 1],
      ab = Math.hypot(b.x - a.x, b.y - a.y),
      bc = Math.hypot(c.x - b.x, c.y - b.y),
      r = Math.min(FLOW_CORNER_RADIUS, ab / 2, bc / 2);
    const u = {
        x: b.x + ((a.x - b.x) * r) / ab,
        y: b.y + ((a.y - b.y) * r) / ab,
      },
      v = { x: b.x + ((c.x - b.x) * r) / bc, y: b.y + ((c.y - b.y) * r) / bc };
    d += ` L ${u.x} ${u.y} Q ${b.x} ${b.y} ${v.x} ${v.y}`;
  }
  return d + ` L ${p.at(-1).x} ${p.at(-1).y}`;
}
function bundleFieldRoutes(edges, routes, nodes, columns) {
  const groups = new Map();
  for (const e of edges) {
    const key =
      e.type === "query"
        ? `in:${e.to}:${e.type}`
        : `out:${e.from}:${e.toNode.stage}:${e.type}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  }
  const clear = (points, e) =>
    points.every((q, i) => {
      if (!i) return true;
      const p = points[i - 1];
      if (q.x < p.x) return false;
      return !nodes.some((n) => {
        if (n.id === e.from || n.id === e.to) return false;
        const l = n.x - n.width / 2 - 4,
          r = n.x + n.width / 2 + 4,
          t = n.y - n.height / 2 - 4,
          b = n.y + n.height / 2 + 4;
        return p.x === q.x
          ? p.x > l &&
              p.x < r &&
              Math.max(p.y, q.y) > t &&
              Math.min(p.y, q.y) < b
          : p.y > t &&
              p.y < b &&
              Math.max(p.x, q.x) > l &&
              Math.min(p.x, q.x) < r;
      });
    });
  for (const [key, group] of groups) {
    if (group.length < 2) continue;
    const lo =
        Math.max(...group.map((e) => e.fromNode.x + e.fromNode.width / 2)) +
        FLOW_PORT_RUN,
      hi =
        Math.min(...group.map((e) => e.toNode.x - e.toNode.width / 2)) -
        FLOW_PORT_RUN;
    if (hi < lo) continue;
    const phase = columns[group[0].toNode.stage],
      buses = [hi, (lo + hi) / 2, lo].filter(
        (x) => x >= phase.left + 16 && x <= phase.left + phase.width - 16,
      );
    let applied = false;
    for (const bus of buses) {
      for (const shift of [0, 24, -24]) {
        const candidates = group.map((e) => {
          const a = { x: e.fromNode.x + e.fromNode.width / 2, y: e.fromNode.y },
            b = { x: e.toNode.x - e.toNode.width / 2, y: e.toNode.y };
          const points = key.startsWith("in:")
            ? [a, { x: bus, y: a.y }, { x: bus, y: b.y }, b]
            : [
                a,
                { x: a.x + FLOW_PORT_RUN, y: a.y },
                { x: a.x + 12, y: a.y + shift },
                { x: bus, y: a.y + shift },
                { x: bus, y: b.y },
                b,
              ];
          return compactFieldPoints(points);
        });
        if (candidates.every((p, i) => clear(p, group[i]))) {
          group.forEach((e, i) => routes.set(e.id, candidates[i]));
          applied = true;
          break;
        }
      }
      if (applied) break;
    }
  }
}

function fieldBranch(points) {
  const p = compactFieldPoints(points),
    a = p.at(-2),
    b = p.at(-1);
  if (p.length < 3) return [a, b];
  const prev = p.at(-3),
    r = Math.min(
      9,
      Math.hypot(a.x - prev.x, a.y - prev.y) / 2,
      Math.hypot(b.x - a.x, b.y - a.y) / 2,
    );
  return [{ x: a.x + r, y: a.y }, b];
}
