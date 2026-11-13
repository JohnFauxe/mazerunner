"""Offline replay of traces: state reconstruction, SVG frames, animated SVG."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from mazerunner.core.trace import load_trace
from mazerunner.render import svg as _svg


def new_state() -> dict:
    return {"links": set(), "current": None, "frontier": set(), "visited": set(),
            "path": [], "marks": {}, "filled": set(), "endpoints": None,
            "phase": "", "walk": [], "merged": []}


def all_adjacencies(header: dict) -> set[tuple[int, int]]:
    """Every inner wall pair from the trace geometry (target of "open_all")."""
    walls = (header.get("geometry") or {}).get("walls", [])
    return {(min(w["a"], w["b"]), max(w["a"], w["b"])) for w in walls if w.get("b") is not None}


def apply_event(state: dict, op: str, cells: list, data: dict | None = None,
                header: dict | None = None) -> None:
    data = data or {}
    if op == "open_all":
        state["links"] = all_adjacencies(header or {})
    elif op == "carve" and len(cells) >= 2:
        state["links"].add((min(cells[0], cells[1]), max(cells[0], cells[1])))
    elif op in ("uncarve", "wall") and len(cells) >= 2:
        state["links"].discard((min(cells[0], cells[1]), max(cells[0], cells[1])))
    elif op == "current":
        state["current"] = cells[0] if cells else None
    elif op == "frontier_add":
        state["frontier"].update(cells)
    elif op == "frontier_remove":
        state["frontier"].difference_update(cells)
    elif op == "walk":
        if cells:
            state["walk"].append(cells[0])
            state["current"] = cells[0]
    elif op == "erase":
        gone = set(cells)
        state["walk"] = [c for c in state["walk"] if c not in gone]
    elif op == "set_merge":
        state["merged"] = list(cells)
    elif op == "visit":
        state["visited"].update(cells)
    elif op == "move":
        if cells:
            state["current"] = cells[-1]
    elif op == "mark":
        if cells:
            state["marks"][cells[0]] = data.get("count", state["marks"].get(cells[0], 0) + 1)
    elif op == "fill":
        state["filled"].update(cells)
    elif op == "path":
        state["path"] = list(cells)
    elif op == "endpoints":
        if len(cells) >= 2:
            state["endpoints"] = (cells[0], cells[1])
    elif op == "phase":
        label = str(data.get("label", ""))
        state["phase"] = label
        state["walk"] = []
        if label.startswith("solve"):
            state["visited"].clear()
            state["frontier"].clear()
            state["current"] = None
    # unknown ops are ignored


def replay_states(header: dict, events: Iterable[list]) -> Iterator[tuple[int, dict]]:
    """Yield (step, state) after each event. The state dict is mutated in place
    between yields: copy what you need to keep."""
    state = new_state()
    for ev in events:
        step, op = ev[0], ev[1]
        apply_event(state, op, ev[2] if len(ev) > 2 else [], ev[3] if len(ev) > 3 else None,
                    header)
        yield step, state


# --- SVG frames -------------------------------------------------------------

def _topology(header: dict):
    from mazerunner.core import registry
    try:
        registry.load_all()
    except Exception:
        import mazerunner.topologies  # noqa: F401
    t = header["topology"]
    name, args = (t["name"], t.get("args", [])) if isinstance(t, dict) else (t, header.get("args", []))
    args = [tuple(a) if isinstance(a, list) else a for a in args]
    return registry.topologies.get(name).obj(*args)


def _geometry(header: dict):
    g = header.get("geometry")
    topo = None
    if not (g and "cells" in g and "walls" in g):
        topo = _topology(header)
        g = topo.geometry()
    centers = None
    if topo is not None:
        centers = [topo.position(c) for c in topo.cell_list]
    else:
        centers = [(sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
                   for poly in g["cells"]]
    return g, centers


def _fills(state: dict) -> dict[int, str]:
    f: dict[int, str] = {}
    for c in state["visited"]:
        f[c] = "var(--mr-vis,#c5cae9)"
    for c in state["filled"]:
        f[c] = "var(--mr-fill,#bdbdbd)"
    for c in state["marks"]:
        f[c] = "var(--mr-mark,#ab47bc)"
    for c in state["walk"]:
        f[c] = "var(--mr-walk,#ffd54f)"
    for c in state["frontier"]:
        f[c] = "var(--mr-fr,#26c6da)"
    return f


def _frame_body(geom, centers, state, cell_size) -> str:
    links = state["links"]
    ep = state["endpoints"] or (None, None)
    return _svg.draw(
        geom, lambda a, b: (min(a, b), max(a, b)) in links, centers,
        start=ep[0], goal=ep[1], path=state["path"] or None, fills=_fills(state),
        current=state["current"], cell_size=cell_size, wrap=False)


def _sample(events: list, every: int, max_frames: int | None) -> list[dict]:
    """Return list of state snapshots (deep enough copies) at sampled steps."""
    every = max(1, every)
    n = len(events)
    if max_frames and n // every + 1 > max_frames:
        every = -(-n // (max_frames - 1))
    snaps = []
    for k, (_, st) in enumerate(replay_states({}, events), 1):
        if k % every == 0 or k == n:
            snaps.append({key: (v.copy() if hasattr(v, "copy") else v) for key, v in st.items()})
    return snaps


def to_svg_frames(header: dict, events: list[list], every: int = 1, *,
                  cell_size: float = 12.0, max_frames: int | None = None) -> list[str]:
    geom, centers = _geometry(header)
    m = cell_size / 2
    W, H = geom["width"] * cell_size + 2 * m, geom["height"] * cell_size + 2 * m
    frames = []
    for st in _sample(events, every, max_frames) or [new_state()]:
        frames.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_svg._fmt(W)} {_svg._fmt(H)}">'
            f'<style>{_svg.STYLE}</style>{_frame_body(geom, centers, st, cell_size)}</svg>')
    return frames


def write_animated_svg(trace_path, out_path, fps: float = 15.0, every: int = 1, *,
                       cell_size: float = 12.0, max_frames: int = 300) -> int:
    """Write one self-contained looping SMIL-animated SVG. Returns frame count."""
    header, events, _ = load_trace(trace_path)
    geom, centers = _geometry(header)
    snaps = _sample(events, every, max_frames) or [new_state()]
    n = len(snaps)
    dur = n / fps
    m = cell_size / 2
    W, H = geom["width"] * cell_size + 2 * m, geom["height"] * cell_size + 2 * m
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_svg._fmt(W)} {_svg._fmt(H)}">'
           f'<style>{_svg.STYLE}</style>']
    for k, st in enumerate(snaps):
        a, b = k / n, (k + 1) / n
        if k == 0:
            vals, keys = "visible;hidden;hidden", f"0;{b:.5f};1"
        elif k == n - 1:
            # hold the final frame for a moment at the end, then loop
            vals, keys = "hidden;visible;visible", f"0;{a:.5f};1"
        else:
            vals, keys = "hidden;visible;hidden;hidden", f"0;{a:.5f};{b:.5f};1"
        out.append(f'<g visibility="hidden"><animate attributeName="visibility" calcMode="discrete" '
                   f'dur="{dur:.3f}s" repeatCount="indefinite" values="{vals}" keyTimes="{keys}"/>'
                   f'{_frame_body(geom, centers, st, cell_size)}</g>')
    out.append("</svg>")
    Path(out_path).write_text("".join(out), encoding="utf-8")
    return n
