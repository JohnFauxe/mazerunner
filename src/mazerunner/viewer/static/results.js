// Results dashboard: sortable tables + bar charts from results/*.jsonl.
import { el } from './watch.js';
import { getJSON, banner } from './net.js';
import { barChart } from './charts.js';

const num = (v) => (typeof v === 'number' && isFinite(v) ? v : null);
const mean = (a) => { a = a.filter((x) => x !== null); return a.length ? a.reduce((s, x) => s + x, 0) / a.length : null; };
const median = (a) => { a = a.filter((x) => x !== null).sort((x, y) => x - y); if (!a.length) return null; const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; };
const g = (o, path) => path.split('.').reduce((x, k) => (x == null ? null : x[k]), o);
const fmtNum = (v) => (v === null || v === undefined ? '-' : Math.abs(v) >= 1000 ? Math.round(v).toLocaleString() : String(+v.toPrecision(3)));
const fmtPct = (v) => (v === null ? '-' : (v * 100).toFixed(0) + '%');
export const fmtTime = (ns) => ns === null || ns === undefined ? '-' : ns < 1e3 ? `${Math.round(ns)} ns` : ns < 1e6 ? `${(ns / 1e3).toFixed(1)} µs` : ns < 1e9 ? `${(ns / 1e6).toFixed(2)} ms` : `${(ns / 1e9).toFixed(2)} s`;
const fmtBytes = (b) => b === null || b === undefined ? '-' : b < 1024 ? `${b} B` : b < 1048576 ? `${(b / 1024).toFixed(1)} kB` : `${(b / 1048576).toFixed(2)} MB`;
const sizeStr = (s) => (Array.isArray(s) ? s.join('x') : String(s ?? ''));

function groupBy(rows, keyFn) {
  const m = new Map();
  for (const r of rows) { const k = keyFn(r); if (!m.has(k)) m.set(k, []); m.get(k).push(r); }
  return m;
}

// cols: [{id, label, v: row=>sortable value, f: value=>string, chart?: {unit, scale?, f?}}]
function sortableTable(cols, rows, { onReplay } = {}) {
  let sortId = null, dir = 1;
  const wrap = el('div', { class: 'scroll' });
  const draw = () => {
    const col = cols.find((c) => c.id === sortId);
    const data = col ? [...rows].sort((a, b) => {
      const x = col.v(a), y = col.v(b);
      if (x === y) return 0; if (x === null || x === undefined) return 1; if (y === null || y === undefined) return -1;
      return (x < y ? -1 : 1) * dir;
    }) : rows;
    const t = el('table');
    const tr = el('tr');
    for (const c of cols) {
      const th = el('th', { class: c.left ? 'l' : '', tabindex: 0, scope: 'col' }, c.label);
      if (c.id === sortId) th.setAttribute('aria-sort', dir > 0 ? 'ascending' : 'descending');
      const act = () => { if (sortId === c.id) dir = -dir; else { sortId = c.id; dir = 1; } draw(); };
      th.addEventListener('click', act);
      th.addEventListener('keydown', (e) => { if (e.key === 'Enter') act(); });
      tr.append(th);
    }
    t.append(el('thead', {}, tr));
    const tb = el('tbody');
    for (const r of data.slice(0, 500)) {
      tb.append(el('tr', {}, ...cols.map((c) => {
        const val = c.v(r);
        if (c.id === '_replay') return el('td', {}, r.trace ? el('a', { href: '#', onclick: (e) => { e.preventDefault(); onReplay(r.trace); } }, 'replay') : '');
        return el('td', { class: c.left ? 'l' : '' }, c.f ? c.f(val) : String(val ?? ''));
      })));
    }
    t.append(tb);
    wrap.replaceChildren(t);
  };
  draw();
  return wrap;
}

