// Watcher: transport bar + one or more lanes (canvas + counters) driven by a Player.
import { Timeline, State, Player } from './engine.js';
import { MazeView } from './render.js';

const watchers = new Set();
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  for (const k of kids) e.append(k);
  return e;
};
export { el };

const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const speedFromSlider = (v) => Math.round(10 ** (v / 20));   // 0..100 -> 1..100000
const fmt = (n) => Number(n).toLocaleString();

export class Watcher {
  constructor(root, { onError } = {}) {
    this.root = root; this.onError = onError || (() => {});
    this.player = new Player(() => this.update());
    this.laneEls = [];
    this.buildTransport();
    this.lanesEl = el('div', { class: 'lanes' });
    this.statusEl = el('p', { class: 'muted' }, 'Nothing loaded yet.');
    this.legend = el('div', { class: 'legend', 'aria-hidden': 'true' });
    for (const [c, t] of [['--c-current', 'current / agent'], ['--c-frontier', 'frontier'], ['--c-walk', 'random walk'],
      ['--c-fill', 'filled dead end'], ['--c-path', 'solution'], ['--c-start', 'start'], ['--c-goal', 'goal']]) {
      const i = el('i'); i.style.background = `var(${c})`; this.legend.append(el('span', {}, i, t));
    }
    this.legend.append(el('span', {}, 'visited: blue (old) to orange (recent)'));
    this.order = 'selection';
    this.orderSel = el('select', { 'aria-label': 'Lane order' },
      el('option', { value: 'selection' }, 'Selection order'),
      el('option', { value: 'rank' }, 'Finish rank (live)'));
    this.orderSel.addEventListener('change', () => { this.order = this.orderSel.value; this.orderSig = ''; this.update(); });
    this.laneBar = el('div', { class: 'lanebar', hidden: '' }, el('label', {}, 'Order', this.orderSel));
    root.append(this.transport, this.statusEl, this.laneBar, this.lanesEl, this.legend);
    watchers.add(this);
    this.ctl.disabled = true;
  }
  visible() { return this.root.offsetParent !== null || !!this.zoomed; }

  buildTransport() {
    const P = this.player, c = {};
    const btn = (label, text, fn, extra = '') => el('button', { type: 'button', 'aria-label': label, title: label + extra, onclick: fn }, text);
    c.restart = btn('Restart', '⏮', () => P.seek(0), ' (Home)');
    c.prevPhase = btn('Previous phase', '⏪', () => P.jumpPhase(-1), ' ([)');
    c.back = btn('Step back', '◀', () => P.step(-1), ' (Left arrow)');
    c.play = btn('Play / pause', '▶', () => P.toggle(), ' (Space)');
    c.fwd = btn('Step forward', '▶▏', () => P.step(1), ' (Right arrow)');
    c.nextPhase = btn('Next phase', '⏩', () => P.jumpPhase(1), ' (])');
    c.skipSolve = el('button', { type: 'button', class: 'skip', title: 'Skip generation, go straight to solving (S)', onclick: () => P.skipToSolve() }, 'Skip to solve ⏭');
    c.scrub = el('input', { type: 'range', min: 0, max: 0, value: 0, class: 'scrub', 'aria-label': 'Scrub position' });
    c.scrub.addEventListener('input', () => { P.playing = false; P.following = false; P.seek(+c.scrub.value); });
    c.speed = el('input', { type: 'range', min: 0, max: 100, value: 40, 'aria-label': 'Speed' });
    c.speedLbl = el('span', {}, '');
    c.speed.addEventListener('input', () => { P.speed = speedFromSlider(+c.speed.value); c.speedLbl.textContent = `${fmt(P.speed)} ev/s`; });
    c.speed.dispatchEvent(new Event('input'));
    this.ctl = { disabled: false };
    Object.defineProperty(this.ctl, 'disabled', { set: (v) => { for (const k of ['restart', 'prevPhase', 'back', 'play', 'fwd', 'nextPhase', 'scrub']) c[k].disabled = v; this.syncSkip(); } });
    this.c = c;
    this.transport = el('div', { class: 'transport', role: 'group', 'aria-label': 'Playback controls' },
      c.restart, c.prevPhase, c.back, c.play, c.fwd, c.nextPhase, c.skipSolve, c.scrub,
      el('label', {}, 'Speed', c.speed, c.speedLbl));
  }
  syncSkip() { // enabled only while there is generation left to skip
    const P = this.player, i = P.solveStart();
    this.c.skipSolve.disabled = this.c.play.disabled || i < 0 || P.pos > i;
  }
  speedBy(d) { const c = this.c; c.speed.value = Math.max(0, Math.min(100, +c.speed.value + d)); c.speed.dispatchEvent(new Event('input')); }

