/* Verify the real canvas command stream, including selected-year occlusion. */
"use strict";
const assert = require("node:assert/strict");
const {
  createTimeline3D,
  projectPoint,
  PITCH,
  timelineRenderLayers,
  cubicPoint,
} = require("../../outputs/paper-atlas/timeline-3d.js");
const helper = require("../../outputs/paper-atlas/timeline-history.js");
global.window = { ATLAS_TIMELINE_HISTORY: helper, devicePixelRatio: 1 };
global.ResizeObserver = class {
  observe() {}
  disconnect() {}
};
let frameId = 0;
const frames = new Map();
global.requestAnimationFrame = (fn) => {
  frames.set(++frameId, fn);
  return frameId;
};
global.cancelAnimationFrame = (id) => frames.delete(id);
const commands = [];
let ellipse = null,
  path = [];
const context = {
  fillStyle: null,
  strokeStyle: null,
  globalAlpha: 1,
  dash: [],
  setLineDash(value) {
    this.dash = value.slice();
  },
  beginPath() {
    ellipse = null;
    path = [];
  },
  ellipse(...args) {
    ellipse = args;
  },
  bezierCurveTo(...args) {
    path.push(args);
  },
  fill() {
    if (ellipse)
      commands.push({
        kind: "fill",
        ellipse: ellipse.slice(),
        style: this.fillStyle,
        alpha: this.globalAlpha,
      });
  },
  stroke() {
    if (path.length)
      commands.push({
        kind: "curves",
        paths: path.map((p) => p.slice()),
        style: this.strokeStyle,
        alpha: this.globalAlpha,
        dash: this.dash.slice(),
        lineWidth: this.lineWidth,
      });
  },
  clearRect() {
    commands.length = 0;
  },
  setTransform() {},
  moveTo() {},
  lineTo() {},
  fillText() {},
};
const ctx = new Proxy(context, {
  get: (object, key) => (key in object ? object[key] : () => {}),
});
const listeners = {};
const canvas = {
  getContext: () => ctx,
  getBoundingClientRect: () => ({ width: 1000, height: 1000, left: 0, top: 0 }),
  addEventListener: (key, value) => (listeners[key] = value),
  removeEventListener() {},
  style: {},
};
const papers = [
  {
    id: "lower-lab",
    year: 2000,
    lab: true,
    displayColor: "#ff0001",
    x: 0,
    y: 0,
  },
  {
    id: "lower-external",
    year: 2000,
    lab: false,
    displayColor: "#00ff02",
    x: 2,
    y: 1,
  },
  {
    id: "upper-external",
    year: 2001,
    lab: false,
    displayColor: "#0000f3",
    x: 3,
    y: 4,
  },
  {
    id: "upper-lab",
    year: 2001,
    lab: true,
    displayColor: "#aaaa04",
    x: 4,
    y: 5,
  },
];
const edges = [
  {
    id: "cross-year",
    source: "lower-lab",
    target: "upper-external",
    kind: "semantic",
    score: 1,
  },
  {
    id: "same-year",
    source: "upper-lab",
    target: "upper-external",
    kind: "semantic",
    score: 0.9,
  },
];
const view = createTimeline3D({ canvas });
view.setData({
  papers,
  edges,
  history: {},
  yearFrom: 2000,
  yearTo: 2001,
  reset: true,
});
view.setActive(true);
function render() {
  const pending = [...frames];
  frames.clear();
  for (const [, callback] of pending) callback(1000);
  return view.inspect();
}
function near(a, b) {
  return Math.abs(a - b) < 1e-7;
}
function planeFill(command, state) {
  if (command.kind !== "fill" || !String(command.style).startsWith("rgba("))
    return null;
  return state.planes.find(
    (p) =>
      near(p.x, command.ellipse[0]) &&
      near(p.y, command.ellipse[1]) &&
      near(p.rx, command.ellipse[2]),
  );
}
function nodeFill(command, state) {
  if (command.kind !== "fill") return null;
  return state.positions.find(
    (p) =>
      near(p.x, command.ellipse[0]) &&
      near(p.y, command.ellipse[1]) &&
      near(p.rx, command.ellipse[2]) &&
      papers.find((paper) => paper.id === p.paperId).displayColor ===
        command.style,
  );
}
function assertPainter(state, expectRelations = false) {
  assert.equal(state.planes.length, 2);
  const fills = commands.map((command, index) => ({
    command,
    index,
    plane: planeFill(command, state),
    node: nodeFill(command, state),
  }));
  const plane2000 = fills.find((item) => item.plane?.year === 2000),
    plane2001 = fills.find((item) => item.plane?.year === 2001);
  assert(plane2000 && plane2001, "both year planes are actually filled");
  const lowerNodes = fills.filter((item) => item.node?.year === 2000),
    upperNodes = fills.filter((item) => item.node?.year === 2001);
  assert.equal(lowerNodes.length, 2);
  assert.equal(upperNodes.length, 4);
  assert(plane2000.index < Math.min(...lowerNodes.map((item) => item.index)));
  assert(
    Math.max(...lowerNodes.map((item) => item.index)) < plane2001.index,
    "lower-year nodes are painted before the upper filled plane can occlude them",
  );
  assert(plane2001.index < Math.min(...upperNodes.map((item) => item.index)));
  for (const items of [lowerNodes, upperNodes])
    for (let i = 1; i < items.length; i++)
      assert(
        items[i - 1].node.depth + 1e-9 >= items[i].node.depth,
        "within a plane actual camera depth determines painting order without laboratory priority",
      );
  const crossing = state.curves.filter(
    (c) => c.a.node && c.b.node && c.a.node.year !== c.b.node.year,
  );
  assert(
    crossing.length,
    "the fixture renders real same-paper growth limbs across years",
  );
  assert(
    crossing.every((curve) =>
      curve.kind === "limb"
        ? curve.a.node.paperId === curve.b.node.paperId
        : curve.a.node.paperId === state.anchor.paperId &&
          curve.b.node.year >= curve.a.node.year,
    ),
    "crossing paths are same-paper growth or selected unique upward relations",
  );
  for (const curve of crossing) {
    const commandIndex = commands.findIndex(
      (command) =>
        command.kind === "curves" &&
        command.paths.some(
          (p) =>
            near(p[0], curve.c1.x) &&
            near(p[1], curve.c1.y) &&
            near(p[2], curve.c2.x) &&
            near(p[3], curve.c2.y) &&
            near(p[4], curve.b.x) &&
            near(p[5], curve.b.y),
        ),
    );
    assert(commandIndex >= 0, "crossing curve is actually stroked");
    assert(commandIndex > Math.max(...lowerNodes.map((item) => item.index)));
    assert(
      commandIndex < plane2001.index,
      "incoming crossing curves are occluded by the upper plane",
    );
  }
  for (const curve of state.curves) {
    const stroke = commands.find(
      (command) =>
        command.kind === "curves" &&
        command.paths.some(
          (p) =>
            near(p[0], curve.c1.x) &&
            near(p[1], curve.c1.y) &&
            near(p[4], curve.b.x) &&
            near(p[5], curve.b.y),
        ),
    );
    assert(stroke);
    if (curve.kind === "association") {
      assert(stroke.lineWidth <= 3);
      assert.deepEqual(
        stroke.dash,
        curve.dash,
        "canvas actually applies association dash style",
      );
    } else {
      assert.deepEqual(stroke.dash, []);
      assert(
        stroke.lineWidth > 3,
        "same-paper growth branches remain thick and solid",
      );
    }
  }
  assert(
    state.curves
      .filter((c) => c.kind === "association")
      .every(
        (c) =>
          c.a.node.paperId === state.anchor.paperId &&
          c.b.node.year >= c.a.node.year &&
          c.year === c.b.node.year,
      ),
    "selected relationships go upward from the earliest visible own instance",
  );
  const sameYear = state.curves.filter(
    (c) =>
      c.kind === "association" &&
      c.a.node?.year === 2001 &&
      c.b.node?.year === 2001,
  );
  if (expectRelations) {
    const associations = state.curves.filter((c) => c.kind === "association");
    assert(associations.length);
    const actualWidths = associations.map(
      (curve) =>
        commands.find(
          (command) =>
            command.kind === "curves" &&
            command.paths.some(
              (p) =>
                near(p[0], curve.c1.x) &&
                near(p[1], curve.c1.y) &&
                near(p[4], curve.b.x) &&
                near(p[5], curve.b.y),
            ),
        ).lineWidth,
    );
    if (associations.length > 1)
      assert(
        Math.max(...actualWidths) > Math.min(...actualWidths),
        "actual selected canvas strokes preserve differing relation scores",
      );
  } else
    assert.equal(
      sameYear.length,
      0,
      "unselected scene renders no associations",
    );
  for (const curve of sameYear) {
    const commandIndex = commands.findIndex(
      (command) =>
        command.kind === "curves" &&
        command.paths.some(
          (p) =>
            near(p[0], curve.c1.x) &&
            near(p[1], curve.c1.y) &&
            near(p[4], curve.b.x) &&
            near(p[5], curve.b.y),
        ),
    );
    assert(commandIndex > plane2001.index);
    assert(
      commandIndex < Math.min(...upperNodes.map((item) => item.index)),
      "same-year curves remain beneath their own nodes",
    );
  }
}
let state = render();
assertPainter(state);
assert.equal(state.curves.filter((c) => c.kind === "association").length, 0);
view.select("lower-lab", { year: 2000 });
state = render();
assertPainter(state, true);
const otherInstanceFill = commands.find(
  (command) =>
    nodeFill(command, state)?.paperId === "lower-lab" &&
    nodeFill(command, state)?.year === 2001,
);
assert.equal(
  otherInstanceFill.alpha,
  1,
  "annual observation highlights all visible instances of the active paper",
);
const selectedFill = commands.find(
  (command) =>
    nodeFill(command, state)?.paperId === "lower-lab" &&
    nodeFill(command, state)?.year === 2000,
);
assert.equal(
  selectedFill.alpha,
  1,
  "selected lower paper remains highlighted without being painted above later years",
);
view.select("upper-external", { year: 2001 });
state = render();
assertPainter(state, true);
view.rotate(2.2);
state = render();
assertPainter(state, true);
view.destroy();
// A pure ordering fixture intentionally mixes classification and depth.
const nodes = [
  { node: { id: "near-lab", year: 2000, paper: { lab: true } }, depth: -10 },
  {
    node: { id: "far-external", year: 2000, paper: { lab: false } },
    depth: 10,
  },
  { node: { id: "upper", year: 2001, paper: { lab: false } }, depth: 0 },
];
const planes = [{ year: 2001 }, { year: 2000 }];
const beforeOrder = JSON.stringify({ nodes, planes });
const layers = timelineRenderLayers(nodes, [], planes);
assert.equal(
  JSON.stringify({ nodes, planes }),
  beforeOrder,
  "pure layer ordering preserves input arrays",
);
assert.deepEqual(
  layers.map((layer) => layer.year),
  [2000, 2001],
);
assert.deepEqual(
  layers[0].nodes.map((node) => node.node.id),
  ["far-external", "near-lab"],
);
// Generic same-paper growth geometry can span three annual intervals.
const span = {
  kind: "limb",
  paperId: "span",
  dash: [],
  a: { x: 0, y: 0, z: 300, node: { year: 2003 } },
  c1: { x: 30, y: 40, z: 200 },
  c2: { x: 60, y: 20, z: 100 },
  b: { x: 90, y: 30, z: 0, node: { year: 2000 } },
};
const spanPlanes = [2000, 2001, 2002, 2003].map((year) => ({
  year,
  z: (year - 2000) * 100,
}));
const spanLayers = timelineRenderLayers([], [span], spanPlanes);
const fragments = spanLayers.flatMap((layer) =>
  layer.crossingCurves.map((curve) => ({ layerYear: layer.year, curve })),
);
assert.equal(fragments.length, 3);
assert.deepEqual(
  fragments.map((item) => item.layerYear),
  [2001, 2002, 2003],
);
for (const item of fragments) {
  const curve = item.curve;
  assert.equal(curve.fragmentYear, item.layerYear);
  assert.equal(curve.paperId, "span");
  assert.deepEqual(curve.dash, []);
  assert.equal(curve.fragmentT.length, 2);
  const [t0, t1] = curve.fragmentT;
  assert(t0 < t1);
  const expectedA = cubicPoint(span, t0),
    expectedB = cubicPoint(span, t1);
  for (const axis of ["x", "y", "z"]) {
    assert(Math.abs(curve.a[axis] - expectedA[axis]) < 1e-8);
    assert(Math.abs(curve.b[axis] - expectedB[axis]) < 1e-8);
  }
}
for (let i = 1; i < fragments.length; i++)
  for (const axis of ["x", "y", "z"])
    assert(
      Math.abs(fragments[i - 1].curve.a[axis] - fragments[i].curve.b[axis]) <
        1e-8,
      "reversed annual curve fragments meet continuously",
    );