function chartsFor(cols, rows, labelFn) {
  const sel = el('select', { 'aria-label': 'Chart metric' });
  const cand = cols.filter((c) => c.chart);
  cand.forEach((c) => sel.append(el('option', { value: c.id }, c.label)));
  const holder = el('div', { class: 'charts' });
  const draw = () => {
    const c = cand.find((x) => x.id === sel.value);
    if (!c) { holder.replaceChildren(); return; }
    const scale = c.chart.scale || 1;
    const data = rows.map((r) => ({ label: labelFn(r), value: c.v(r) })).filter((d) => d.value !== null && d.value !== undefined)
      .map((d) => ({ ...d, value: d.value / scale })).sort((a, b) => b.value - a.value).slice(0, 25);
    holder.replaceChildren(data.length ? barChart(data, { title: c.label, unit: c.chart.unit, fmt: c.chart.f })
      : el('div', { class: 'empty' }, 'No data for this metric.'));
  };
  sel.addEventListener('change', draw); draw();
  return el('div', {}, el('label', { class: 'field' }, el('span', {}, 'Chart metric'), sel), holder);
}

function timeUnit(vals) { // pick ns/us/ms/s for a chart from the max value
  const m = Math.max(0, ...vals.filter((v) => v !== null));
  return m < 1e3 ? { unit: 'ns', scale: 1 } : m < 1e6 ? { unit: 'µs', scale: 1e3 } : m < 1e9 ? { unit: 'ms', scale: 1e6 } : { unit: 's', scale: 1e9 };
}

function emptyBox(msg) {
  return el('div', { class: 'empty' }, msg, el('br'), 'Generate results with ', el('code', {}, 'mazerunner bench benchmarks/configs/smoke.toml'), '.');
}

