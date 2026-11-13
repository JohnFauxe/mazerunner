"""Generic SVG renderer: any topology, using only topology.geometry() + maze.linked."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from xml.sax.saxutils import escape

from mazerunner.core.maze import Maze

STYLE = """
svg{color:#222;--mr-wall:currentColor;--mr-start:#16a34a;--mr-goal:#e53935;--mr-path:#0057ff;
--mr-cur:#fb8c00;--mr-fr:#26c6da;--mr-vis:#c5cae9;--mr-fill:#bdbdbd;--mr-mark:#ab47bc;--mr-walk:#ffd54f}
@media (prefers-color-scheme:dark){svg{color:#e6e6e6;--mr-vis:#3949ab;--mr-fill:#616161;--mr-walk:#8d6e00}}
.w{fill:none;stroke:var(--mr-wall,currentColor);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.p{fill:none;stroke:var(--mr-path,#0057ff);stroke-width:3;stroke-linecap:round;stroke-linejoin:round;opacity:.85}
""".strip()


def _fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def draw(geom: dict, linked: Callable[[int, int], bool], centers: list[tuple[float, float]], *,
         start: int | None = None, goal: int | None = None, path: list[int] | None = None,
         fills: dict[int, str] | None = None, current: int | None = None,
         cell_size: float = 20.0, margin: float | None = None, title: str | None = None,
         extra: str = "", wrap: bool = True) -> str:
    """Index-space drawing. `fills` maps cell index -> CSS colour (or var(--mr-x))."""
    m = cell_size / 2 if margin is None else margin
    k = cell_size

    def pt(p):
        return f"{_fmt(p[0] * k + m)} {_fmt(p[1] * k + m)}"

    def poly(pts, close=False):
        return "M" + " L".join(pt(p) for p in pts) + (" Z" if close else "")

    W, H = geom["width"] * k + 2 * m, geom["height"] * k + 2 * m
    layers: dict[str, list[int]] = {}
    for i, col in (fills or {}).items():
        layers.setdefault(col, []).append(i)
    if start is not None:
        layers.setdefault("var(--mr-start,#16a34a)", []).append(start)
    if goal is not None:
        layers.setdefault("var(--mr-goal,#e53935)", []).append(goal)
    cells = geom["cells"]
    parts = []
    for col, idxs in layers.items():
        d = " ".join(poly(cells[i], True) for i in idxs)
        parts.append(f'<path style="fill:{col}" d="{d}"/>')
    walls = [w for w in geom["walls"] if w["b"] is None or not linked(w["a"], w["b"])]
    if walls:
        parts.append(f'<path class="w" d="{" ".join(poly(w["pts"]) for w in walls)}"/>')
    if path and len(path) > 1:
        parts.append(f'<path class="p" d="{poly([centers[i] for i in path])}"/>')
    if current is not None:
        x, y = (float(v) for v in pt(centers[current]).split())
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(k * 0.25)}" '
                     f'style="fill:var(--mr-cur,#fb8c00)"/>')
    body = "".join(parts) + extra
    if not wrap:
        return body
    t = f"<title>{escape(title)}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(W)} {_fmt(H)}" '
            f'width="{_fmt(W)}" height="{_fmt(H)}">{t}<style>{STYLE}</style>{body}</svg>')


def render(maze: Maze, path=None, *, cell_size: float = 20.0,
           show_cells: dict | None = None, title: str | None = None) -> str:
    topo = maze.topology
    idx, cl = topo.index, topo.cell_list
    geom = topo.geometry()
    centers = [topo.position(c) for c in cl]
    return draw(
        geom, lambda a, b: maze.linked(cl[a], cl[b]), centers,
        start=None if maze.start is None else idx[maze.start],
        goal=None if maze.goal is None else idx[maze.goal],
        path=[idx[c] for c in path] if path else None,
        fills={idx[c]: v for c, v in (show_cells or {}).items()},
        cell_size=cell_size, title=title)


def save_svg(maze: Maze, path, out_path, **kw) -> None:
    Path(out_path).write_text(render(maze, path, **kw), encoding="utf-8")
