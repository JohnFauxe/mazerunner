// Tiny inline-SVG horizontal bar chart (no libraries).
const NS = 'http://www.w3.org/2000/svg';
const s = (tag, attrs = {}, text) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
};

export function niceMax(v) {
  if (!(v > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(v)), f = v / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
}

// data: [{label, value}], opts: {title, unit, fmt}
export function barChart(data, { title = '', unit = '', fmt = (v) => String(+v.toPrecision(3)) } = {}) {
  const rowH = 22, left = 170, right = 60, top = 34, bottom = 38, W = 560;
  const H = top + bottom + rowH * data.length;
  const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `${title} (${unit})`, width: '100%' });
  svg.append(s('title', {}, `${title} (${unit})`));
  const max = niceMax(Math.max(0, ...data.map((d) => d.value)));
  const pw = W - left - right, x = (v) => left + (v / max) * pw;
  svg.append(s('text', { x: 6, y: 16, 'font-weight': '600' }, title));
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4, px = x(v);
    svg.append(s('line', { x1: px, x2: px, y1: top - 4, y2: H - bottom + 2, class: 'grid' }));
    svg.append(s('text', { x: px, y: H - bottom + 15, 'text-anchor': 'middle', class: 'sub' }, fmt(v)));
  }
  svg.append(s('line', { x1: left, x2: left, y1: top - 4, y2: H - bottom + 2, class: 'axis' }));
  svg.append(s('text', { x: left + pw / 2, y: H - 6, 'text-anchor': 'middle', class: 'sub' }, unit));
  data.forEach((d, i) => {
    const y = top + i * rowH;
    const lab = d.label.length > 26 ? d.label.slice(0, 25) + '…' : d.label;
    const t = s('text', { x: left - 6, y: y + 14, 'text-anchor': 'end' }, lab);
    t.append(s('title', {}, d.label)); svg.append(t);
    const bar = s('rect', { x: left, y: y + 3, width: Math.max(1, x(d.value) - left), height: rowH - 7, rx: 3, fill: 'var(--accent)', opacity: 0.85 });
    bar.append(s('title', {}, `${d.label}: ${fmt(d.value)} ${unit}`));
    svg.append(bar);
    svg.append(s('text', { x: x(d.value) + 4, y: y + 14, class: 'sub' }, fmt(d.value)));
  });
  return svg;
}