// Older publications connect to the selected year's repeated instance, never to an earlier plane.
commands.length = 0;
frames.clear();
const spanCanvas = {
  ...canvas,
  getBoundingClientRect: () => ({ width: 1000, height: 2400, left: 0, top: 0 }),
};
const spanPapers = [
  { id: "older", year: 2000, lab: true, displayColor: "#123401" },
  { id: "later", year: 2003, lab: true, displayColor: "#123402" },
  { id: "intermediate", year: 2001, lab: false, displayColor: "#123403" },
];
const spanEdgeHits = [];
const spanView = createTimeline3D({
  canvas: spanCanvas,
  onSelectEdge: (edge) => spanEdgeHits.push(edge.id),
});
const spanInput = {
  papers: spanPapers,
  edges: [
    {
      id: "annual-association",
      source: "later",
      target: "older",
      kind: "semantic",
      score: 1,
    },
    {
      id: "repeated-association",
      source: "older",
      target: "intermediate",
      kind: "semantic",
      score: 0.5,
    },
    {
      id: "incoming-publication",
      source: "intermediate",
      target: "older",
      kind: "citation",
      score: 0.6,
    },
    {
      id: "outgoing-reference",
      source: "older",
      target: "later",
      kind: "citation",
      score: 0.7,
    },
  ],
  yearFrom: 2000,
  yearTo: 2003,
  history: {},
  reset: true,
};
spanView.setData(spanInput);
spanView.setActive(true);
spanView.select("later", { year: 2003 });
const pending = [...frames];
frames.clear();
for (const [, callback] of pending) callback(2000);
const spanState = spanView.inspect();
assert.equal(spanState.planes.length, 4);
const association = spanState.curves.find(
  (curve) => curve.edgeId === "annual-association",
);
assert(association);
assert.deepEqual(
  [
    association.sourceYear,
    association.targetYear,
    association.a.node.year,
    association.b.node.year,
  ],
  [2003, 2003, 2003, 2003],
);
assert.deepEqual(spanState.highlightInstanceIds.slice().sort(), [
  "later@2003",
  "older@2003",
]);
assert.equal(spanView.contextForPaper("older").year, 2003);
const planeIndices = spanState.planes.map((plane) => ({
  year: plane.year,
  index: commands.findIndex(
    (command) =>
      command.kind === "fill" &&
      String(command.style).startsWith("rgba(") &&
      near(command.ellipse[0], plane.x) &&
      near(command.ellipse[1], plane.y) &&
      near(command.ellipse[2], plane.rx),
  ),
}));
assert(planeIndices.every((p) => p.index >= 0));
const dashed = commands
  .map((command, index) => ({ command, index }))
  .filter((item) => item.command.kind === "curves" && item.command.dash.length);
