"""Step-by-step event tracing for live viewing and replay (PLAN §5).

Algorithms never print or draw. They emit small events into a Tracer:

    maze.tracer.emit("carve", a, b)       # done automatically by Maze.link()
    tracer.emit("frontier_add", cell)
    tracer.emit("visit", cell)

Benchmarks use NULL (a no-op). Timed runs are always untraced, and the trace is
captured on a separate run of the same seed, so viewing never skews results.

Event vocabulary (extend when needed; the viewer ignores unknown ops):
  generation : carve, uncarve, wall (wall-adders), current, frontier_add,
               frontier_remove, walk (random-walk step), erase (loop erasure),
               set_merge (Kruskal/Eller), phase (free-text label)
  solving    : visit, frontier_add, frontier_remove, current, move (agent),
               mark (Trémaux), fill (dead-end filling), path (final route)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import IO, Any

from mazerunner.core.topology import Cell


class Tracer:
    """No-op base. `enabled` lets hot loops skip building event args."""

    enabled = False

    def emit(self, op: str, *cells: Cell, **data: Any) -> None:
        pass


NULL = Tracer()


class Recorder(Tracer):
    """Collects events in memory; dump to a .trace.jsonl for replay."""

    enabled = True

    def __init__(self, header: dict | None = None) -> None:
        self.header = header or {}
        self.events: list[tuple] = []

    def emit(self, op: str, *cells: Cell, **data: Any) -> None:
        self.events.append((len(self.events), op, cells, data or None))

    def dump(self, fp: IO[str], cell_index: dict[Cell, int]) -> None:
        """Write header line, then one compact array per event: [step, op, [cell ids], data?].
        Cells are written as integer indexes into header.geometry.cells."""
        fp.write(json.dumps({"type": "header", **self.header}) + "\n")
        for step, op, cells, data in self.events:
            row = [step, op, [cell_index[c] for c in cells]]
            if data:
                row.append(data)
            fp.write(json.dumps(row) + "\n")


class StreamTracer(Tracer):
    """Pushes each event to a sink as it happens (live mode, e.g. SSE/WebSocket).
    `delay` throttles so humans can watch. Placeholder (phase 2)."""

    enabled = True

    def __init__(self, sink: Callable[[tuple], None], delay: float = 0.0) -> None:
        self.sink, self.delay, self.step = sink, delay, 0

    def emit(self, op: str, *cells: Cell, **data: Any) -> None:
        raise NotImplementedError("live streaming: phase 2")
