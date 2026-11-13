// Run tab (replay + live) and Race tab (several solvers, one maze, lanes).
import { Timeline } from './engine.js';
import { Watcher, el } from './watch.js';
import { RunForm } from './form.js';
import { postJSON, sse, banner } from './net.js';

function laneTimeline(data, key) {
  const evs = key ? data.generation.concat(data.solves[key].events) : data.generation;
  const tl = new Timeline(data.header, evs);
  if (key) tl.result = data.solves[key].result;
  return tl;
}

export function initRun(root, catalog) {
  const form = new RunForm(catalog, { live: true });
  const replay = el('button', { type: 'button', class: 'primary' }, 'Replay');
  const live = el('button', { type: 'button' }, 'Live');
  form.actions.append(replay, live);
  const w = new Watcher(root.appendChild(el('div', { class: 'stack' })));
  root.firstChild.prepend(form.root);
  let abort = null;
  const busy = (b) => { replay.disabled = live.disabled = b; };
  const title = (c) => `${c.generator}${c.solvers[0] ? ' / ' + c.solvers[0] : ''}`;

  replay.addEventListener('click', async () => {
    banner(''); if (abort) abort.abort(); busy(true);
    const cfg = form.config();
    try {
      const data = await postJSON('/api/run', cfg);
      const k = cfg.solvers[0];
      w.show([{ title: title(cfg), tl: laneTimeline(data, k) }],
        { status: `${cfg.topology} ${cfg.size.join('x')}, seed ${cfg.seed}` });
    } catch (e) { banner(`Run failed: ${e.message}`); }
    busy(false);
  });

  live.addEventListener('click', async () => {
    banner(''); if (abort) abort.abort();
    abort = new AbortController(); busy(true);
    const cfg = form.config(); let h = null, first = true, cur = null;
    const results = {};
    try {
      await sse('/api/live?' + form.liveQuery(), {
        header: (hd) => { h = w.showLive(hd, title(cfg)); },
        gen: (e) => h.push(e),
        'solve-start': (d) => { cur = d.solver; if (!first) h.push([0, '_reset', []]); first = false; },
        solve: (d) => h.push(d.e),
        'solve-end': (d) => { results[d.solver] = d.result; h.tl.result = d.result; },
        done: () => { h.finish(h.tl.result); },
        error: (d) => { banner(`Live run failed: ${d.error}`); if (h) h.finish(h.tl.result); },
      }, abort.signal);
    } catch (e) { if (e.name !== 'AbortError') banner(`Live run failed: ${e.message}`); }
    if (h && h.tl && w.player.following) h.finish(h.tl.result);
    busy(false);
  });
  return { form, replay: () => replay.click(), live: () => live.click() };
}

export function initRace(root, catalog) {
  const form = new RunForm(catalog, { multi: true });
  const go = el('button', { type: 'button', class: 'primary' }, 'Race');
  form.actions.append(go, el('small', { class: 'muted' }, 'Same maze for every solver; generation plays once, then all lanes advance in lockstep.'));
  const box = root.appendChild(el('div', { class: 'stack' }));
  box.prepend(form.root);
  const w = new Watcher(box);
  go.addEventListener('click', async () => {
    banner(''); go.disabled = true;
    const cfg = form.config();
    try {
      if (cfg.solvers.length < 1) throw new Error('pick at least one solver');
      const data = await postJSON('/api/run', cfg);
      const title = (k) => (catalog.solvers.find((s) => s.key === k) || { title: k }).title;
      w.show(cfg.solvers.map((k) => ({ title: title(k), tl: laneTimeline(data, k) })),
        { status: `${cfg.topology} ${cfg.size.join('x')}, ${cfg.generator}, seed ${cfg.seed}` });
    } catch (e) { banner(`Race failed: ${e.message}`); }
    go.disabled = false;
  });
  return { form, go: () => go.click() };
}