assert.equal(
  dashed.length,
  1,
  "the selected association is painted once on its own plane",
);
assert(dashed[0].index > planeIndices.find((p) => p.year === 2003).index);
const ownNodeFillIndices = spanState.positions
  .filter((p) => p.year === 2003)
  .map((node) =>
    commands.findIndex(
      (command) =>
        command.kind === "fill" &&
        String(command.style).startsWith("#") &&
        near(command.ellipse[0], node.x) &&
        near(command.ellipse[1], node.y) &&
        near(command.ellipse[2], node.rx),
    ),
  );
assert(
  ownNodeFillIndices.every((index) => index > dashed[0].index),
  "same-year association lies above its own plane and beneath its endpoint nodes",
);
assert(
  spanState.curves
    .filter((curve) => curve.a.node.year !== curve.b.node.year)
    .every(
      (curve) =>
        curve.kind === "limb" && curve.a.node.paperId === curve.b.node.paperId,
    ),
);
const insideEllipse = (point, shape, pad = 0) =>
  ((point.x - shape.x) / (shape.rx + pad)) ** 2 +
    ((point.y - shape.y) / (shape.ry + pad)) ** 2 <=
  1;
let hitPoint = null;
for (let i = 1; i < 100; i++) {
  const point = cubicPoint(association, i / 100);
  if (!spanState.positions.some((node) => insideEllipse(point, node, 5))) {
    hitPoint = point;
    break;
  }
}
assert(
  hitPoint,
  "fixture has a same-year association interior outside endpoint nodes",
);
const click = {
  clientX: hitPoint.x,
  clientY: hitPoint.y,
  pointerId: 1,
  button: 0,
  shiftKey: false,
};
listeners.pointerdown(click);
listeners.pointerup(click);
assert.deepEqual(spanEdgeHits, ["annual-association"]);
assert.deepEqual(
  spanView.inspect().anchor,
  { paperId: "later", year: 2003, instanceId: "later@2003" },
  "clicking the same-plane association preserves its anchor",
);
spanView.select("older", { year: 2000 });
const annualFrames = [...frames];
frames.clear();
for (const [, callback] of annualFrames) callback(3000);
const annualState = spanView.inspect();
assert.deepEqual(
  annualState.highlightInstanceIds
    .filter((id) => id.startsWith("older@"))
    .sort(),
  ["older@2000", "older@2001", "older@2002", "older@2003"],
);
const repeated = annualState.curves.filter(
  (c) => c.edgeId === "repeated-association",
);
assert.deepEqual(
  repeated.map((c) => c.year),
  [2001],
  "each relation is painted only once at its first eligible visible year",
);
for (const curve of repeated) {
  assert.deepEqual([curve.sourceYear, curve.targetYear], [2000, 2001]);
  const plane = annualState.planes.find((p) => p.year === curve.year);
  const planeIndex = commands.findIndex(
    (command) =>
      command.kind === "fill" &&
      String(command.style).startsWith("rgba(") &&
      near(command.ellipse[0], plane.x) &&
      near(command.ellipse[1], plane.y),
  );
  const strokeIndex = commands.findIndex(
    (command) =>
      command.kind === "curves" &&
      command.dash.length &&
      command.paths.some(
        (p) =>
          near(p[0], curve.c1.x) &&
          near(p[1], curve.c1.y) &&
          near(p[4], curve.b.x) &&
          near(p[5], curve.b.y),
      ),
  );
  const lowerPlane = annualState.planes.find((p) => p.year === 2000);
  const lowerPlaneIndex = commands.findIndex(
    (command) =>
      command.kind === "fill" &&
      String(command.style).startsWith("rgba(") &&
      near(command.ellipse[0], lowerPlane.x) &&
      near(command.ellipse[1], lowerPlane.y),
  );
  assert(
    strokeIndex > lowerPlaneIndex && strokeIndex < planeIndex,
    "unique ascending associations are actually stroked between their endpoint planes",
  );
}
for (const node of annualState.positions.filter((p) => p.paperId === "older")) {
  const fill = commands.find(
    (command) =>
      command.kind === "fill" &&
      command.style === "#123401" &&
      near(command.ellipse[0], node.x) &&
      near(command.ellipse[1], node.y),
  );
  assert.equal(
    fill.alpha,
    1,
    "all active paper annual instances are actually highlighted",
  );
}
const annualCamera = { ...annualState.camera },
  annualSizes = annualState.positions.map((p) => ({
    id: p.id,
    rx: p.rx,
    ry: p.ry,
  }));
