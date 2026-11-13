"""Terminal replay for square traces: ANSI cursor-home redraw, no curses."""

from __future__ import annotations

import sys
import time

from mazerunner.core.trace import read_trace
from mazerunner.render.animate import new_state, replay_states
from mazerunner.render.ascii import draw_grid

RESET = "\x1b[0m"
_BG = {"current": "\x1b[43;30m", "frontier": "\x1b[46;30m", "visited": "\x1b[44;37m",
       "path": "\x1b[42;30m", "filled": "\x1b[100;37m", "mark": "\x1b[45;37m",
       "walk": "\x1b[103;30m", "start": "\x1b[42;1;30m", "goal": "\x1b[41;1;37m"}


def frame_text(state: dict, rows: int, cols: int, *, step: int | None = None,
               total: int | None = None, color: bool = True, style: str = "box") -> str:
    """Pure renderer: grid for `state` plus a status line."""
    links = state["links"]
    ep = state["endpoints"] or (None, None)
    path = set(state["path"])

    def linked(r, c, d):
        i = r * cols + c
        j = i + 1 if d == "E" else i + cols
        return (i, j) in links

    def text(r, c):
        i = r * cols + c
        if i == state["current"]:
            kind, ch = "current", "@"
        elif i == ep[0]:
            kind, ch = "start", "S"
        elif i == ep[1]:
            kind, ch = "goal", "G"
        elif i in path:
            kind, ch = "path", "·"
        elif i in state["frontier"]:
            kind, ch = "frontier", "+"
        elif i in state["marks"]:
            kind, ch = "mark", str(min(state["marks"][i], 9))
        elif i in state["filled"]:
            kind, ch = "filled", "x"
        elif i in state["walk"]:
            kind, ch = "walk", "~"
        elif i in state["visited"]:
            kind, ch = "visited", "."
        else:
            return "   "
        s = f" {ch} "
        return f"{_BG[kind]}{s}{RESET}" if color else s

    grid = draw_grid(rows, cols, linked, text, style)
    status = (f"step {step if step is not None else '-'}/{total if total is not None else '-'}"
              f"  phase: {state['phase'] or '-'}  links: {len(links)}"
              f"  frontier: {len(state['frontier'])}  visited: {len(state['visited'])}"
              f"  path: {len(state['path'])}")
    return f"{grid}\n{status}"


def play(trace_path, *, fps: float = 30.0, every: int = 1, out=None, sleep=time.sleep) -> None:
    out = sys.stdout if out is None else out
    with open(trace_path, encoding="utf-8") as fp:
        header, events, _ = read_trace(fp)
    topo = header.get("topology")
    name = topo.get("name") if isinstance(topo, dict) else topo
    args = topo.get("args", []) if isinstance(topo, dict) else header.get("args", [])
    if name != "square":
        out.write(f"Terminal replay supports square mazes only (got {name!r}); "
                  "use `mazerunner serve` for other topologies.\n")
        return
    rows, cols = args[0], (args[1] if len(args) > 1 else args[0])
    color = bool(getattr(out, "isatty", lambda: False)())
    every, total, delay = max(1, every), len(events), 1.0 / fps if fps > 0 else 0.0
    out.write("\x1b[2J\x1b[?25l" if color else "")
    try:
        last = None
        for k, (step, st) in enumerate(replay_states(header, events), 1):
            last = step
            if k % every == 0 or k == total:
                out.write(("\x1b[H" if color else "") + frame_text(
                    st, rows, cols, step=k, total=total, color=color)
                    + ("\x1b[J\n" if color else "\n"))
                out.flush()
                if delay and k != total:
                    sleep(delay)
        if last is None:
            out.write(frame_text(new_state(), rows, cols, step=0, total=0, color=color) + "\n")
    except KeyboardInterrupt:
        out.write("\ninterrupted\n")
    finally:
        out.write("\x1b[?25h" if color else "")
        out.flush()
