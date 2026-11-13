import { Timeline } from './engine.js';
import { Watcher, el } from './watch.js';
import { getJSON, banner } from './net.js';

const kb = (n) => n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1e3)) + ' kB';

export function initTraces(root) {
  const list = el('div');
  const refresh = el('button', { type: 'button' }, 'Refresh');
  const watchBox = el('div');
  root.append(el('div', { class: 'stack' }, el('div', { class: 'card' }, el('h2', {}, 'Recorded traces'), refresh, list), watchBox));
  const w = new Watcher(watchBox);

  async function load(name) {
    banner('');
    try {
      const d = await getJSON('/api/traces/' + encodeURIComponent(name));
      const tl = new Timeline(d.header, d.events);
      tl.result = d.footer && d.footer.result;
      const h = d.header;
      w.show([{ title: name, tl }], { status: `${name}: ${d.events.length.toLocaleString()} events` +
        (h.solver ? `, solver ${h.solver}` : '') });
    } catch (e) { banner(`Cannot load trace ${name}: ${e.message}`); }
  }
  async function reload() {
    try {
      const rows = await getJSON('/api/traces');
      if (!rows.length) {
        list.replaceChildren(el('div', { class: 'empty' }, 'No traces yet. Record one with ',
          el('code', {}, 'mazerunner record ...'), ' or use the Run tab.'));
        return;
      }
      const t = el('table'); t.append(el('thead', {}, el('tr', {}, ...['Name', 'Topology', 'Generator', 'Solver', 'Seed', 'Size', 'Modified', ''].map((h) => el('th', { class: h === 'Name' ? 'l' : '' }, h)))));
      const tb = el('tbody');
      for (const r of rows) {
        tb.append(el('tr', {}, el('td', {}, r.name), el('td', {}, r.topology ?? ''), el('td', {}, r.generator ?? ''),
          el('td', {}, r.solver ?? ''), el('td', {}, String(r.seed ?? '')), el('td', {}, kb(r.size)),
          el('td', {}, new Date(r.mtime * 1000).toLocaleString()),
          el('td', {}, el('button', { type: 'button', onclick: () => load(r.name), 'aria-label': 'Replay ' + r.name }, 'Replay'))));
      }
      t.append(tb); list.replaceChildren(el('div', { class: 'scroll' }, t));
    } catch (e) { banner(`Cannot list traces: ${e.message}`); }
  }
  refresh.addEventListener('click', reload);
  reload();
  return { load, reload };
}
