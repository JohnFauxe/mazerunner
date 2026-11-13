// Trace state machine: applies events (vocabulary in core/trace.py) to a drawable
// state, with periodic snapshots so scrubbing backwards stays fast.

export class Geo {
  constructor(geometry) {
    this.width = geometry.width; this.height = geometry.height;
    this.polys = geometry.cells;
    this.n = this.polys.length;
    this.walls = geometry.walls || [];
    this.pair = new Map();
    this.walls.forEach((w, i) => {
      if (w.b === null || w.b === undefined) return;
      const k = this.key(w.a, w.b);
      const l = this.pair.get(k);
      if (l) l.push(i); else this.pair.set(k, [i]);
    });
    this.inner = [];
    this.walls.forEach((w, i) => { if (w.b !== null && w.b !== undefined) this.inner.push(i); });
    this.centroids = this.polys.map(centroid);
    let area = 0;
    for (const p of this.polys) area += Math.abs(polyArea(p));
    this.cellSize = Math.sqrt(area / Math.max(1, this.n)) || 1;
  }
  key(a, b) { return a < b ? a * this.n + b : b * this.n + a; }
}

function polyArea(p) {
  let a = 0;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) a += p[j][0] * p[i][1] - p[i][0] * p[j][1];
  return a / 2;
}
function centroid(p) {
  const A = polyArea(p);
  if (Math.abs(A) < 1e-9) {
    let x = 0, y = 0; for (const q of p) { x += q[0]; y += q[1]; }
    return [x / p.length, y / p.length];
  }
  let cx = 0, cy = 0;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    const f = p[j][0] * p[i][1] - p[i][0] * p[j][1];
    cx += (p[j][0] + p[i][0]) * f; cy += (p[j][1] + p[i][1]) * f;
  }
  return [cx / (6 * A), cy / (6 * A)];
}

export class Timeline {
  constructor(header, events = []) {
    this.header = header; this.events = events;
    this.geo = new Geo(header.geometry);
    this.phases = []; this._scanned = 0;
    this.result = null; this.optimal = null;
    this.scan();
  }
  get length() { return this.events.length; }
  scan() { // index phase events (also called when live events are appended)
    for (; this._scanned < this.events.length; this._scanned++) {
      const e = this.events[this._scanned];
      if (e[1] === 'phase') this.phases.push({ idx: this._scanned, label: (e[3] && e[3].label) || 'phase' });
    }
  }
  push(ev) { this.events.push(ev); }
}

const SNAP_EVERY = 500, SNAP_MAX = 300;

export class State {
  constructor(tl) {
    this.tl = tl; const g = tl.geo; this.geo = g;
    const n = g.n;
    this.open = new Uint8Array(g.walls.length);
    this.vis = new Int32Array(n);
    this.fr = new Uint8Array(n); this.walk = new Uint8Array(n);
    this.mk = new Uint8Array(n); this.fill = new Uint8Array(n);
    this.snaps = new Map();
    this.every = SNAP_EVERY;
    this.reset();
  }
  reset() {
    this.open.fill(0); this.vis.fill(0); this.fr.fill(0); this.walk.fill(0);
    this.mk.fill(0); this.fill.fill(0);
    this.pos = 0; this.cur = -1; this.nfr = 0; this.nvis = 0; this.moves = 0;
    this.start = -1; this.goal = -1; this.label = ''; this.path = null; this.trail = [];
    this.nopen = 0;
  }
  resetSolve() {
    this.vis.fill(0); this.fr.fill(0); this.mk.fill(0); this.fill.fill(0); this.walk.fill(0);
    this.nfr = 0; this.nvis = 0; this.moves = 0; this.path = null; this.trail = []; this.cur = -1;
  }
  setLink(a, b, v) {
    const l = this.geo.pair.get(this.geo.key(a, b));
    if (!l) return;
    for (const i of l) this.open[i] = v;
  }
  apply(ev) {
    const op = ev[1], cells = ev[2], data = ev[3];
    const order = this.pos + 1;
    switch (op) {
      case 'carve': this.setLink(cells[0], cells[1], 1); this.walk[cells[0]] = 0; this.walk[cells[1]] = 0; break;
      case 'open_all': for (const i of this.geo.inner) this.open[i] = 1; break;
      case 'uncarve': case 'wall': this.setLink(cells[0], cells[1], 0); break;
      case 'current': this.cur = cells.length ? cells[0] : -1; break;
      case 'frontier_add': for (const c of cells) if (!this.fr[c]) { this.fr[c] = 1; this.nfr++; } break;
      case 'frontier_remove': for (const c of cells) if (this.fr[c]) { this.fr[c] = 0; this.nfr--; } break;
      case 'walk': for (const c of cells) { this.walk[c] = 1; this.cur = c; } break;
      case 'erase': for (const c of cells) this.walk[c] = 0; break;
      case 'visit':
        for (const c of cells) {
          if (!this.vis[c]) this.nvis++;
          this.vis[c] = order;
          if (this.fr[c]) { this.fr[c] = 0; this.nfr--; }
          this.cur = c;
        }
        break;
      case 'move':
        for (const c of cells) {
          this.cur = c; this.trail.push(c); this.moves++;
          if (!this.vis[c]) { this.vis[c] = order; this.nvis++; }
        }
        break;
      case 'mark': { const n = (data && data.count) || 1; if (this.mk[cells[0]] < n) this.mk[cells[0]] = Math.min(n, 255); break; }
      case 'fill': for (const c of cells) this.fill[c] = 1; break;
      case 'path': this.path = cells; break;
      case 'endpoints': this.start = cells[0]; this.goal = cells[1]; break;
      case 'phase':
        this.label = (data && data.label) || '';
        if (this.label.startsWith('solve')) {
          this.fr.fill(0); this.walk.fill(0); this.nfr = 0; this.cur = -1;
        }
        break;
      case '_reset': this.resetSolve(); break;
      default: break; // set_merge and unknown ops are ignored
    }
    this.pos++;
    if (this.pos % this.every === 0 && this.snaps.size < SNAP_MAX && !this.snaps.has(this.pos)) this.snapshot();
  }
  snapshot() {
    this.snaps.set(this.pos, {
      pos: this.pos, open: this.open.slice(), vis: this.vis.slice(), fr: this.fr.slice(),
      walk: this.walk.slice(), mk: this.mk.slice(), fill: this.fill.slice(),
      cur: this.cur, nfr: this.nfr, nvis: this.nvis, moves: this.moves, start: this.start,
      goal: this.goal, label: this.label, path: this.path, trail: this.trail, trailLen: this.trail.length,
    });
  }
  restore(s) {
    this.open.set(s.open); this.vis.set(s.vis); this.fr.set(s.fr); this.walk.set(s.walk);
    this.mk.set(s.mk); this.fill.set(s.fill);
    Object.assign(this, { pos: s.pos, cur: s.cur, nfr: s.nfr, nvis: s.nvis, moves: s.moves, start: s.start,
      goal: s.goal, label: s.label, path: s.path, trail: s.trail });
    this.trail.length = s.trailLen;
  }
  seek(target) {
    const ev = this.tl.events;
    target = Math.max(0, Math.min(target, ev.length));
    if (target < this.pos) {
      let best = null;
      for (const [p, s] of this.snaps) if (p <= target && (!best || p > best.pos)) best = s;
      if (best) this.restore(best); else this.reset();
    }
    while (this.pos < target) this.apply(ev[this.pos]);
  }
}