export function initResults(root, { onReplay }) {
  const sel = el('select', { 'aria-label': 'Results file' });
  const refresh = el('button', { type: 'button' }, 'Refresh');
  const body = el('div', { class: 'stack' });
  root.append(el('div', { class: 'stack' }, el('div', { class: 'card' }, el('div', { class: 'row', style: 'display:flex;gap:8px;align-items:center;flex-wrap:wrap' }, el('span', {}, 'Results file'), sel, refresh)), body));

  async function list() {
    try {
      const files = await getJSON('/api/results');
      sel.replaceChildren(...files.map((f) => el('option', { value: f.name }, `${f.name} (${new Date(f.mtime * 1000).toLocaleString()})`)));
      if (!files.length) { body.replaceChildren(emptyBox('No results files found in the results directory.')); return; }
      sel.value = files[files.length - 1].name; // newest-ish (sorted by name)
      await open(sel.value);
    } catch (e) { banner(`Cannot list results: ${e.message}`); }
  }
  async function open(name) {
    try { render((await getJSON('/api/results/' + encodeURIComponent(name))).rows); }
    catch (e) { banner(`Cannot load ${name}: ${e.message}`); }
  }

  function render(rows) {
    const trials = rows.filter((r) => r.kind === 'trial' && !r.error);
    const errors = rows.filter((r) => r.kind === 'trial' && r.error);
    const skips = rows.filter((r) => r.kind === 'skip');
    const runs = rows.filter((r) => r.kind === 'run');
    const parts = [];
    parts.push(el('div', { class: 'card' }, el('b', {}, `${trials.length} trials`),
      ` · ${skips.length} skipped · `, el('span', { class: errors.length ? 'err' : '' }, `${errors.length} errors`),
      runs.length ? el('div', { class: 'muted' }, runs.map((r) => r.name || r.config || r.id || '').filter(Boolean).join(', ')) : ''));
    if (errors.length) parts.push(el('details', { class: 'card' }, el('summary', {}, `Errors (${errors.length})`),
      el('pre', {}, errors.slice(0, 20).map((r) => `${r.topology} ${sizeStr(r.size)} ${r.generator}/${r.solver}: ${r.error}`).join('\n'))));
    if (skips.length) parts.push(el('details', { class: 'card' }, el('summary', {}, `Skipped combinations (${skips.length})`),
      el('pre', {}, skips.slice(0, 40).map((r) => JSON.stringify(r)).join('\n'))));
    if (!trials.length) { parts.push(emptyBox('This file has no trial rows.')); body.replaceChildren(...parts); return; }

    // --- generation: one entry per (topology,size,generator,braid), dedup trials across solvers
    const genRows = [];
    for (const [k, rs] of groupBy(trials, (r) => [r.topology, sizeStr(r.size), r.generator, r.braid ?? 0, r.trial ?? 0, r.seed].join('|'))) {
      genRows.push(rs[0]);
    }
    const gGroups = [...groupBy(genRows, (r) => [r.topology, sizeStr(r.size), r.generator, r.braid ?? 0].join('|')).values()].map((rs) => {
      const r0 = rs[0], texKeys = new Set(); rs.forEach((r) => Object.keys(g(r, 'gen.texture') || {}).forEach((k) => texKeys.add(k)));
      const tex = {}; for (const k of texKeys) tex[k] = mean(rs.map((r) => num(g(r, 'gen.texture.' + k))));
      return { label: `${r0.topology} ${sizeStr(r0.size)} ${r0.generator}${r0.braid ? ' braid ' + r0.braid : ''}`,
        topology: r0.topology, size: sizeStr(r0.size), generator: r0.generator, braid: r0.braid ?? 0, n: rs.length,
        time: median(rs.map((r) => num(g(r, 'gen.time_ns_median')))), peak: median(rs.map((r) => num(g(r, 'gen.peak_bytes')))),
        tex, trace: (rs.find((r) => r.trace) || {}).trace };
    });
    const texKeys = [...new Set(gGroups.flatMap((x) => Object.keys(x.tex)))].filter((k) => gGroups.some((x) => x.tex[k] !== null && typeof x.tex[k] === 'number'));
    const gt = timeUnit(gGroups.map((x) => x.time));
    const gcols = [
      { id: 'topology', label: 'Topology', left: 1, v: (r) => r.topology }, { id: 'size', label: 'Size', left: 1, v: (r) => r.size },
      { id: 'generator', label: 'Generator', left: 1, v: (r) => r.generator }, { id: 'braid', label: 'Braid', v: (r) => r.braid },
      { id: 'n', label: 'Trials', v: (r) => r.n },
      { id: 'time', label: 'Time (median)', v: (r) => r.time, f: fmtTime, chart: { unit: gt.unit, scale: gt.scale } },
      { id: 'peak', label: 'Peak memory', v: (r) => r.peak, f: fmtBytes, chart: { unit: 'kB', scale: 1024 } },
      ...texKeys.map((k) => ({ id: 'tex.' + k, label: k.replace(/_/g, ' '), v: (r) => r.tex[k], f: fmtNum, chart: { unit: k.replace(/_/g, ' ') } })),
      { id: '_replay', label: '', v: (r) => r.trace, left: 1 },
    ];
    parts.push(el('div', { class: 'card stack' }, el('h2', {}, 'Generation'), sortableTable(gcols, gGroups, { onReplay }),
      chartsFor(gcols, gGroups, (r) => r.label)));

    // --- solving
    const sGroups = [...groupBy(trials.filter((r) => r.solver && r.solve), (r) => [r.topology, sizeStr(r.size), r.solver, r.braid ?? 0].join('|')).values()].map((rs) => {
      const r0 = rs[0];
      return { label: `${r0.topology} ${sizeStr(r0.size)} ${r0.solver}${r0.braid ? ' braid ' + r0.braid : ''}`,
        topology: r0.topology, size: sizeStr(r0.size), solver: r0.solver, braid: r0.braid ?? 0, n: rs.length,
        success: rs.filter((r) => g(r, 'solve.outcome') === 'solved').length / rs.length,
        time: median(rs.map((r) => num(g(r, 'solve.time_ns_median')))),
        nodes: mean(rs.map((r) => num(g(r, 'solve.counters.nodes_expanded')))),
        steps: mean(rs.map((r) => num(g(r, 'solve.steps')))),
        optimality: mean(rs.map((r) => num(g(r, 'solve.optimality')))),
        pathLen: mean(rs.map((r) => num(g(r, 'solve.path_len')))),
        peak: median(rs.map((r) => num(g(r, 'solve.peak_bytes')))),
        trace: (rs.find((r) => r.trace) || {}).trace };
    });
    const st = timeUnit(sGroups.map((x) => x.time));
    const scols = [
      { id: 'topology', label: 'Topology', left: 1, v: (r) => r.topology }, { id: 'size', label: 'Size', left: 1, v: (r) => r.size },
      { id: 'solver', label: 'Solver', left: 1, v: (r) => r.solver }, { id: 'braid', label: 'Braid', v: (r) => r.braid }, { id: 'n', label: 'Trials', v: (r) => r.n },
      { id: 'success', label: 'Success', v: (r) => r.success, f: fmtPct, chart: { unit: 'success rate (0-1)', f: (v) => String(+v.toFixed(2)) } },
      { id: 'time', label: 'Time (median)', v: (r) => r.time, f: fmtTime, chart: { unit: st.unit, scale: st.scale } },
      { id: 'nodes', label: 'Nodes expanded', v: (r) => r.nodes, f: fmtNum, chart: { unit: 'nodes expanded' } },
      { id: 'steps', label: 'Steps', v: (r) => r.steps, f: fmtNum, chart: { unit: 'steps walked' } },
      { id: 'optimality', label: 'Optimality', v: (r) => r.optimality, f: (v) => (v === null ? '-' : v.toFixed(3)), chart: { unit: 'path / optimal (1 = optimal)' } },
      { id: 'pathLen', label: 'Path length', v: (r) => r.pathLen, f: fmtNum, chart: { unit: 'path length (cells)' } },
      { id: 'peak', label: 'Peak memory', v: (r) => r.peak, f: fmtBytes, chart: { unit: 'kB', scale: 1024 } },
      { id: '_replay', label: '', v: (r) => r.trace, left: 1 },
    ];
    if (sGroups.length) parts.push(el('div', { class: 'card stack' }, el('h2', {}, 'Solving'), sortableTable(scols, sGroups, { onReplay }),
      chartsFor(scols, sGroups, (r) => r.label)));

    // --- raw trials
    const tcols = [
      { id: 'topology', label: 'Topology', left: 1, v: (r) => r.topology }, { id: 'size', label: 'Size', left: 1, v: (r) => sizeStr(r.size) },
      { id: 'generator', label: 'Generator', left: 1, v: (r) => r.generator }, { id: 'solver', label: 'Solver', left: 1, v: (r) => r.solver },
      { id: 'trial', label: 'Trial', v: (r) => r.trial }, { id: 'seed', label: 'Seed', v: (r) => r.seed },
      { id: 'gt', label: 'Gen time', v: (r) => num(g(r, 'gen.time_ns_median')), f: fmtTime },
      { id: 'st', label: 'Solve time', v: (r) => num(g(r, 'solve.time_ns_median')), f: fmtTime },
      { id: 'out', label: 'Outcome', left: 1, v: (r) => g(r, 'solve.outcome') },
      { id: 'opt', label: 'Optimality', v: (r) => num(g(r, 'solve.optimality')), f: (v) => (v === null ? '-' : v.toFixed(3)) },
      { id: '_replay', label: '', v: (r) => r.trace, left: 1 },
    ];
    parts.push(el('details', { class: 'card' }, el('summary', {}, `All trials (${trials.length}${trials.length > 500 ? ', first 500 shown' : ''})`), sortableTable(tcols, trials, { onReplay })));
    body.replaceChildren(...parts);
  }

  sel.addEventListener('change', () => open(sel.value));
  refresh.addEventListener('click', list);
  list();
  return { reload: list };
}
