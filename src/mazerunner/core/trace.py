"""Step-by-step event tracing for live viewing and replay (PLAN §5).

Algorithms never print or draw. They emit small events into a Tracer:

    maze.tracer.emit("carve", a, b)       # done automatically by Maze.link()
    self.tracer.emit("frontier_add", cell)
    self.tracer.emit("visit", cell)

Benchmarks use NULL (a no-op). Timed runs are always untraced, and the trace is
captured on a separate run of the same seed, so viewing never skews results.
Hot loops may guard expensive argument building with `if tracer.enabled:`.

Event vocabulary (the viewer ignores unknown ops):
  generation : open_all (no cells: every adjacency linked; wall-adders start here),
               carve, uncarve, wall (alias of uncarve for wall-adders), current,
               frontier_add, frontier_remove, walk (random-walk step),
               erase (loop erasure; cells), set_merge (cells), phase {"label"}
  placement  : endpoints [start, goal]
  solving    : visit, frontier_add, frontier_remove, current, move (agent),
               mark (Trémaux; [here, toward], {"count"}), fill (dead-end filling),
               path (final route; all cells), phase {"label"}

Wire format (.trace.jsonl and live SSE share it):
  line 1  : {"type": "header", "version": 1, "topology": {...describe()},
             "geometry": {...}, "generator": ..., "solver": ..., "seed": ...}
  then    : [step, op, [cell indexes], data?]    one JSON array per event
  last    : {"type": "footer", "result": {...}}  (optional summary)
"""

from __future__ import annotations

import gzip
import json
import time
from pathlib import Path
from collections.abc import Callable
from typing import IO, Any

TRACE_VERSION = 1


class Tracer:
    """No-op base. `enabled` lets hot loops skip building event args."""

    enabled = False

    def emit(self, op: str, *cells: Any, **data: Any) -> None:
        pass


NULL = Tracer()


class _Encoding(Tracer):
    enabled = True

    def __init__(self, index: dict) -> None:
        self.index = index
        self.step = 0

    def encode(self, op: str, cells: tuple, data: dict) -> list:
        row = [self.step, op, [self.index[c] for c in cells]]
        if data:
            row.append(data)
        self.step += 1
        return row


class Recorder(_Encoding):
    """Collects encoded events in memory; `dump()` writes a .trace.jsonl."""

    def __init__(self, index: dict, header: dict | None = None) -> None:
        super().__init__(index)
        self.header = dict(header or {})
        self.events: list[list] = []
        self.footer: dict | None = None

    def emit(self, op: str, *cells: Any, **data: Any) -> None:
        self.events.append(self.encode(op, cells, data))

    def dump(self, fp: IO[str]) -> None:
        fp.write(json.dumps({"type": "header", "version": TRACE_VERSION, **self.header}) + "\n")
        for row in self.events:
            fp.write(json.dumps(row, separators=(",", ":")) + "\n")
        if self.footer is not None:
            fp.write(json.dumps({"type": "footer", **self.footer}, default=str) + "\n")


class StreamTracer(_Encoding):
    """Pushes each encoded event to `sink` as it happens (live mode).
    `delay` seconds between events lets humans watch."""

    def __init__(self, index: dict, sink: Callable[[list], None], delay: float = 0.0) -> None:
        super().__init__(index)
        self.sink, self.delay = sink, delay

    def emit(self, op: str, *cells: Any, **data: Any) -> None:
        self.sink(self.encode(op, cells, data))
        if self.delay:
            time.sleep(self.delay)


TRACE_SUFFIXES = (".trace.jsonl.gz", ".trace.jsonl")


def is_trace_name(name: str) -> bool:
    return name.endswith(TRACE_SUFFIXES)


def open_trace(path, mode: str = "rt") -> IO[str]:
    """Open a trace for text reading/writing; `.gz` paths are gzip-compressed."""
    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, mode, encoding="utf-8")
    return open(p, mode.replace("t", ""), encoding="utf-8")


def fill_geometry(header: dict) -> dict:
    """Traces may omit `geometry` (it is large and fully determined by the
    topology). Rebuild it from header["topology"] = {"name", "args"} when missing."""
    if not header.get("geometry"):
        from mazerunner.core.registry import load_all, topologies
        load_all()
        t = header["topology"]
        name, args = (t["name"], t.get("args", [])) if isinstance(t, dict) else (t, header.get("args", []))
        header["geometry"] = topologies.get(name).obj(*args).geometry()
    return header


def load_trace(path) -> tuple[dict, list[list], dict | None]:
    """Read a .trace.jsonl or .trace.jsonl.gz file; header geometry is always filled in."""
    with open_trace(path) as fp:
        header, events, footer = read_trace(fp)
    return fill_geometry(header), events, footer


def read_trace_header(path) -> dict:
    with open_trace(path) as fp:
        return json.loads(fp.readline())


def read_trace(fp: IO[str]) -> tuple[dict, list[list], dict | None]:
    header, events, footer = None, [], None
    for line in fp:
        if not line.strip():
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            if obj.get("type") == "header":
                header = obj
            elif obj.get("type") == "footer":
                footer = obj
        else:
            events.append(obj)
    if header is None:
        raise ValueError("trace has no header")
    return header, events, footer
