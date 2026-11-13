// Canvas renderer. Draws purely from header.geometry (polygons + wall polylines).

let theme = null, themeKey = '';
function readTheme() {
  const dark = matchMedia('(prefers-color-scheme: dark)').matches;
  if (theme && themeKey === String(dark)) return theme;
  const cs = getComputedStyle(document.documentElement);
  const v = (n) => cs.getPropertyValue(n).trim();
  const heat = [];
  for (let i = 0; i < 64; i++) {
    const t = i / 63;
    heat.push(`hsl(${Math.round(215 - 175 * t)} 65% ${dark ? 30 + 22 * t : 80 - 18 * t}%)`);
  }
  themeKey = String(dark);
  theme = { cell: v('--c-cell'), wall: v('--c-wall'), frontier: v('--c-frontier'), current: v('--c-current'),
    walk: v('--c-walk'), fill: v('--c-fill'), path: v('--c-path'), agent: v('--c-agent'),
    mark1: v('--c-mark1'), mark2: v('--c-mark2'), start: v('--c-start'), goal: v('--c-goal'), heat };
  return theme;
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { theme = null; });

export class MazeView {
  constructor(canvas, geo) {
    this.canvas = canvas; this.geo = geo; this.ctx = canvas.getContext('2d');
    this.last = null;
    const wrap = canvas.parentElement;
    wrap.style.maxWidth = `calc(72vh * ${geo.width / geo.height})`;
    canvas.style.aspectRatio = `${geo.width} / ${geo.height}`;
    this.ro = new ResizeObserver(() => { this.resize(); if (this.last) this.draw(this.last); });
    this.ro.observe(canvas);
    this.resize();
  }
  destroy() { this.ro.disconnect(); }
  resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(1, Math.round(this.canvas.clientWidth * dpr));
    const h = Math.max(1, Math.round(this.canvas.clientHeight * dpr));
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
  }
  draw(st) {
    this.last = st;
    const { ctx, geo, canvas } = this;
    const T = readTheme();
    const pad = 8 * (window.devicePixelRatio || 1);
    const sc = Math.min((canvas.width - 2 * pad) / geo.width, (canvas.height - 2 * pad) / geo.height);
    const ox = (canvas.width - geo.width * sc) / 2, oy = (canvas.height - geo.height * sc) / 2;
    const X = (x) => ox + x * sc, Y = (y) => oy + y * sc;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';

    // cell fills
    const cur = st.pos || 1;
    const fillCell = (i, color) => {
      const p = geo.polys[i];
      ctx.fillStyle = color; ctx.beginPath();
      ctx.moveTo(X(p[0][0]), Y(p[0][1]));
      for (let k = 1; k < p.length; k++) ctx.lineTo(X(p[k][0]), Y(p[k][1]));
      ctx.closePath(); ctx.fill();
    };
    const n = geo.n;
    for (let i = 0; i < n; i++) {
      let c = null;
      if (st.fill[i]) c = T.fill;
      else if (st.walk[i]) c = T.walk;
      else if (st.fr[i]) c = T.frontier;
      else if (st.mk[i]) c = st.mk[i] > 1 ? T.mark2 : T.mark1;
      else if (st.vis[i]) c = T.heat[Math.min(63, Math.floor(63 * st.vis[i] / cur))];
      if (c) fillCell(i, c);
    }
    const cellPx = geo.cellSize * sc;
    // agent trail
    if (st.trail.length > 1) {
      ctx.strokeStyle = T.agent; ctx.globalAlpha = 0.45; ctx.lineWidth = Math.max(1, cellPx * 0.18);
      ctx.beginPath();
      const from = Math.max(0, st.trail.length - 4000);
      for (let k = from; k < st.trail.length; k++) {
        const c = geo.centroids[st.trail[k]];
        if (k === from) ctx.moveTo(X(c[0]), Y(c[1])); else ctx.lineTo(X(c[0]), Y(c[1]));
      }
      ctx.stroke(); ctx.globalAlpha = 1;
    }
    // walls: drawn when outer (b null) or not open
    ctx.strokeStyle = T.wall; ctx.lineWidth = Math.max(1, Math.min(4, cellPx * 0.1));
    ctx.beginPath();
    const walls = geo.walls;
    for (let i = 0; i < walls.length; i++) {
      if (st.open[i]) continue;
      const pts = walls[i].pts;
      ctx.moveTo(X(pts[0][0]), Y(pts[0][1]));
      for (let k = 1; k < pts.length; k++) ctx.lineTo(X(pts[k][0]), Y(pts[k][1]));
    }
    ctx.stroke();
    // final path
    if (st.path && st.path.length) {
      ctx.strokeStyle = T.path; ctx.lineWidth = Math.max(2, cellPx * 0.3);
      ctx.beginPath();
      st.path.forEach((c, k) => {
        const q = geo.centroids[c];
        if (k === 0) ctx.moveTo(X(q[0]), Y(q[1])); else ctx.lineTo(X(q[0]), Y(q[1]));
      });
      ctx.stroke();
    }
    // current cell / agent
    if (st.cur >= 0) {
      const q = geo.centroids[st.cur];
      ctx.fillStyle = T.current; ctx.beginPath();
      ctx.arc(X(q[0]), Y(q[1]), Math.max(2.5, cellPx * 0.28), 0, 6.2832); ctx.fill();
    }
    // endpoints
    const marker = (c, color, label) => {
      if (c < 0) return;
      const q = geo.centroids[c], r = Math.max(5, cellPx * 0.42);
      ctx.fillStyle = color; ctx.beginPath(); ctx.arc(X(q[0]), Y(q[1]), r, 0, 6.2832); ctx.fill();
      if (r >= 7) {
        ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.round(r * 1.1)}px system-ui`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, X(q[0]), Y(q[1]) + 1);
      }
    };
    marker(st.start, T.start, 'S'); marker(st.goal, T.goal, 'G');
  }
}
