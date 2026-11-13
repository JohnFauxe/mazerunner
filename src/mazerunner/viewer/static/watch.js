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
    root.append(this.transport, this.statusEl, this.lanesEl, this.legend);
    watchers.add(this);
    this.ctl.disabled = true;
  }
  visible() { return this.root.offsetParent !== null; }

  buildTransport() {
    const P = this.player, c = {};
    const btn = (label, text, fn, extra = '') => el('button', { type: 'button', 'aria-label': label, title: label + extra, onclick: fn }, text);
    c.restart = btn('Restart', '⏮', () => P.seek(0), ' (Home)');
    c.prevPhase = btn('Previous phase', '⏪', () => P.jumpPhase(-1), ' ([)');
    c.back = btn('Step back', '◀', () => P.step(-1), ' (Left arrow)');
    c.play = btn('Play / pause', '▶', () => P.toggle(), ' (Space)');
    c.fwd = btn('Step forward', '▶▏', () => P.step(1), ' (Right arrow)');
    c.nextPhase = btn('Next phase', '⏩', () => P.jumpPhase(1), ' (])');
    c.scrub = el('input', { type: 'range', min: 0, max: 0, value: 0, class: 'scrub', 'aria-label': 'Scrub position' });
    c.scrub.addEventListener('input', () => { P.playing = false; P.following = false; P.seek(+c.scrub.value); });
    c.speed = el('input', { type: 'range', min: 0, max: 100, value: 40, 'aria-label': 'Speed' });
    c.speedLbl = el('span', {}, '');
    c.speed.addEventListener('input', () => { P.speed = speedFromSlider(+c.speed.value); c.speedLbl.textContent = `${fmt(P.speed)} ev/s`; });
    c.speed.dispatchEvent(new Event('input'));
    this.ctl = { disabled: false };
    Object.defineProperty(this.ctl, 'disabled', { set: (v) => { for (const k of ['restart', 'prevPhase', 'back', 'play', 'fwd', 'nextPhase', 'scrub']) c[k].disabled = v; } });
    this.c = c;
    this.transport = el('div', { class: 'transport', role: 'group', 'aria-label': 'Playback controls' },
      c.restart, c.prevPhase, c.back, c.play, c.fwd, c.nextPhase, c.scrub,
      el('label', {}, 'Speed', c.speed, c.speedLbl));
  }
  speedBy(d) { const c = this.c; c.speed.value = Math.max(0, Math.min(100, +c.speed.value + d)); c.speed.dispatchEvent(new Event('input')); }

  clear() {
    this.player.playing = false; this.player.following = false;
    for (const l of this.player.lanes) l.view && l.view.destroy();
    this.lanesEl.replaceChildren(); this.laneEls = [];
  }
  // lanes: [{title, tl, result?, optimal?}]
  show(lanes, { autoplay = true, status = '' } = {}) {
    this.clear();
    const single = lanes.length === 1;
    const out = lanes.map((ln) => {
      const canvas = el('canvas', { role: 'img', 'aria-label': ln.title || 'maze' });
      const wrap = el('div', { class: 'canvaswrap' }, canvas);
      const dl = el('dl'); const counters = el('div', { class: 'counters' }, dl);
      const badge = el('span');
      const box = el('div', { class: 'lane card' + (single ? ' single' : '') });
      if (single) box.append(wrap, counters);
      else box.append(el('h3', {}, el('span', {}, ln.title || ''), badge), wrap, counters);
      this.lanesEl.append(box);
      const view = new MazeView(canvas, ln.tl.geo);
      this.laneEls.push({ dl, badge });
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
    const lens = P.lanes.map((l) => l.tl.length);
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
        const done = P.pos >= lens[i] && lens[i] > 0;
        const rank = 1 + lens.filter((n) => n < lens[i]).length;
        const b = this.laneEls[i].badge;
        b.className = done ? 'badge' : ''; b.textContent = done ? `finished #${rank}` : '';
      }
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
