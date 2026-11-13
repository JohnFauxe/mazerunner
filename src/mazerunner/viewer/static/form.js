// Run/Race configuration form, populated from /api/catalog.
import { el } from './watch.js';

const SIZE_LABELS = { square: ['rows', 'cols'], hex: ['rows', 'cols'], polar: ['rings'] };

export class RunForm {
  // opts.multi: solvers as checkboxes (any number) instead of a single select
  constructor(catalog, { multi = false, live = false } = {}) {
    this.cat = catalog; this.multi = multi;
    const C = this.c = {};
    C.topology = el('select', { 'aria-label': 'Topology' });
    for (const t of catalog.topologies) {
      const o = el('option', { value: t.key }, t.title + (t.implemented ? '' : ' (not implemented)'));
      if (!t.implemented) { o.disabled = true; o.title = 'This topology is a placeholder.'; }
      C.topology.append(o);
    }
    C.topology.addEventListener('change', () => { this.syncSize(); this.syncCompat(); });
    C.sizeBox = el('div', { class: 'row' });
    C.generator = el('select', { 'aria-label': 'Generator' });
    for (const g of catalog.generators) C.generator.append(el('option', { value: g.key }, g.title));
    C.generator.addEventListener('change', () => { this.syncGenInfo(); });
    if (multi) {
      C.solvers = el('div', { class: 'checks', role: 'group', 'aria-label': 'Solvers' });
      this.checks = new Map();
      for (const s of catalog.solvers) {
        const cb = el('input', { type: 'checkbox', value: s.key });
        cb.addEventListener('change', () => this.limitChecks());
        const lab = el('label', {}, cb, s.title);
        this.checks.set(s.key, { cb, lab, info: s });
        C.solvers.append(lab);
      }
    } else {
      C.solvers = el('select', { 'aria-label': 'Solver' }, el('option', { value: '' }, '(none, generation only)'));
      for (const s of catalog.solvers) C.solvers.append(el('option', { value: s.key }, s.title));
    }
    C.placement = el('select', { 'aria-label': 'Endpoint placement' });
    for (const p of catalog.placements) C.placement.append(el('option', { value: p }, p));
    C.placement.value = 'opposite-sides';
    C.side = el('input', { type: 'number', min: 0, max: 1, step: 0.05, value: 0, 'aria-label': 'Side (fraction of boundary)' });
    C.along = el('select', { 'aria-label': 'Along the side' }, el('option', { value: 'center' }, 'center'), el('option', { value: 'random' }, 'random'));
    C.braid = el('input', { type: 'range', min: 0, max: 1, step: 0.05, value: 0, 'aria-label': 'Braid amount' });
    C.braidLbl = el('span', {}, '0.00');
    C.braid.addEventListener('input', () => { C.braidLbl.textContent = (+C.braid.value).toFixed(2); });
    C.seed = el('input', { type: 'number', value: 1, step: 1, 'aria-label': 'Seed' });
    C.dice = el('button', { type: 'button', title: 'Random seed', 'aria-label': 'Random seed', onclick: () => { C.seed.value = Math.floor(Math.random() * 1e6); } }, '\u{1F3B2}');
    C.delay = el('input', { type: 'number', min: 0, max: 2, step: 0.005, value: 0.01, 'aria-label': 'Live delay seconds' });
    this.genInfo = el('small', { class: 'muted' });
    const f = (label, ...kids) => el('div', { class: 'field' }, el('span', {}, label), ...kids);
    this.form = el('div', { class: 'form' },
      f('Topology', C.topology), f('Size', C.sizeBox), f('Generator', C.generator, this.genInfo),
      f(multi ? 'Solvers' : 'Solver', ...(multi ? [this.solverTools(), C.solvers] : [C.solvers])),
      f('Endpoints', C.placement, el('div', { class: 'row' }, 'side', C.side, 'along', C.along)),
      f('Braid (remove dead ends)', el('div', { class: 'row' }, C.braid, C.braidLbl)),
      f('Seed', el('div', { class: 'row' }, C.seed, C.dice)),
      ...(live ? [f('Live delay (s / event)', C.delay)] : []));
    this.actions = el('div', { class: 'actions' });
    this.root = el('div', { class: 'card' }, this.form, this.actions);
    const first = catalog.topologies.find((t) => t.implemented);
    if (first) C.topology.value = first.key;
    this.syncSize(); this.syncCompat();
  }
  topo() { return this.cat.topologies.find((t) => t.key === this.c.topology.value); }
  syncSize() {
    const t = this.topo(), labels = SIZE_LABELS[t.key] || t.default_size.map((_, i) => 'dim ' + (i + 1));
    this.c.sizeBox.replaceChildren(...t.default_size.flatMap((v, i) => [
      el('input', { type: 'number', min: 1, step: 1, value: v, 'aria-label': labels[i] || 'size' }), labels[i] || '']));
  }
  size() { return [...this.c.sizeBox.querySelectorAll('input')].map((i) => Math.max(1, parseInt(i.value, 10) || 1)); }
  reason(info) {
    if (!info.implemented) return 'Not implemented yet.';
    const have = new Set(this.topo().traits);
    const miss = info.requires.filter((r) => !have.has(r));
    return miss.length ? `Needs ${miss.join(', ')}, which ${this.topo().title} lacks.` : '';
  }
  syncCompat() {
    const mark = (opt, info) => { const r = this.reason(info); opt.disabled = !!r; opt.title = r; };
    const gsel = this.c.generator;
    [...gsel.options].forEach((o, i) => mark(o, this.cat.generators[i]));
    if (gsel.selectedOptions[0]?.disabled) gsel.value = ([...gsel.options].find((o) => !o.disabled) || {}).value;
    if (this.multi) {
      for (const { cb, lab, info } of this.checks.values()) {
        const r = this.reason(info); cb.disabled = !!r; lab.title = r; lab.classList.toggle('off', !!r);
        if (r) cb.checked = false;
      }
      this.limitChecks();
    } else {
      const ssel = this.c.solvers;
      [...ssel.options].slice(1).forEach((o, i) => mark(o, this.cat.solvers[i]));
      if (ssel.selectedOptions[0]?.disabled) ssel.value = '';
    }
    this.syncGenInfo();
  }
  syncGenInfo() {
    const g = this.cat.generators.find((x) => x.key === this.c.generator.value);
    this.genInfo.textContent = g && g.tags.length ? g.tags.join(', ') : '';
  }
  limitChecks() {
    for (const { cb, info } of this.checks.values()) {
      cb.disabled = !!this.reason(info);
      if (cb.disabled) cb.checked = false;
    }
    if (this.countEl) {
      const n = [...this.checks.values()].filter((x) => x.cb.checked).length;
      this.countEl.textContent = `${n} selected`;
    }
  }
  solverTools() {
    const pick = (on) => () => {
      for (const { cb } of this.checks.values()) if (!cb.disabled) cb.checked = on;
      this.limitChecks();
    };
    this.countEl = el('small', { class: 'muted' });
    return el('div', { class: 'row' },
      el('button', { type: 'button', onclick: pick(true) }, 'All compatible'),
      el('button', { type: 'button', onclick: pick(false) }, 'None'),
      this.countEl);
  }
  solverKeys() {
    if (this.override) return this.override;
    if (this.multi) return [...this.checks.entries()].filter(([, v]) => v.cb.checked).map(([k]) => k);
    return this.c.solvers.value ? [this.c.solvers.value] : [];
  }
  // Prefill from URL query params (topology, size, generator, solvers, seed, braid, placement, side, along, delay).
  prefill(q) {
    const C = this.c, has = (k) => q.get(k) !== null && q.get(k) !== '';
    if (has('topology') && [...C.topology.options].some((o) => o.value === q.get('topology'))) { C.topology.value = q.get('topology'); this.syncSize(); this.syncCompat(); }
    if (has('size')) { const v = q.get('size').split(/[,x]/).map((x) => parseInt(x, 10)); [...C.sizeBox.querySelectorAll('input')].forEach((i, k) => { if (v[k] > 0) i.value = v[k]; }); }
    if (has('generator') && [...C.generator.options].some((o) => o.value === q.get('generator'))) { C.generator.value = q.get('generator'); this.syncGenInfo(); }
    const sol = (q.get('solvers') || '').split(',').filter(Boolean);
    if (this.multi) { for (const k of sol) { const x = this.checks.get(k); if (x && !x.cb.disabled) x.cb.checked = true; } this.limitChecks(); }
    else if (sol.length) {
      if ([...C.solvers.options].some((o) => o.value === sol[0])) C.solvers.value = sol[0];
      this.override = sol.length > 1 ? sol : null;
      C.solvers.addEventListener('change', () => { this.override = null; }, { once: true });
    }
    if (has('seed')) C.seed.value = q.get('seed');
    if (has('braid')) { C.braid.value = q.get('braid'); C.braid.dispatchEvent(new Event('input')); }
    if (has('placement') && [...C.placement.options].some((o) => o.value === q.get('placement'))) C.placement.value = q.get('placement');
    if (has('side')) C.side.value = q.get('side');
    if (has('along')) C.along.value = q.get('along');
    if (has('delay')) C.delay.value = q.get('delay');
  }
  config() {
    const C = this.c;
    return { topology: C.topology.value, size: this.size(), generator: C.generator.value, solvers: this.solverKeys(),
      seed: parseInt(C.seed.value, 10) || 0, braid: +C.braid.value,
      endpoints: { placement: C.placement.value, side: +C.side.value || 0, along: C.along.value } };
  }
  liveQuery() {
    const c = this.config(), q = new URLSearchParams({ topology: c.topology, size: c.size.join(','), generator: c.generator,
      solvers: c.solvers.join(','), seed: c.seed, braid: c.braid, placement: c.endpoints.placement,
      side: c.endpoints.side, along: c.endpoints.along, delay: this.c.delay.value || 0 });
    return q.toString();
  }
}