  // Popup: moves the lane card (and the transport bar) into a modal <dialog> so the
  // same canvas keeps rendering; everything is moved back on close.
  openZoom(i) {
    const lane = this.laneEls[i];
    if (!lane || this.zoomed) return;
    const dlg = this.zoomDlg || this.buildZoom();
    const ph = el('div', { class: 'lane-placeholder card' });
    ph.style.height = `${lane.box.offsetHeight}px`;
    lane.box.replaceWith(ph);
    this.zoomed = { lane, ph, tHome: this.transport.parentNode, tNext: this.transport.nextSibling, maxW: lane.wrap.style.maxWidth };
    lane.wrap.style.maxWidth = `calc((86vh - 190px) * ${lane.ratio})`;
    lane.box.classList.add('zoomed');
    this.zoomBody.replaceChildren(this.transport, lane.box);
    dlg.showModal();
    dlg.focus(); // keep keyboard shortcuts (Space, arrows, S) working; Esc closes
  }
  buildZoom() {
    const dlg = el('dialog', { class: 'zoom', 'aria-label': 'Enlarged lane', tabindex: '-1' });
    this.zoomClose = el('button', { type: 'button', class: 'zoom-close', 'aria-label': 'Close (Esc)', title: 'Close (Esc)', onclick: () => dlg.close() }, '✕');
    this.zoomBody = el('div', { class: 'zoom-body' });
    dlg.append(el('div', { class: 'zoom-inner' }, this.zoomClose, this.zoomBody));
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); }); // backdrop click
    dlg.addEventListener('close', () => this.closeZoom());
    document.body.append(dlg);
    return (this.zoomDlg = dlg);
  }
  closeZoom() {
    const z = this.zoomed;
    if (!z) return;
    this.zoomed = null;
    z.lane.box.classList.remove('zoomed');
    z.lane.wrap.style.maxWidth = z.maxW;
    z.ph.replaceWith(z.lane.box);
    z.tHome.insertBefore(this.transport, z.tNext);
    if (this.zoomDlg.open) this.zoomDlg.close();
    z.lane.box.focus({ preventScroll: true });
  }

  clear() {
    if (this.zoomed) this.closeZoom();
    this.player.playing = false; this.player.following = false;
    for (const l of this.player.lanes) l.view && l.view.destroy();
    this.lanesEl.replaceChildren(); this.laneEls = [];
  }
  // lanes: [{title, tl, result?, optimal?}]
  show(lanes, { autoplay = true, status = '' } = {}) {
    this.clear();
    const single = lanes.length === 1;
    this.lanesEl.classList.toggle('many', lanes.length > 4);
    this.laneBar.hidden = single; this.orderSig = '';
    const out = lanes.map((ln) => {
      const canvas = el('canvas', { role: 'img', 'aria-label': ln.title || 'maze' });
      const wrap = el('div', { class: 'canvaswrap' }, canvas);
      const dl = el('dl'); const counters = el('div', { class: 'counters' }, dl);
      const badge = el('span');
      const box = el('div', { class: 'lane card' + (single ? ' single' : '') });
      if (single) box.append(wrap, counters);
      else {
        const i = this.laneEls.length;
        const expand = el('button', { type: 'button', class: 'expand', 'aria-label': `Enlarge ${ln.title || 'lane'}`, title: 'Enlarge (or click the card)' }, '⤢');
        box.append(el('h3', {}, el('span', {}, ln.title || ''), el('span', { class: 'row' }, badge, expand)), wrap, counters);
        box.classList.add('zoomable');
        box.tabIndex = 0;
        box.addEventListener('click', (e) => { if (!this.zoomed && (e.target === expand || !e.target.closest('button,a,input,select'))) this.openZoom(i); });
        box.addEventListener('keydown', (e) => { if (!this.zoomed && e.key === 'Enter' && e.target === box) this.openZoom(i); });
      }
      this.lanesEl.append(box);
      const view = new MazeView(canvas, ln.tl.geo);
      this.laneEls.push({ dl, badge, box, wrap, ratio: ln.tl.geo.width / ln.tl.geo.height });
      return { ...ln, state: new State(ln.tl), view };
    });
    this.player.setLanes(out);
    this.statusEl.textContent = status;
    this.ctl.disabled = false;
    if (autoplay && !reduced()) { this.player.playing = true; }
    this.player.touch();
  }
  // live: returns a handle {push(ev), finish()}; a single lane that follows the stream.
  showLive(header, title) {
    const tl = new Timeline(header, []);
    this.show([{ title, tl }], { autoplay: false });
    this.player.following = true; this.player.playing = false;
    this.ctl.disabled = true; this.player.touch();
    return {
      tl,
      push: (ev) => { tl.push(ev); tl.scan(); this.player.touch(); },
      finish: (result) => { tl.scan(); tl.result = result || tl.result; this.player.following = false; this.player.seek(tl.length); this.ctl.disabled = false; },
    };
  }

  update() {
    const P = this.player, c = this.c;
    c.scrub.max = P.total; c.scrub.value = P.pos;
    c.play.textContent = P.playing ? '⏸' : '▶';
    this.syncSkip();
    const rk = this.ranks();
    P.lanes.forEach((l, i) => {
      const st = l.state, dl = this.laneEls[i].dl, tl = l.tl;
      const steps = st.path ? st.path.length - 1 : null;
      const opt = tl.optimal ?? (tl.result && tl.result.optimal);
      const rows = [['Step', `${fmt(st.pos)} / ${fmt(tl.length)}`], ['Phase', st.label || '-'],
        ['Frontier size', fmt(st.nfr)], ['Visited cells', fmt(st.nvis)], ['Steps walked', fmt(st.moves)],
        ['Path length', steps === null ? '-' : `${fmt(steps)}${opt != null ? ` (optimal ${fmt(opt)})` : ''}`]];
      if (tl.result) rows.push(['Outcome', tl.result.outcome]);
      dl.replaceChildren(...rows.flatMap(([k, v]) => [el('dt', {}, k), el('dd', {}, String(v))]));
      if (P.lanes.length > 1) {
        const r = rk[i], b = this.laneEls[i].badge;
        b.className = r.done ? (r.failed ? 'badge fail' : 'badge') : '';
        b.textContent = !r.done ? '' : r.failed ? (tl.result ? tl.result.outcome : 'failed') : `finished #${r.rank}`;
      }
    });
    if (P.lanes.length > 1) this.reorder(rk);
  }
  // Rank: solvers that reached the goal, by events used (fewer = faster); failures/timeouts last.
  ranks() {
    const P = this.player;
    const info = P.lanes.map((l) => {
      const len = l.tl.length, oc = l.tl.result && l.tl.result.outcome;
      return { len, done: len > 0 && P.pos >= len, failed: !!oc && oc !== 'solved' };
    });
    const ok = info.filter((x) => !x.failed).map((x) => x.len);
    for (const x of info) if (!x.failed) x.rank = 1 + ok.filter((n) => n < x.len).length;
    return info;
  }
  // In "rank" mode, finished lanes move to the front in rank order (live leaderboard);
  // unfinished lanes keep selection order behind them, failed lanes go last.
  reorder(rk) {
    const idx = rk.map((_, i) => i);
    if (this.order === 'rank') {
      const key = (i) => { const r = rk[i]; return !r.done ? [1, 0, i] : r.failed ? [2, 0, i] : [0, r.rank, i]; };
      idx.sort((a, b) => { const A = key(a), B = key(b); return A[0] - B[0] || A[1] - B[1] || A[2] - B[2]; });
    }
    const sig = idx.join(',');
    if (sig === this.orderSig) return;
    this.orderSig = sig;
    const slot = (i) => (this.zoomed && this.zoomed.lane === this.laneEls[i] ? this.zoomed.ph : this.laneEls[i].box);
    const animate = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    const before = animate ? idx.map((i) => slot(i).getBoundingClientRect()) : null;
    for (const i of idx) this.lanesEl.append(slot(i));
    if (animate) idx.forEach((i, k) => { // FLIP: slide cards from their old spot
      const e = slot(i), a = before[k], b = e.getBoundingClientRect();
      const dx = a.left - b.left, dy = a.top - b.top;
      if (dx || dy) e.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }], { duration: 260, easing: 'ease-out' });
    });
  }
  key(e) {
    const P = this.player;
    switch (e.key) {
      case ' ': P.toggle(); break;
      case 'ArrowLeft': P.step(e.shiftKey ? -100 : -1); break;
      case 'ArrowRight': P.step(e.shiftKey ? 100 : 1); break;
      case '[': P.jumpPhase(-1); break;
      case ']': P.jumpPhase(1); break;
      case 's': case 'S': P.skipToSolve(); break;
      case '-': this.speedBy(-5); break;
      case '+': case '=': this.speedBy(5); break;
      case 'Home': P.seek(0); break;
      case 'End': P.step(1e12); break;
      default: return false;
    }
    return true;
  }
}

document.addEventListener('keydown', (e) => {
  const t = e.target;
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (t && (t.tagName === 'INPUT' && t.type !== 'range' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.tagName === 'BUTTON' && e.key === ' ')) return;
  for (const w of watchers) {
    if (w.visible() && w.player.lanes.length && !w.c.play.disabled && w.key(e)) { e.preventDefault(); return; }
  }
});
