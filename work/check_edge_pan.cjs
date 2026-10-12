'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
class Target {
  listeners = new Map();
  options = new Map();
  addEventListener(type, fn, options) { if (!this.listeners.has(type)) this.listeners.set(type, new Set()); this.listeners.get(type).add(fn); this.options.set(fn, options); }
  removeEventListener(type, fn, options) { assert.equal(options, this.options.get(fn), 'Cleanup must use the same event options'); this.listeners.get(type)?.delete(fn); this.options.delete(fn); }
  emit(type, event = {}) { for (const fn of this.listeners.get(type) || []) fn(event); }
}
const win = new Target(), doc = new Target(), container = new Target();
let clock = 0, nextId = 0;
const timers = new Map(), frames = new Map(), pans = [];
win.setTimeout = (fn, delay) => { const id = ++nextId; timers.set(id, {fn, due:clock + delay}); return id; };
win.clearTimeout = id => timers.delete(id);
win.requestAnimationFrame = fn => { const id = ++nextId; frames.set(id, fn); return id; };
win.cancelAnimationFrame = id => frames.delete(id);
doc.defaultView = win;
doc.hidden = false;
container.ownerDocument = doc;
container.getBoundingClientRect = () => ({left:100, top:100, width:800, height:600});
container.contains = target => target === canvas || target === button;
const canvas = {closest:() => null}, button = {closest:() => button};
const cy = {panBy:p => pans.push(p), destroyed:() => false, zoom:() => { throw Error('Auto pan must never change zoom'); }};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../outputs/paper-atlas/edge-pan.js'), 'utf8'), {window:win});
const stop = win.installEdgePan({container, cy});
const mouse = (x, y, extra = {}) => ({pointerType:'mouse', clientX:x + 100, clientY:y + 100, buttons:0, target:canvas, ...extra});
const advance = milliseconds => {
  clock += milliseconds;
  for (const [id, timer] of [...timers]) if (timer.due <= clock) { timers.delete(id); timer.fn(); }
};
const render = milliseconds => {
  clock += milliseconds;
  const callbacks = [...frames.values()]; frames.clear();
  callbacks.forEach(fn => fn(clock));
};
const idle = () => { assert.equal(timers.size, 0); assert.equal(frames.size, 0); };
container.emit('pointerenter', mouse(0, 300));
advance(349); assert.equal(frames.size, 0);
advance(1); render(0); render(50);
assert.deepEqual({...pans.at(-1)}, {x:10, y:0});
render(1000);
assert.equal(pans.at(-1).x, 10, 'A stalled frame must not cause a large jump');
container.emit('pointermove', mouse(24, 300)); render(50);
assert.equal(pans.at(-1).x, 5, 'Speed should increase closer to the edge');
container.emit('pointermove', mouse(800, 600));
assert.equal(frames.size, 0, 'Changing edge restarts dwell');
advance(350); render(0); render(50);
assert.ok(pans.at(-1).x < 0 && pans.at(-1).y < 0);
assert.ok(Math.abs(Math.hypot(pans.at(-1).x, pans.at(-1).y) - 10) < 1e-10, 'Diagonal speed is normalized');
for (const [x, y, expectedX, expectedY] of [[0, 300, 10, 0], [800, 300, -10, 0], [400, 0, 0, 10], [400, 600, 0, -10]]) {
  container.emit('pointermove', mouse(400, 300));
  container.emit('pointermove', mouse(x, y));
  advance(350); render(0); render(50);
  assert.deepEqual({...pans.at(-1)}, {x:expectedX, y:expectedY}, 'Each edge pans toward its hidden content');
}
container.emit('pointermove', mouse(400, 300)); idle();
container.emit('pointermove', mouse(0, 300));
container.emit('pointerleave'); idle();
container.emit('pointermove', mouse(0, 300));
win.emit('resize'); idle();
container.emit('pointermove', mouse(0, 300, {target:button})); idle();
container.emit('pointermove', mouse(0, 300, {pointerType:'touch'})); idle();
container.emit('pointermove', mouse(0, 300));
doc.emit('pointerdown', mouse(0, 300, {buttons:1})); idle();
for (const type of ['pointerdown', 'pointerup', 'pointercancel']) for (const fn of doc.listeners.get(type)) assert.equal(doc.options.get(fn), true, 'Drag events must be captured before graph handlers');
container.emit('pointermove', mouse(0, 300, {buttons:1})); idle();
doc.emit('pointerup', mouse(0, 300)); assert.equal(timers.size, 1);
advance(349); assert.equal(frames.size, 0);
win.emit('blur'); idle();
container.emit('pointermove', mouse(0, 300));
doc.hidden = true; doc.emit('visibilitychange'); idle();
container.emit('pointermove', mouse(0, 300)); idle();
doc.hidden = false;
container.emit('pointermove', mouse(0, 300)); advance(350); render(0);
stop(); idle();
for (const target of [container, doc, win]) for (const listeners of target.listeners.values()) assert.equal(listeners.size, 0);
container.emit('pointermove', mouse(0, 300)); idle();
console.log('Edge pan checks passed: dwell, speed, direction, corners, controls, drag, visibility and disposal.');
