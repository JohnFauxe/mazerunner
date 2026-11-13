import { getJSON, banner } from './net.js';
import { initRun, initRace } from './run.js';
import { initTraces } from './traces.js';
import { initResults } from './results.js';

const tabs = [...document.querySelectorAll('#tabs button')];
const views = Object.fromEntries(tabs.map((b) => [b.dataset.tab, document.getElementById('view-' + b.dataset.tab)]));
const inited = {};
let catalog = null, traces = null;

function select(name) {
  for (const b of tabs) b.setAttribute('aria-selected', String(b.dataset.tab === name));
  for (const [k, v] of Object.entries(views)) v.hidden = k !== name;
  try { history.replaceState(null, '', '#' + name); } catch { /* ignore */ }
}
tabs.forEach((b) => b.addEventListener('click', () => select(b.dataset.tab)));

const help = document.getElementById('help'), helpBtn = document.getElementById('help-btn');
const toggleHelp = (on = help.hidden) => { help.hidden = !on; helpBtn.setAttribute('aria-expanded', String(on)); };
helpBtn.addEventListener('click', () => toggleHelp());
document.addEventListener('keydown', (e) => {
  if (e.key === '?' && !/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) toggleHelp();
  if (e.key === 'Escape') toggleHelp(false);
});

async function boot() {
  initTraces0();
  try { catalog = await getJSON('/api/catalog'); }
  catch (e) { banner(`Cannot load the algorithm catalog: ${e.message}`); return; }
  const run = initRun(views.run, catalog), race = initRace(views.race, catalog);
  const h = location.hash.slice(1);
  if (views[h]) select(h);
  const q = new URLSearchParams(location.search), mode = q.get('mode');
  if (q.get('trace')) { select('traces'); await traces.load(q.get('trace')); }
  else if (mode === 'race') { race.form.prefill(q); select('race'); race.go(); }
  else if (mode === 'live' || mode === 'replay') { run.form.prefill(q); select('run'); (mode === 'live' ? run.live : run.replay)(); }
}

function initTraces0() {
  traces = initTraces(views.traces);
  initResults(views.results, {
    onReplay: async (path) => {
      const name = String(path).split(/[\\/]/).pop();
      select('traces');
      await traces.load(name);
    },
  });
}
boot();