spanView.setData({ ...spanInput, reset: false });
const offFrames = [...frames];
frames.clear();
for (const [, callback] of offFrames) callback(4000);
const offState = spanView.inspect();
assert.deepEqual(offState.camera, annualCamera);
assert.deepEqual(
  offState.positions.map((p) => ({ id: p.id, rx: p.rx, ry: p.ry })),
  annualSizes,
);
const offAssociations = offState.curves.filter((c) => c.kind === "association");
assert.deepEqual(offAssociations.map((c) => c.edgeId).sort(), [
  "annual-association",
  "incoming-publication",
  "repeated-association",
]);
assert(
  offAssociations.every(
    (c) =>
      c.a.node.paperId === "older" &&
      c.a.node.year === 2000 &&
      c.b.node.year >= 2000,
  ),
);
assert.equal(
  new Set(offAssociations.map((c) => c.edgeId)).size,
  offAssociations.length,
);
assert.deepEqual(
  offState.highlightInstanceIds.filter((id) => id.startsWith("older@")).sort(),
  ["older@2000", "older@2001", "older@2002", "older@2003"],
);
assert.equal(spanView.contextForPaper("intermediate").year, 2001);
assert.equal(spanView.contextForPaper("later").year, 2003);
const offPlaneIndex = (year) => {
  const plane = offState.planes.find((p) => p.year === year);
  return commands.findIndex(
    (c) =>
      c.kind === "fill" &&
      String(c.style).startsWith("rgba(") &&
      near(c.ellipse[0], plane.x) &&
      near(c.ellipse[1], plane.y),
  );
};
for (const layer of timelineRenderLayers([], offAssociations, offState.planes))
  for (const curve of layer.crossingCurves) {
    const index = commands.findIndex(
      (command) =>
        command.kind === "curves" &&
        JSON.stringify(command.dash) === JSON.stringify(curve.dash) &&
        command.paths.some(
          (p) =>
            near(p[0], curve.c1.x) &&
            near(p[1], curve.c1.y) &&
            near(p[2], curve.c2.x) &&
            near(p[3], curve.c2.y) &&
            near(p[4], curve.b.x) &&
            near(p[5], curve.b.y),
        ),
    );
    assert(
      index > offPlaneIndex(layer.year - 1) &&
        index < offPlaneIndex(layer.year),
      "off-mode ascending fragments are actually painted between their annual planes",
    );
  }
spanView.destroy();

const far = projectPoint({ x: 0, y: 2, z: 0 }, { yaw: 0, pitch: PITCH }),
  nearer = projectPoint({ x: 0, y: -2, z: 0 }, { yaw: 0, pitch: PITCH });
assert(far.depth < nearer.depth);
console.log(
  "Timeline painter passed: real canvas plane/node chronology, incoming curves beneath upper planes, same-year curves beneath nodes, true depth order and selected lower-year occlusion.",
);