// Drives one or more lanes ({tl, state, view, ...}) in lockstep.
export class Player {
  constructor(onChange) {
    this.lanes = []; this.pos = 0; this.playing = false; this.speed = 100;
    this.acc = 0; this.last = 0; this.following = false; this.onChange = onChange || (() => {});
    this.dirty = false; this.raf = 0;
    this._loop = (t) => this.frame(t);
  }
  setLanes(lanes) { this.lanes = lanes; this.pos = 0; this.playing = false; this.following = false; this.touch(); }
  get total() { return this.lanes.reduce((m, l) => Math.max(m, l.tl.length), 0); }
  phases() { // merged, sorted phase indices over all lanes
    const s = new Map();
    for (const l of this.lanes) for (const p of l.tl.phases) if (!s.has(p.idx)) s.set(p.idx, p.label);
    return [...s.entries()].sort((a, b) => a[0] - b[0]).map(([idx, label]) => ({ idx, label }));
  }
  seek(p) {
    this.pos = Math.max(0, Math.min(p, this.total));
    for (const l of this.lanes) l.state.seek(Math.min(this.pos, l.tl.length));
    this.touch();
  }
  step(d) { this.playing = false; this.following = false; this.seek(this.pos + d); }
  toggle() {
    if (this.pos >= this.total && !this.following) this.seek(0);
    this.playing = !this.playing; this.last = 0; this.touch();
  }
  jumpPhase(dir) {
    const ph = this.phases();
    if (dir > 0) { const n = ph.find((p) => p.idx + 1 > this.pos && p.idx >= this.pos); this.seek(n ? n.idx + 1 : this.total); }
    else { const prev = [...ph].reverse().find((p) => p.idx + 1 < this.pos); this.seek(prev ? prev.idx + 1 : 0); }
  }
  touch() { this.dirty = true; if (!this.raf) this.raf = requestAnimationFrame(this._loop); }
  frame(t) {
    this.raf = 0;
    if (this.following) { // live: apply everything that arrived
      this.pos = this.total;
      for (const l of this.lanes) l.state.seek(l.tl.length);
      this.dirty = true;
    } else if (this.playing) {
      const dt = this.last ? Math.min(0.25, (t - this.last) / 1000) : 0;
      this.last = t; this.acc += dt * this.speed;
      const n = Math.floor(this.acc);
      if (n > 0) {
        this.acc -= n;
        this.pos = Math.min(this.total, this.pos + n);
        for (const l of this.lanes) {
          const target = Math.min(this.pos, l.tl.length);
          while (l.state.pos < target) l.state.apply(l.tl.events[l.state.pos]);
        }
        this.dirty = true;
      }
      if (this.pos >= this.total) this.playing = false;
    }
    if (this.dirty) {
      this.dirty = false;
      for (const l of this.lanes) l.view && l.view.draw(l.state);
      this.onChange(this);
    }
    if (this.playing || this.following) this.raf = requestAnimationFrame(this._loop);
  }
}
